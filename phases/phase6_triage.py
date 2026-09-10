"""
Phase 6 — Pattern-Based Vulnerability Triage
==============================================
Uses gf patterns to bucket URLs by likely vulnerability class.
"""

import os
import shutil
from typing import Dict, Callable
import time

from phases.base_phase import BasePhase, PhaseResult


class TriagePhase(BasePhase):
    """Phase 6: Pattern-Based Vulnerability Triage using gf."""

    GF_PATTERNS = [
        ("sqli", "sqli.txt", "SQL Injection"),
        ("lfi", "lfi.txt", "Local File Inclusion"),
        ("redirect", "redirect.txt", "Open Redirect"),
        ("cors", "cors.txt", "CORS Misconfiguration"),
        ("xss", "xss.txt", "Cross-Site Scripting"),
        ("ssrf", "ssrf.txt", "Server-Side Request Forgery"),
        ("idor", "idor.txt", "Insecure Direct Object Reference"),
        ("ssti", "ssti.txt", "Server-Side Template Injection"),
        ("rce", "rce.txt", "Remote Code Execution"),
    ]

    def __init__(self):
        super().__init__(
            phase_id=5,
            name="Vulnerability Triage",
            description="Bucket URLs by likely vuln class using gf patterns",
            required_tools=["gf"],
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
        output_files = {}
        stats = {}

        mainurls = previous_results.get("mainurls", "")
        if not self._file_exists_with_content(mainurls):
            on_output("[!] No mainurls file from Phase 3 — skipping triage")
            errors.append("No URLs available")
            return PhaseResult(
                phase_id=self.phase_id,
                phase_name=self.name,
                success=True,
                output_files=output_files,
                stats=stats,
                duration=time.time() - start,
                errors=errors,
            )

        has_gf = shutil.which("gf") is not None
        if not has_gf:
            on_output("[!] gf not installed — skipping vulnerability triage")
            errors.append("gf not found")
            return PhaseResult(
                phase_id=self.phase_id,
                phase_name=self.name,
                success=True,
                output_files=output_files,
                stats=stats,
                duration=time.time() - start,
                errors=errors,
            )

        on_output("[*] Running gf pattern matching for vulnerability triage...")

        for pattern, filename, description in self.GF_PATTERNS:
            if self._cancelled:
                break

            out_path = os.path.join(output_dir, filename)
            on_output(f"  [*] Filtering for {description} ({pattern})...")

            cmd = f"cat {mainurls} | gf {pattern} > {out_path} 2>/dev/null || true"
            self._run_cmd(cmd, on_output, timeout=120)
            self._ensure_file(out_path)

            count = self._file_line_count(out_path)
            output_files[pattern] = out_path
            stats[f"{pattern}_urls"] = count

            if count > 0:
                on_output(f"  [+] {description}: {count} potential URLs")
            else:
                on_output(f"  [-] {description}: 0 URLs matched")

        total_triaged = sum(stats.values())
        on_output(f"\n  [✓] Vulnerability triage complete: {total_triaged} total URLs triaged")

        return PhaseResult(
            phase_id=self.phase_id,
            phase_name=self.name,
            success=True,
            output_files=output_files,
            stats=stats,
            duration=time.time() - start,
            errors=errors,
        )
