"""
Phase 2 — Live Host / Port Probing
====================================
Filters subdomains to those that actually respond using httpx.
"""

import os
import shutil
from typing import Dict, Callable
import time

from phases.base_phase import BasePhase, PhaseResult


class ProbingPhase(BasePhase):
    """Phase 2: Live Host / Port Probing."""

    def __init__(self):
        super().__init__(
            phase_id=2,
            name="Live Host Probing",
            description="Filter hosts that respond on ports 80, 443, 8080, 8000, 8888",
            required_tools=["httpx"],
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
        alive_file = os.path.join(output_dir, "subdomain_alive.txt")

        # Get input from Phase 1
        all_subs = previous_results.get("all_subdomains", "")
        if not self._file_exists_with_content(all_subs):
            on_output("[!] No subdomains file found from Phase 1 — creating minimal list from target")
            # Fall back to just the target domain
            all_subs = os.path.join(output_dir, "fallback_subs.txt")
            with open(all_subs, "w") as f:
                f.write(f"{target}\n")
                f.write(f"www.{target}\n")
            errors.append("No subdomains from Phase 1 — using target domain directly")

        # Run httpx probing
        if not self._cancelled:
            # Try httpx-toolkit first (Kali), then httpx (Go binary)
            httpx_cmd = None
            for name in ["httpx-toolkit", "httpx"]:
                if shutil.which(name):
                    httpx_cmd = name
                    break

            if httpx_cmd:
                on_output(f"[*] Probing live hosts with {httpx_cmd}...")
                cmd = (
                    f"cat {all_subs} | {httpx_cmd} "
                    f"-ports 80,443,8080,8000,8888 "
                    f"-threads 200 "
                    f"-o {alive_file}"
                )
                rc = self._run_cmd(cmd, on_output, timeout=900)
                if rc != 0:
                    errors.append(f"{httpx_cmd} returned non-zero exit code")
                    on_output(f"  [!] {httpx_cmd} had issues, continuing...")
                self._ensure_file(alive_file)
            else:
                on_output("[!] httpx / httpx-toolkit not installed — skipping probing")
                errors.append("httpx not found")
                # Fall back: treat all subdomains as alive (prepend https://)
                self._ensure_file(alive_file)
                if self._file_exists_with_content(all_subs):
                    on_output("[*] Falling back: treating all subdomains as alive...")
                    with open(all_subs, "r") as f_in, open(alive_file, "w") as f_out:
                        for line in f_in:
                            domain = line.strip()
                            if domain:
                                f_out.write(f"https://{domain}\n")

        total_subs = self._file_line_count(all_subs)
        alive_count = self._file_line_count(alive_file)
        on_output(f"  [✓] Alive hosts: {alive_count}/{total_subs}")

        return PhaseResult(
            phase_id=self.phase_id,
            phase_name=self.name,
            success=True,  # Always continue pipeline
            output_files={"subdomain_alive": alive_file},
            stats={"alive_hosts": alive_count},
            duration=time.time() - start,
            errors=errors,
        )
