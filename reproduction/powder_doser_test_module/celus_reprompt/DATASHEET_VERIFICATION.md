# Datasheet verification — powder-doser CELUS re-prompt

This note closes the open caveat from
[`../CELUS_EVALUATION.md`](../CELUS_EVALUATION.md) §4 and the PR #4 thread
([comment 4664077324](https://github.com/vertical-cloud-lab/PCBSchemaGen/pull/4#issuecomment-4664077324)):
the first CELUS re-prompt produced MPN / Manufacturer / Datasheet fields that
were *plausible but model-supplied and unverified*. Per the request, the
sourcing metadata on every component has now been **confirmed against the
powder-doser project itself and against the manufacturers' own material**, and
the fabricated / wrong / dead links have been replaced with verified ones.

## How each part was confirmed

The single strongest source is the powder-doser project's own
**`hardware/vendor-files/`** directory (added in
[`vertical-cloud-lab/powder-doser` PR #25](https://github.com/vertical-cloud-lab/powder-doser/pull/25)),
which mirrors the vendor-published datasheets / CAD next to a per-part
`SOURCES.txt` + `SPECS.md`, indexed in
[`hardware/vendor-files/README.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/5d10fcc18f90bd03bcf1729071df22faf4061219/hardware/vendor-files/README.md).
The part identities themselves come from the bench-rig BOM in
[`hardware/test-module/README.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/refs%2Fpull%2F61%2Fhead/hardware/test-module/README.md)
(the design being reproduced, PR #61). Each datasheet/product link was then
cross-checked against the manufacturer's own page (and, for the driver ICs,
the silicon vendor's datasheet) and the URL confirmed reachable (HTTP 200/redirect).

| Ref | Part (as built on the bench rig) | MPN | Manufacturer | Datasheet (verified) | Confirming sources |
|-----|----------------------------------|-----|--------------|----------------------|--------------------|
| U2  | Raspberry Pi Pico W | SC0918 | Raspberry Pi | <https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf> | PR #61 BOM (U2); official Raspberry Pi datasheet (resolves to `pip.raspberrypi.com/.../pico-w-datasheet.pdf`) |
| U1  | Pololu D24V22F5 5 V/2.5 A buck | 2858 | Pololu | <https://www.pololu.com/product/2858> | PR #61 BOM (U1, item 15); vendor-files `pololu-2858-d24v22f5/` (vendor STEP + dimension PDFs, `SOURCES.txt`) |
| U3  | Adafruit DRV2605L haptic breakout | 2305 | Adafruit | <https://www.adafruit.com/product/2305> | PR #61 BOM (U3, item 1); vendor-files `adafruit-2305-drv2605l/` (Adafruit CAD + Eagle PCB); silicon: TI DRV2605L (<https://www.ti.com/lit/ds/symlink/drv2605l.pdf>) |
| M1  | Adafruit Vibrating Mini Motor Disc (10 mm ERM coin) | 1201 | Adafruit | <https://www.adafruit.com/product/1201> | PR #61 BOM (M1, item 2 "Adafruit #1201"); vendor-files README row 2 |
| U4  | Adafruit DRV8871 motor-driver breakout | 3190 | Adafruit | <https://www.adafruit.com/product/3190> | PR #61 BOM (U4, item 5); vendor-files `adafruit-3190-drv8871/`; silicon: TI DRV8871 (<https://www.ti.com/lit/ds/symlink/drv8871.pdf>) |
| SOL1 | JF-0530B 5 V push-pull solenoid | JF-0530B | Adafruit | <https://www.adafruit.com/product/412> | PR #61 BOM (SOL1, item 4 "Adafruit #412"); vendor-files `adafruit-412-jf-0530b-solenoid/` (`412_C514-B_diagram.pdf`, `C514-datasheet.pdf`) |
| U5  | Pololu Tic T500 stepper controller | 3134 | Pololu | <https://www.pololu.com/product/3134> | PR #61 BOM (U5, item 11 "#3134"); user's guide (<https://www.pololu.com/docs/0J71>); vendor-files `pololu-3135-tic-t500/` — see note below |
| SR1 | Pololu 33 V/9 W shunt regulator | 3776 | Pololu | <https://www.pololu.com/product/3776> | PR #61 BOM (SR1, item 18); vendor-files `pololu-3776-shunt-regulator-9w/` |
| M2  | StepperOnline NEMA-11 bipolar stepper | 11HS18-0674S | StepperOnline | <https://www.omc-stepperonline.com/nema-11-bipolar-1-8deg-10ncm-14-16oz-in-0-67a-28x28x45mm-4-wires-11hs18-0674s> | PR #61 BOM (M2, item 10); vendor-files `stepperonline-11hs18-0674s/` (full datasheet + torque-curve PDFs + `SPECS.md`) |
| M3  | Power HD HD-1810MG metal-gear servo | HD-1810MG | Power HD | <https://www.adafruit.com/product/1142> | PR #61 BOM (M3, item 16 "Adafruit #1142"); vendor-files `adafruit-1142-metal-gear-servo/SPECS.md`; manufacturer confirmed Power HD (Adafruit #1142 == Power HD HD-1810MG) |
| J1  | Adafruit 2.1 mm DC barrel-jack input | 373 | Adafruit | <https://www.adafruit.com/product/373> | PR #61 BOM (J1 power input); vendor-files `adafruit-373-barrel-jack/` (`21mmdcjackDatasheet.pdf`) — see note below |
| C1  | 100 µF / 25 V radial electrolytic | UVR1E101MDD | Nichicon | <https://www.nichicon.co.jp/series_items/catalog_pdf/ja/pdf/xja043/uvr.pdf> | Nichicon UVR series datasheet; representative real part (see caveat) |
| C2  | 100 µF / 10 V radial electrolytic | UVR1A101MDD | Nichicon | <https://www.nichicon.co.jp/series_items/catalog_pdf/ja/pdf/xja043/uvr.pdf> | Nichicon UVR series datasheet; representative real part (see caveat) |
| C3  | 100 µF / 25 V radial electrolytic (Tic VIN) | UVR1E101MDD | Nichicon | <https://www.nichicon.co.jp/series_items/catalog_pdf/ja/pdf/xja043/uvr.pdf> | Nichicon UVR series datasheet; representative real part (see caveat) |

## What changed vs. the first re-prompt (corrections)

The first run's metadata was accepted as-is from the model. Verification found
several entries that were wrong or pointed at dead/fabricated URLs; all are now
fixed against the project's vendor files and the manufacturers' material:

| Ref | Field | Was (unverified) | Now (verified) | Why |
|-----|-------|------------------|----------------|-----|
| M3  | Manufacturer | `Hitec` | `Power HD` | HD-1810MG is a **Power HD** servo (sold as Adafruit #1142), not a Hitec part; the old `hitecrcd.com/.../hd-1810mg` link does not exist. |
| M3  | Datasheet | dead `hitecrcd.com` URL | Adafruit #1142 product page | The Hitec URL was fabricated; the part's real product page is the Adafruit listing. |
| M2  | MPN / Mfr | `NEMA11-Bipolar-Stepper` / `Generic` | `11HS18-0674S` / `StepperOnline` | Real part identified in the BOM (item 10); datasheet committed in vendor-files. The old link pointed at a Pololu **category** page (wrong vendor). |
| M1  | MPN / Mfr | `ERM-10mm-Coin` / `Generic` | `1201` / `Adafruit` | The ERM is Adafruit #1201 (BOM item 2); old link was a generic Precision Microdrives category page. |
| SOL1| Mfr / Datasheet | `Zonhen` / fabricated `zonhen.com` PDF | `Adafruit` / Adafruit #412 page | Sourced as Adafruit #412 (BOM item 4); the `zonhen.com/uploads/.../JF-0530B.pdf` URL was fabricated. Mechanical/coil datasheets are committed in vendor-files. |
| J1  | MPN / Mfr / Datasheet | `PJ-002A` / `CUI Devices` / dead `cui.com` PDF | `373` / `Adafruit` / Adafruit #373 page | The bench rig's barrel-jack input is Adafruit #373 (BOM item 8); the old CUI PDF link 403s (redirects to bel­fuse.com). The KiCad **footprint** `BarrelJack_CUI_PJ-002A` is a generic barrel-jack outline and is retained. |
| C1/C2/C3 | Datasheet | dead `…/pdfs/e-uvr.pdf` (404) | current Nichicon UVR series PDF (200) | The previous Nichicon path 404s; replaced with the live UVR series catalog datasheet. |

The remaining components (U1, U2, U3, U4, U5, SR1) already carried correct
identities; only their datasheet links were confirmed reachable and left as the
manufacturer product/resources pages.

## Notes and remaining caveats

* **Tic T500 SKU (#3134 vs #3135).** The PR #61 BOM lists the Tic T500 as
  Pololu **#3134**; the PR #25 vendor-files folder is named `pololu-3135-tic-t500`.
  These are the **same controller** — #3134 ships with the connectors *not*
  soldered and #3135 ships with them *pre-soldered*; they share one user's
  guide (`tic.pdf`, <https://www.pololu.com/docs/0J71>). The MPN here is kept as
  **3134** to match the design being reproduced (PR #61); swap to 3135 if the
  pre-soldered variant is preferred.
* **Electrolytic caps are generic-by-spec.** The bench-rig BOM specifies the
  bulk caps only as "100 µF / 25 V" and "100 µF / 10 V" electrolytics with no
  MPN. The MPNs here (Nichicon UVR-series `UVR1E101MDD` / `UVR1A101MDD`) are
  real, correctly-rated representative parts pointing at the genuine UVR series
  datasheet; any equivalent 100 µF radial electrolytic at the stated voltage is
  acceptable.
* **Footprints remain pin-count generics.** As in the first run, the breakout
  modules use generic pin-header footprints sized to their pin count (and J1 a
  generic barrel-jack outline); CELUS or a designer should substitute each
  module's true mechanical footprint before layout. The vendor-files directory
  ships vendor STEP/CAD for the Pololu boards, the stepper, and the Adafruit
  breakouts to support that step.
* **Datasheet PDFs are not re-hosted here.** The verified PDFs already live in
  the powder-doser project's `hardware/vendor-files/<part>/datasheets/`; this
  evaluation links to the project's own copies and the manufacturer pages rather
  than duplicating binaries into PCBSchemaGen.
