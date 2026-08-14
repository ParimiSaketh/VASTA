"""
Phase 3 — Endpoint & URL Discovery
=====================================
Crawls live hosts with katana and pulls historical URLs with waybackurls.
"""

import os
import shutil
from typing import Dict, Callable
import time

from phases.base_phase import BasePhase, PhaseResult


class EndpointPhase(BasePhase):
    """Phase 3: Endpoint & URL Discovery."""

    def __init__(self):
        super().__init__(
            phase_id=3,
            name="Endpoint Discovery",
            description="Crawl live hosts and pull historical URLs",
            required_tools=["katana", "waybackurls"],
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
        katana_file = os.path.join(output_dir, "katana_endpoints.txt")
        wayback_file = os.path.join(output_dir, "waybackurls.txt")
        mainurls_file = os.path.join(output_dir, "mainurls.txt")

        alive_file = previous_results.get("subdomain_alive", "")
        if not self._file_exists_with_content(alive_file):
            on_output("[!] No alive hosts file from Phase 2 — using target domain")
            alive_file = os.path.join(output_dir, "fallback_alive.txt")
            with open(alive_file, "w") as f:
                f.write(f"https://{target}\n")
            errors.append("No alive hosts — using target domain")

        # Step 1: Katana crawling
        if not self._cancelled:
            if shutil.which("katana"):
                on_output("[*] Crawling endpoints with katana (depth 5)...")
                cmd = f"katana -list {alive_file} -depth 5 -o {katana_file}"
                rc = self._run_cmd(cmd, on_output, timeout=1800)
                if rc != 0:
                    errors.append("katana had issues")
                    on_output("  [!] katana had issues, continuing...")
                self._ensure_file(katana_file)
                count = self._file_line_count(katana_file)
                on_output(f"  [+] katana found {count} endpoints")
            else:
                on_output("[!] katana not installed — skipping crawling")
                errors.append("katana not found")
                self._ensure_file(katana_file)

        # Step 2: Wayback URLs
        if not self._cancelled:
            if shutil.which("waybackurls"):
                on_output("[*] Fetching historical URLs from Wayback Machine...")
                cmd = f"cat {alive_file} | waybackurls > {wayback_file}"
                rc = self._run_cmd(cmd, on_output, timeout=600)
                if rc != 0:
                    errors.append("waybackurls had issues")
                    on_output("  [!] waybackurls had issues, continuing...")
                self._ensure_file(wayback_file)
                count = self._file_line_count(wayback_file)
                on_output(f"  [+] waybackurls found {count} URLs")
            else:
                on_output("[!] waybackurls not installed — skipping")
                errors.append("waybackurls not found")
                self._ensure_file(wayback_file)

        # Step 3: Merge and deduplicate
        if not self._cancelled:
            on_output("[*] Merging and deduplicating URLs...")
            self._ensure_file(katana_file)
            self._ensure_file(wayback_file)
            cmd = f"sort -u {katana_file} {wayback_file} > {mainurls_file}"
            self._run_cmd(cmd, on_output)
            self._ensure_file(mainurls_file)

        total = self._file_line_count(mainurls_file)
        on_output(f"  [✓] Total unique URLs: {total}")

        return PhaseResult(
            phase_id=self.phase_id,
            phase_name=self.name,
            success=True,
            output_files={
                "mainurls": mainurls_file,
                "katana_endpoints": katana_file,
                "waybackurls": wayback_file,
            },
            stats={"endpoints": total},
            duration=time.time() - start,
            errors=errors,
        )
