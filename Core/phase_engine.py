"""
VASTA Phase Engine
==================
Orchestrates sequential execution of scanning phases.
Manages phase lifecycle, result passing, and callback notifications.
"""

import os
import threading
import time
from datetime import datetime
from typing import List, Dict, Optional, Callable, Any


class PhaseEngine:
    """
    Orchestrates the sequential execution of scanning phases.
    Each phase runs in a background thread, with results passed forward
    to subsequent phases.
    """

    # Phase statuses
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETE = "complete"
    STATUS_ERROR = "error"
    STATUS_CANCELLED = "cancelled"
    STATUS_SKIPPED = "skipped"

    def __init__(self, phases: List[Any], output_base: str = "output"):
        """
        Args:
            phases: List of BasePhase instances to execute sequentially.
            output_base: Base directory for scan output.
        """
        self._phases = phases
        self._output_base = output_base
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._paused = False
        self._cancelled = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused by default

        # State tracking
        self._current_phase_idx = -1
        self._phase_statuses: Dict[int, str] = {}
        self._phase_results: Dict[int, Any] = {}
        self._all_output_files: Dict[str, str] = {}
        self._output_dir = ""
        self._start_time = 0.0

        # Callbacks
        self.on_phase_start: Optional[Callable[[int, str], None]] = None
        self.on_phase_complete: Optional[Callable[[int, Any], None]] = None
        self.on_output: Optional[Callable[[int, str], None]] = None
        self.on_error: Optional[Callable[[int, str], None]] = None
        self.on_scan_complete: Optional[Callable[[Dict], None]] = None
        self.on_vulnerability: Optional[Callable[[Any], None]] = None

        # Initialize phase statuses
        for phase in self._phases:
            self._phase_statuses[phase.phase_id] = self.STATUS_PENDING

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def current_phase(self) -> int:
        if 0 <= self._current_phase_idx < len(self._phases):
            return self._phases[self._current_phase_idx].phase_id
        return -1

    @property
    def elapsed_time(self) -> float:
        if self._start_time > 0:
            return time.time() - self._start_time
        return 0.0

    def get_phase_status(self, phase_id: int) -> str:
        return self._phase_statuses.get(phase_id, self.STATUS_PENDING)

    def start(self, target_domain: str, enabled_phases: Optional[List[int]] = None):
        """
        Start the scanning pipeline.

        Args:
            target_domain: The target domain to scan.
            enabled_phases: List of phase IDs to run (None = all).
        """
        if self._running:
            return

        self._running = True
        self._cancelled = False
        self._paused = False
        self._pause_event.set()
        self._start_time = time.time()

        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_domain = target_domain.replace(".", "_").replace("/", "_")
        self._output_dir = os.path.join(
            self._output_base, f"{safe_domain}_{timestamp}"
        )
        os.makedirs(self._output_dir, exist_ok=True)

        # Determine which phases to run
        self._enabled_phases = set(
            enabled_phases if enabled_phases else [p.phase_id for p in self._phases]
        )

        # Start execution thread
        self._thread = threading.Thread(
            target=self._execute_pipeline,
            args=(target_domain,),
            daemon=True,
        )
        self._thread.start()

    def pause(self):
        """Pause the pipeline execution."""
        if self._running and not self._paused:
            self._paused = True
            self._pause_event.clear()
            self._emit_output(-1, "[⏸] Scan paused")

    def resume(self):
        """Resume the pipeline execution."""
        if self._running and self._paused:
            self._paused = False
            self._pause_event.set()
            self._emit_output(-1, "[▶] Scan resumed")

    def cancel(self):
        """Cancel the pipeline execution."""
        self._cancelled = True
        self._running = False
        self._paused = False
        self._pause_event.set()  # Unblock if paused

        # Cancel current phase
        if 0 <= self._current_phase_idx < len(self._phases):
            self._phases[self._current_phase_idx].cancel()

        self._emit_output(-1, "[■] Scan cancelled by user")

    def _execute_pipeline(self, target: str):
        """Main pipeline execution loop (runs in background thread)."""
        self._emit_output(
            -1,
            f"\n{'═' * 60}\n"
            f"  🛡  VASTA SCAN STARTED\n"
            f"  Target: {target}\n"
            f"  Output: {self._output_dir}\n"
            f"  Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'═' * 60}\n"
        )

        accumulated_results: Dict[str, str] = {}

        for idx, phase in enumerate(self._phases):
            if self._cancelled:
                break

            # Wait if paused
            self._pause_event.wait()

            if self._cancelled:
                break

            # Skip disabled phases
            if phase.phase_id not in self._enabled_phases:
                self._phase_statuses[phase.phase_id] = self.STATUS_SKIPPED
                self._emit_output(
                    phase.phase_id,
                    f"[⊘] Phase {phase.phase_id} ({phase.name}) — SKIPPED"
                )
                continue

            # Start phase
            self._current_phase_idx = idx
            self._phase_statuses[phase.phase_id] = self.STATUS_RUNNING

            self._emit_output(
                phase.phase_id,
                f"\n{'─' * 50}\n"
                f"  {phase.name}  [{phase.phase_id}/7]\n"
                f"  {phase.description}\n"
                f"{'─' * 50}"
            )

            if self.on_phase_start:
                self.on_phase_start(phase.phase_id, phase.name)

            try:
                # Run the phase
                result = phase.run(
                    target=target,
                    output_dir=self._output_dir,
                    previous_results=accumulated_results,
                    on_output=lambda line, pid=phase.phase_id: self._emit_output(pid, line),
                )

                if self._cancelled:
                    self._phase_statuses[phase.phase_id] = self.STATUS_CANCELLED
                    break

                # Store results
                self._phase_results[phase.phase_id] = result

                if result.success:
                    self._phase_statuses[phase.phase_id] = self.STATUS_COMPLETE

                    # Merge output files for next phases
                    accumulated_results.update(result.output_files)
                    self._all_output_files.update(result.output_files)

                    # Report stats
                    stats_str = ", ".join(
                        f"{k}: {v}" for k, v in result.stats.items()
                    )
                    self._emit_output(
                        phase.phase_id,
                        f"  [✓] Phase {phase.phase_id} complete — {stats_str}"
                    )

                    # Report vulnerabilities
                    if result.vulnerabilities:
                        for vuln in result.vulnerabilities:
                            if self.on_vulnerability:
                                self.on_vulnerability(vuln)
                        self._emit_output(
                            phase.phase_id,
                            f"  [🐛] Found {len(result.vulnerabilities)} vulnerabilities"
                        )
                else:
                    self._phase_statuses[phase.phase_id] = self.STATUS_ERROR
                    errors_str = "; ".join(result.errors) if result.errors else "Unknown error"
                    self._emit_output(
                        phase.phase_id,
                        f"  [✗] Phase {phase.phase_id} failed: {errors_str}"
                    )

                if self.on_phase_complete:
                    self.on_phase_complete(phase.phase_id, result)

            except Exception as e:
                self._phase_statuses[phase.phase_id] = self.STATUS_ERROR
                error_msg = f"Phase {phase.phase_id} exception: {str(e)}"
                self._emit_output(phase.phase_id, f"  [✗] {error_msg}")

                if self.on_error:
                    self.on_error(phase.phase_id, error_msg)

        # Scan complete
        self._running = False
        elapsed = time.time() - self._start_time

        self._emit_output(
            -1,
            f"\n{'═' * 60}\n"
            f"  🛡  VASTA SCAN {'CANCELLED' if self._cancelled else 'COMPLETE'}\n"
            f"  Duration: {self._format_duration(elapsed)}\n"
            f"  Output:   {self._output_dir}\n"
            f"{'═' * 60}\n"
        )

        if self.on_scan_complete:
            self.on_scan_complete({
                "phase_results": self._phase_results,
                "phase_statuses": self._phase_statuses,
                "output_files": self._all_output_files,
                "output_dir": self._output_dir,
                "duration": elapsed,
                "cancelled": self._cancelled,
            })

    def _emit_output(self, phase_id: int, text: str):
        """Emit output line to callback."""
        if self.on_output:
            self.on_output(phase_id, text)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format seconds into human-readable duration."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def get_output_dir(self) -> str:
        """Return the output directory for the current scan."""
        return self._output_dir

    def get_all_results(self) -> Dict[int, Any]:
        """Return results from all completed phases."""
        return self._phase_results.copy()
