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


class FallingTemperatureTest(unittest.TestCase):
    """"This test case verifies response and protections to falling Temperatures.  Initial conditions: Power supply providing 26V and battery is ON.
    This test requires user action to raise and lower temperature.  This test requires setting the TMIN parameter above 0F to allow testing with ice water"""

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
        cls.tmax = 55  # 'cell over temperature switch-off'
        cls.tmin = 5   # 'cell under-temperature charging disable' - MODIFY TO > 0 Default was -10C

        cls.test_fixture = BMSTestFixture()
        cls.test_fixture.powersupply.set_voltage_set(cls.initial_voltage)
        cls.test_fixture.start()
        time.sleep(1)

        # Walk Voltage down to min cell voltage == CLOW evidenced by SOC <= 3 to make sure charging is fully enabled

        print("test_fixture.can_monitor.state_of_charge=" + str(cls.test_fixture.can_monitor.state_of_charge))

        while cls.test_fixture.can_monitor.state_of_charge > 3:
            print("SOC is > 3 => decrementing")
            cls.decrement_voltage_and_wait(voltage_increment=0.5)
        time.sleep(10)
        
        # Reset to Starting Voltage
        cls.test_fixture.powersupply.set_voltage_set(cls.initial_voltage)
        time.sleep(10)


        cls.test_fixture.logger.filename = 'falling_temperature_test'
        cls.test_fixture.logger.start()

        print("Apply cold to one battery temperature sensor.")
        # Use ice water bath to lower the temperature of a battery sensor

        while cls.test_fixture.can_monitor.min_temperature >= cls.tmin:
            time.sleep(1)
        
        time.sleep(10) # time hysteresis
        cls.charge_enable_at_tmin = cls.test_fixture.bin_monitor.chargeEnable
        cls.ccl_at_tmin = cls.test_fixture.can_monitor.charge_current_limit

        print("Remove cold from the battery temperature sensor.")
        while cls.test_fixture.can_monitor.min_temperature <= cls.tmin + 2:
            time.sleep(1)
        
        time.sleep(10) # for time hysteresis plus precharge

        cls.charge_enable_at_tmin_plus_2c = cls.test_fixture.bin_monitor.chargeEnable
        cls.ccl_at_tmin_plus_2c = cls.test_fixture.can_monitor.charge_current_limit

        time.sleep(10)
        
        cls.test_fixture.logger.stop()

    def setUp(self) -> None:
        pass

    def test_charge_enable_state_at_tmin(self):
        self.assertEqual(
            self.charge_enable_at_tmin, 
            0, 
            msg="Charge Enable State Mismatch: Charge Enable = " + str(self.charge_enable_at_tmin) + ', Should be 0')
    
    def test_charge_current_limit_at_tmin(self):
        self.assertEqual(
            self.ccl_at_tmin, 
            0, 
            msg="charge Current Limit Value Mismatch: CCL = " + str(self.ccl_at_tmin) + ', Should be 0')
    
    def test_charge_enable_state_at_tmin_plus_2c(self):
        self.assertEqual(
            self.charge_enable_at_tmin_plus_2c, 
            1, 
            msg="Charge Enable State Mismatch: Charge Enable = " + str(self.charge_enable_at_tmin_plus_2c) + ', Should be 1')
    
    def test_charge_current_limit_at_tmin_plus_2c(self):
        self.assertGreater(
            self.ccl_at_tmin_plus_2c, 
            0, 
            msg="Charge Current Limit Value Mismatch: CCL = " + str(self.ccl_at_tmin_plus_2c) + ', Should be > 0')


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
        
