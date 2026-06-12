# CELUS-readiness re-prompt

This directory is the **executed re-prompt** referenced in
[`../CELUS_EVALUATION.md`](../CELUS_EVALUATION.md). It re-runs the PCBSchemaGen
feedback loop for the powder-doser board with the prompt extended so the output
carries the metadata a component-driven board-synthesis tool such as
[CELUS](https://celus.io) needs (manufacturer part numbers, datasheets, real
footprints, functional-block tags), and it derives a BOM and a functional block
diagram from the resulting netlist.

The board specification and the 20-net connectivity contract are **unchanged**
from [`../run_powder_doser.py`](../run_powder_doser.py); only the *deliverable*
requirements were added. The re-prompted netlist is **net-for-net identical** to
the first run (same nets, same per-net component membership, still 0 ERC
errors).

## Files

| File | Description |
|------|-------------|
| `run_powder_doser_celus.py`        | The CELUS-oriented loop (adds MPN/Manufacturer/Datasheet/Block + real-footprint requirements, a field-completeness readiness gate, and BOM/block-diagram derivation) |
| `powder_doser_celus_skidl.py`      | LLM-generated SKiDL source (every part tagged with the four fields + a real footprint), with the MPN/Manufacturer/Datasheet fields updated to the verified values (see `DATASHEET_VERIFICATION.md`) |
| `powder_doser_celus.net`           | KiCad netlist (now carrying MPN/Manufacturer/Datasheet/Block fields) |
| `powder_doser_celus.svg` / `.png`  | Schematic render |
| `powder_doser_celus.erc`           | ERC report (**0 errors**) |
| `powder_doser_celus_bom.csv`       | Consolidated BOM derived from the netlist (ref, value, block, MPN, manufacturer, footprint, datasheet) |
| `powder_doser_celus_blocks.json`   | Functional block diagram: blocks → members, plus the typed inter-block interfaces (POWER/I2C/UART/GPIO/PWM/MOTOR/STEPPER) inferred from net names |
| `powder_doser_celus_stats.json`    | Run stats (model, attempts, tokens, status) |
| `task_output.txt`                  | Final raw LLM response (chain-of-thought + code) |
| `DATASHEET_VERIFICATION.md`        | Per-component verification of every MPN / manufacturer / datasheet against the powder-doser project's `hardware/vendor-files/` and the manufacturers' pages (with the corrections applied) |

## Reproduce

```bash
export OPENAI_API_KEY="$YOUR_KEY"
KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols \
  python3 run_powder_doser_celus.py \
    --model claude-sonnet-4-6 \
    --base_url https://api.anthropic.com/v1/ \
    --num_of_retry 4
```

## Caveats

The MPNs, manufacturers and datasheet URLs have been **verified** against the
powder-doser project's own `hardware/vendor-files/` (committed vendor datasheets
+ `SOURCES.txt`/`SPECS.md`) and the manufacturers' product pages — see
[`DATASHEET_VERIFICATION.md`](DATASHEET_VERIFICATION.md) for the per-part sources
and the corrections that were applied (e.g. the servo is Power HD, not Hitec;
the solenoid/ERM/stepper are real Adafruit / StepperOnline parts; dead CUI /
Nichicon / Hitec / Zonhen links were replaced). Live distributor **stock/price**
should still be confirmed before ordering, the bulk caps are generic-by-spec
(any 100 µF radial electrolytic at the rated voltage), and the breakout
footprints are generic pin-headers sized to each part's pin count. See
[`../CELUS_EVALUATION.md`](../CELUS_EVALUATION.md) §4 for the full list of
solutions and caveats.
