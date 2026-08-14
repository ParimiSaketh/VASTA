"""
Phase 7 — Active Vulnerability Scanning
=========================================
Runs targeted scanners (dalfox, sqlmap, etc.) against triaged URLs.
"""

import os
import shutil
from typing import Dict, Callable, List
import time

from phases.base_phase import BasePhase, PhaseResult
from core.result_parser import Vulnerability


class ScanningPhase(BasePhase):
    """Phase 7: Active Vulnerability Scanning."""

    # Scanner definitions: (pattern_key, tool_name, tool_cmd_template, vuln_type, severity)
    SCANNERS = [
        {
            "pattern": "xss",
            "tool": "dalfox",
            "severity": "high",
            "vuln_type": "XSS",
            "cmd": "dalfox file {input_file} -o {output_file} --silence 2>/dev/null || true",
        },
        {
            "pattern": "sqli",
            "tool": "sqlmap",
            "severity": "critical",
            "vuln_type": "SQL Injection",
            "cmd": "sqlmap -m {input_file} --batch --random-agent --level 1 --risk 1 --output-dir={output_dir}/sqlmap_out 2>&1 | tee {output_file} || true",
        },
        {
            "pattern": "lfi",
            "tool": "python3",  # LFI-FINDER is a python tool
            "severity": "high",
            "vuln_type": "LFI",
            "cmd": "python3 -c \"print('LFI scanning requires manual review of: {input_file}')\" > {output_file} || true",
        },
        {
            "pattern": "redirect",
            "tool": "python3",
            "severity": "medium",
            "vuln_type": "Open Redirect",
            "cmd": "python3 -c \"print('Open Redirect scanning requires manual review of: {input_file}')\" > {output_file} || true",
        },
        {
            "pattern": "cors",
            "tool": "python3",
            "severity": "medium",
            "vuln_type": "CORS",
            "cmd": "python3 -c \"print('CORS scanning requires manual review of: {input_file}')\" > {output_file} || true",
        },
    ]

    def __init__(self):
        super().__init__(
            phase_id=7,
            name="Active Scanning",
            description="Run targeted scanners against triaged URLs",
            required_tools=["dalfox", "sqlmap"],
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
        stats = {}
        all_vulns: List[Vulnerability] = []
        output_files = {}

        on_output("[*] Starting active vulnerability scanning...")

        for scanner in self.SCANNERS:
            if self._cancelled:
                break

            pattern = scanner["pattern"]
            tool = scanner["tool"]
            vuln_type = scanner["vuln_type"]
            severity = scanner["severity"]

            # Check if we have triaged URLs for this pattern
            input_file = previous_results.get(pattern, "")
            if not self._file_exists_with_content(input_file):
                on_output(f"  [⊘] No {vuln_type} URLs to scan — skipping")
                stats[f"{vuln_type}_vulns"] = 0
                continue

            url_count = self._file_line_count(input_file)

            # Check tool availability
            if tool not in ("python3",) and not shutil.which(tool):
                on_output(f"  [!] {tool} not installed — skipping {vuln_type} scan")
                errors.append(f"{tool} not found")
                stats[f"{vuln_type}_vulns"] = 0
                continue

            # ── Clear banner showing which tool is running ──
            on_output(f"\n  {'─' * 40}")
            on_output(f"  🔧 TOOL: {tool.upper()}")
            on_output(f"  🎯 Scanning for: {vuln_type} ({severity.upper()} severity)")
            on_output(f"  📄 Processing: {url_count} URLs")
            on_output(f"  {'─' * 40}")

            # Build output file and command
            output_file = os.path.join(output_dir, f"scan_{pattern}_results.txt")
            cmd = scanner["cmd"].format(
                input_file=input_file,
                output_file=output_file,
                output_dir=output_dir,
            )

            rc = self._run_cmd(cmd, on_output, timeout=1800)
            self._ensure_file(output_file)

            # Count results
            result_count = self._file_line_count(output_file)
            stats[f"{vuln_type}_vulns"] = result_count
            output_files[f"{pattern}_results"] = output_file

            if result_count > 0:
                on_output(f"  [🐛] {vuln_type}: {result_count} potential findings!")

                # Parse results into Vulnerability objects
                try:
                    with open(output_file, "r", errors="ignore") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                vuln = Vulnerability(
                                    severity=severity,
                                    vuln_type=vuln_type,
                                    url=line[:500],  # Truncate very long URLs
                                    tool=tool,
                                    details=f"Found by {tool}",
                                )
                                all_vulns.append(vuln)
                except Exception as e:
                    errors.append(f"Error parsing {output_file}: {e}")
            else:
                on_output(f"  [-] {vuln_type}: No vulnerabilities found")

        total_vulns = len(all_vulns)
        on_output(f"\n  [✓] Active scanning complete: {total_vulns} total vulnerabilities found")

        return PhaseResult(
            phase_id=self.phase_id,
            phase_name=self.name,
            success=True,
            output_files=output_files,
            stats=stats,
            vulnerabilities=all_vulns,
            duration=time.time() - start,
            errors=errors,
        )
