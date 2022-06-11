from uni_t import DMMMonitor
from instrument_logger import InstrumentLogger
import can
import os
import time
from balance_setup import BalanceTestFixture
from datetime import datetime

"""This script leverages BalanceTestFixture to record parameters during the initial battery precharge performed prior to a parallel cell top-balance."""
"""All Power supply parameters are set manually, except output enable (bug)."""
"""Riden voltage setpoint should be 3.5V"""
"""Rident current setpoint should be 18A"""
"""DMM Should be set to measure voltage across all cells in parallel"""
"""O-scope will be used to measure voltage ripple across all cells in parallel"""
"""This script will disable Riden output and terminate when current has dropped to less than or equal 1A"""
"""After termination of this script the remainder of the balance to 3.65V will be handled manually with a linear power supply"""

test_fixture = BalanceTestFixture(dmm_parametername='Cell_Voltage')


test_fixture.start()
time.sleep(1)

# Start logging
# message user to turn on system (precharge and close contactor)
# message user to enable riden

test_fixture.logger.filename = 'initial-battery-balance'
test_fixture.logger.start()

# User has 30 seconds to turn on system and enable riden, otherwise logging will stop, and script will end
print("Turn on linear power supply, ensure OCP is off, and set voltage to 3.5-3.65V.")

    
# Print DMM Voltage and Log until script is interupted.
while True:
    print('Cell Voltage = ' + test_fixture.dmm_monitor.getmeasurement('I can put anything here'))
    time.sleep(1)


