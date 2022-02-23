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

"""All Power supply parameters are set manually, including enable.  This script only monitors."""

"""CMAX 'End of charge hysterisis per cell' MUST be changed from the default 3.85 to 3.65 prior to initial battery precharge."""
"""MAXH 'Over-voltage switch-off hysteresis per cell' SHOULD be changed from the default 0.25 to 0.05."""

"""DMM Should be set to measure voltage across the battery pack"""

"""Contactor Aux Contacts should be wired to logging pi 3.3v and to contactor input pin"""
"""BMS IR-in should be wired to Battery Postive by way of (fused) switch per BMS wiring diagram."""
"""BMS IR-out should be wired to pre-charge per BMS wiring diagram."""


test_fixture = BMSTestFixture(dmm_parametername='Pack_Voltage[v]')


test_fixture.start()
time.sleep(1)

# Start logging
# message user to turn on system (precharge and close contactor)
# message user to enable riden

test_fixture.logger.filename = 'initial-battery-precharge'
test_fixture.logger.start()

# User has 60 seconds to turn on system and enable riden, otherwise logging will stop, and script will end

time.sleep(60)

# Log until BMS opens contactor or output is disabled

while test_fixture.bin_monitor.contactor and test_fixture.powersupply.is_output:
    time.sleep(1)

time.sleep(5)
test_fixture.logger.stop()
test_fixture.stop()
