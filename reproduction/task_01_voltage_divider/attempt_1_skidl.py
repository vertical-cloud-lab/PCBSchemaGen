from skidl import *

# 1. Define Nets
vin    = Net("VIN")
vsense = Net("VSENSE")
gnd    = Net("GND")

# 2. Instantiate Components

# Top resistor of divider: 100k
r1 = Part("test", "R", value="100k", footprint="test:R_0805")

# Bottom resistor of divider: 10k
r2 = Part("test", "R", value="10k", footprint="test:R_0805")

# Filter capacitor across bottom resistor: 100nF
c1 = Part("test", "C", value="100nF", footprint="test:C_0805")

# 3. Connections

# VIN -> R1 -> VSENSE
vin      += r1[1]
r1[2]    += vsense

# VSENSE -> R2 -> GND
vsense   += r2[1]
r2[2]    += gnd

# C1 across R2 (VSENSE to GND) for noise filtering
c1[1]    += vsense
c1[2]    += gnd

# 4. ERC Check
ERC()
