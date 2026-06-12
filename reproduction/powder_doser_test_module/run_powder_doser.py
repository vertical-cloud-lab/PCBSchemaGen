"""PCBSchemaGen-style generation loop for the powder-doser test module.

This mirrors ``task/run.py``'s feedback loop (LLM -> SKiDL code -> syntax /
ERC verification -> SVG+netlist render -> retry-with-feedback) but targets the
single-Pico-W bench rig from vertical-cloud-lab/powder-doser PR #61, whose
microcontroller-breakout parts are not in PCBSchemaGen's power-electronics
``test`` library.  Parts are therefore defined inline with SKiDL's ``SKIDL``
tool (same approach as the committed ground-truth ``powder_doser_test_module.py``).

Usage::

    export OPENAI_API_KEY="$MY_ANTHROPIC_API_KEY"
    KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols \
      python3 run_powder_doser.py --model claude-sonnet-4-6 \
      --base_url https://api.anthropic.com/v1/ --num_of_retry 4
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import time

from openai import OpenAI

HERE = os.path.dirname(os.path.abspath(__file__))

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

LIBRARY_GUIDE = """\
These microcontroller-breakout parts are NOT in PCBSchemaGen's `test` library,
so define each one inline using SKiDL's SKIDL tool. Use this exact helper and
pin functions so ERC and netlist/SVG generation succeed:

```python
from skidl import (Part, Pin, Net, ERC, TEMPLATE, SKIDL,
                   generate_netlist, generate_svg, set_default_tool, KICAD9)
set_default_tool(KICAD9)

def make(name, ref, pins, footprint="Package_TO_SOT_SMD:SOT-23"):
    t = Part(tool=SKIDL, name=name, ref_prefix=ref[0], dest=TEMPLATE,
             footprint=footprint)
    for num, pname, func in pins:
        t += Pin(num=num, name=pname, func=func)
    return t(ref=ref)
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

{LIBRARY_GUIDE}

Output a single, complete, self-contained Python (SKiDL) script inside one
```python ... ``` code block that builds every net above exactly, calls ERC(),
then generate_netlist() and generate_svg(). Do not add components or nets that
are not listed.
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
        if ok:
            print("Verification PASSED")
            passed = True
            # Promote final artifacts to stable filenames.
            for ext in (".net", ".svg"):
                src = os.path.join(HERE, f"attempt_{attempt}_skidl{ext}")
                if os.path.exists(src):
                    os.replace(src, os.path.join(HERE, f"powder_doser_llm{ext}"))
            failure_reason = ""
            break

        failure_reason = "\n".join(erc_errs) or out[-1500:]
        print("Verification FAILED:\n" + failure_reason)
        messages += [{"role": "assistant", "content": content},
                     {"role": "user",
                      "content": "The script failed verification:\n" + failure_reason +
                      "\nFix the issues and output the full corrected script."}]

    stats = {
        "task": "powder_doser_test_module",
        "source": "vertical-cloud-lab/powder-doser PR #61 (head 147e505)",
        "model": args.model,
        "base_url": args.base_url,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_duration_seconds": round(time.time() - start, 2),
        "attempts": attempts,
        "total_prompt_tokens": prompt_tokens,
        "total_completion_tokens": completion_tokens,
        "status": "PASS" if passed else "FAIL",
        "failure_reason": failure_reason,
    }
    with open(os.path.join(HERE, "powder_doser_llm_stats.json"), "w") as f:
        json.dump(stats, f, indent=2)
    print(json.dumps(stats, indent=2))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
