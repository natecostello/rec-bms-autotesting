from riden.registers import TIME_MINUTE
from riden_monitor import RidenMonitor
from uni_t import DMMMonitor
from riden import Riden
from recq.binary import BinaryMonitor
from recq.canbus import CanBusMonitor
from instrument_logger import InstrumentLogger
import can
import os
import time
import unittest
from standard_setup import BMSTestFixture
from datetime import datetime


class HighCellVoltageTest(unittest.TestCase):
    """"This test case verifies response and protections to high cell voltage.  Initial conditions: Power supply providing 26V and battery is ON."""
    def setUp(self) -> None:
        
        # power supply parameters
        self.initial_voltage = 26.0
        self.voltage_limit = 31.0
        self.voltage_increment = 0.01

        # default BMS Parameters
        # ultimately it would be nice to pull all these parameters from the BMS
        self.bmin = 3.45 # 'Balance Start Voltage'
        self.bvol = 3.58 # 'Balance End Voltage'
        self.cmax = 3.85 # 'Cell over-voltage switch-off per cell
        self.maxh = 0.25 # 'Over-voltage switch-off hysteresis per cell'
        self.char = 3.58 # 'Cell end of charge voltage'
        self.chis = 0.25 # 'End of charge hysterisis per cell'
        self.maxc = 70.0 # 'Maximum charging curren'

        self.test_fixture = BMSTestFixture()
        self.test_fixture.powersupply.set_voltage_set(self.initial_voltage)
        self.test_fixture.start()
        time.sleep(1)

        
        # Walk Voltage down to min cell voltage == CLOW evidenced by SOC <= 3
        while self.test_fixture.can_monitor.state_of_charge_hi_res > 3:
            self.decrement_voltage_and_wait()
        


        self.test_fixture.logger.filename = 'rising_voltage_test'
        self.test_fixture.logger.start()

        # Walk Voltage Up To max cell voltage == bmin evidenced by reduction in CCL
        while self.test_fixture.can_monitor.charge_current_limit >= self.maxc:
            self.increment_voltage_and_wait()
        
        # hold at this voltage and note parameters
        time.sleep(10)

        self.max_cell_voltage_at_ccl_reduction = self.test_fixture.can_monitor.max_cell_voltage
        self.charge_voltage_limit_at_ccl_reduction = self.test_fixture.can_monitor.charge_voltage_limit

        # Walk Voltage Up To max cell voltage == 0.502*(bmin+bvol) evidenced by SOC >= 96
        while self.test_fixture.can_monitor.state_of_charge_hi_res < 96.0:
            self.increment_voltage_and_wait()
        
        # hold at this voltage and note parameters
        self.min_cell_voltage_at_soc_to_96 = self.test_fixture.can_monitor.min_cell_voltage


        # Walk Voltage up to min cell voltage == char evidenced by reduction in CVL
        while self.test_fixture.can_monitor.charge_voltage_limit >= 28.7: # This value is as reported via CAN normally.  Note sure what the basis is. 
            self.increment_voltage_and_wait()
        
        # hold at this voltage and note parameters
        time.sleep(10)

        self.min_cell_voltage_at_cvl_reduction = self.test_fixture.can_monitor.min_cell_voltage
        self.charge_voltage_limit_at_cvl_reduction = self.test_fixture.can_monitor.charge_voltage_limit
        # In this condition per manual, CVL is set to = num_cells * (char - 0.2 * chis)
        self.soc_hr_at_cvl_reduction = self.test_fixture.can_monitor.state_of_charge_hi_res # should be 100
        self.soc_at_cvl_reductioin = self.test_fixture.can_monitor.state_of_charge # should be 100
        self.charge_enable_status_at_cvl_reductioin = self.test_fixture.bin_monitor.chargeEnable # should be off 

        # Walk voltage up to cutoff
        while self.test_fixture.bin_monitor.contactor:
            self.increment_voltage_and_wait()
        
        # hold at this voltage and note parameters
        time.sleep(1)
        self.max_cell_voltage_at_relay_cutoff = self.test_fixture.can_monitor.max_cell_voltage # should be cmax + maxh
        self.charge_enable_status_at_relay_cutoff = self.test_fixture.bin_monitor.chargeEnable # should be off
 
        
        time.sleep(1)
        self.reset_voltage()
        time.sleep(10)
        self.test_fixture.logger.stop()
        




        # self.test_fixture.logger.filename = 'high_cell_voltage_test_' + str(datetime.now()).replace(" ", "_").replace(":", "_")

    def test_charge_current_limit_reduction(self):
        # TODO: Rewrite to just compare values

        self.test_fixture.logger.filename = 'charge_current_limit_reduction_test'
        self.test_fixture.logger.start()

        time.sleep(2)

        self.assertEqual(self.test_fixture.bin_monitor.contactor, True, msg="contactor is not closed but should be")
        self.assertEqual(self.test_fixture.bin_monitor.chargeEnable, True, msg="chargeEnable is false but should be true")
        

        while self.test_fixture.can_monitor.charge_current_limit >= self.maxc:
            self.increment_voltage_and_wait()
        
        self.assertAlmostEqual(self.test_fixture.can_monitor.max_cell_voltage, self.bmin, 2, msg="Charge Limit Reduction Voltage Mismatch: Max Cell Voltage = " + str(self.test_fixture.can_monitor.max_cell_voltage) + ', BMIN = ' + str(self.bmin))
        
        #hold at this voltage

        time.sleep(10)
        self.reset_voltage()
        time.sleep(10)
        self.test_fixture.logger.stop()
        
    # TODO: Rewrite remaining test cases

    def increment_voltage_and_wait(self):
        voltage_setpoint = self.test_fixture.powersupply.get_voltage_set()
        if voltage_setpoint + self.voltage_increment < self.voltage_limit:
            self.test_fixture.powersupply.set_voltage_set(voltage_setpoint + self.voltage_increment)
            time.sleep(2)
        else:
            self.reset_voltage()
            raise NameError("Max Voltage Limit Exceeded")

    def decrement_voltage_and_wait(self):
        voltage_setpoint = self.test_fixture.powersupply.get_voltage_set()
        self.test_fixture.powersupply.set_voltage_set(voltage_setpoint - self.voltage_increment)
        time.sleep(2)

    def reset_voltage(self):
        self.test_fixture.powersupply.set_voltage_set(self.initial_voltage)
        
        





# # ultimately it would be nice to pull all these parameters from the BMS
# # prompt user for parameters


# # promp user to start
# print("Press Enter to Start")
# input()

# # start logging
# logger.start()

# # prompt user to turn on battery
# print("Turn on Battery")

# # verify contactor close and CE signal
# while not bin_monitor.contactor:
#     time.sleep(0.1)

# print("Contactor Closed")

# # raise voltage until CCL is lowered LOG - verify high cell ~BMIN
# while can_monitor.charge_current_limit >= maxc:
#     powersupply_voltage_setting += 0.05
#     if powersupply_voltage_setting < max_voltage:
#         powersupply.voltage = powersupply_voltage_setting
#     else:
#         print("maximum allowed voltage exceeded")
#         raise NameError("MaxVoltageExceeded")
#     time.sleep(2)
#     print(f"actual output voltage: {powersupply.measvoltage}  can max cell: {can_monitor.max_cell_voltage}", end = "\r")
    

# print("Threshold for lowering charge current limit reached")
# time.sleep(1)
# log()
# print(f"Criteria for pass is abs(DMM Max Cell Voltage - Balance Start Voltage) < 0.05")
# testvalue = abs(dmm_monitor.value - bmin)
# print(f"Result is {testvalue}")
# if testvalue <= 0.05:
#     print("PASS")
# else:
#     print("FAIL")

# #print("Press enter to continue test...")
# #x = input()
        
# # raise voltage until CE removed and LOG - verify low cell ~CHAR
# while bin_monitor.chargeEnable:
#     powersupply_voltage_setting += 0.05
#     if powersupply_voltage_setting < max_voltage:
#         powersupply.voltage = powersupply_voltage_setting
#     else:
#         print("maximum allowed voltage exceeded")
#         raise NameError("MaxVoltageExceeded")
#     time.sleep(2)
#     print(f"actual output voltage: {powersupply.measvoltage}  can max cell: {can_monitor.max_cell_voltage}", end = "\r")
    
# print("Threshold for removing charge enable reached")
# time.sleep(1)
# log()
# print(f"Criteria for pass is abs(Can Min Cell Voltage - Cell end of charge voltage) < 0.05")
# testvalue = abs(can_monitor.min_cell_voltage - char)
# print(f"Result is {testvalue}")
# if testvalue <= 0.05:
#     print("PASS")
# else:
#     print("FAIL")


# # raise voltage until Contactor open and LOG - verify high cell ~CMAX
# while bin_monitor.contactor:
#     powersupply_voltage_setting += 0.05
#     if powersupply_voltage_setting < max_voltage:
#         powersupply.voltage = powersupply_voltage_setting
#     else:
#         print("maximum allowed voltage exceeded")
#         raise NameError("MaxVoltageExceeded")
#     time.sleep(2)
#     print(f"actual output voltage: {powersupply.measvoltage}  can max cell: {can_monitor.max_cell_voltage}", end = "\r")
    
# print("Threshold for cell over voltage disconnect reached")
# time.sleep(1)
# log()
# print(f"Criteria for pass is abs(Can Max Cell Voltage - Cell over-voltage switch-off per cell) < 0.05")
# testvalue = abs(can_monitor.max_cell_voltage - cmax)
# print(f"Result is {testvalue}")
# if testvalue <= 0.05:
#     print("PASS")
# else:
#     print("FAIL")


# # stop

# # lower voltage until contactor close and LOG
# while not bin_monitor.contactor:
#     powersupply_voltage_setting -= 0.05
#     if powersupply_voltage_setting < max_voltage:
#         powersupply.voltage = powersupply_voltage_setting
#     else:
#         print("maximum allowed voltage exceeded")
#         raise NameError("MaxVoltageExceeded")
#     time.sleep(2)
#     print(f"actual output voltage: {powersupply.measvoltage}  can max cell: {can_monitor.max_cell_voltage}", end = "\r")
    
# print("Threshold for cell over voltage reconnect reached")
# time.sleep(1)
# log()
# print(f"Criteria for pass is abs(Can Max Cell Voltage - (Cell over-voltage switch-off per cell - hysteresis)) < 0.05")
# testvalue = abs(can_monitor.max_cell_voltage - (cmax - maxh))
# print(f"Result is {testvalue}")
# if testvalue <= 0.05:
#     print("PASS")
# else:
#     print("FAIL")

# # lower voltage until CE applied and LOG 
# while not bin_monitor.chargeEnable:
#     powersupply_voltage_setting -= 0.05
#     if powersupply_voltage_setting < max_voltage:
#         powersupply.voltage = powersupply_voltage_setting
#     else:
#         print("maximum allowed voltage exceeded")
#         raise NameError("MaxVoltageExceeded")
#     if powersupply_voltage_setting <= 26.0:
#         print("nominal voltage reached")
#         break
#     time.sleep(2)
#     print(f"actual output voltage: {powersupply.measvoltage}  can max cell: {can_monitor.max_cell_voltage}", end = "\r")
    
# print("Threshold for restoring charge enablec reached")
# time.sleep(1)
# log()
# print(f"Criteria for pass is abs(Can Max Cell Voltage - (Cell end of charge voltage - hysteresis)) < 0.05")
# testvalue = abs(can_monitor.max_cell_voltage - (char - chis))
# print(f"Result is {testvalue}")
# if testvalue <= 0.05:
#     print("PASS")
# else:
#     print("FAIL")

# # lower voltage until nominal 26V
# while powersupply_voltage_setting > 26.0:
#     powersupply_voltage_setting -= 0.05
#     if powersupply_voltage_setting < max_voltage:
#         powersupply.voltage = powersupply_voltage_setting
#     else:
#         print("maximum allowed voltage exceeded")
#         raise NameError("MaxVoltageExceeded")
#     time.sleep(2)
#     print(f"actual output voltage: {powersupply.measvoltage}  can max cell: {can_monitor.max_cell_voltage}", end = "\r")
    
# print("Test Complete")
