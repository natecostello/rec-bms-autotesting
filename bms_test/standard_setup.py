from riden_monitor import RidenMonitor
from uni_t import DMMMonitor
from riden import Riden
from recq.binary import BinaryMonitor
from recq.canbus import CanBusMonitor
from instrument_logger import InstrumentLogger
import can
from can import Notifier
import os
import time

class BMSTestFixture:

    def __init__(self, dmm_parametername = None) -> None:
        
        os.system("sudo /sbin/ip link set can0 up type can bitrate 250000")
        self._can_monitor = CanBusMonitor()
        self._bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=250000)    
        self._notifier = Notifier(self._bus, [self._can_monitor])
        print("") #clear the line
        
        # power supply is required
        if not os.path.exists('/dev/ttyUSBrd6018'):
            raise ValueError('No Riden RD6018 Detected')
        powersupply_port = '/dev/ttyUSBrd6018'
        self._powersupply = Riden(powersupply_port)
        self._powersupply_monitor = RidenMonitor(rd60xx=self._powersupply)
        self._powersupply_monitor.start()

        # DMM is optional depending on test
        if dmm_parametername:
            if not os.path.exists('/dev/ttyUSBut61e'):
                raise ValueError('No UT61E Detected')
            dmm_port = '/dev/ttyUSBut61e'

            self._dmm_monitor = DMMMonitor(dmm_port)
            self._dmm_monitor.parametername = dmm_parametername
        else:
            self._dmm_monitor = None
        
        # binary monitor is required
        self._bin_monitor = BinaryMonitor()


        # setup logger
        self._logger = InstrumentLogger()
        self._logger.addinstrument(self._powersupply_monitor)
        if self._dmm_monitor:
            self._logger.addinstrument(self._dmm_monitor)
        self._logger.addinstrument(self._bin_monitor)
        self._logger.addinstrument(self._can_monitor)
    
    @property
    def powersupply(self) -> Riden:
        return self._powersupply
    
    @property
    def powersupply_monitor(self) -> RidenMonitor:
        return self._powersupply_monitor
    
    @property
    def dmm_monitor(self) -> DMMMonitor:
        return self._dmm_monitor
    
    @property
    def can_monitor(self) -> CanBusMonitor:
        return self._can_monitor
    
    @property
    def bin_monitor(self) -> BinaryMonitor:
        return self._bin_monitor
    
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
        self._notifier.remove_listener(self._can_monitor)
        self._bus.shutdown()
        os.system("sudo /sbin/ip link set can0 down")
        


