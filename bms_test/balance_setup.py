from uni_t import DMMMonitor
from instrument_logger import InstrumentLogger
import os
import time

class BalanceTestFixture:

    def __init__(self, dmm_parametername = None) -> None:
        
        # power supply to be used is manual, linear power supply.  No code.
    
        # DMM is required
        if dmm_parametername:
            if not os.path.exists('/dev/ttyUSBut61e'):
                raise ValueError('No UT61E Detected')
            dmm_port = '/dev/ttyUSBut61e'

            self._dmm_monitor = DMMMonitor(dmm_port)
            self._dmm_monitor.parametername = dmm_parametername
        else:
            self._dmm_monitor = None
        
        # setup logger
        self._logger = InstrumentLogger()
        if self._dmm_monitor:
            self._logger.addinstrument(self._dmm_monitor)
        
    @property
    def dmm_monitor(self) -> DMMMonitor:
        return self._dmm_monitor
        
    @property
    def logger(self) -> InstrumentLogger:
        return self._logger
        
    def start(self) -> None:
        """Starts any Instrument threads"""
        if self.dmm_monitor:
            self.dmm_monitor.start()

    def stop(self) -> None:
        """Stops any Instrument threads, stops logging"""
        if self.dmm_monitor:
            self.dmm_monitor.stop()
