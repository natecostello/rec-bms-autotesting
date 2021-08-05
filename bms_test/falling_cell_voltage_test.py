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


class FallingCellVoltageTest(unittest.TestCase):
    """"This test case verifies response and protections to falling cell voltage.  Initial conditions: Power supply providing 26V and battery is ON."""

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
        cls.clow = 2.9 # 'Cell Under-voltage discharge protection'
        cls.cmin = 2.8 # 'Cell Under-voltage protection switch-off'
        cls.minh = 0.1 # 'Min allowed cell voltage hysterisis' - error in manual
        cls.maxd = 100 # 'maximum discharge current per device'
        cls.dchc = 1.5 # 'discharge coefficient'
        cls.capa = 560 # 'battery pack capacity'

        cls.test_fixture = BMSTestFixture()
        cls.test_fixture.powersupply.set_voltage_set(cls.initial_voltage)
        cls.test_fixture.start()
        time.sleep(1)

        # Walk Voltage up to min cell voltage == CHAR evidenced by SOC = 100

        print("test_fixture.can_monitor.state_of_charge=" + str(cls.test_fixture.can_monitor.state_of_charge))

        while cls.test_fixture.can_monitor.state_of_charge < 100:
            print("SOC is < 100 => incrementing")
            cls.increment_voltage_and_wait(voltage_increment=0.25)
        time.sleep(10)
        
        # Reset to 8*(CMIN+MINH+0.1)
        cls.test_fixture.powersupply.set_voltage_set(8*(cls.cmin + cls.minh + 0.1))
        time.sleep(10)


        cls.test_fixture.logger.filename = 'falling_voltage_test'
        cls.test_fixture.logger.start()

        # Walk Voltage Down To min cell voltage < 0.99*CLOW
        while cls.test_fixture.can_monitor.min_cell_voltage > 0.995 * cls.clow:
            cls.decrement_voltage_and_wait(voltage_increment=0.01)
        
        # hold at this voltage and note parameters dcl should decreasee to 0.02C or 0?, SOC set to 3%
        # SOC is reset to 2%, however SOC_HR is reset to 2.9%
        time.sleep(10)
        cls.dcl_at_min_cell_voltage_below_clow = cls.test_fixture.can_monitor.discharge_current_limit
        cls.soc_at_min_cell_voltage_below_clow = cls.test_fixture.can_monitor.state_of_charge
        
        # Walk Voltage Down To min cell voltage < 0.99*CMIN
        while cls.test_fixture.can_monitor.min_cell_voltage > 0.995 * cls.cmin:
            cls.decrement_voltage_and_wait(voltage_increment=0.01)
        
        # hold at this voltage and note parameters, SOC should be set to 1%, Contactor open
        time.sleep(10)
        cls.soc_at_min_cell_voltage_below_cmin = cls.test_fixture.can_monitor.state_of_charge
        cls.contactor_at_min_cell_voltage_below_cmin = cls.test_fixture.bin_monitor.contactor

        # Walk Voltage Up to min cell voltage > CMIN + MINH
        while cls.test_fixture.can_monitor.min_cell_voltage < cls.cmin + cls.minh:
            cls.increment_voltage_and_wait(voltage_increment=0.01)
        
        # hold at this voltage and note parameters, Contactor should close
        time.sleep(10)
        cls.contactor_at_min_cell_voltage_above_cmin_plus_minh = cls.test_fixture.bin_monitor.contactor

        cls.reset_voltage()
        time.sleep(10)

        # check parameters?  Not sure when Charge Enable is set back to 1, Not sure when relay is enabled

        cls.test_fixture.logger.stop()

    def setUp(self) -> None:
        pass

    def test_discharge_current_limit_reduction_value_at_clow(self):
        self.assertLessEqual(
            self.dcl_at_min_cell_voltage_below_clow, 
            0.02*self.capa, 
            msg="Discharge Current Limit Reduction Value Mismatch: DCL = " + str(self.dcl_at_min_cell_voltage_below_clow) + ', Should be < ' + str(0.02*self.capa))
    
    # Note: SOC_HR is reset to 2.9, SOC is reset to 2
    def test_SOC_reduction_value_at_clow(self):
        self.assertEqual(
            self.soc_at_min_cell_voltage_below_clow, 
            2, 
            msg="SOC Reduction Value Mismatch: SOC = " + str(self.soc_at_min_cell_voltage_below_clow) + ', Should = ' + str(2))

    def test_SOC_reduction_value_at_cmin(self):
        self.assertEqual(
            self.soc_at_min_cell_voltage_below_cmin, 
            1, 
            msg="SOC Reduction Value Mismatch: SOC = " + str(self.soc_at_min_cell_voltage_below_cmin) + ', Should = ' + str(1))

    def test_contactor_state_at_cmin(self):
        self.assertEqual(
            self.contactor_at_min_cell_voltage_below_cmin, 
            0, 
            msg="Contactor State Mismatch: Contactor = " + str(self.contactor_at_min_cell_voltage_below_cmin) + ', Should = ' + str(0))
    
    def test_contactor_state_at_cmin_plus_minh(self):
        self.assertEqual(
            self.contactor_at_min_cell_voltage_above_cmin_plus_minh, 
            1, 
            msg="Contactor State Mismatch: Contactor = " + str(self.contactor_at_min_cell_voltage_above_cmin_plus_minh) + ', Should = ' + str(1))
    

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
        
