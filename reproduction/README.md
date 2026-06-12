# Reproduction Artifacts

End-to-end run artifacts from reproducing two benchmark tasks with the full
PCBSchemaGen pipeline (LLM generation → ERC → topology verification → KiCad
artifact generation). Both runs used the OpenAI-compatible Anthropic endpoint
(`--base_url https://api.anthropic.com/v1/`) with model `claude-sonnet-4-6`.

| Task | Description | Level | Result | Attempts | Components |
|------|-------------|-------|--------|----------|-----------|
| [Task 1](task_01_voltage_divider) | Resistor divider (60 V → 3.3 V sense) | Easy | PASS | 1 | 3 |
| [Task 17](task_17_sync_buck) | Synchronous buck converter | Hard | PASS | 2 | 80 |
| [powder-doser test module](powder_doser_test_module) | Single-Pico-W bench rig ([powder-doser PR #61](https://github.com/vertical-cloud-lab/powder-doser/pull/61)) | External | PASS | 3 | 14 |

Task 17 is the paper's flagship example (compare with [`../example_output/`](../example_output)).
It passed on the second attempt: the first attempt was rejected by the topology
verifier (insufficient output capacitors) and the feedback loop drove the fix.

The [powder-doser test module](powder_doser_test_module) is a real external
design (a microcontroller/breakout board rather than a power-electronics
topology) used to exercise the pipeline outside the benchmark; see its
[README](powder_doser_test_module/README.md) for provenance and the
generation loop. Its
[`CELUS_EVALUATION.md`](powder_doser_test_module/CELUS_EVALUATION.md) assesses
how usable the generated files are for import into a component-driven
board-synthesis tool ([CELUS](https://celus.io)) and demonstrates a re-prompt
that adds the missing sourcing metadata (MPNs, datasheets, real footprints, BOM,
block diagram).

## How these were generated

```bash
cd task
OPENAI_API_KEY="YOUR_KEY" XDG_DATA_HOME=$(pwd)/.. python3 run.py \
  --task_id 1 \
  --model claude-sonnet-4-6 \
  --base_url https://api.anthropic.com/v1/ \
  --num_of_retry 3
# results land in task/p1_results/ (and task/p17_results/ for --task_id 17)
```

## Files (per task)

| File | Description |
|------|-------------|
| `extracted_task_*.png` | Schematic render (PNG, rendered from the SVG) |
| `extracted_task_*.svg` | Schematic render (vector) |
| `extracted_task_*.kicad_pcb` | KiCad PCB model |
| `extracted_task_*.kicad_pro` / `.kicad_prl` | KiCad project files |
| `extracted_task_*.net` | KiCad netlist |
| `extracted_task_*.erc` | Electrical rule check report |
| `extracted_task_*.py` | Final SKiDL source (with artifact-generation wrapper) |
| `attempt_*_skidl.py` | Per-attempt LLM-generated SKiDL code |
| `attempt_*.svg` | Per-attempt intermediate schematic render |
| `task_*_output.txt` | Full LLM response (chain-of-thought + code) |
| `task_*_stats.json` | Run statistics (tokens, timing, status) |
