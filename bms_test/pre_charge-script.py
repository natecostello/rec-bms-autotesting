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

"""This script leverages BMSTestFixture to record parameters during the initial battery precharge performed prior to a parallel cell top-balance."""
"""All Power supply parameters are set manually, except output enable (bug).  This script only monitors."""
"""CMAX 'End of charge hysterisis per cell' MUST be changed from the default 3.85 to 3.65 prior to initial battery precharge."""
"""MAXH 'Over-voltage switch-off hysteresis per cell' SHOULD be changed from the default 0.25 to 0.05."""
"""Riden voltage setpoint should be 29.2V (For a subsequent 3.65V top balance)"""
"""Rident current setpoint should be 15A (for p/s margin)"""
"""DMM Should be set to measure voltage across the battery pack"""
"""O-scope will be used to measure voltage ripple across battery pack"""
"""Contactor Aux Contacts should be wired to logging pi 3.3v and to contactor input pin"""
"""BMS IR, BMS CE, and Precharge Sys+ should be monitored by the logging pi"""


test_fixture = BMSTestFixture(dmm_parametername='Pack_Voltage')


test_fixture.start()
time.sleep(1)

# Start logging
# message user to turn on system (precharge and close contactor)
# message user to enable riden

test_fixture.logger.filename = 'initial-battery-precharge'
test_fixture.logger.start()

# User has 30 seconds to turn on system and enable riden, otherwise logging will stop, and script will end
print("Turn on system via main switch.")

time.sleep(30)

if test_fixture.bin_monitor.contactor:
    time.sleep(1)
    test_fixture.powersupply.set_output(True)
    
# Log until BMS opens contactor or output is disabled

while test_fixture.bin_monitor.contactor and test_fixture.powersupply.is_output:
    time.sleep(1)

time.sleep(5)
test_fixture.logger.stop()
test_fixture.stop()
