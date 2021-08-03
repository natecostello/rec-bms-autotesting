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
        
        time.sleep(10)
        self.test_fixture.logger.filename = 'rising_voltage_test'
        self.test_fixture.logger.start()

        # Walk Voltage Up To max cell voltage == bmin, evidenced by reduction in CCL
        while self.test_fixture.can_monitor.charge_current_limit >= self.maxc:
            self.increment_voltage_and_wait()
        
        # hold at this voltage and note parameters
        time.sleep(10)
        self.max_cell_voltage_at_ccl_reduction = self.test_fixture.can_monitor.max_cell_voltage
        
        # Walk Voltage Up To max cell voltage == 0.502*(bmin+bvol), evidenced by SOC >= 96
        while self.test_fixture.can_monitor.state_of_charge_hi_res < 96.0:
            self.increment_voltage_and_wait()
        
        # hold at this voltage and note parameters
        time.sleep(10)
        self.min_cell_voltage_at_soc_to_96 = self.test_fixture.can_monitor.min_cell_voltage


        # Walk Voltage up to min cell voltage == char, evidenced by reduction in CVL
        while self.test_fixture.can_monitor.charge_voltage_limit >= 28.7: # This value is as reported via CAN normally.  Note sure what the basis is. 
            self.increment_voltage_and_wait()
        
        # hold at this voltage and note parameters
        time.sleep(10)
        self.min_cell_voltage_at_cvl_reduction = self.test_fixture.can_monitor.min_cell_voltage
        self.charge_voltage_limit_at_cvl_reduction = self.test_fixture.can_monitor.charge_voltage_limit
        # In this condition per manual, CVL is set to = num_cells * (char - 0.2 * chis)
        self.soc_hr_at_cvl_reduction = self.test_fixture.can_monitor.state_of_charge_hi_res # should be 100
        self.soc_at_cvl_reduction = self.test_fixture.can_monitor.state_of_charge # should be 100
        self.charge_enable_status_at_cvl_reduction = self.test_fixture.bin_monitor.chargeEnable # should be off 

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

        # check parameters?  Not sure when Charge Enable is set back to 1, Not sure when relay is enabled

        self.test_fixture.logger.stop()
        

    def test_charge_current_limit_reduction_voltage(self):
        self.assertAlmostEqual(
            self.max_cell_voltage_at_ccl_reduction, 
            self.bmin, 
            2, 
            msg="Charge Current Limit Reduction Voltage Mismatch: Max Cell Voltage = " + str(self.max_cell_voltage_at_ccl_reduction) + ', BMIN = ' + str(self.bmin))

    def test_soc_to_ninetysix_voltage(self):
        self.assertAlmostEqual(
            self.min_cell_voltage_at_soc_to_96, 
            0.502 * (self.bmin + self.bvol), 
            2, 
            msg="SOC to 96% Voltage Mismatch: Min Cell Voltage = " + str(self.min_cell_voltage_at_soc_to_96) + ', 0.502(BMIN+BVOL) = ' + str(0.502*(self.bmin + self.bvol)))

    def test_charge_voltage_limit_reduction_voltage(self):
        self.assertAlmostEqual(
            self.min_cell_voltage_at_cvl_reduction,
            self.char,
            2,
            msg="Charge Voltage Limit Reduction Voltage Mismatch: Min Cell Voltage = " + str(self.min_cell_voltage_at_cvl_reduction) + ', CHAR = ' + str(self.char))
    
    def test_charge_voltage_limit_reduction_CVL_value(self):
        num_cells = 8
        self.assertAlmostEqual(
            self.charge_voltage_limit_at_cvl_reduction,
            num_cells * (self.char - 0.2 * self.chis),
            2,
            msg="Charge Voltage Limit Reduction Value Mismatch: Charge Voltage Limit = " + str(self.charge_voltage_limit_at_cvl_reduction) + ', num_cells(CHAR - 0.2*CHIS) = ' + str(num_cells * (self.char - 0.2 * self.chis)))
    
    def test_charge_voltage_limit_reduction_soc_hr_value(self):
        self.assertAlmostEqual(
            self.soc_hr_at_cvl_reduction,
            100.00,
            2,
            msg="Charge Voltage Limit Reduction Value Mismatch: SOC_HR = " + str(self.soc_hr_at_cvl_reduction) + ', Value should = 100.00')
    
    def test_charge_voltage_limit_reduction_soc_value(self):
        self.assertEqual(
            self.soc_at_cvl_reduction,
            100,
            msg="Charge Voltage Limit Reduction Value Mismatch: SOC = " + str(self.soc_at_cvl_reduction) + ', Value should = 100')
    
    def test_charge_voltage_limit_reduction_charge_enable_status(self):
        self.assertEqual(
            self.charge_enable_status_at_cvl_reduction,
            0,
            msg="Charge Voltage Limit Reduction Value Mismatch: Charge Enable = " + str(self.charge_enable_status_at_cvl_reduction) + ', Value should = 0')
    
    def test_relay_cutoff_voltage(self):
        self.assertAlmostEqual(
            self.max_cell_voltage_at_relay_cutoff,
            self.cmax + self.maxh,
            2,
            msg="Relay Cutoff Voltage Mismatch: Max Cell Voltage = " + str(self.max_cell_voltage_at_relay_cutoff) + ', CMAX + MAXH = ' + str(self.cmax + self.maxh))

    def test_relay_cutoff_charge_enable_status(self):
        self.assertEqual(
            self.charge_enable_status_at_relay_cutoff,
            0,
            msg="Relay Cutoff Value Mismatch: Charge Enable = " + str(self.charge_enable_status_at_relay_cutoff) + ', Value should = 0')


    # TODO: Test Relay Turn On?  Not sure when that is supposed to happen.  Need to watch BMS temp carefully when it starts to balance all cells.

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
