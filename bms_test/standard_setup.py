from rd6006 import RD6006
from uni_t import DMMMonitor
from riden import RidenMonitor
from recq.binary import BinaryMonitor
from recq.canbus import CanBusMonitor
from instrument_logger import InstrumentLogger
import can
import os
import time

class BMSTestFixture:

    def __init__(self, dmm_parametername = None) -> None:

        # power supply is required
        if not os.path.exists('/dev/ttyUSBrd6018'):
            raise ValueError('No Riden RD6018 Detected')
        powersupply_port = '/dev/ttyUSBrd6018'
        self._powersupply = RD6006(powersupply_port)
        self._powersupply_monitor = RidenMonitor(powersupply)

        # DMM is optional depending on test
        if dmm_parametername:
            if not os.path.exists('/dev/ttyUSBut61e'):
                raise ValueError('No Riden RD6018 Detected')
            dmm_port = '/dev/ttyUSBut61e'

            self._dmm_monitor = DMMMonitor(dmm_port)
            self._dmm_monitor.parametername = dmm_parametername
        else:
            self._dmm_monitor = None
        
        # binary monitor is required
        self._bin_monitor = BinaryMonitor()

        # canbus monitor is required
        # setup canbus and recq can monitor
        os.system("sudo /sbin/ip link set can0 up type can bitrate 250000")
        self._bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=250000)         
        self._notifier = can.Notifier(self._bus)
        self._can_monitor = CanBusMonitor()
        self._notifier.add_listener(self._can_monitor)

        # setup logger
        self._logger = InstrumentLogger()
        self._logger.addinstrument(self._powersupply_monitor)
        if self._dmm_monitor:
            self._logger.addinstrument(self._dmm_monitor)
        self._logger.addinstrument(self._bin_monitor)
        self._logger.addinstrument(self._can_monitor)
    
    @property
    def powersupply(self) -> RD6006:
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
    def logger(self) -> InstrumentLogger:
        return self._logger
        


