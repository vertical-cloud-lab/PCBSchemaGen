"""
Powder-Doser Single-Module Bench Rig – SKiDL Schematic
Vertical-Cloud-Lab / powder-doser PR #61

Generates: netlist + SVG for CELUS board-synthesis import.
"""

from skidl import (
    Part, Pin, Net, ERC, TEMPLATE, SKIDL,
    generate_netlist, generate_svg, set_default_tool, KICAD9
)

set_default_tool(KICAD9)

# ---------------------------------------------------------------------------
# Helper – build a SKIDL-defined part, instantiate it, and tag CELUS fields
# ---------------------------------------------------------------------------
def make(name, ref, pins, footprint, mpn, mfr, datasheet, block):
    t = Part(tool=SKIDL, name=name, ref_prefix=ref[0], dest=TEMPLATE,
             footprint=footprint)
    for num, pname, func in pins:
        t += Pin(num=num, name=pname, func=func)
    p = t(ref=ref)
    p.fields["MPN"]          = mpn
    p.fields["Manufacturer"] = mfr
    p.fields["Datasheet"]    = datasheet
    p.fields["Block"]        = block
    return p

# ===========================================================================
# COMPONENT INSTANTIATION
# ===========================================================================

# ---------------------------------------------------------------------------
# J1 – 12 V barrel-jack power input  (Adafruit #373, powder-doser BOM item 8)
# ---------------------------------------------------------------------------
J1 = make(
    name      = "BarrelJack_12V",
    ref       = "J1",
    pins      = [
        (1, "+", Pin.types.PWROUT),
        (2, "-", Pin.types.PWRIN),
    ],
    footprint = "Connector_BarrelJack:BarrelJack_CUI_PJ-002A",
    mpn       = "373",
    mfr       = "Adafruit",
    datasheet = "https://www.adafruit.com/product/373",
    block     = "POWER",
)

# ---------------------------------------------------------------------------
# U1 – Pololu D24V22F5 buck regulator (5 V / 2.2 A)
# ---------------------------------------------------------------------------
U1 = make(
    name      = "D24V22F5",
    ref       = "U1",
    pins      = [
        (1, "VIN",  Pin.types.PWRIN),
        (2, "GND",  Pin.types.PWRIN),
        (3, "VOUT", Pin.types.PWROUT),
    ],
    footprint = "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    mpn       = "2858",
    mfr       = "Pololu",
    datasheet = "https://www.pololu.com/product/2858",
    block     = "POWER",
)

# ---------------------------------------------------------------------------
# U2 – Raspberry Pi Pico W
# ---------------------------------------------------------------------------
U2 = make(
    name      = "PicoW",
    ref       = "U2",
    pins      = [
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
    ],
    footprint = "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical",
    mpn       = "SC0918",
    mfr       = "Raspberry Pi",
    datasheet = "https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf",
    block     = "MCU",
)

# ---------------------------------------------------------------------------
# U3 – Adafruit DRV2605L haptic driver breakout
# ---------------------------------------------------------------------------
U3 = make(
    name      = "DRV2605L",
    ref       = "U3",
    pins      = [
        (1, "VIN",     Pin.types.PWRIN),
        (2, "GND",     Pin.types.PWRIN),
        (3, "SDA",     Pin.types.BIDIR),
        (4, "SCL",     Pin.types.INPUT),
        (5, "EN",      Pin.types.INPUT),
        (6, "IN_TRIG", Pin.types.INPUT),
        (7, "OUT+",    Pin.types.OUTPUT),
        (8, "OUT-",    Pin.types.OUTPUT),
    ],
    footprint = "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
    mpn       = "2305",
    mfr       = "Adafruit",
    datasheet = "https://www.adafruit.com/product/2305",
    block     = "HAPTIC",
)

# ---------------------------------------------------------------------------
# M1 – 10 mm ERM coin motor
# ---------------------------------------------------------------------------
M1 = make(
    name      = "ERM_Coin_10mm",
    ref       = "M1",
    pins      = [
        (1, "+", Pin.types.PASSIVE),
        (2, "-", Pin.types.PASSIVE),
    ],
    footprint = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    mpn       = "1201",
    mfr       = "Adafruit",
    datasheet = "https://www.adafruit.com/product/1201",
    block     = "ACTUATOR",
)

# ---------------------------------------------------------------------------
# U4 – Adafruit DRV8871 motor driver breakout
# ---------------------------------------------------------------------------
U4 = make(
    name      = "DRV8871",
    ref       = "U4",
    pins      = [
        (1, "VM",   Pin.types.PWRIN),
        (2, "GND",  Pin.types.PWRIN),
        (3, "IN1",  Pin.types.INPUT),
        (4, "IN2",  Pin.types.INPUT),
        (5, "OUT1", Pin.types.OUTPUT),
        (6, "OUT2", Pin.types.OUTPUT),
    ],
    footprint = "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
    mpn       = "3190",
    mfr       = "Adafruit",
    datasheet = "https://www.adafruit.com/product/3190",
    block     = "MOTOR_DRIVE",
)

# ---------------------------------------------------------------------------
# SOL1 – JF-0530B 5 V solenoid
# ---------------------------------------------------------------------------
SOL1 = make(
    name      = "JF-0530B",
    ref       = "SOL1",
    pins      = [
        (1, "+", Pin.types.PASSIVE),
        (2, "-", Pin.types.PASSIVE),
    ],
    footprint = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    mpn       = "JF-0530B",
    mfr       = "Adafruit",
    datasheet = "https://www.adafruit.com/product/412",
    block     = "ACTUATOR",
)

# ---------------------------------------------------------------------------
# U5 – Pololu Tic T500 stepper motor controller
# ---------------------------------------------------------------------------
U5 = make(
    name      = "TicT500",
    ref       = "U5",
    pins      = [
        (1,  "VIN", Pin.types.PWRIN),
        (2,  "GND", Pin.types.PWRIN),
        (3,  "RX",  Pin.types.INPUT),
        (4,  "TX",  Pin.types.OUTPUT),
        (5,  "ERR", Pin.types.OUTPUT),
        (6,  "A1",  Pin.types.OUTPUT),
        (7,  "A2",  Pin.types.OUTPUT),
        (8,  "B1",  Pin.types.OUTPUT),
        (9,  "B2",  Pin.types.OUTPUT),
    ],
    footprint = "Connector_PinHeader_2.54mm:PinHeader_1x09_P2.54mm_Vertical",
    mpn       = "3134",
    mfr       = "Pololu",
    datasheet = "https://www.pololu.com/product/3134",
    block     = "STEPPER_DRIVE",
)

# ---------------------------------------------------------------------------
# SR1 – Pololu #3776 shunt regulator
# ---------------------------------------------------------------------------
SR1 = make(
    name      = "ShuntReg_3776",
    ref       = "SR1",
    pins      = [
        (1, "+", Pin.types.PWRIN),
        (2, "-", Pin.types.PWRIN),
    ],
    footprint = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    mpn       = "3776",
    mfr       = "Pololu",
    datasheet = "https://www.pololu.com/product/3776",
    block     = "POWER",
)

# ---------------------------------------------------------------------------
# M2 – NEMA-11 bipolar stepper motor
# ---------------------------------------------------------------------------
M2 = make(
    name      = "NEMA11_Stepper",
    ref       = "M2",
    pins      = [
        (1, "A1", Pin.types.PASSIVE),
        (2, "A2", Pin.types.PASSIVE),
        (3, "B1", Pin.types.PASSIVE),
        (4, "B2", Pin.types.PASSIVE),
    ],
    footprint = "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    mpn       = "11HS18-0674S",
    mfr       = "StepperOnline",
    datasheet = "https://www.omc-stepperonline.com/nema-11-bipolar-1-8deg-10ncm-14-16oz-in-0-67a-28x28x45mm-4-wires-11hs18-0674s",
    block     = "ACTUATOR",
)

# ---------------------------------------------------------------------------
# M3 – HD-1810MG hobby servo
# ---------------------------------------------------------------------------
M3 = make(
    name      = "HD-1810MG_Servo",
    ref       = "M3",
    pins      = [
        (1, "+5V", Pin.types.PWRIN),
        (2, "GND", Pin.types.PWRIN),
        (3, "SIG", Pin.types.INPUT),
    ],
    footprint = "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    mpn       = "HD-1810MG",
    mfr       = "Power HD",
    datasheet = "https://www.adafruit.com/product/1142",
    block     = "SERVO",
)

# ---------------------------------------------------------------------------
# C1 – 100 uF / 25 V bulk cap (12 V rail)
# ---------------------------------------------------------------------------
C1 = make(
    name      = "Cap_100uF_25V",
    ref       = "C1",
    pins      = [
        (1, "+", Pin.types.PASSIVE),
        (2, "-", Pin.types.PASSIVE),
    ],
    footprint = "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
    mpn       = "UVR1E101MDD",
    mfr       = "Nichicon",
    datasheet = "https://www.nichicon.co.jp/series_items/catalog_pdf/ja/pdf/xja043/uvr.pdf",
    block     = "BULK_DECOUPLE",
)

# ---------------------------------------------------------------------------
# C2 – 100 uF / 10 V bulk cap (5 V rail)
# ---------------------------------------------------------------------------
C2 = make(
    name      = "Cap_100uF_10V",
    ref       = "C2",
    pins      = [
        (1, "+", Pin.types.PASSIVE),
        (2, "-", Pin.types.PASSIVE),
    ],
    footprint = "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
    mpn       = "UVR1A101MDD",
    mfr       = "Nichicon",
    datasheet = "https://www.nichicon.co.jp/series_items/catalog_pdf/ja/pdf/xja043/uvr.pdf",
    block     = "BULK_DECOUPLE",
)

# ---------------------------------------------------------------------------
# C3 – 100 uF / 25 V bulk cap (Tic T500 VIN)
# ---------------------------------------------------------------------------
C3 = make(
    name      = "Cap_100uF_25V_Tic",
    ref       = "C3",
    pins      = [
        (1, "+", Pin.types.PASSIVE),
        (2, "-", Pin.types.PASSIVE),
    ],
    footprint = "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
    mpn       = "UVR1E101MDD",
    mfr       = "Nichicon",
    datasheet = "https://www.nichicon.co.jp/series_items/catalog_pdf/ja/pdf/xja043/uvr.pdf",
    block     = "BULK_DECOUPLE",
)

# ===========================================================================
# NET DEFINITIONS AND CONNECTIONS
# ===========================================================================

# ---------------------------------------------------------------------------
# +12V rail
# ---------------------------------------------------------------------------
net_12V = Net("+12V")
net_12V += (
    J1["+"],
    U1["VIN"],
    U4["VM"],
    U5["VIN"],
    SR1["+"],
    C1["+"],
    C3["+"],
)

# ---------------------------------------------------------------------------
# +5V rail
# ---------------------------------------------------------------------------
net_5V = Net("+5V")
net_5V += (
    U1["VOUT"],
    U2["VSYS"],
    M3["+5V"],
    C2["+"],
)

# ---------------------------------------------------------------------------
# +3V3 rail
# ---------------------------------------------------------------------------
net_3V3 = Net("+3V3")
net_3V3 += (
    U2["3V3"],
    U3["VIN"],
)

# ---------------------------------------------------------------------------
# GND rail
# ---------------------------------------------------------------------------
net_GND = Net("GND")
net_GND += (
    J1["-"],
    U1["GND"],
    U2["GND"],
    U3["GND"],
    U4["GND"],
    U5["GND"],
    SR1["-"],
    M3["GND"],
    C1["-"],
    C2["-"],
    C3["-"],
)

# ---------------------------------------------------------------------------
# I2C bus
# ---------------------------------------------------------------------------
net_I2C_SDA = Net("I2C_SDA")
net_I2C_SDA += U2["GP0"], U3["SDA"]

net_I2C_SCL = Net("I2C_SCL")
net_I2C_SCL += U2["GP1"], U3["SCL"]

# ---------------------------------------------------------------------------
# UART to Tic T500 stepper controller
# ---------------------------------------------------------------------------
net_STP_TX = Net("STP_TX")
net_STP_TX += U2["GP4"], U5["RX"]

net_STP_RX = Net("STP_RX")
net_STP_RX += U2["GP5"], U5["TX"]

# ---------------------------------------------------------------------------
# Solenoid H-bridge control (DRV8871)
# ---------------------------------------------------------------------------
net_SOL_IN1 = Net("SOL_IN1")
net_SOL_IN1 += U2["GP10"], U4["IN1"]

net_SOL_IN2 = Net("SOL_IN2")
net_SOL_IN2 += U2["GP11"], U4["IN2"]

# ---------------------------------------------------------------------------
# Haptic enable / trigger
# ---------------------------------------------------------------------------
net_HAPT_EN = Net("HAPT_EN")
net_HAPT_EN += U2["GP14"], U3["EN"], U3["IN_TRIG"]

# ---------------------------------------------------------------------------
# Servo signal
# ---------------------------------------------------------------------------
net_SERVO_SIG = Net("SERVO_SIG")
net_SERVO_SIG += U2["GP15"], M3["SIG"]

# ---------------------------------------------------------------------------
# Stepper motor coil connections (Tic T500 -> NEMA-11)
# ---------------------------------------------------------------------------
net_STP_A1 = Net("STP_A1")
net_STP_A1 += U5["A1"], M2["A1"]

net_STP_A2 = Net("STP_A2")
net_STP_A2 += U5["A2"], M2["A2"]

net_STP_B1 = Net("STP_B1")
net_STP_B1 += U5["B1"], M2["B1"]

net_STP_B2 = Net("STP_B2")
net_STP_B2 += U5["B2"], M2["B2"]

# ---------------------------------------------------------------------------
# ERM vibration motor (DRV2605L -> ERM coin motor)
# ---------------------------------------------------------------------------
net_VIB_A = Net("VIB_A")
net_VIB_A += U3["OUT+"], M1["+"]

net_VIB_B = Net("VIB_B")
net_VIB_B += U3["OUT-"], M1["-"]

# ---------------------------------------------------------------------------
# Solenoid drive (DRV8871 -> JF-0530B)
# ---------------------------------------------------------------------------
net_SOL_A = Net("SOL_A")
net_SOL_A += U4["OUT1"], SOL1["+"]

net_SOL_B = Net("SOL_B")
net_SOL_B += U4["OUT2"], SOL1["-"]

# ---------------------------------------------------------------------------
# U5.ERR – left unconnected (optional fault line per spec)
# ---------------------------------------------------------------------------
# No connection needed; SKiDL leaves unconnected pins as NC by default.

# ===========================================================================
# DESIGN-RULE CHECK  →  NETLIST  →  SVG
# ===========================================================================
ERC()
generate_netlist()
generate_svg()
