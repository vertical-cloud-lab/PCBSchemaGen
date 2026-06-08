from skidl import *

# ─────────────────────────────────────────────
# Top-level nets
# ─────────────────────────────────────────────
vin      = Net("VIN")       # Main DC bus positive
vout     = Net("VOUT")      # Buck converter output
pgnd     = Net("PGND")      # Power ground
vsw      = Net("VSW")       # Switch node

pwm_h    = Net("PWM_H")     # High-side PWM input
pwm_l    = Net("PWM_L")     # Low-side PWM input

# Primary-side logic/control power (12V assumed, provided externally)
vcc_pri  = Net("VCC_PRI")   # 12V primary supply for isolated DC-DCs
gnd_pri  = Net("GND_PRI")   # Primary ground

# ─────────────────────────────────────────────
# High-side isolated power supply (MGJ2D121505SC_H)
# ─────────────────────────────────────────────
iso_psu_h = Part("test", "MGJ2D121505SC", footprint="test:MGJ2D121505SC")
iso_psu_h.ref = "U_ISO_H"

vdd_h    = Net("VDD_H")     # +15V high-side gate driver supply
gnd_sec_h = Net("GND_SEC_H") # Isolated 0V for high-side
vee_h    = Net("VEE_H")     # -9V high-side gate driver supply

iso_psu_h[1] += vcc_pri     # Primary +VIN
iso_psu_h[2] += gnd_pri     # Primary -VIN
iso_psu_h[7] += vdd_h       # Secondary +VOUT (+15V)
iso_psu_h[6] += gnd_sec_h   # Secondary 0V
iso_psu_h[5] += vee_h       # Secondary -VOUT (-9V)

# Decoupling on high-side isolated PSU output
c_vdd_h = Part("test", "C", value="100nF", footprint="test:C_0805")
c_vdd_h[1] += vdd_h
c_vdd_h[2] += gnd_sec_h

c_vee_h = Part("test", "C", value="100nF", footprint="test:C_0805")
c_vee_h[1] += gnd_sec_h
c_vee_h[2] += vee_h

c_bulk_h = Part("test", "C", value="10uF", footprint="test:C_0805")
c_bulk_h[1] += vdd_h
c_bulk_h[2] += vee_h

# ─────────────────────────────────────────────
# Low-side isolated power supply (MGJ2D121505SC_L)
# ─────────────────────────────────────────────
iso_psu_l = Part("test", "MGJ2D121505SC", footprint="test:MGJ2D121505SC")
iso_psu_l.ref = "U_ISO_L"

vdd_l    = Net("VDD_L")     # +15V low-side gate driver supply
gnd_sec_l = Net("GND_SEC_L") # Isolated 0V for low-side
vee_l    = Net("VEE_L")     # -9V low-side gate driver supply

iso_psu_l[1] += vcc_pri     # Primary +VIN
iso_psu_l[2] += gnd_pri     # Primary -VIN
iso_psu_l[7] += vdd_l       # Secondary +VOUT (+15V)
iso_psu_l[6] += gnd_sec_l   # Secondary 0V
iso_psu_l[5] += vee_l       # Secondary -VOUT (-9V)

# Decoupling on low-side isolated PSU output
c_vdd_l = Part("test", "C", value="100nF", footprint="test:C_0805")
c_vdd_l[1] += vdd_l
c_vdd_l[2] += gnd_sec_l

c_vee_l = Part("test", "C", value="100nF", footprint="test:C_0805")
c_vee_l[1] += gnd_sec_l
c_vee_l[2] += vee_l

c_bulk_l = Part("test", "C", value="10uF", footprint="test:C_0805")
c_bulk_l[1] += vdd_l
c_bulk_l[2] += vee_l

# ─────────────────────────────────────────────
# High-side gate driver (UCC5390E_H)
# ─────────────────────────────────────────────
drv_h = Part("test", "UCC5390E", footprint="test:UCC5390E")
drv_h.ref = "U_DRV_H"

# Primary side connections
drv_h[1] += vcc_pri          # VCC1 - primary supply
drv_h[4] += gnd_pri          # GND1 - primary ground
drv_h[2] += pwm_h            # IN+  - PWM high-side input
drv_h[3] += gnd_pri          # IN-  - tied to primary GND (active high input)

# Secondary side connections
drv_h[5] += vdd_h            # VCC2 - +15V
drv_h[7] += gnd_sec_h        # GND2 - isolated 0V (also connects to KS)
drv_h[8] += vee_h            # VEE2 - -9V

# Decoupling on driver primary
c_drv_h_pri = Part("test", "C", value="100nF", footprint="test:C_0805")
c_drv_h_pri[1] += vcc_pri
c_drv_h_pri[2] += gnd_pri

# Decoupling on driver secondary
c_drv_h_sec = Part("test", "C", value="100nF", footprint="test:C_0805")
c_drv_h_sec[1] += vdd_h
c_drv_h_sec[2] += gnd_sec_h

# ─────────────────────────────────────────────
# High-side gate resistor network (turn-on / turn-off)
# ─────────────────────────────────────────────
# Driver output net (before gate resistors)
drv_h_out = Net("DRV_H_OUT")
drv_h[6] += drv_h_out        # OUT pin of high-side driver

# Gate node of high-side MOSFET
gate_h = Net("GATE_H")

# Turn-on resistor
r_gon_h = Part("test", "R", value="10R", footprint="test:R_0805")
r_gon_h.ref = "R_GON_H"
r_gon_h[1] += drv_h_out
r_gon_h[2] += gate_h

# Turn-off resistor (parallel path via diode)
r_goff_h = Part("test", "R", value="2R2", footprint="test:R_0805")
r_goff_h.ref = "R_GOFF_H"

# Anti-parallel diode for turn-off path (anode toward gate, cathode toward driver)
# During turn-off: current flows gate -> diode anode(K pin=1) -> diode cathode(A pin=2) -> r_goff -> driver
# D component: pin1=K(Anode in schematic label), pin2=A(Cathode in schematic label)
# Note: per component definition pin1 is labeled K(Anode) and pin2 is A(Cathode) - using as specified
d_goff_h = Part("test", "D", footprint="test:BAT165")
d_goff_h.ref = "D_GOFF_H"

# Turn-off path: gate_h -> D anode(pin2) -> D cathode(pin1) -> r_goff_h -> drv_h_out
# Anti-parallel to turn-on resistor: diode conducts during turn-off (gate discharging)
d_goff_h[2] += gate_h        # Anode at gate (pin2 = A = Cathode label, but connects to gate for turn-off)
d_goff_h[1] += r_goff_h[1]  # Cathode toward driver side
r_goff_h[2] += drv_h_out

# Kelvin source net for high-side
ks_h = Net("KS_H")
# GND2 of driver connects to Kelvin Source of high-side MOSFET
gnd_sec_h += ks_h            # Driver secondary GND tied to KS

# ─────────────────────────────────────────────
# High-side MOSFET (IMZA65R015M2H)
# ─────────────────────────────────────────────
q_h = Part("test", "IMZA65R015M2H", footprint="test:IMZA65R015M2H")
q_h.ref = "Q_H"

q_h[1] += vin                # Drain  -> VIN (DC bus)
q_h[2] += vsw                # Source -> Switch node
q_h[3] += ks_h               # Kelvin Source -> driver GND2
q_h[4] += gate_h             # Gate   -> gate resistor network

# ─────────────────────────────────────────────
# Low-side gate driver (UCC5390E_L)
# ─────────────────────────────────────────────
drv_l = Part("test", "UCC5390E", footprint="test:UCC5390E")
drv_l.ref = "U_DRV_L"

# Primary side connections
drv_l[1] += vcc_pri          # VCC1
drv_l[4] += gnd_pri          # GND1
drv_l[2] += pwm_l            # IN+
drv_l[3] += gnd_pri          # IN-

# Secondary side connections
drv_l[5] += vdd_l            # VCC2 - +15V
drv_l[7] += gnd_sec_l        # GND2 - isolated 0V
drv_l[8] += vee_l            # VEE2 - -9V

# Decoupling on driver primary
c_drv_l_pri = Part("test", "C", value="100nF", footprint="test:C_0805")
c_drv_l_pri[1] += vcc_pri
c_drv_l_pri[2] += gnd_pri

# Decoupling on driver secondary
c_drv_l_sec = Part("test", "C", value="100nF", footprint="test:C_0805")
c_drv_l_sec[1] += vdd_l
c_drv_l_sec[2] += gnd_sec_l

# ─────────────────────────────────────────────
# Low-side gate resistor network (turn-on / turn-off)
# ─────────────────────────────────────────────
drv_l_out = Net("DRV_L_OUT")
drv_l[6] += drv_l_out        # OUT pin of low-side driver

gate_l = Net("GATE_L")

# Turn-on resistor
r_gon_l = Part("test", "R", value="10R", footprint="test:R_0805")
r_gon_l.ref = "R_GON_L"
r_gon_l[1] += drv_l_out
r_gon_l[2] += gate_l

# Turn-off resistor with anti-parallel diode
r_goff_l = Part("test", "R", value="2R2", footprint="test:R_0805")
r_goff_l.ref = "R_GOFF_L"

d_goff_l = Part("test", "D", footprint="test:BAT165")
d_goff_l.ref = "D_GOFF_L"

d_goff_l[2] += gate_l        # Anode at gate
d_goff_l[1] += r_goff_l[1]  # Cathode toward driver
r_goff_l[2] += drv_l_out

# Kelvin source net for low-side
ks_l = Net("KS_L")
gnd_sec_l += ks_l            # Driver secondary GND tied to KS

# ─────────────────────────────────────────────
# Low-side MOSFET (IMZA65R015M2H)
# ─────────────────────────────────────────────
q_l = Part("test", "IMZA65R015M2H", footprint="test:IMZA65R015M2H")
q_l.ref = "Q_L"

q_l[1] += vsw                # Drain  -> Switch node
q_l[2] += pgnd               # Source -> Power GND
q_l[3] += ks_l               # Kelvin Source -> driver GND2
q_l[4] += gate_l             # Gate   -> gate resistor network

# ─────────────────────────────────────────────
# VBUS decoupling capacitors (minimum 8 required)
# ─────────────────────────────────────────────
vbus_dec_values = ["100nF", "100nF", "100nF", "100nF",
                   "100nF", "100nF", "100nF", "100nF",
                   "10uF",  "10uF"]

for i, val in enumerate(vbus_dec_values):
    c = Part("test", "C", value=val, footprint="test:C_0805")
    c.ref = "C_VBUS{}".format(i + 1)
    c[1] += vin
    c[2] += pgnd

# ─────────────────────────────────────────────
# Output LC filter
# ─────────────────────────────────────────────
# Power inductor: pins 1-6 = Terminal A, pins 7-12 = Terminal B
l_out = Part("test", "Inductor_power", footprint="test:Inductor_power")
l_out.ref = "L_OUT"
l_out.value = "10uH"

# Connect all A-side pins to VSW
l_out[1] += vsw
l_out[2] += vsw
l_out[3] += vsw
l_out[4] += vsw
l_out[5] += vsw
l_out[6] += vsw

# Connect all B-side pins to VOUT
l_out[7]  += vout
l_out[8]  += vout
l_out[9]  += vout
l_out[10] += vout
l_out[11] += vout
l_out[12] += vout

# Output filter capacitors
c_out1 = Part("test", "C", value="100uF", footprint="test:C_0805")
c_out1.ref = "C_OUT1"
c_out1[1] += vout
c_out1[2] += pgnd

c_out2 = Part("test", "C", value="100uF", footprint="test:C_0805")
c_out2.ref = "C_OUT2"
c_out2[1] += vout
c_out2[2] += pgnd

c_out3 = Part("test", "C", value="100nF", footprint="test:C_0805")
c_out3.ref = "C_OUT3"
c_out3[1] += vout
c_out3[2] += pgnd

# ─────────────────────────────────────────────
# Primary-side decoupling for VCC_PRI
# ─────────────────────────────────────────────
c_vcc_pri1 = Part("test", "C", value="100nF", footprint="test:C_0805")
c_vcc_pri1.ref = "C_VCCPRI1"
c_vcc_pri1[1] += vcc_pri
c_vcc_pri1[2] += gnd_pri

c_vcc_pri2 = Part("test", "C", value="10uF", footprint="test:C_0805")
c_vcc_pri2.ref = "C_VCCPRI2"
c_vcc_pri2[1] += vcc_pri
c_vcc_pri2[2] += gnd_pri

# ─────────────────────────────────────────────
ERC()
