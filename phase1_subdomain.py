"""
Phase 1 — Subdomain Enumeration
================================
Discovers subdomains using subfinder and assetfinder, then merges results.
Continues even if one tool fails — partial results are still useful.
"""

import os
import shutil
from typing import Dict, Callable
import time

from phases.base_phase import BasePhase, PhaseResult


class SubdomainPhase(BasePhase):
    """Phase 1: Subdomain Enumeration."""

    def __init__(self):
        super().__init__(
            phase_id=1,
            name="Subdomain Enumeration",
            description="Discover subdomains using subfinder & assetfinder",
            required_tools=["subfinder", "assetfinder"],
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
        subfinder_file = os.path.join(output_dir, "subfinder.txt")
        assetfinder_file = os.path.join(output_dir, "assetfinder.txt")
        all_subs_file = os.path.join(output_dir, "all_subdomains.txt")

        # Step 1: subfinder
        if not self._cancelled:
            if shutil.which("subfinder"):
                on_output("[*] Running subfinder...")
                cmd = f"subfinder -d {target} -all -recursive -o {subfinder_file}"
                rc = self._run_cmd(cmd, on_output, timeout=600)
                if rc != 0:
                    errors.append("subfinder returned non-zero exit code")
                    on_output("  [!] subfinder had issues, continuing with any partial results...")
                self._ensure_file(subfinder_file)
                count = self._file_line_count(subfinder_file)
                on_output(f"  [+] subfinder found {count} subdomains")
            else:
                on_output("[!] subfinder not installed — skipping")
                errors.append("subfinder not found")
                self._ensure_file(subfinder_file)

        # Step 2: assetfinder
        if not self._cancelled:
            if shutil.which("assetfinder"):
                on_output("[*] Running assetfinder...")
                cmd = f"assetfinder --subs-only {target} > {assetfinder_file}"
                rc = self._run_cmd(cmd, on_output, timeout=300)
                if rc != 0:
                    errors.append("assetfinder returned non-zero exit code")
                    on_output("  [!] assetfinder had issues, continuing with any partial results...")
                self._ensure_file(assetfinder_file)
                count = self._file_line_count(assetfinder_file)
                on_output(f"  [+] assetfinder found {count} subdomains")
            else:
                on_output("[!] assetfinder not installed — skipping")
                errors.append("assetfinder not found")
                self._ensure_file(assetfinder_file)

        # Step 3: Merge and deduplicate
        if not self._cancelled:
            on_output("[*] Merging and deduplicating subdomains...")
            self._ensure_file(subfinder_file)
            self._ensure_file(assetfinder_file)
            cmd = f"sort -u {subfinder_file} {assetfinder_file} > {all_subs_file}"
            self._run_cmd(cmd, on_output)
            self._ensure_file(all_subs_file)

        total = self._file_line_count(all_subs_file)
        on_output(f"  [✓] Total unique subdomains: {total}")

        # Phase is "successful" even with errors, as long as the output file exists.
        # This allows subsequent phases to run on whatever data we collected.
        return PhaseResult(
            phase_id=self.phase_id,
            phase_name=self.name,
            success=True,  # Always succeed — partial results are still useful
            output_files={"all_subdomains": all_subs_file},
            stats={"subdomains": total},
            vulnerabilities=[],
            duration=time.time() - start,
            errors=errors,
        )
