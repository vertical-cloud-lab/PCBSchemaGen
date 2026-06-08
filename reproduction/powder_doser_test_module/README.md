# Reproduction: powder-doser single-Pico-W test module

This directory applies the **PCBSchemaGen** flow to a real, external design —
the single-Raspberry-Pi-Pico-W bench rig from
[`vertical-cloud-lab/powder-doser` PR #61](https://github.com/vertical-cloud-lab/powder-doser/pull/61)
("Add single-Pico-W test-module electronics") at head
[`147e505`](https://github.com/vertical-cloud-lab/powder-doser/commit/147e5055fb6ec935af164a88e447ed1748f370df).

It mirrors the `reproduction/` work for the paper examples (Task 1 / Task 17):
run the generation + verification + render loop end-to-end and commit every
artifact. The difference is that the powder-doser bench rig is a
microcontroller / breakout board (Pico W + DRV2605L + DRV8871 + Pololu Tic T500
+ servo + solenoid + ERM), whose parts are **not** in PCBSchemaGen's
power-electronics `test` library — so the parts are defined inline with SKiDL's
`SKIDL` tool instead of `Part("test", ...)`.

## The design

A single Pico W drives one powder-doser channel — dispensing-angle servo,
tapping solenoid, vibration (ERM via DRV2605L), and auger rotation (NEMA-11
stepper via a Pololu Tic T500 over UART1). Power is a 12 V barrel-jack brick,
stepped to 5 V by a Pololu D24V22F5 buck; the Pico's on-board LDO supplies 3V3;
a Pololu #3776 shunt regulator clamps stepper back-EMF on the 12 V rail.

The connectivity is a 1:1 transcription of the **"Pin / net table"** in
`hardware/test-module/README.md` of PR #61 — 20 nets, verified identical in both
the ground-truth and the LLM-generated netlists.

## Two artifact sets

### 1. Ground-truth reference (`powder_doser_test_module.*`)

A hand-written SKiDL transcription of the PR #61 pin/net table, run through the
same SKiDL → KiCad-netlist → `netlistsvg` pipeline that the sample suite uses.

| File | Description |
|------|-------------|
| `powder_doser_test_module.py`  | Ground-truth SKiDL source (the net table) |
| `powder_doser_test_module.net` | KiCad netlist |
| `powder_doser_test_module.svg` | `netlistsvg` schematic render |
| `powder_doser_test_module.png` | Rasterised schematic (via `cairosvg`) |
| `powder_doser_test_module.erc` | SKiDL ERC report (**0 errors**) |

Run it standalone:

```bash
KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols \
  python3 powder_doser_test_module.py
```

### 2. PCBSchemaGen LLM loop (`powder_doser_llm.*`, `run_powder_doser.py`)

`run_powder_doser.py` reproduces `task/run.py`'s feedback loop — LLM →
extract SKiDL → syntax check → ERC + netlist + SVG render → retry with the error
fed back — but for this board. The model is given the PR #61 spec and the net
contract and must regenerate the schematic from scratch.

| File | Description |
|------|-------------|
| `run_powder_doser.py`           | The PCBSchemaGen-style generation loop |
| `powder_doser_llm_skidl.py`     | Final LLM-generated SKiDL source |
| `powder_doser_llm.net`          | KiCad netlist from the LLM design |
| `powder_doser_llm.svg`          | `netlistsvg` render of the LLM design |
| `powder_doser_llm.png`          | Rasterised LLM schematic |
| `powder_doser_llm.erc`          | ERC report of the LLM design (**0 errors**) |
| `powder_doser_llm_stats.json`   | Run stats (model, attempts, tokens, status) |
| `task_output.txt`               | Final raw LLM response (chain-of-thought + code) |

Reproduce the run (uses an OpenAI-compatible endpoint; the Anthropic endpoint
was used here):

```bash
export OPENAI_API_KEY="$YOUR_KEY"
KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols \
  python3 run_powder_doser.py \
    --model claude-sonnet-4-6 \
    --base_url https://api.anthropic.com/v1/ \
    --num_of_retry 4
```

## Result

`claude-sonnet-4-6` produced an ERC-clean schematic on the 3rd attempt (the
loop fed back the verification errors from the first two). The LLM netlist's net
connectivity is **identical** to the ground-truth net table for all 20 nets
(only the Pico's internal GPIO pin-number assignment differs, which is
cosmetic). The remaining ERC output is warnings only — "insufficient drive
current on GND" (a SKiDL artifact of modelling every ground pin as `POWER-IN`)
and the intentionally-unconnected Tic T500 `ERR` line — **0 ERC errors** in both
designs.

## Provenance / notes

- Source design: powder-doser PR #61, head `147e505`, file
  `hardware/test-module/README.md` (pin/net table) and `kicad/generate.py`.
- Pipeline tooling matches the repo install docs: KiCad 9 (`pcbnew`,
  `kicad-cli`), `skidl`, and the `netlistsvg` npm CLI (the dependency documented
  in PR #2).
- No secrets are committed; the API key is read from the environment at runtime
  and never written to any artifact.
