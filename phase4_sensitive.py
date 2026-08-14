"""
Phase 4 — Sensitive File / JS Discovery
=========================================
Surfaces JS files and exposed sensitive file extensions.
"""

import os
from typing import Dict, Callable
import time

from phases.base_phase import BasePhase, PhaseResult


class SensitivePhase(BasePhase):
    """Phase 4: Sensitive File / JS Discovery."""

    def __init__(self):
        super().__init__(
            phase_id=4,
            name="Sensitive File Discovery",
            description="Surface JS files and exposed sensitive extensions",
            required_tools=[],
        )

    def run(
        self,
        target: str,
        output_dir: str,
        previous_results: Dict[str, str],
        on_output: Callable[[str], None],
    ) -> PhaseResult:
        start = time.time()
        errors = []
        js_file = os.path.join(output_dir, "js.txt")
        sensitive_file = os.path.join(output_dir, "sensitive_files.txt")

        mainurls = previous_results.get("mainurls", "")
        if not self._file_exists_with_content(mainurls):
            on_output("[!] No mainurls file from Phase 3 — skipping sensitive file scanning")
            errors.append("No URLs available")
            self._ensure_file(js_file)
            self._ensure_file(sensitive_file)
            return PhaseResult(
                phase_id=self.phase_id,
                phase_name=self.name,
                success=True,
                output_files={"js_files": js_file, "sensitive_files": sensitive_file},
                stats={"js_files": 0, "sensitive_files": 0},
                duration=time.time() - start,
                errors=errors,
            )

        # Step 1: Extract JS files
        if not self._cancelled:
            on_output("[*] Extracting JavaScript file URLs...")
            cmd = f"grep -iE '\\.js(\\?|$)' {mainurls} > {js_file} || true"
            self._run_cmd(cmd, on_output)
            self._ensure_file(js_file)
            js_count = self._file_line_count(js_file)
            on_output(f"  [+] Found {js_count} JS files")

        # Step 2: Extract sensitive file extensions
        if not self._cancelled:
            on_output("[*] Extracting sensitive file URLs...")
            extensions = (
                r"\.(txt|log|cache|secret|db|backup|yml|yaml|json|gz|rar|zip|"
                r"config|bak|old|sql|env|key|pem|cfg)(\?|$)"
            )
            cmd = f"grep -iE '{extensions}' {mainurls} > {sensitive_file} || true"
            self._run_cmd(cmd, on_output)
            self._ensure_file(sensitive_file)
            sens_count = self._file_line_count(sensitive_file)
            on_output(f"  [+] Found {sens_count} sensitive files")

        js_count = self._file_line_count(js_file)
        sens_count = self._file_line_count(sensitive_file)
        on_output(f"  [✓] JS files: {js_count}, Sensitive files: {sens_count}")

        return PhaseResult(
            phase_id=self.phase_id,
            phase_name=self.name,
            success=True,
            output_files={
                "js_files": js_file,
                "sensitive_files": sensitive_file,
            },
            stats={"js_files": js_count, "sensitive_files": sens_count},
            duration=time.time() - start,
            errors=errors,
        )
