from instrument_logger import InstrumentLogger
import can
import os
import time
from charge_setup import ChargeTestFixture
from datetime import datetime

"""This script leverages ChargeTestFixture to record BMS CAN parameters during a batterycharge."""

test_fixture = ChargeTestFixture()


test_fixture.start()
time.sleep(1)

# Start logging
# message user to turn on system (precharge and close contactor)
# message user to enable riden

test_fixture.logger.filename = 'charge'
test_fixture.logger.start()

val = input('Enter any key to secure logging and stop the test:')
test_fixture.logger.stop()
