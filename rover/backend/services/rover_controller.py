"""Background controller for the rover decision loop."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from agents.core.agent_state import get_rover_state_container
from agents.core.interrupt_handler import InterruptReason, get_interrupt_handler
from agents.shared.mock_generators import get_mock_generator
from agents.workflows.rover_decision_loop import execute_rover_decision_loop

logger = logging.getLogger(__name__)


@dataclass
class RoverControllerStatus:
    """Snapshot of the rover controller state."""

    running: bool = False
    paused: bool = False
    stopped: bool = False
    cycles_completed: int = 0
    max_cycles: int = 100
    started_at: Optional[str] = None
    updated_at: Optional[str] = None
    reason: Optional[str] = None
    last_state: Dict[str, Any] = field(default_factory=dict)


class RoverController:
    """Owns a background thread that advances the rover loop one cycle at a time."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._status = RoverControllerStatus()
        self._worker: Optional[threading.Thread] = None
        self._pause_event = threading.Event()
        self._stop_event = threading.Event()

    def start(self, initial_state: Optional[Dict[str, Any]] = None, max_cycles: Optional[int] = None) -> RoverControllerStatus:
        with self._lock:
            if self._worker and self._worker.is_alive():
                return self._snapshot()

            self._stop_event.clear()
            self._pause_event.set()

            state = initial_state or get_rover_state_container().get_state() or get_mock_generator().generate_initial_state()
            target_max_cycles = int(max_cycles or state.get("max_cycles", 100) or 100)
            state["max_cycles"] = target_max_cycles

            get_rover_state_container(state).set_state(state)
            handler = get_interrupt_handler()
            handler.clear()
            handler.clear_pause()

            self._status = RoverControllerStatus(
                running=True,
                paused=False,
                stopped=False,
                cycles_completed=0,
                max_cycles=target_max_cycles,
                started_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
                reason=None,
                last_state=state.copy(),
            )

            self._worker = threading.Thread(target=self._run, name="rover-controller", daemon=True)
            self._worker.start()
            return self._snapshot()

    def pause(self) -> RoverControllerStatus:
        with self._lock:
            self._pause_event.clear()
            get_interrupt_handler().pause()
            self._status.paused = True
            self._status.updated_at = datetime.utcnow().isoformat()
            self._status.reason = InterruptReason.USER_PAUSE.value
            return self._snapshot()

    def resume(self) -> RoverControllerStatus:
        with self._lock:
            self._pause_event.set()
            get_interrupt_handler().resume()
            self._status.paused = False
            self._status.updated_at = datetime.utcnow().isoformat()
            self._status.reason = InterruptReason.USER_RESUME.value
            return self._snapshot()

    def stop(self) -> RoverControllerStatus:
        with self._lock:
            self._stop_event.set()
            self._pause_event.set()
            get_interrupt_handler().stop()
            self._status.stopped = True
            self._status.running = False
            self._status.paused = False
            self._status.updated_at = datetime.utcnow().isoformat()
            self._status.reason = InterruptReason.USER_STOP.value
            return self._snapshot()

    def status(self) -> RoverControllerStatus:
        return self._snapshot()

    def _snapshot(self) -> RoverControllerStatus:
        with self._lock:
            return RoverControllerStatus(
                running=self._status.running,
                paused=self._status.paused,
                stopped=self._status.stopped,
                cycles_completed=self._status.cycles_completed,
                max_cycles=self._status.max_cycles,
                started_at=self._status.started_at,
                updated_at=self._status.updated_at,
                reason=self._status.reason,
                last_state=self._status.last_state.copy(),
            )

    def _run(self) -> None:
        logger.info("Rover controller thread started")
        try:
            while not self._stop_event.is_set() and self._status.cycles_completed < self._status.max_cycles:
                self._pause_event.wait()
                if self._stop_event.is_set():
                    break

                current_state = get_rover_state_container().get_state()
                if not current_state:
                    current_state = get_mock_generator().generate_initial_state()

                current_state["max_cycles"] = 1
                result = execute_rover_decision_loop(initial_state=current_state, max_iterations=1)

                with self._lock:
                    self._status.cycles_completed += result.iterations
                    self._status.last_state = result.state.copy()
                    self._status.updated_at = datetime.utcnow().isoformat()
                    self._status.reason = result.reason
                    self._status.paused = bool(get_interrupt_handler().check_pause())

                get_rover_state_container(result.state).set_state(result.state)

                if result.interrupted or result.state.get("current_action") == "reached_goal":
                    break

            with self._lock:
                self._status.running = False
                self._status.updated_at = datetime.utcnow().isoformat()
                if not self._status.reason:
                    self._status.reason = InterruptReason.CYCLE_LIMIT.value
        except Exception as exc:  # pragma: no cover - defensive background guard
            logger.exception("Rover controller failed: %s", exc)
            with self._lock:
                self._status.running = False
                self._status.stopped = True
                self._status.updated_at = datetime.utcnow().isoformat()
                self._status.reason = InterruptReason.ERROR.value


_controller: Optional[RoverController] = None


def get_rover_controller() -> RoverController:
    """Get the singleton rover controller."""
    global _controller
    if _controller is None:
        _controller = RoverController()
    return _controller
