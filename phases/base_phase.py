"""
VASTA Base Phase
================
Abstract base class for all scanning phases.
"""

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional

from core.command_runner import CommandRunner
from core.result_parser import Vulnerability


@dataclass
class PhaseResult:
    """Result from a completed phase."""
    phase_id: int
    phase_name: str
    success: bool
    output_files: Dict[str, str] = field(default_factory=dict)
    stats: Dict[str, int] = field(default_factory=dict)
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    duration: float = 0.0
    errors: List[str] = field(default_factory=list)


class BasePhase(ABC):
    """Abstract base class for scanning phases."""

    def __init__(
        self,
        phase_id: int,
        name: str,
        description: str,
        required_tools: List[str],
    ):
        self.phase_id = phase_id
        self.name = name
        self.description = description
        self.required_tools = required_tools
        self._cancelled = False
        self._runner = CommandRunner()

    @abstractmethod
    def run(
        self,
        target: str,
        output_dir: str,
        previous_results: Dict[str, str],
        on_output: Callable[[str], None],
    ) -> PhaseResult:
        """
        Execute the phase.

        Args:
            target: Target domain.
            output_dir: Directory to write output files.
            previous_results: Dict of output file keys -> paths from prior phases.
            on_output: Callback for logging output lines.

        Returns:
            PhaseResult with findings and metadata.
        """
        pass

    def cancel(self):
        """Cancel this phase's execution."""
        self._cancelled = True
        self._runner.cancel()

    def _run_cmd(
        self,
        cmd: str,
        on_output: Callable[[str], None],
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> int:
        """
        Helper to run a shell command with output streaming.

        Returns:
            Process return code.
        """
        on_output(f"  ❯ {cmd}")
        return self._runner.run(
            cmd,
            cwd=cwd,
            timeout=timeout,
            on_output=lambda line: on_output(f"    {line}"),
        )

    def _file_line_count(self, filepath: str) -> int:
        """Count non-empty lines in a file."""
        if not filepath or not os.path.exists(filepath):
            return 0
        try:
            with open(filepath, "r", errors="ignore") as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0

    def _file_exists_with_content(self, filepath: str) -> bool:
        """Check if file exists and has content."""
        return os.path.exists(filepath) and os.path.getsize(filepath) > 0

    def _ensure_file(self, filepath: str):
        """Create empty file if it doesn't exist."""
        if not os.path.exists(filepath):
            open(filepath, "w").close()
