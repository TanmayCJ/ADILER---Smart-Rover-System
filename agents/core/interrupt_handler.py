"""
Interrupt handler for rover control.
Allows user commands to pause, stop, or change goals during execution.
"""

import logging
import threading
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class InterruptReason(Enum):
    """Enumeration of interrupt reasons."""
    NONE = "none"
    USER_STOP = "user_stop"
    USER_PAUSE = "user_pause"
    USER_GOAL_CHANGE = "user_goal_change"
    USER_RESUME = "user_resume"
    ERROR = "error"
    CYCLE_LIMIT = "cycle_limit"


class InterruptHandler:
    """
    Thread-safe interrupt handler for rover control.
    Manages pause/stop/goal_change commands from user.
    """
    
    def __init__(self):
        """Initialize interrupt handler."""
        self.interrupt_flag = False
        self.interrupt_reason = InterruptReason.NONE
        self.paused = False
        self.new_goal: Optional[Dict[str, Any]] = None
        self.lock = threading.Lock()
        self.callbacks: List[Callable] = []
        self.interrupt_history: List[Dict[str, Any]] = []
    
    def register_callback(self, callback: Callable):
        """
        Register callback to be called on interrupt.
        
        Args:
            callback: Function to call on interrupt
        """
        self.callbacks.append(callback)
        logger.debug(f"Registered interrupt callback: {callback.__name__}")
    
    def stop(self):
        """
        Signal rover to stop immediately.
        """
        with self.lock:
            self.interrupt_flag = True
            self.interrupt_reason = InterruptReason.USER_STOP
            self.paused = False
            logger.warning("✗ STOP command received - halting rover")
            self._trigger_callbacks("stop")
            self._log_interrupt()
    
    def pause(self):
        """
        Pause rover execution (can be resumed later).
        """
        with self.lock:
            self.interrupt_flag = True
            self.interrupt_reason = InterruptReason.USER_PAUSE
            self.paused = True
            logger.warning("⏸ PAUSE command received - suspending rover")
            self._trigger_callbacks("pause")
            self._log_interrupt()
    
    def resume(self):
        """
        Resume execution after pause.
        """
        with self.lock:
            if self.paused:
                self.interrupt_flag = False
                self.interrupt_reason = InterruptReason.USER_RESUME
                self.paused = False
                logger.info("▶ RESUME command received - restarting rover")
                self._trigger_callbacks("resume")
                self._log_interrupt()
            else:
                logger.warning("Resume called but rover is not paused")
    
    def change_goal(self, new_goal: Dict[str, Any]):
        """
        Change navigation goal during execution.
        
        Args:
            new_goal: New goal {latitude, longitude, name, priority}
        """
        with self.lock:
            if not self._validate_goal(new_goal):
                logger.error(f"Invalid goal: {new_goal}")
                return
            
            self.interrupt_flag = True
            self.interrupt_reason = InterruptReason.USER_GOAL_CHANGE
            self.new_goal = new_goal
            logger.warning(f"🎯 GOAL CHANGE command received - new goal: {new_goal['name']}")
            self._trigger_callbacks("goal_change")
            self._log_interrupt()
    
    def signal_error(self, error_message: str):
        """
        Signal error state (stops rover and logs error).
        
        Args:
            error_message: Description of error
        """
        with self.lock:
            self.interrupt_flag = True
            self.interrupt_reason = InterruptReason.ERROR
            logger.error(f"✗ ERROR signal: {error_message}")
            self._trigger_callbacks("error")
            self._log_interrupt()
    
    def signal_cycle_limit(self):
        """Signal that max cycles reached."""
        with self.lock:
            self.interrupt_flag = True
            self.interrupt_reason = InterruptReason.CYCLE_LIMIT
            logger.info("Cycle limit reached - halting rover")
            self._trigger_callbacks("cycle_limit")
            self._log_interrupt()
    
    def check_interrupt(self) -> bool:
        """
        Check if interrupt flag is set (thread-safe).
        
        Returns:
            True if interrupted, False otherwise
        """
        with self.lock:
            return self.interrupt_flag
    
    def check_pause(self) -> bool:
        """
        Check if rover is paused (thread-safe).
        
        Returns:
            True if paused, False otherwise
        """
        with self.lock:
            return self.paused
    
    def get_interrupt_reason(self) -> InterruptReason:
        """
        Get current interrupt reason (thread-safe).
        
        Returns:
            InterruptReason enum
        """
        with self.lock:
            return self.interrupt_reason
    
    def get_new_goal(self) -> Optional[Dict[str, Any]]:
        """
        Get new goal if goal_change interrupt (thread-safe).
        
        Returns:
            Goal dict or None
        """
        with self.lock:
            return self.new_goal.copy() if self.new_goal else None
    
    def clear(self):
        """
        Clear interrupt state (used after handling interrupt).
        """
        with self.lock:
            self.interrupt_flag = False
            self.interrupt_reason = InterruptReason.NONE
            self.new_goal = None
            logger.debug("Interrupt state cleared")
    
    def clear_pause(self):
        """Clear pause state specifically."""
        with self.lock:
            if self.paused:
                self.paused = False
                self.interrupt_flag = False
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get current interrupt state (thread-safe).
        
        Returns:
            State dictionary
        """
        with self.lock:
            return {
                "interrupt_flag": self.interrupt_flag,
                "interrupt_reason": self.interrupt_reason.value,
                "paused": self.paused,
                "new_goal": self.new_goal,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get interrupt history (thread-safe).
        
        Args:
            limit: Max number of recent interrupts to return
            
        Returns:
            List of interrupt records
        """
        with self.lock:
            return self.interrupt_history[-limit:]
    
    def _validate_goal(self, goal: Dict[str, Any]) -> bool:
        """Validate goal structure."""
        required_keys = {"latitude", "longitude", "name", "priority"}
        if not all(key in goal for key in required_keys):
            logger.error(f"Goal missing required keys: {required_keys}")
            return False
        
        # Validate coordinates
        if not (-90 <= goal["latitude"] <= 90):
            logger.error("Invalid latitude (must be -90 to 90)")
            return False
        if not (-180 <= goal["longitude"] <= 180):
            logger.error("Invalid longitude (must be -180 to 180)")
            return False
        if not (0 <= goal["priority"] <= 10):
            logger.error("Invalid priority (must be 0-10)")
            return False
        
        return True
    
    def _trigger_callbacks(self, interrupt_type: str):
        """Trigger registered callbacks."""
        for callback in self.callbacks:
            try:
                callback(interrupt_type)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def _log_interrupt(self):
        """Log interrupt to history."""
        record = {
            "reason": self.interrupt_reason.value,
            "paused": self.paused,
            "timestamp": datetime.now().isoformat(),
            "new_goal": self.new_goal
        }
        self.interrupt_history.append(record)
        if len(self.interrupt_history) > 100:
            self.interrupt_history.pop(0)  # Keep last 100


# Singleton instance
_interrupt_handler: Optional[InterruptHandler] = None


def get_interrupt_handler() -> InterruptHandler:
    """
    Get or create singleton InterruptHandler instance.
    
    Returns:
        InterruptHandler instance
    """
    global _interrupt_handler
    if _interrupt_handler is None:
        _interrupt_handler = InterruptHandler()
    return _interrupt_handler
