from skidl import (Part, Pin, Net, ERC, TEMPLATE, SKIDL,
                   generate_netlist, generate_svg, set_default_tool, KICAD9)

set_default_tool(KICAD9)

def make(name, ref, pins, footprint="Package_TO_SOT_SMD:SOT-23"):
    t = Part(tool=SKIDL, name=name, ref_prefix=ref[0], dest=TEMPLATE,
             footprint=footprint)
    for num, pname, func in pins:
        t += Pin(num=num, name=pname, func=func)
    return t(ref=ref)

# ---------------------------------------------------------------------------
# Instantiate all parts
# ---------------------------------------------------------------------------

# J1 - 12V barrel jack
J1 = make("BarrelJack", "J1", [
    (1, "+",  Pin.types.PWROUT),
    (2, "-",  Pin.types.PWRIN),
], footprint="Connector_BarrelJack:BarrelJack_CUI_PJ-002A")

# U1 - Pololu D24V22F5 buck (5V)
U1 = make("D24V22F5", "U1", [
    (1, "VIN",  Pin.types.PWRIN),
    (2, "GND",  Pin.types.PWRIN),
    (3, "VOUT", Pin.types.PWROUT),
], footprint="Package_TO_SOT_SMD:SOT-23")

# U2 - Raspberry Pi Pico W
U2 = make("PicoW", "U2", [
    (1,  "GP0",  Pin.types.BIDIR),
    (2,  "GP1",  Pin.types.BIDIR),
    (3,  "GP4",  Pin.types.BIDIR),
    (4,  "GP5",  Pin.types.BIDIR),
    (5,  "GP10", Pin.types.BIDIR),
    (6,  "GP11", Pin.types.BIDIR),
    (7,  "GP14", Pin.types.BIDIR),
    (8,  "GP15", Pin.types.BIDIR),
    (9,  "3V3",  Pin.types.PWROUT),
    (10, "VSYS", Pin.types.PWRIN),
    (11, "GND",  Pin.types.PWRIN),
], footprint="Package_TO_SOT_SMD:SOT-23")

# U3 - Adafruit DRV2605L haptic driver
U3 = make("DRV2605L", "U3", [
    (1, "VIN",     Pin.types.PWRIN),
    (2, "GND",     Pin.types.PWRIN),
    (3, "SDA",     Pin.types.BIDIR),
    (4, "SCL",     Pin.types.INPUT),
    (5, "EN",      Pin.types.INPUT),
    (6, "IN_TRIG", Pin.types.INPUT),
    (7, "OUT+",    Pin.types.OUTPUT),
    (8, "OUT-",    Pin.types.OUTPUT),
], footprint="Package_TO_SOT_SMD:SOT-23")

# M1 - 10mm ERM coin motor
M1 = make("ERMMotor", "M1", [
    (1, "+", Pin.types.PASSIVE),
    (2, "-", Pin.types.PASSIVE),
], footprint="Package_TO_SOT_SMD:SOT-23")

# U4 - Adafruit DRV8871 motor driver
U4 = make("DRV8871", "U4", [
    (1, "VM",   Pin.types.PWRIN),
    (2, "GND",  Pin.types.PWRIN),
    (3, "IN1",  Pin.types.INPUT),
    (4, "IN2",  Pin.types.INPUT),
    (5, "OUT1", Pin.types.OUTPUT),
    (6, "OUT2", Pin.types.OUTPUT),
], footprint="Package_TO_SOT_SMD:SOT-23")

# SOL1 - JF-0530B 5V solenoid
SOL1 = make("Solenoid", "SOL1", [
    (1, "+", Pin.types.PASSIVE),
    (2, "-", Pin.types.PASSIVE),
], footprint="Package_TO_SOT_SMD:SOT-23")

# U5 - Pololu Tic T500 stepper controller
U5 = make("TicT500", "U5", [
    (1,  "VIN", Pin.types.PWRIN),
    (2,  "GND", Pin.types.PWRIN),
    (3,  "RX",  Pin.types.INPUT),
    (4,  "TX",  Pin.types.OUTPUT),
    (5,  "ERR", Pin.types.OUTPUT),
    (6,  "A1",  Pin.types.OUTPUT),
    (7,  "A2",  Pin.types.OUTPUT),
    (8,  "B1",  Pin.types.OUTPUT),
    (9,  "B2",  Pin.types.OUTPUT),
], footprint="Package_TO_SOT_SMD:SOT-23")

# SR1 - Pololu #3776 shunt regulator
SR1 = make("ShuntReg3776", "SR1", [
    (1, "+", Pin.types.PWRIN),
    (2, "-", Pin.types.PWRIN),
], footprint="Package_TO_SOT_SMD:SOT-23")

# M2 - NEMA-11 bipolar stepper
M2 = make("NEMA11Stepper", "M2", [
    (1, "A1", Pin.types.PASSIVE),
    (2, "A2", Pin.types.PASSIVE),
    (3, "B1", Pin.types.PASSIVE),
    (4, "B2", Pin.types.PASSIVE),
], footprint="Package_TO_SOT_SMD:SOT-23")

# M3 - HD-1810MG hobby servo
M3 = make("HobbyServo", "M3", [
    (1, "+5V", Pin.types.PWRIN),
    (2, "GND", Pin.types.PWRIN),
    (3, "SIG", Pin.types.INPUT),
], footprint="Package_TO_SOT_SMD:SOT-23")

# C1 - 100uF/25V bulk cap for 12V rail
C1 = make("Cap100uF25V", "C1", [
    (1, "+", Pin.types.PASSIVE),
    (2, "-", Pin.types.PASSIVE),
], footprint="Capacitor_THT:CP_Radial_D6.3mm_P2.50mm")

# C2 - 100uF/10V bulk cap for 5V rail
C2 = make("Cap100uF10V", "C2", [
    (1, "+", Pin.types.PASSIVE),
    (2, "-", Pin.types.PASSIVE),
], footprint="Capacitor_THT:CP_Radial_D6.3mm_P2.50mm")

# C3 - 100uF/25V bulk cap for Tic VIN
C3 = make("Cap100uF25V_C3", "C3", [
    (1, "+", Pin.types.PASSIVE),
    (2, "-", Pin.types.PASSIVE),
], footprint="Capacitor_THT:CP_Radial_D6.3mm_P2.50mm")

# ---------------------------------------------------------------------------
# Define nets and make connections
# ---------------------------------------------------------------------------

# +12V net
pwr_12v = Net("+12V")
pwr_12v += J1["+"], U1["VIN"], U4["VM"], U5["VIN"], SR1["+"], C1["+"], C3["+"]

# +5V net
pwr_5v = Net("+5V")
pwr_5v += U1["VOUT"], U2["VSYS"], M3["+5V"], C2["+"]

# +3V3 net
pwr_3v3 = Net("+3V3")
pwr_3v3 += U2["3V3"], U3["VIN"]

# GND net
gnd = Net("GND")
gnd += (J1["-"], U1["GND"], U2["GND"], U3["GND"], U4["GND"], U5["GND"],
        SR1["-"], M3["GND"], C1["-"], C2["-"], C3["-"])

# I2C_SDA: U2.GP0 -> U3.SDA
i2c_sda = Net("I2C_SDA")
i2c_sda += U2["GP0"], U3["SDA"]

# I2C_SCL: U2.GP1 -> U3.SCL
i2c_scl = Net("I2C_SCL")
i2c_scl += U2["GP1"], U3["SCL"]

# STP_TX: U2.GP4 -> U5.RX
stp_tx = Net("STP_TX")
stp_tx += U2["GP4"], U5["RX"]

# STP_RX: U2.GP5 <- U5.TX
stp_rx = Net("STP_RX")
stp_rx += U2["GP5"], U5["TX"]

# SOL_IN1: U2.GP10 -> U4.IN1
sol_in1 = Net("SOL_IN1")
sol_in1 += U2["GP10"], U4["IN1"]

# SOL_IN2: U2.GP11 -> U4.IN2
sol_in2 = Net("SOL_IN2")
sol_in2 += U2["GP11"], U4["IN2"]

# HAPT_EN: U2.GP14 -> U3.EN and U3.IN_TRIG
hapt_en = Net("HAPT_EN")
hapt_en += U2["GP14"], U3["EN"], U3["IN_TRIG"]

# SERVO_SIG: U2.GP15 -> M3.SIG
servo_sig = Net("SERVO_SIG")
servo_sig += U2["GP15"], M3["SIG"]

# STP_A1: U5.A1 <-> M2.A1
stp_a1 = Net("STP_A1")
stp_a1 += U5["A1"], M2["A1"]

# STP_A2: U5.A2 <-> M2.A2
stp_a2 = Net("STP_A2")
stp_a2 += U5["A2"], M2["A2"]

# STP_B1: U5.B1 <-> M2.B1
stp_b1 = Net("STP_B1")
stp_b1 += U5["B1"], M2["B1"]

# STP_B2: U5.B2 <-> M2.B2
stp_b2 = Net("STP_B2")
stp_b2 += U5["B2"], M2["B2"]

# VIB_A: U3.OUT+ <-> M1.+
vib_a = Net("VIB_A")
vib_a += U3["OUT+"], M1["+"]

# VIB_B: U3.OUT- <-> M1.-
vib_b = Net("VIB_B")
vib_b += U3["OUT-"], M1["-"]

# SOL_A: U4.OUT1 <-> SOL1.+
sol_a = Net("SOL_A")
sol_a += U4["OUT1"], SOL1["+"]

# SOL_B: U4.OUT2 <-> SOL1.-
sol_b = Net("SOL_B")
sol_b += U4["OUT2"], SOL1["-"]

# U5.ERR is left unconnected (optional fault line) - no net connection

# ---------------------------------------------------------------------------
# ERC, netlist, and SVG generation
# ---------------------------------------------------------------------------

ERC()
generate_netlist()
generate_svg()
