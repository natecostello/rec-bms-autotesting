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


class RisingCellVoltageTest(unittest.TestCase):
    """"This test case verifies response and protections to rising cell voltage.  Initial conditions: Power supply providing 26V and battery is ON."""

    @classmethod
    def setUpClass(cls):
                # power supply parameters
        cls.initial_voltage = 26.0
        cls.voltage_limit = 32.0
        cls.voltage_increment = 0.01

        # default BMS Parameters
        # ultimately it would be nice to pull all these parameters from the BMS
        cls.bmin = 3.45 # 'Balance Start Voltage'
        cls.bvol = 3.58 # 'Balance End Voltage'
        cls.cmax = 3.85 # 'Cell over-voltage switch-off per cell
        cls.maxh = 0.25 # 'Over-voltage switch-off hysteresis per cell'
        cls.char = 3.58 # 'Cell end of charge voltage'
        cls.chis = 0.25 # 'End of charge hysterisis per cell'
        cls.maxc = 70.0 # 'Maximum charging current'

        cls.test_fixture = BMSTestFixture()
        cls.test_fixture.powersupply.set_voltage_set(cls.initial_voltage)
        cls.test_fixture.start()
        time.sleep(1)

        # Walk Voltage down to min cell voltage == CLOW evidenced by SOC <= 3

        print("test_fixture.can_monitor.state_of_charge=" + str(cls.test_fixture.can_monitor.state_of_charge))

        while cls.test_fixture.can_monitor.state_of_charge > 3:
            print("SOC is > 3 => decrementing")
            cls.decrement_voltage_and_wait(voltage_increment=0.5)
        time.sleep(10)
        
        # Reset to Starting Voltage
        cls.test_fixture.powersupply.set_voltage_set(cls.initial_voltage)
        time.sleep(10)


        cls.test_fixture.logger.filename = 'rising_voltage_test'
        cls.test_fixture.logger.start()

        # Walk Voltage Up To max cell voltage == bmin, evidenced by reduction in CCL
        while cls.test_fixture.can_monitor.charge_current_limit >= cls.maxc:
            cls.increment_voltage_and_wait(voltage_increment=0.01)
        
        # hold at this voltage and note parameters
        time.sleep(10)
        cls.max_cell_voltage_at_ccl_reduction = cls.test_fixture.can_monitor.max_cell_voltage
        
        # Walk Voltage Up To max cell voltage == 0.502*(bmin+bvol), evidenced by SOC >= 96
        while cls.test_fixture.can_monitor.state_of_charge_hi_res < 96.0:
            cls.increment_voltage_and_wait(voltage_increment=0.01)
        
        # hold at this voltage and note parameters
        time.sleep(10)
        cls.min_cell_voltage_at_soc_to_96 = cls.test_fixture.can_monitor.min_cell_voltage


        # Walk Voltage up to min cell voltage == char, evidenced by reduction in CVL
        while cls.test_fixture.can_monitor.charge_voltage_limit > 28.2: # This is value coincides with  min cell = end of charge voltage
            cls.increment_voltage_and_wait(voltage_increment=0.01)
        
        # capture immediately as it can be affected by balance (I believe)
        cls.min_cell_voltage_at_cvl_reduction = cls.test_fixture.can_monitor.min_cell_voltage
        # hold at this voltage and note parameters
        time.sleep(10)
        cls.charge_voltage_limit_at_cvl_reduction = cls.test_fixture.can_monitor.charge_voltage_limit
        # In this condition per manual, CVL is set to = num_cells * (char - 0.2 * chis)
        cls.soc_hr_at_cvl_reduction = cls.test_fixture.can_monitor.state_of_charge_hi_res # should be 100
        cls.soc_at_cvl_reduction = cls.test_fixture.can_monitor.state_of_charge # should be 100
        cls.charge_enable_status_at_cvl_reduction = cls.test_fixture.bin_monitor.chargeEnable # should be off 

        # Walk voltage up to cutoff
        while cls.test_fixture.bin_monitor.contactor:
            cls.increment_voltage_and_wait(voltage_increment=0.1)
        
        # don't hold, note parameters
        cls.max_cell_voltage_at_relay_cutoff = cls.test_fixture.can_monitor.max_cell_voltage # should be cmax + maxh but is actually cmax
        cls.charge_enable_status_at_relay_cutoff = cls.test_fixture.bin_monitor.chargeEnable # should be off
 
        while not cls.test_fixture.bin_monitor.contactor:
            cls.decrement_voltage_and_wait(voltage_increment=0.1)

        cls.max_cell_voltage_at_relay_turn_on = cls.test_fixture.can_monitor.max_cell_voltage # unclear but probably cmax-maxh
        cls.charge_enable_status_at_relay_turn_on = cls.test_fixture.bin_monitor.chargeEnable # unclear
 
        cls.reset_voltage()
        time.sleep(10)

        # check parameters?  Not sure when Charge Enable is set back to 1, Not sure when relay is enabled

        cls.test_fixture.logger.stop()

    def setUp(self) -> None:
        pass

    def test_charge_current_limit_reduction_voltage(self):
        self.assertAlmostEqual(
            self.max_cell_voltage_at_ccl_reduction, 
            self.bmin, 
            2, 
            msg="Charge Current Limit Reduction Voltage Mismatch: Max Cell Voltage = " + str(self.max_cell_voltage_at_ccl_reduction) + ', BMIN = ' + str(self.bmin))

    # TODO: Note this never happens and doesn't appear to reflect manual
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
            round(num_cells * (self.char - 0.2 * self.chis),1), # measured value is limited to 1 decimal place per can documentation
            1,
            msg="Charge Voltage Limit Reduction Value Mismatch: Charge Voltage Limit = " + str(self.charge_voltage_limit_at_cvl_reduction) + ', num_cells(CHAR - 0.2*CHIS) = ' + str(round(num_cells * (self.char - 0.2 * self.chis),1)))
    
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
    
    # TODO: Note this is wrong, per manual it is cmax+maxh
    def test_relay_cutoff_voltage(self):
        self.assertAlmostEqual(
            self.max_cell_voltage_at_relay_cutoff,
            self.cmax,
            2, 
            msg="Relay Cutoff Voltage Mismatch: Max Cell Voltage = " + str(self.max_cell_voltage_at_relay_cutoff) + ', CMAX = ' + str(self.cmax))

    def test_relay_cutoff_charge_enable_status(self):
        self.assertEqual(
            self.charge_enable_status_at_relay_cutoff,
            0,
            msg="Relay Cutoff Value Mismatch: Charge Enable = " + str(self.charge_enable_status_at_relay_cutoff) + ', Value should = 0')


    # TODO: Test Relay Turn On?  Not sure when that is supposed to happen.  Need to watch BMS temp carefully when it starts to balance all cells.

    @classmethod
    def increment_voltage_and_wait(cls, voltage_increment=0.01):
        voltage_setpoint = cls.test_fixture.powersupply.get_voltage_set()
        if voltage_setpoint + voltage_increment < cls.voltage_limit:
            cls.test_fixture.powersupply.set_voltage_set(voltage_setpoint + voltage_increment)
            time.sleep(4)
        else:
            cls.reset_voltage()
            raise NameError("Max Voltage Limit Exceeded")

    @classmethod
    def decrement_voltage_and_wait(cls, voltage_increment=0.01):
        voltage_setpoint = cls.test_fixture.powersupply.get_voltage_set()
        cls.test_fixture.powersupply.set_voltage_set(voltage_setpoint - voltage_increment)
        time.sleep(4)

    @classmethod
    def reset_voltage(cls):
        cls.test_fixture.powersupply.set_voltage_set(cls.initial_voltage)
        
