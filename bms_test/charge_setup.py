from recq.canbus import CanBusMonitor
from instrument_logger import InstrumentLogger
from wakespeed import WakespeedMonitor
import can
from can import Notifier
import os
import time

class ChargeTestFixture:

    def __init__(self) -> None:
        
        os.system("sudo /sbin/ip link set can0 up type can bitrate 250000")
        self._can_monitor = CanBusMonitor()
        self._wake_monitor = WakespeedMonitor()
        self._bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=250000)    
        self._notifier = Notifier(self._bus, [self._can_monitor, self._wake_monitor])
        print("") #clear the line
        
        # No power supply
        # No DMM 
        # No binary monitor
        
        # setup logger
        self._logger = InstrumentLogger()
        self._logger.addinstrument(self._can_monitor)
        self._logger.addinstrument(self._wake_monitor)
    
    @property
    def can_monitor(self) -> CanBusMonitor:
        return self._can_monitor

    @property
    def wake_monitor(self) -> WakespeedMonitor:
        return self._wake_monitor
    
    @property
    def logger(self) -> InstrumentLogger:
        return self._logger
        
    def start(self) -> None:
        """Starts any Instrument threads"""
        
    def stop(self) -> None:
        """Stops any Instrument threads, stops logging"""
        
        self._notifier.remove_listener(self._can_monitor)
        self._notifier.remove_listener(self._wake_monitor)       
        self._bus.shutdown()
        os.system("sudo /sbin/ip link set can0 down")
        


