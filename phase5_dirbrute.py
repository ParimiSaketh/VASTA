"""
Phase 5 — Directory & Content Bruteforce
==========================================
Finds hidden files and paths not caught by crawling using dirsearch.
"""

import os
import shutil
from typing import Dict, Callable
import time

from phases.base_phase import BasePhase, PhaseResult


class DirBrutePhase(BasePhase):
    """Phase 5: Directory & Content Bruteforce."""

    def __init__(self):
        super().__init__(
            phase_id=6,
            name="Directory Bruteforce",
            description="Find hidden files/paths not caught by crawling",
            required_tools=["dirsearch"],
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
        dirsearch_file = os.path.join(output_dir, "dirsearch_results.txt")

        alive_file = previous_results.get("subdomain_alive", "")
        if not self._file_exists_with_content(alive_file):
            on_output("[!] No alive hosts file — skipping directory bruteforce")
            errors.append("No alive hosts available")
            self._ensure_file(dirsearch_file)
            return PhaseResult(
                phase_id=self.phase_id,
                phase_name=self.name,
                success=True,
                output_files={"dirsearch_results": dirsearch_file},
                stats={"dirs_found": 0},
                duration=time.time() - start,
                errors=errors,
            )

        # Run dirsearch
        if not self._cancelled:
            if shutil.which("dirsearch"):
                on_output(f"[*] Running dirsearch on {target}...")
                extensions = (
                    "conf,config,bak,backup,old,db,sql,php,"
                    "html,js,json,log,txt,xml,zip"
                )
                cmd = (
                    f"dirsearch -u {target} "
                    f"-e {extensions} "
                    f"-o {dirsearch_file} "
                    f"--format plain "
                    f"-t 50 "
                    f"--no-color"
                )
                rc = self._run_cmd(cmd, on_output, timeout=3600)
                if rc != 0:
                    errors.append("dirsearch had issues")
                    on_output("  [!] dirsearch had issues, continuing...")
                self._ensure_file(dirsearch_file)
            else:
                on_output("[!] dirsearch not installed — skipping")
                errors.append("dirsearch not found")
                self._ensure_file(dirsearch_file)

        dirs_count = self._file_line_count(dirsearch_file)
        on_output(f"  [✓] Directory bruteforce found {dirs_count} results")

        return PhaseResult(
            phase_id=self.phase_id,
            phase_name=self.name,
            success=True,
            output_files={"dirsearch_results": dirsearch_file},
            stats={"dirs_found": dirs_count},
            duration=time.time() - start,
            errors=errors,
        )
