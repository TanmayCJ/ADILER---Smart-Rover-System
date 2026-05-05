"""
Rover state container for LangGraph.
Manages in-memory state with thread-safe access.
"""

import logging
import threading
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class RoverStateContainer:
    """
    Thread-safe container for rover state.
    Acts as the central store for LangGraph execution.
    """
    
    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        """
        Initialize state container.
        
        Args:
            initial_state: Initial state dict (optional)
        """
        self.state: Dict[str, Any] = initial_state or {}
        self.lock = threading.RLock()
        self.update_count = 0
        self.version = 0
        logger.info(f"RoverStateContainer initialized with {len(self.state)} keys")
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update state with new values (thread-safe).
        Performs shallow merge of updates into state.
        
        Args:
            updates: Dictionary of updates
        """
        with self.lock:
            self.state.update(updates)
            self.update_count += 1
            self.version += 1
            
            # Update timestamp
            if "timestamp" not in updates:
                self.state["timestamp"] = datetime.now().isoformat()
            
            logger.debug(f"State updated (v{self.version}, {len(updates)} fields)")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get state value by key (thread-safe).
        
        Args:
            key: State key
            
        Returns:
            Value or None if not found
        """
        with self.lock:
            return self.state.get(key)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get complete state copy (thread-safe).
        
        Returns:
            Deep copy of state dictionary
        """
        with self.lock:
            return self.state.copy()
    
    def set_state(self, new_state: Dict[str, Any]) -> None:
        """
        Replace entire state (thread-safe).
        
        Args:
            new_state: New state dictionary
        """
        with self.lock:
            self.state = new_state.copy()
            self.version += 1
            self.update_count += 1
            logger.info(f"State replaced (v{self.version})")
    
    def increment_cycle(self) -> int:
        """
        Increment cycle counter.
        
        Returns:
            New cycle count
        """
        with self.lock:
            current_cycle = self.state.get("cycle_count", 0)
            new_cycle = current_cycle + 1
            self.state["cycle_count"] = new_cycle
            self.state["timestamp"] = datetime.now().isoformat()
            return new_cycle
    
    def add_error(self, error_message: str) -> None:
        """
        Add error to error log.
        
        Args:
            error_message: Error description
        """
        with self.lock:
            if "error_log" not in self.state:
                self.state["error_log"] = []
            
            error_entry = {
                "message": error_message,
                "timestamp": datetime.now().isoformat(),
                "cycle": self.state.get("cycle_count", 0)
            }
            self.state["error_log"].append(error_entry)
            logger.error(f"Error logged: {error_message}")
            
            # Keep last 100 errors
            if len(self.state["error_log"]) > 100:
                self.state["error_log"] = self.state["error_log"][-100:]
    
    def add_llm_call(self) -> None:
        """Increment LLM call counter."""
        with self.lock:
            current = self.state.get("llm_calls", 0)
            self.state["llm_calls"] = current + 1
    
    def add_experience(self, experience: Dict[str, Any]) -> None:
        """
        Add experience to buffer.
        
        Args:
            experience: Experience record
        """
        with self.lock:
            if "experience_buffer" not in self.state:
                self.state["experience_buffer"] = []
            
            self.state["experience_buffer"].append(experience)
            
            # Keep last 100 experiences in buffer
            if len(self.state["experience_buffer"]) > 100:
                self.state["experience_buffer"] = self.state["experience_buffer"][-100:]
            
            logger.debug(f"Experience added (total: {len(self.state['experience_buffer'])})")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get state container statistics.
        
        Returns:
            Statistics dictionary
        """
        with self.lock:
            return {
                "version": self.version,
                "update_count": self.update_count,
                "state_size": len(self.state),
                "cycle_count": self.state.get("cycle_count", 0),
                "llm_calls": self.state.get("llm_calls", 0),
                "error_count": len(self.state.get("error_log", [])),
                "experience_buffer_size": len(self.state.get("experience_buffer", [])),
                "timestamp": datetime.now().isoformat()
            }
    
    def save_checkpoint(self, filename: str) -> None:
        """
        Save state checkpoint to JSON file.
        
        Args:
            filename: Output filename
        """
        with self.lock:
            try:
                # Remove non-serializable items for JSON
                serializable_state = self._make_serializable(self.state)
                
                with open(filename, 'w') as f:
                    json.dump(serializable_state, f, indent=2, default=str)
                
                logger.info(f"State checkpoint saved to {filename}")
            except Exception as e:
                logger.error(f"Failed to save checkpoint: {e}")
    
    def load_checkpoint(self, filename: str) -> None:
        """
        Load state from checkpoint file.
        
        Args:
            filename: Input filename
        """
        with self.lock:
            try:
                with open(filename, 'r') as f:
                    self.state = json.load(f)
                
                self.version += 1
                logger.info(f"State checkpoint loaded from {filename}")
            except Exception as e:
                logger.error(f"Failed to load checkpoint: {e}")
    
    def clear(self) -> None:
        """Clear all state."""
        with self.lock:
            self.state.clear()
            self.version += 1
            logger.warning("State cleared")
    
    def _make_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format."""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(v) for v in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)


# Singleton instance
_state_container: Optional[RoverStateContainer] = None


def get_rover_state_container(initial_state: Optional[Dict[str, Any]] = None) -> RoverStateContainer:
    """
    Get or create singleton RoverStateContainer instance.
    
    Args:
        initial_state: Initial state for creation
        
    Returns:
        RoverStateContainer instance
    """
    global _state_container
    if _state_container is None:
        _state_container = RoverStateContainer(initial_state=initial_state)
    return _state_container
