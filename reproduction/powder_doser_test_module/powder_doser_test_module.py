"""PCBSchemaGen reproduction: powder-doser single-Pico-W test module.

Models the bench-rig electronics from vertical-cloud-lab/powder-doser PR #61
("Add single-Pico-W test-module electronics") as a SKiDL circuit so the
PCBSchemaGen netlist / SVG / PCB pipeline can render it.

The connectivity below is a 1:1 transcription of the "Pin / net table" in
``hardware/test-module/README.md`` of that PR (head 147e505): a single
Raspberry Pi Pico W driving one powder-doser channel — DRV2605L haptic +
ERM, DRV8871 + solenoid, Pololu Tic T500 + NEMA-11 stepper (over UART1),
and a hobby servo, powered from a 12 V brick through a Pololu D24V22F5 buck
with a Pololu #3776 shunt regulator clamping stepper back-EMF.

Run standalone (renders ``*.net`` and ``*.svg`` next to this file)::

    KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols python3 powder_doser_test_module.py
"""

from skidl import (
    Part,
    Pin,
    Net,
    ERC,
    TEMPLATE,
    SKIDL,
    generate_netlist,
    generate_svg,
    set_default_tool,
    KICAD9,
)

set_default_tool(KICAD9)

BIDIR = Pin.types.BIDIR
PWRIN = Pin.types.PWRIN
PWROUT = Pin.types.PWROUT
PASSIVE = Pin.types.PASSIVE
INPUT = Pin.types.INPUT
OUTPUT = Pin.types.OUTPUT
PWR = Pin.types.PWRIN


def _part(name, ref, pins, footprint="Package_TO_SOT_SMD:SOT-23"):
    """Build a SKiDL part from ``(num, name, func)`` tuples and instantiate it."""
    tmpl = Part(tool=SKIDL, name=name, ref_prefix=ref[0], dest=TEMPLATE,
                footprint=footprint)
    for num, pname, func in pins:
        tmpl += Pin(num=num, name=pname, func=func)
    return tmpl(ref=ref)


# --- U2: Raspberry Pi Pico W (only GP0..GP15 used, family-identical pinout) ---
pico = _part("RaspberryPi_Pico_W", "U2", [
    (1, "GP0", BIDIR),
    (2, "GP1", BIDIR),
    (6, "GP4", BIDIR),
    (7, "GP5", BIDIR),
    (14, "GP10", BIDIR),
    (15, "GP11", BIDIR),
    (19, "GP14", BIDIR),
    (20, "GP15", BIDIR),
    (36, "3V3", PWROUT),
    (39, "VSYS", PWRIN),
    (3, "GND", PWRIN),
])

# --- U1: Pololu D24V22F5 5 V / 2.5 A buck regulator -----------------------
buck = _part("Pololu_D24V22F5", "U1", [
    (1, "VIN", PWRIN),
    (2, "GND", PWRIN),
    (3, "VOUT", PWROUT),
])

# --- U3: Adafruit DRV2605L haptic driver breakout -------------------------
drv2605 = _part("DRV2605L", "U3", [
    (1, "VIN", PWRIN),
    (2, "GND", PWRIN),
    (3, "SDA", BIDIR),
    (4, "SCL", INPUT),
    (5, "EN", INPUT),
    (6, "IN_TRIG", INPUT),
    (7, "OUT+", OUTPUT),
    (8, "OUT-", OUTPUT),
])

# --- M1: 10 mm ERM coin motor --------------------------------------------
erm = _part("ERM_Motor", "M1", [
    (1, "+", PASSIVE),
    (2, "-", PASSIVE),
], footprint="Motor:Fan_4pin")

# --- U4: Adafruit DRV8871 DC motor driver breakout ------------------------
drv8871 = _part("DRV8871", "U4", [
    (1, "VM", PWRIN),
    (2, "GND", PWRIN),
    (3, "IN1", INPUT),
    (4, "IN2", INPUT),
    (5, "OUT1", OUTPUT),
    (6, "OUT2", OUTPUT),
])

# --- SOL1: JF-0530B 5 V push-pull solenoid (tap actuator) -----------------
solenoid = _part("JF_0530B_Solenoid", "SOL1", [
    (1, "+", PASSIVE),
    (2, "-", PASSIVE),
], footprint="Motor:Fan_4pin")

# --- U5: Pololu Tic T500 USB stepper controller (UART control) ------------
tic = _part("Pololu_Tic_T500", "U5", [
    (1, "VIN", PWRIN),
    (2, "GND", PWRIN),
    (3, "RX", INPUT),
    (4, "TX", OUTPUT),
    (5, "ERR", OUTPUT),
    (8, "A1", OUTPUT),
    (9, "A2", OUTPUT),
    (10, "B1", OUTPUT),
    (11, "B2", OUTPUT),
])

# --- SR1: Pololu #3776 33 V / 9 W shunt regulator -------------------------
shunt = _part("Pololu_3776_Shunt", "SR1", [
    (1, "+", PWRIN),
    (2, "-", PWRIN),
])

# --- M2: NEMA-11 11HS18-0674S bipolar stepper -----------------------------
stepper = _part("NEMA11_Stepper", "M2", [
    (1, "A1", PASSIVE),
    (2, "A2", PASSIVE),
    (3, "B1", PASSIVE),
    (4, "B2", PASSIVE),
], footprint="Motor:Stepper_Motor_Nidec_Copal_KP39HM2-005")

# --- M3: HD-1810MG metal-gear digital servo -------------------------------
servo = _part("HD_1810MG_Servo", "M3", [
    (1, "+5V", PWRIN),
    (2, "GND", PWRIN),
    (3, "SIG", INPUT),
], footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical")

# --- J1: Mean Well GST60A12 12 V barrel-jack PSU input --------------------
jack = _part("Barrel_Jack_12V", "J1", [
    (1, "+", PWROUT),
    (2, "-", PWROUT),
], footprint="Connector_BarrelJack:BarrelJack_Horizontal")

# --- Bulk decoupling capacitors ------------------------------------------
c1 = Part(tool=SKIDL, name="CP", ref_prefix="C", dest=TEMPLATE,
          footprint="Capacitor_THT:CP_Radial_D6.3mm_P2.50mm")
c1 += Pin(num=1, name="+", func=PASSIVE)
c1 += Pin(num=2, name="-", func=PASSIVE)
c1_12v = c1(ref="C1", value="100uF/25V")   # 12 V bulk
c2_5v = c1(ref="C2", value="100uF/10V")    # 5 V bulk
c3_tic = c1(ref="C3", value="100uF/25V")   # Tic VIN bulk

# =========================================================================
# Power rails
# =========================================================================
n_12v = Net("+12V")
n_12v += (jack["+"], buck["VIN"], drv8871["VM"], tic["VIN"],
          shunt["+"], c1_12v["+"], c3_tic["+"])

n_5v = Net("+5V")
n_5v += buck["VOUT"], pico["VSYS"], servo["+5V"], c2_5v["+"]

n_3v3 = Net("+3V3")          # Tic T500 makes its own logic supply from VIN
n_3v3 += pico["3V3"], drv2605["VIN"]

gnd = Net("GND")
gnd += (jack["-"], buck["GND"], pico["GND"], drv2605["GND"], drv8871["GND"],
        tic["GND"], shunt["-"], servo["GND"],
        c1_12v["-"], c2_5v["-"], c3_tic["-"])

# =========================================================================
# Control / signal nets (Pico W GPIO -> drivers)
# =========================================================================
net_sda = Net("I2C_SDA"); net_sda += pico["GP0"], drv2605["SDA"]
net_scl = Net("I2C_SCL"); net_scl += pico["GP1"], drv2605["SCL"]

# Pico UART1 cross-over to the Tic T500
net_stp_tx = Net("STP_TX"); net_stp_tx += pico["GP4"], tic["RX"]
net_stp_rx = Net("STP_RX"); net_stp_rx += pico["GP5"], tic["TX"]

net_sol_in1 = Net("SOL_IN1"); net_sol_in1 += pico["GP10"], drv8871["IN1"]
net_sol_in2 = Net("SOL_IN2"); net_sol_in2 += pico["GP11"], drv8871["IN2"]

net_hapt_en = Net("HAPT_EN"); net_hapt_en += pico["GP14"], drv2605["EN"], drv2605["IN_TRIG"]
net_servo_sig = Net("SERVO_SIG"); net_servo_sig += pico["GP15"], servo["SIG"]

# =========================================================================
# Actuator power nets
# =========================================================================
Net("STP_A1").connect(tic["A1"], stepper["A1"])
Net("STP_A2").connect(tic["A2"], stepper["A2"])
Net("STP_B1").connect(tic["B1"], stepper["B1"])
Net("STP_B2").connect(tic["B2"], stepper["B2"])

Net("VIB_A").connect(drv2605["OUT+"], erm["+"])
Net("VIB_B").connect(drv2605["OUT-"], erm["-"])

Net("SOL_A").connect(drv8871["OUT1"], solenoid["+"])
Net("SOL_B").connect(drv8871["OUT2"], solenoid["-"])

# U5.ERR is intentionally left unconnected (optional fault line).

ERC()
generate_netlist()
generate_svg()
