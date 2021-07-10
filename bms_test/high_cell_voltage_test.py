from rd6006 import RD6006
from uni_t import DMMMonitor
from riden import RidenMonitor
from recq.binary import BinaryMonitor
from recq.canbus import CanBusMonitor
from instrument_logger import InstrumentLogger
import can
import os
import time


# TODO: consider moving all setup to another script since it will be common for all tests
# setup powersupply and monitor
if os.path.exists('/dev/ttyUSBrd6018'):
    powersupply_port = '/dev/ttyUSBrd6018'
else:
    print("No powersupply detected. Enter port (e.g., /dev/ttyUSB0):")
    powersupply_port = input()

powersupply = RD6006(powersupply_port)
powersupply_monitor = RidenMonitor(powersupply)

# setup multimeter monitor
if os.path.exists('/dev/ttyUSBut61e'):
    dmm_port = '/dev/ttyUSBut61e'
else:
    print("No multimeter detected. Enter port (e.g., /dev/ttyUSB0):")
    dmm_port = input()

dmm_monitor = DMMMonitor(dmm_port)
print("Enter the name of the parameter measured by the multimeter (e.g., 'Cell_1_Voltage'):")
dmm_monitor.parametername = input()
dmm_monitor.start()


# setup recq binary monitor
bin_monitor = BinaryMonitor()

# setup canbus and recq can monitor
os.system("sudo /sbin/ip link set can0 up type can bitrate 250000")
bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=250000)         
notifier = can.Notifier(bus)
can_monitor = CanBusMonitor()
notifier.add_listener(can_monitor)

# setup logger
logger = InstrumentLogger()
logger.addinstrument(powersupply_monitor)
logger.addinstrument(dmm_monitor)
logger.addinstrument(bin_monitor)
logger.addinstrument(can_monitor)
print("Enter log file prefix:")
logger.filenameprefix = input()

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

# set limits and test parameters
max_voltage = 31
initial_voltage = 26
powersupply.voltage = initial_voltage


# ultimately it would be nice to pull all these parameters from the BMS
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
logger.start()

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
