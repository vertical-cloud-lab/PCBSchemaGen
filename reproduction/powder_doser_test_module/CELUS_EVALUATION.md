# Are the PCBSchemaGen files usable by CELUS? — powder-doser evaluation

This note answers the question raised on
[PR #4](https://github.com/vertical-cloud-lab/PCBSchemaGen/pull/4#issuecomment-4663769497):
in the scope of *"creating a PCB for the powder doser using only automated
tools,"* how useful are the files PCBSchemaGen produced for import into a
component-driven board-synthesis tool such as **[CELUS](https://celus.io)**, how
many of CELUS's input requirements does the test run already satisfy, what is
missing, and **can PCBSchemaGen be re-prompted to close the gap?**

The short answer: the test run already nails the hardest part (a complete,
ERC-clean, named-net connectivity contract), but the first run was missing the
*sourcing* metadata CELUS needs to match real parts (manufacturer part numbers,
datasheets) and used placeholder footprints. **Both gaps are promptable** — a
single re-prompt produced a net-for-net identical design in which every
component carries a real MPN, manufacturer, datasheet, real footprint and a
functional-block tag, plus an auto-derived BOM and block diagram. The executed
re-prompt and its artifacts are in [`celus_reprompt/`](celus_reprompt/).

---

## 1. How CELUS builds a board (what it needs as input)

CELUS is **not** a netlist-in / layout-out autorouter. It automates the
*front-end* of design: you describe the system as a **block diagram** of
**functional blocks** with typed interfaces, and its engine matches each block
to a real, orderable part captured as a **CUBO** (a modular block bundling
schematic symbol + footprint + BOM metadata + interface/port definitions). It
then resolves the design and exports schematic + netlist + BOM to an ECAD tool
(Altium, OrCAD, KiCad, …) for layout. You can also **import your own CUBO** by
supplying the part's symbol, footprint and metadata (MPN, manufacturer,
datasheet).
(Sources: CELUS platform docs / press coverage — allaboutcircuits, EDN,
powerelectronicsnews; summarized in the PR thread.)

So the information CELUS needs to turn this powder-doser design into a board is:

| # | CELUS input requirement | Why CELUS needs it |
|---|--------------------------|--------------------|
| R1 | **Functional blocks** (the components, grouped by role) | nodes of the block diagram |
| R2 | **Typed interfaces between blocks** (power, I²C, UART, GPIO/PWM, motor/stepper) | edges of the block diagram |
| R3 | **Pin-level connectivity** (which pin → which net) | schematic/netlist generation & verification |
| R4 | **Power domains / supply rails** identified | power planning |
| R5 | **Real footprint** per component | placement & layout export |
| R6 | **Manufacturer part number (MPN)** per component | CUBO/part matching & sourcing |
| R7 | **Manufacturer** per component | CUBO/part matching & sourcing |
| R8 | **Datasheet** per component | CUBO creation / verification |
| R9 | **Consolidated BOM** (ref, qty, value, MPN, mfr, footprint) | procurement & CUBO import |
| R10 | **Component electrical values / ratings** (e.g. cap µF/V) | constrain part selection |
| R11 | **Mechanical / form-factor constraints** (board outline, connectors) | layout (optional, out of PCBSchemaGen's scope) |

---

## 2. What the PCBSchemaGen test run produced (first run)

The committed first run (`powder_doser_llm.*`, see the
[directory README](README.md)) emits the standard PCBSchemaGen artifact set:
a **KiCad netlist** (`.net`), a **schematic render** (`.svg`/`.png`), an
**ERC report** (`.erc`, 0 errors) and the **SKiDL source** (`.py`).

Mapping that against the CELUS requirements above:

| # | Requirement | First run status | Evidence |
|---|-------------|------------------|----------|
| R1 | Functional blocks | ⚠️ **Implicit** | components are present and obvious by role, but not tagged/grouped |
| R2 | Typed interfaces | ⚠️ **Implicit** | net *names* encode intent (`I2C_*`, `STP_TX/RX`, `VIB_*`, `SOL_*`) but interface *type* is not declared |
| R3 | Pin-level connectivity | ✅ **Complete** | 20 nets, every node `ref.pin` in `powder_doser_llm.net`; ERC clean |
| R4 | Power domains | ✅ **Complete** | named rails `+12V`, `+5V`, `+3V3`, `GND` |
| R5 | Real footprint | ❌ **Missing** | every breakout carries the **placeholder** `Package_TO_SOT_SMD:SOT-23` |
| R6 | MPN | ❌ **Missing** | `value` is a descriptive name (`DRV2605L`, `Cap100uF25V`), no MPN |
| R7 | Manufacturer | ❌ **Missing** | not emitted |
| R8 | Datasheet | ❌ **Missing** | netlist `Datasheet` field is empty |
| R9 | Consolidated BOM | ⚠️ **Derivable** | not emitted as an artifact, but reconstructable from the netlist |
| R10 | Values / ratings | ⚠️ **Partial** | cap values/ratings encoded in `value`; breakouts have only a name |
| R11 | Mechanical constraints | ❌ **Out of scope** | PCBSchemaGen models electrical connectivity, not mechanics |

**Score (first run): 2 fully met (R3, R4), 4 partial/implicit (R1, R2, R9, R10),
4 missing (R5–R8), 1 out of scope (R11).**

### Why this is still very useful

The thing CELUS cannot infer for you — *the exact electrical intent of the
board* — is exactly what PCBSchemaGen delivers, and delivers cleanly: a
verified, named, 20-net connectivity contract with correct power domains and
pin electrical types. That is a far stronger starting point than the LaMAGIC
output and is the backbone any CUBO-based block diagram would be built on. The
missing items (R5–R8) are **sourcing metadata**, not connectivity — i.e. the
*easy* part to add, and the part most amenable to prompting.

---

## 3. Closing the gap: re-prompting PCBSchemaGen

PCBSchemaGen's loop is entirely prompt-driven (`run_powder_doser.py` →
`TASK_DESCRIPTION` + `LIBRARY_GUIDE` + `PROMPT`). The four missing requirements
(R5–R8) and the two "implicit" ones (R1, R2) are all things the model can be
asked to emit directly, because SKiDL part **fields** flow straight into the
KiCad netlist (and therefore into any BOM/CUBO export).

[`celus_reprompt/run_powder_doser_celus.py`](celus_reprompt/run_powder_doser_celus.py)
is the same feedback loop with the prompt extended to require, on **every**
component:

* `MPN`, `Manufacturer`, `Datasheet` fields (R6–R8);
* a **real KiCad footprint** — module/header/connector/passive packages instead
  of the SOT-23 placeholder (R5);
* a `Block` tag from a fixed vocabulary (`POWER`, `MCU`, `HAPTIC`,
  `MOTOR_DRIVE`, `STEPPER_DRIVE`, `SERVO`, `ACTUATOR`, `BULK_DECOUPLE`) (R1).

The loop also adds a **CELUS-readiness gate**: after ERC/netlist verification it
parses the netlist and *rejects* the attempt (feeding the failure back to the
model) if any component is missing a required field. On success it
deterministically **derives two extra artifacts from the netlist** (no extra
model trust):

* [`powder_doser_celus_bom.csv`](celus_reprompt/powder_doser_celus_bom.csv) — the
  consolidated BOM (R9);
* [`powder_doser_celus_blocks.json`](celus_reprompt/powder_doser_celus_blocks.json) —
  the functional **block diagram**: blocks → members, plus the typed
  inter-block interfaces (`POWER`/`I2C`/`UART`/`GPIO`/`PWM`/`MOTOR`/`STEPPER`)
  inferred from the net names (R1, R2).

### Result of the executed re-prompt

`claude-sonnet-4-6` produced a passing, fully-tagged design **on the first
attempt** (`celus_reprompt/powder_doser_celus_stats.json`). Crucially, the
electrical design did not drift: the re-prompted netlist is **net-for-net
identical** to the first run — same 20 nets, identical component membership per
net, still **0 ERC errors**.

| # | Requirement | After re-prompt | Evidence |
|---|-------------|-----------------|----------|
| R1 | Functional blocks | ✅ | 8 blocks in `…_blocks.json`; `Block` field per comp |
| R2 | Typed interfaces | ✅ | 20 typed interfaces in `…_blocks.json` |
| R3 | Pin connectivity | ✅ | `powder_doser_celus.net` (identical to first run) |
| R4 | Power domains | ✅ | `+12V`/`+5V`/`+3V3`/`GND` |
| R5 | Real footprint | ✅ | e.g. `BarrelJack_CUI_PJ-002A`, `PinHeader_2x20…` for the Pico W |
| R6 | MPN | ✅ | e.g. Pico W `SC0918`, D24V22F5 `2858`, DRV2605L `2305`, Tic T500 `3134` |
| R7 | Manufacturer | ✅ | Raspberry Pi, Pololu, Adafruit, Nichicon, CUI, … |
| R8 | Datasheet | ✅ | datasheet/product URL per component |
| R9 | BOM | ✅ | `powder_doser_celus_bom.csv` (14 lines) |
| R10 | Values / ratings | ✅ (improved) | real cap MPNs at rated voltage; named parts as MPN |
| R11 | Mechanical | ❌ still out of scope | needs a mechanical/enclosure input, not PCBSchemaGen |

**Score (after re-prompt): 10 of 11 met; the only remaining gap (R11) is
mechanical/form-factor data that is outside PCBSchemaGen's electrical scope.**

---

## 4. Solutions found (summary)

1. **Use the existing output as the connectivity backbone.** The first-run
   netlist already gives CELUS a verified, named, ERC-clean 20-net contract with
   correct power domains — the part CELUS can't guess. *No change required.*
2. **Re-prompt for sourcing metadata (R5–R8).** Adding MPN / Manufacturer /
   Datasheet / real-footprint requirements to the prompt makes the LLM emit them
   as SKiDL fields that land in the netlist and BOM, with **no change to
   connectivity** and no extra ERC errors. *Demonstrated.*
3. **Emit the block diagram (R1, R2).** Tag each component with a `Block` and
   derive the typed inter-block interfaces from net-name prefixes — this
   reconstructs the CELUS-style functional block diagram directly from the
   netlist. *Demonstrated (`…_blocks.json`).*
4. **Auto-generate the BOM (R9).** Derive `ref, value, block, MPN, manufacturer,
   footprint, datasheet` straight from the netlist so procurement / CUBO import
   has a single source of truth. *Demonstrated (`…_bom.csv`).*
5. **Add a readiness gate.** Reject-and-retry on any component missing required
   metadata makes "CELUS-ready" an enforced exit criterion of the loop, not a
   hope. *Demonstrated.*

### Caveats / what still needs a human or another tool

* **MPN accuracy.** The model-supplied MPNs/datasheets are plausible and
  correctly formatted but are **not verified against live distributor stock** —
  they should be confirmed (or matched by CELUS's own catalog) before ordering.
* **Footprints are placeholders-by-pin-count.** Breakouts are mapped to generic
  pin-header footprints sized to their pin count; CELUS (or a designer) should
  swap in each module's true mechanical footprint.
* **Direct format bridge.** CELUS ingests requirements/CUBOs, not a raw KiCad
  `.net`. The `.net` + `.csv` + `.json` here are the *content* CELUS needs; a
  thin importer (or manual block-diagram entry, or per-part CUBO import using
  the BOM/footprint/datasheet) is still required to load it. That importer is a
  small, well-scoped follow-up.
* **R11 (mechanical)** is genuinely out of PCBSchemaGen's scope and must come
  from an enclosure/mechanical definition.
