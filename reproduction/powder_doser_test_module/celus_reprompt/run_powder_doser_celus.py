"""CELUS-oriented reprompt of the PCBSchemaGen loop for the powder-doser board.

This is the same feedback loop as ``../run_powder_doser.py`` (LLM -> SKiDL ->
syntax / ERC verification -> netlist + SVG render -> retry-with-feedback), but
the prompt is extended to make the generated design carry the metadata a
component-driven board-synthesis tool such as **CELUS** needs to turn the
schematic into a board:

* a real **manufacturer part number (MPN)**, **manufacturer**, and
  **datasheet** URL on every component (written as SKiDL part *fields*, which
  flow straight into the KiCad netlist and so into any BOM/CUBO export);
* a **real KiCad footprint** per component (module / connector / passive
  package) instead of the SOT-23 placeholder used in the first run;
* an explicit **functional-block tag** on each component (the block-diagram
  grouping CELUS asks for at project start).

After a verification pass the script *derives* two extra artifacts directly
from the resulting netlist (no extra LLM trust required):

* ``powder_doser_celus_bom.csv`` - consolidated BOM (ref, qty, value, MPN,
  manufacturer, footprint, datasheet, block);
* ``powder_doser_celus_blocks.json`` - the functional block diagram (blocks,
  their components, and the typed inter-block interfaces inferred from the
  net names).

Usage::

    export OPENAI_API_KEY="$MY_ANTHROPIC_API_KEY"
    KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols \
      python3 run_powder_doser_celus.py --model claude-sonnet-4-6 \
      --base_url https://api.anthropic.com/v1/ --num_of_retry 4
"""

import argparse
import ast
import csv
import json
import os
import re
import subprocess
import sys
import time

from openai import OpenAI

HERE = os.path.dirname(os.path.abspath(__file__))

# The board specification + net contract is identical to the first run; only
# the *deliverable* requirements (metadata) below are new.
TASK_DESCRIPTION = """\
Design the PCB schematic for the powder-doser single-module bench rig
(vertical-cloud-lab/powder-doser PR #61). A single Raspberry Pi Pico W drives
ONE powder-doser channel: dispensing-angle servo, tapping solenoid, vibration
(ERM), and auger rotation (stepper). Power comes from a 12 V barrel-jack brick,
stepped to 5 V by a Pololu D24V22F5 buck; the Pico's on-board LDO supplies 3V3.

Components (reference designators are fixed):
- U2  Raspberry Pi Pico W            pins: GP0,GP1,GP4,GP5,GP10,GP11,GP14,GP15, 3V3, VSYS, GND
- U1  Pololu D24V22F5 buck (5V)      pins: VIN, GND, VOUT
- U3  Adafruit DRV2605L haptic       pins: VIN, GND, SDA, SCL, EN, IN_TRIG, OUT+, OUT-
- M1  10mm ERM coin motor            pins: +, -
- U4  Adafruit DRV8871 motor driver  pins: VM, GND, IN1, IN2, OUT1, OUT2
- SOL1 JF-0530B 5V solenoid          pins: +, -
- U5  Pololu Tic T500 stepper ctrl   pins: VIN, GND, RX, TX, ERR, A1, A2, B1, B2
- SR1 Pololu #3776 shunt regulator   pins: +, -
- M2  NEMA-11 bipolar stepper        pins: A1, A2, B1, B2
- M3  HD-1810MG hobby servo          pins: +5V, GND, SIG
- J1  12V barrel-jack PSU            pins: +, -
- C1  100uF/25V (12V bulk), C2 100uF/10V (5V bulk), C3 100uF/25V (Tic VIN bulk)

Required nets (this is the contract between schematic and firmware):
- +12V : J1.+, U1.VIN, U4.VM, U5.VIN, SR1.+, C1.+, C3.+
- +5V  : U1.VOUT, U2.VSYS, M3.+5V, C2.+
- +3V3 : U2.3V3, U3.VIN          (the Tic T500 makes its own logic supply from VIN)
- GND  : J1.-, U1.GND, U2.GND, U3.GND, U4.GND, U5.GND, SR1.-, M3.GND, C1.-, C2.-, C3.-
- I2C_SDA   : U2.GP0  -> U3.SDA
- I2C_SCL   : U2.GP1  -> U3.SCL
- STP_TX    : U2.GP4  -> U5.RX   (Pico UART1 TX -> Tic RX)
- STP_RX    : U2.GP5  <- U5.TX   (Pico UART1 RX <- Tic TX)
- SOL_IN1   : U2.GP10 -> U4.IN1
- SOL_IN2   : U2.GP11 -> U4.IN2
- HAPT_EN   : U2.GP14 -> U3.EN and U3.IN_TRIG
- SERVO_SIG : U2.GP15 -> M3.SIG
- STP_A1/A2 : U5.A1/A2 <-> M2.A1/A2
- STP_B1/B2 : U5.B1/B2 <-> M2.B1/B2
- VIB_A/B   : U3.OUT+/OUT- <-> M1.+/-
- SOL_A/B   : U4.OUT1/OUT2 <-> SOL1.+/-
- U5.ERR is left unconnected (optional fault line).
"""

# New, CELUS-oriented deliverable requirements.
CELUS_REQUIREMENTS = """\
This design will be imported into a component-driven board-synthesis tool
(CELUS). CELUS needs, for every component, the information that lets it match a
real orderable part (a "CUBO") and place a real footprint. Therefore, in
addition to the connectivity above, every component instance MUST carry these
SKiDL part fields (set them with `part.fields[...] = "..."` after instantiating
the part):

  - "MPN"          : the manufacturer part number of a real, orderable part.
  - "Manufacturer" : the manufacturer / vendor name.
  - "Datasheet"    : a datasheet or product-page URL.
  - "Block"        : the functional block this part belongs to. Use exactly one
                     of: POWER, MCU, HAPTIC, MOTOR_DRIVE, STEPPER_DRIVE, SERVO,
                     ACTUATOR, BULK_DECOUPLE.

Use the real, known parts where they are named in the spec, e.g.:
  - U2 Raspberry Pi Pico W -> MPN "SC0918", Manufacturer "Raspberry Pi".
  - U1 Pololu D24V22F5      -> MPN "2858",   Manufacturer "Pololu".
  - U3 Adafruit DRV2605L    -> MPN "2305",   Manufacturer "Adafruit".
  - U4 Adafruit DRV8871     -> MPN "3190",   Manufacturer "Adafruit".
  - U5 Pololu Tic T500      -> MPN "3134",   Manufacturer "Pololu".
  - SR1 Pololu shunt reg    -> MPN "3776",   Manufacturer "Pololu".
  - J1 barrel jack          -> a CUI PJ-002A or equivalent.
  - C1/C2/C3 100uF caps     -> a real electrolytic MPN at the stated voltage.
For the servo (M3 HD-1810MG), solenoid (SOL1 JF-0530B), ERM (M1), and stepper
(M2 NEMA-11), use the named part as the MPN with its vendor.

Use a REAL KiCad footprint for each part (not a generic SOT-23 placeholder):
breakout modules -> a pin-header / module footprint (e.g.
`Connector_PinHeader_2.54mm:PinHeader_1x..._P2.54mm_Vertical`); the barrel jack
-> `Connector_BarrelJack:BarrelJack_CUI_PJ-002A`; the electrolytic caps ->
`Capacitor_THT:CP_Radial_D6.3mm_P2.50mm`; motors / solenoid -> a 1x2 (or 1x4 for
the stepper / 1x3 for the servo) pin header. Pick the header pin-count to match
the part's pin count.
"""

LIBRARY_GUIDE = """\
These microcontroller-breakout parts are NOT in PCBSchemaGen's `test` library,
so define each one inline using SKiDL's SKIDL tool. Use this exact helper and
pin functions so ERC and netlist/SVG generation succeed:

```python
from skidl import (Part, Pin, Net, ERC, TEMPLATE, SKIDL,
                   generate_netlist, generate_svg, set_default_tool, KICAD9)
set_default_tool(KICAD9)

def make(name, ref, pins, footprint, mpn, mfr, datasheet, block):
    t = Part(tool=SKIDL, name=name, ref_prefix=ref[0], dest=TEMPLATE,
             footprint=footprint)
    for num, pname, func in pins:
        t += Pin(num=num, name=pname, func=func)
    p = t(ref=ref)
    p.fields["MPN"] = mpn
    p.fields["Manufacturer"] = mfr
    p.fields["Datasheet"] = datasheet
    p.fields["Block"] = block
    return p
```

Pin function constants: `Pin.types.PWRIN`, `Pin.types.PWROUT`,
`Pin.types.INPUT`, `Pin.types.OUTPUT`, `Pin.types.BIDIR`, `Pin.types.PASSIVE`.
Power inputs (VIN/VM/GND/VSYS) should be PWRIN; a regulator/jack/Pico-3V3 output
should be PWROUT; motor/solenoid/cap leads PASSIVE; GPIO BIDIR. Connect nets
with `Net("NAME") += partA["PINNAME"], partB["PINNAME"]`. End the script with
`ERC()`, then `generate_netlist()`, then `generate_svg()`.
"""

SYSTEM = "You are a PCB design expert using SKiDL (Python)."

PROMPT = f"""{TASK_DESCRIPTION}

{CELUS_REQUIREMENTS}

{LIBRARY_GUIDE}

Output a single, complete, self-contained Python (SKiDL) script inside one
```python ... ``` code block that builds every net above exactly, sets the four
required fields (MPN, Manufacturer, Datasheet, Block) on every component, uses a
real footprint per part, calls ERC(), then generate_netlist() and
generate_svg(). Do not add components or nets that are not listed.
"""

VERIFY_FOOTER = """

# --- injected verification / render (PCBSchemaGen pipeline) ---
import sys as _sys
try:
    ERC()
except Exception as _e:
    print(f"VERIFY_ERROR ERC: {_e}"); _sys.exit(3)
try:
    generate_netlist()
except Exception as _e:
    print(f"VERIFY_ERROR NETLIST: {_e}"); _sys.exit(4)
try:
    generate_svg()
except Exception as _e:
    print(f"VERIFY_ERROR SVG: {_e}"); _sys.exit(5)
print("VERIFY_OK")
"""

# Required fields every component must carry for a clean CELUS/CUBO import.
REQUIRED_FIELDS = ("MPN", "Manufacturer", "Datasheet", "Block")

# Net-name prefix -> typed interface, used to infer the inter-block bus topology.
INTERFACE_BY_NET = {
    "+12V": "POWER", "+5V": "POWER", "+3V3": "POWER", "GND": "POWER",
    "I2C": "I2C", "STP_TX": "UART", "STP_RX": "UART",
    "SOL_IN": "GPIO", "HAPT_EN": "GPIO", "SERVO_SIG": "PWM",
    "STP_A": "STEPPER", "STP_B": "STEPPER",
    "VIB": "MOTOR", "SOL_A": "MOTOR", "SOL_B": "MOTOR",
}


def extract_code(text):
    m = re.search(r"```python\s*(.*?)```", text, re.S)
    if not m:
        m = re.search(r"```\s*(.*?)```", text, re.S)
    return m.group(1).strip() if m else ""


def check_syntax(code):
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"


def parse_netlist(path):
    """Minimal KiCad-netlist reader: returns components and nets.

    components: {ref: {value, footprint, fields:{name:val}}}
    nets:       {netname: [(ref, pin), ...]}

    The KiCad netlist is parsed by splitting on the ``(comp`` / ``(net`` tokens
    rather than trying to balance parentheses with one regex.
    """
    text = open(path).read()
    comps, nets = {}, {}

    nets_start = text.find("\n  (nets")
    if nets_start == -1:
        nets_start = text.find("(nets")
    comp_text = text[:nets_start]
    nets_text = text[nets_start:]

    comp_section = re.search(r"\(components\b(.*)\Z", comp_text, re.S)
    if comp_section:
        for chunk in re.split(r"\n\s*\(comp\b", comp_section.group(1))[1:]:
            ref_m = re.search(r"\(ref\s+\"([^\"]+)\"\)", chunk)
            if not ref_m:
                continue
            ref = ref_m.group(1)
            val = (re.search(r"\(value\s+\"([^\"]*)\"\)", chunk) or [None, ""])[1]
            fp = (re.search(r"\(footprint\s+\"([^\"]*)\"\)", chunk) or [None, ""])[1]
            fields = {}
            # (field\n  (name "X") "value")  OR  (name "X"))  [no value]
            for fm in re.finditer(
                    r"\(name\s+\"([^\"]+)\"\)\s*(?:\"([^\"]*)\")?", chunk):
                key, value = fm.group(1), fm.group(2)
                # Keep the first non-empty value seen for a given field name.
                if value and not fields.get(key):
                    fields[key] = value
                fields.setdefault(key, value or "")
            comps[ref] = {"value": val, "footprint": fp, "fields": fields}

    net_section = re.search(r"\(nets\b(.*)\Z", nets_text, re.S)
    if net_section:
        for chunk in re.split(r"\n\s*\(net\b", net_section.group(1))[1:]:
            name_m = re.search(r"\(name\s+\"([^\"]+)\"\)", chunk)
            if not name_m:
                continue
            nodes = [(nm.group(1), nm.group(2)) for nm in re.finditer(
                r"\(node\s*\(ref\s+\"([^\"]+)\"\)\s*\(pin\s+\"([^\"]+)\"\)",
                chunk, re.S)]
            nets[name_m.group(1)] = nodes
    return comps, nets


def interface_for(net_name):
    for prefix, iface in INTERFACE_BY_NET.items():
        if net_name == prefix or net_name.startswith(prefix):
            return iface
    return "SIGNAL"


def derive_bom_and_blocks(net_path):
    comps, nets = parse_netlist(net_path)

    # BOM
    bom_path = os.path.join(HERE, "powder_doser_celus_bom.csv")
    with open(bom_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Ref", "Value", "Block", "MPN", "Manufacturer",
                    "Footprint", "Datasheet"])
        for ref in sorted(comps, key=lambda r: (re.sub(r"\d", "", r), int(re.sub(r"\D", "", r) or 0))):
            c = comps[ref]
            fl = c["fields"]
            w.writerow([ref, c["value"], fl.get("Block", ""), fl.get("MPN", ""),
                        fl.get("Manufacturer", ""), c["footprint"],
                        fl.get("Datasheet", "")])

    # Functional block diagram
    blocks = {}
    for ref, c in comps.items():
        blk = c["fields"].get("Block", "UNASSIGNED")
        blocks.setdefault(blk, []).append(ref)
    block_of = {ref: c["fields"].get("Block", "UNASSIGNED")
                for ref, c in comps.items()}

    interfaces = []
    for net_name, nodes in nets.items():
        block_set = sorted({block_of.get(ref, "UNASSIGNED") for ref, _ in nodes})
        if len(block_set) > 1:
            interfaces.append({
                "net": net_name,
                "interface": interface_for(net_name),
                "between": block_set,
                "nodes": [f"{r}.{p}" for r, p in nodes],
            })

    blocks_path = os.path.join(HERE, "powder_doser_celus_blocks.json")
    with open(blocks_path, "w") as f:
        json.dump({
            "blocks": {b: sorted(refs) for b, refs in sorted(blocks.items())},
            "interfaces": sorted(interfaces, key=lambda i: i["net"]),
        }, f, indent=2)

    # Field-completeness audit (the CELUS readiness gate).
    missing = {ref: [k for k in REQUIRED_FIELDS if not c["fields"].get(k)]
               for ref, c in comps.items()}
    missing = {ref: ks for ref, ks in missing.items() if ks}
    return comps, missing


def run_candidate(code, idx):
    script = os.path.join(HERE, f"attempt_{idx}_skidl.py")
    with open(script, "w") as f:
        f.write(code + VERIFY_FOOTER)
    env = os.environ.copy()
    env.setdefault("KICAD9_SYMBOL_DIR", "/usr/share/kicad/symbols")
    env.setdefault("KICAD_SYMBOL_DIR", "/usr/share/kicad/symbols")
    proc = subprocess.run([sys.executable, os.path.basename(script)],
                          cwd=HERE, env=env, capture_output=True, text=True)
    out = proc.stdout + "\n" + proc.stderr
    ok = proc.returncode == 0 and "VERIFY_OK" in out
    erc_errs = [ln for ln in out.splitlines()
                if "ERC ERROR" in ln or "VERIFY_ERROR" in ln]
    return ok, out, erc_errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-sonnet-4-6")
    ap.add_argument("--base_url", default="https://api.anthropic.com/v1/")
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--num_of_retry", type=int, default=4)
    args = ap.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("MY_ANTHROPIC_API_KEY")
    client = OpenAI(base_url=args.base_url, api_key=api_key)

    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": PROMPT}]

    start = time.time()
    prompt_tokens = completion_tokens = 0
    passed = False
    attempts = 0
    failure_reason = ""

    for attempt in range(1, args.num_of_retry + 1):
        attempts = attempt
        print(f"\n--- Attempt {attempt}/{args.num_of_retry} ---")
        resp = client.chat.completions.create(
            model=args.model, messages=messages, temperature=args.temperature,
            max_tokens=8000)
        content = resp.choices[0].message.content
        if resp.usage:
            prompt_tokens += resp.usage.prompt_tokens
            completion_tokens += resp.usage.completion_tokens
        with open(os.path.join(HERE, "task_output.txt"), "w") as f:
            f.write(content)

        code = extract_code(content)
        if not code:
            failure_reason = "No python code block in response."
            messages += [{"role": "assistant", "content": content},
                         {"role": "user", "content": failure_reason + " Output the full script."}]
            continue

        ok_syntax, syn_msg = check_syntax(code)
        if not ok_syntax:
            failure_reason = syn_msg
            messages += [{"role": "assistant", "content": content},
                         {"role": "user", "content": f"{syn_msg}\nFix and output the full script."}]
            continue

        ok, out, erc_errs = run_candidate(code, attempt)
        feedback = None
        if ok:
            # Promote artifacts, then run the CELUS-readiness checks.
            for ext in (".net", ".svg", ".erc"):
                src = os.path.join(HERE, f"attempt_{attempt}_skidl{ext}")
                if os.path.exists(src):
                    os.replace(src, os.path.join(HERE, f"powder_doser_celus{ext}"))
            # Save the clean LLM SKiDL source (without the injected footer).
            with open(os.path.join(HERE, "powder_doser_celus_skidl.py"), "w") as f:
                f.write(code + "\n")
            net_path = os.path.join(HERE, "powder_doser_celus.net")
            _comps, missing = derive_bom_and_blocks(net_path)
            if not _comps:
                feedback = ("The netlist parsed with zero components; the "
                            "schematic did not build correctly. Output the full "
                            "corrected script.")
            elif missing:
                feedback = ("The schematic verified, but these components are "
                            "missing required CELUS fields (MPN/Manufacturer/"
                            "Datasheet/Block): " +
                            "; ".join(f"{r}: {', '.join(ks)}"
                                      for r, ks in missing.items()) +
                            ". Add the missing fields and output the full script.")
            else:
                print("Verification PASSED; all components CELUS-ready.")
                passed = True
                failure_reason = ""
                break
        else:
            feedback = ("The script failed verification:\n" +
                        ("\n".join(erc_errs) or out[-1500:]) +
                        "\nFix the issues and output the full corrected script.")

        failure_reason = feedback
        print("Verification/readiness FAILED:\n" + feedback)
        messages += [{"role": "assistant", "content": content},
                     {"role": "user", "content": feedback}]

    # Rasterise the SVG to PNG, matching the other artifact sets.
    try:
        import cairosvg
        svg = os.path.join(HERE, "powder_doser_celus.svg")
        if os.path.exists(svg):
            cairosvg.svg2png(url=svg,
                             write_to=os.path.join(HERE, "powder_doser_celus.png"),
                             output_width=2000)
    except Exception as e:  # pragma: no cover - PNG is a convenience artifact
        print(f"PNG rasterise skipped: {e}")

    stats = {
        "task": "powder_doser_test_module_celus",
        "source": "vertical-cloud-lab/powder-doser PR #61 (head 147e505)",
        "purpose": "CELUS-readiness reprompt (MPN/Manufacturer/Datasheet/"
                   "Block fields + real footprints + derived BOM/block diagram)",
        "model": args.model,
        "base_url": args.base_url,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_duration_seconds": round(time.time() - start, 2),
        "attempts": attempts,
        "total_prompt_tokens": prompt_tokens,
        "total_completion_tokens": completion_tokens,
        "status": "PASS" if passed else "FAIL",
        "failure_reason": failure_reason or "",
    }
    with open(os.path.join(HERE, "powder_doser_celus_stats.json"), "w") as f:
        json.dump(stats, f, indent=2)
    print(json.dumps(stats, indent=2))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
