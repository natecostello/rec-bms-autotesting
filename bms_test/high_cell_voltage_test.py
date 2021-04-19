from rd6006 import RD6006
from uni_t import DMMMonitor
from recq.binary import BinaryMonitor
from recq.canbus import CanBusMonitor

import os
import time
    
# determine power supply and DMM usb
print("Enter device path for power supply (e.g., USB0):")
powerSupplyInterface = '/dev/tty' + input().upper()

print("Enter device path for DMM (e.g., USB1):")
dmmInterface = input()

# setup
ps = RD6006(powerSupplyInterface)

#wrapper class to round (maybe refactor later)
class RD6006rounded:
    def __init__(self, ps):
        self._powersupply = ps
    
    @property
    def voltage(self):
        return round(self._powersupply.voltage, 2)
    
    @property
    def measvoltage(self):
        return round(self._powersupply.measvoltage, 2)
    
    @voltage.setter
    def voltage(self, value):
        self._powersupply.voltage = value

powersupply = RD6006rounded(ps)

dmm_monitor = DMMMonitor('volts', interface=dmmInterface)
dmm_monitor.start()

bin_monitor = BinaryMonitor()

os.system("sudo /sbin/ip link set can0 up type can bitrate 250000")
time.sleep(1)
can_monitor = CanBusMonitor()
can_monitor.start()

def log():
    print(f'CE State                {bin_monitor.chargeEnable}')
    print(f'Contactor State         {bin_monitor.contactor}')
    print(f'DMM Max Cell Voltage    {dmm_monitor.value}')
    print(f'CAN Max Cell Voltage    {can_monitor.max_cell_voltage}')
    print(f'CAN Min Cell Voltage    {can_monitor.min_cell_voltage}')
    print(f'CCL                     {can_monitor.charge_current_limit}')
    print(f'CVL                     {can_monitor.charge_voltage_limit}')
    print(f'CAN State of Charge     {can_monitor.state_of_charge_hi_res}')
    print(f'CAN Alarm Bits          {can_monitor.alarmBits}')
    print(f'CAN Warn Bits           {can_monitor.warningBits}')

powersupply_voltage_setting = powersupply.voltage
powersupply_voltage_output = powersupply.measvoltage

max_voltage = 31

# prompt user for parameters
print("Use default BMS params? (Y/N)")
default = input()
if default == 'Y':
    bmin = 3.45
    bvol = 3.58
    cmax = 3.85
    maxh = 0.25
    char = 3.58
    chis = 0.25
    maxc = 70.0
else:
    print("Enter the following parameters from the current BMS configuration.")

    print("Enter 'Balance start voltage' aka 'BMIN':")
    bmin = float(input())

    print("Enter 'Balance end voltage' aka 'BVOL':")
    bvol = float(input())

    print("Enter 'Cell over-voltage switch-off per cell' aka 'CMAX':")
    cmax = float(input())

    print("Enter 'Over-voltage switch-off hysteresis per cell' aka 'MAXH':")
    maxh = float(input())

    print("Enter 'Cell end of charge voltage' aka 'CHAR':")
    char = float(input())

    print("Enter 'End of charge hysteresis per cell' aka 'CHIS':")
    chis = float(input())

    print("Enter 'Maximum charging current' aka 'MAXC':")
    maxc = float(input())

# promp user to start
print("Press Enter to Start")
input()
# start logging

# prompt user to turn on battery
print("Turn on Battery")

# verify contactor close and CE signal
while not bin_monitor.contactor:
    time.sleep(0.1)

print("Contactor Closed")

# raise voltage until CCL is lowered LOG - verify high cell ~BMIN
while can_monitor.charge_current_limit >= maxc:
    powersupply_voltage_setting += 0.05
    if powersupply_voltage_setting < max_voltage:
        powersupply.voltage = powersupply_voltage_setting
    else:
        print("maximum allowed voltage exceeded")
        raise NameError("MaxVoltageExceeded")
    time.sleep(2)
    print(f"actual output voltage: {powersupply.measvoltage}  can max cell: {can_monitor.max_cell_voltage}", end = "\r")
    

print("Threshold for lowering charge current limit reached")
time.sleep(1)
log()
print(f"Criteria for pass is abs(DMM Max Cell Voltage - Balance Start Voltage) < 0.05")
testvalue = abs(dmm_monitor.value - bmin)
print(f"Result is {testvalue}")
if testvalue <= 0.05:
    print("PASS")
else:
    print("FAIL")

#print("Press enter to continue test...")
#x = input()
        
# raise voltage until CE removed and LOG - verify low cell ~CHAR
while bin_monitor.chargeEnable:
    powersupply_voltage_setting += 0.05
    if powersupply_voltage_setting < max_voltage:
        powersupply.voltage = powersupply_voltage_setting
    else:
        print("maximum allowed voltage exceeded")
        raise NameError("MaxVoltageExceeded")
    time.sleep(2)
    print(f"actual output voltage: {powersupply.measvoltage}  can max cell: {can_monitor.max_cell_voltage}", end = "\r")
    
print("Threshold for removing charge enable reached")
time.sleep(1)
log()
print(f"Criteria for pass is abs(Can Min Cell Voltage - Cell end of charge voltage) < 0.05")
testvalue = abs(can_monitor.min_cell_voltage - char)
print(f"Result is {testvalue}")
if testvalue <= 0.05:
    print("PASS")
else:
    print("FAIL")


# raise voltage until Contactor open and LOG - verify high cell ~CMAX
while bin_monitor.contactor:
    powersupply_voltage_setting += 0.05
    if powersupply_voltage_setting < max_voltage:
        powersupply.voltage = powersupply_voltage_setting
    else:
        print("maximum allowed voltage exceeded")
        raise NameError("MaxVoltageExceeded")
    time.sleep(2)
    print(f"actual output voltage: {powersupply.measvoltage}  can max cell: {can_monitor.max_cell_voltage}", end = "\r")
    
print("Threshold for cell over voltage disconnect reached")
time.sleep(1)
log()
print(f"Criteria for pass is abs(Can Max Cell Voltage - Cell over-voltage switch-off per cell) < 0.05")
testvalue = abs(can_monitor.max_cell_voltage - cmax)
print(f"Result is {testvalue}")
if testvalue <= 0.05:
    print("PASS")
else:
    print("FAIL")


# stop

# lower voltage until contactor close and LOG
while not bin_monitor.contactor:
    powersupply_voltage_setting -= 0.05
    if powersupply_voltage_setting < max_voltage:
        powersupply.voltage = powersupply_voltage_setting
    else:
        print("maximum allowed voltage exceeded")
        raise NameError("MaxVoltageExceeded")
    time.sleep(2)
    print(f"actual output voltage: {powersupply.measvoltage}  can max cell: {can_monitor.max_cell_voltage}", end = "\r")
    
print("Threshold for cell over voltage reconnect reached")
time.sleep(1)
log()
print(f"Criteria for pass is abs(Can Max Cell Voltage - (Cell over-voltage switch-off per cell - hysteresis)) < 0.05")
testvalue = abs(can_monitor.max_cell_voltage - (cmax - maxh))
print(f"Result is {testvalue}")
if testvalue <= 0.05:
    print("PASS")
else:
    print("FAIL")

# lower voltage until CE applied and LOG 
while not bin_monitor.chargeEnable:
    powersupply_voltage_setting -= 0.05
    if powersupply_voltage_setting < max_voltage:
        powersupply.voltage = powersupply_voltage_setting
    else:
        print("maximum allowed voltage exceeded")
        raise NameError("MaxVoltageExceeded")
    if powersupply_voltage_setting <= 26.0:
        print("nominal voltage reached")
        break
    time.sleep(2)
    print(f"actual output voltage: {powersupply.measvoltage}  can max cell: {can_monitor.max_cell_voltage}", end = "\r")
    
print("Threshold for restoring charge enablec reached")
time.sleep(1)
log()
print(f"Criteria for pass is abs(Can Max Cell Voltage - (Cell end of charge voltage - hysteresis)) < 0.05")
testvalue = abs(can_monitor.max_cell_voltage - (char - chis))
print(f"Result is {testvalue}")
if testvalue <= 0.05:
    print("PASS")
else:
    print("FAIL")

# lower voltage until nominal 26V
while powersupply_voltage_setting > 26.0:
    powersupply_voltage_setting -= 0.05
    if powersupply_voltage_setting < max_voltage:
        powersupply.voltage = powersupply_voltage_setting
    else:
        print("maximum allowed voltage exceeded")
        raise NameError("MaxVoltageExceeded")
    time.sleep(2)
    print(f"actual output voltage: {powersupply.measvoltage}  can max cell: {can_monitor.max_cell_voltage}", end = "\r")
    
print("Test Complete")
