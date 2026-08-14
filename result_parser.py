"""
VASTA Result Parser
===================
Parses output from various security scanning tools into structured data.
Provides dataclasses for Vulnerability and ScanSummary.
"""

import os
import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime


@dataclass
class Vulnerability:
    """Represents a discovered vulnerability."""
    severity: str  # "critical", "high", "medium", "low", "info"
    vuln_type: str  # "XSS", "SQLi", "LFI", "CORS", etc.
    url: str
    tool: str
    details: str = ""
    payload: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "vuln_type": self.vuln_type,
            "url": self.url,
            "tool": self.tool,
            "details": self.details,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


@dataclass
class ScanSummary:
    """Overall scan summary statistics."""
    total_subdomains: int = 0
    alive_hosts: int = 0
    total_endpoints: int = 0
    js_files: int = 0
    sensitive_files: int = 0
    dirs_found: int = 0
    vulnerabilities: List[Vulnerability] = field(default_factory=list)

    @property
    def vuln_count(self) -> int:
        return len(self.vulnerabilities)

    @property
    def severity_counts(self) -> Dict[str, int]:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for v in self.vulnerabilities:
            sev = v.severity.lower()
            if sev in counts:
                counts[sev] += 1
        return counts

    def to_dict(self) -> dict:
        return {
            "total_subdomains": self.total_subdomains,
            "alive_hosts": self.alive_hosts,
            "total_endpoints": self.total_endpoints,
            "js_files": self.js_files,
            "sensitive_files": self.sensitive_files,
            "dirs_found": self.dirs_found,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "severity_counts": self.severity_counts,
        }


class ResultParser:
    """Parses output files from security scanning tools."""

    @staticmethod
    def _read_lines(file_path: str) -> List[str]:
        """Read non-empty lines from a file."""
        if not file_path or not os.path.exists(file_path):
            return []
        try:
            with open(file_path, "r", errors="ignore") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception:
            return []

    @staticmethod
    def _count_lines(file_path: str) -> int:
        """Count non-empty lines in a file."""
        if not file_path or not os.path.exists(file_path):
            return 0
        try:
            with open(file_path, "r", errors="ignore") as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0

    def parse_subdomains(self, file_path: str) -> Tuple[List[str], int]:
        """Parse subdomain enumeration results."""
        lines = self._read_lines(file_path)
        return lines, len(lines)

    def parse_alive_hosts(self, file_path: str) -> Tuple[List[str], int]:
        """Parse httpx alive host results."""
        lines = self._read_lines(file_path)
        return lines, len(lines)

    def parse_endpoints(self, file_path: str) -> Tuple[List[str], int]:
        """Parse endpoint/URL discovery results."""
        lines = self._read_lines(file_path)
        return lines, len(lines)

    def parse_js_files(self, file_path: str) -> Tuple[List[str], int]:
        """Parse JS file discovery results."""
        lines = self._read_lines(file_path)
        return lines, len(lines)

    def parse_sensitive_files(self, file_path: str) -> Tuple[List[str], int]:
        """Parse sensitive file discovery results."""
        lines = self._read_lines(file_path)
        return lines, len(lines)

    def parse_gf_results(
        self, vuln_type: str, file_path: str
    ) -> List[Dict[str, str]]:
        """Parse gf pattern matching results."""
        lines = self._read_lines(file_path)
        results = []
        for line in lines:
            results.append({
                "type": vuln_type,
                "url": line,
                "params": self._extract_params(line),
            })
        return results

    def parse_dalfox_output(self, file_path: str) -> List[Vulnerability]:
        """Parse dalfox XSS scanner output."""
        vulns = []
        lines = self._read_lines(file_path)

        for line in lines:
            # Dalfox outputs in format: [POC][type] url payload
            # Try JSON format first
            try:
                data = json.loads(line)
                vulns.append(Vulnerability(
                    severity="high",
                    vuln_type="XSS",
                    url=data.get("data", data.get("url", line)),
                    tool="dalfox",
                    details=data.get("message", ""),
                    payload=data.get("payload", data.get("data", "")),
                ))
                continue
            except (json.JSONDecodeError, TypeError):
                pass

            # Try text format: [POC][type] url
            if "[POC]" in line or "[V]" in line:
                vulns.append(Vulnerability(
                    severity="high",
                    vuln_type="XSS",
                    url=line,
                    tool="dalfox",
                    details="Reflected XSS found by dalfox",
                    payload=line,
                ))
            elif "Verified" in line.lower() or "vuln" in line.lower():
                vulns.append(Vulnerability(
                    severity="medium",
                    vuln_type="XSS",
                    url=line,
                    tool="dalfox",
                    details="Potential XSS found by dalfox",
                ))

        return vulns

    def parse_sqlmap_output(self, output_dir: str) -> List[Vulnerability]:
        """Parse sqlmap output directory for findings."""
        vulns = []
        if not os.path.exists(output_dir):
            return vulns

        # Walk the sqlmap output directory
        for root, dirs, files in os.walk(output_dir):
            for fname in files:
                fpath = os.path.join(root, fname)
                if fname == "log":
                    try:
                        with open(fpath, "r", errors="ignore") as f:
                            content = f.read()

                        # Extract injection details
                        target_match = re.search(
                            r"Target URL:\s*(.+)", content
                        )
                        url = target_match.group(1).strip() if target_match else root

                        if "is vulnerable" in content.lower() or "injectable" in content.lower():
                            # Extract parameter info
                            param_matches = re.findall(
                                r"Parameter:\s*(.+?)(?:\n|$)", content
                            )
                            dbms_matches = re.findall(
                                r"back-end DBMS:\s*(.+?)(?:\n|$)", content
                            )

                            vulns.append(Vulnerability(
                                severity="critical",
                                vuln_type="SQLi",
                                url=url,
                                tool="sqlmap",
                                details=(
                                    f"SQL Injection found. "
                                    f"Parameters: {', '.join(param_matches)}. "
                                    f"DBMS: {', '.join(dbms_matches)}"
                                ),
                            ))
                    except Exception:
                        continue

        return vulns

    def parse_dirsearch_output(self, file_path: str) -> List[Dict]:
        """Parse dirsearch directory bruteforce results."""
        results = []
        lines = self._read_lines(file_path)

        for line in lines:
            # dirsearch plain format: STATUS_CODE  SIZE  URL
            parts = line.split()
            if len(parts) >= 2:
                try:
                    status_code = int(parts[0])
                    url = parts[-1]
                    size = parts[1] if len(parts) >= 3 else "0"
                    results.append({
                        "status_code": status_code,
                        "url": url,
                        "size": size,
                    })
                except (ValueError, IndexError):
                    # Not in expected format, store raw
                    results.append({
                        "status_code": 0,
                        "url": line,
                        "size": "0",
                    })

        return results

    def parse_generic_scanner_output(
        self, file_path: str, vuln_type: str, tool: str, severity: str = "medium"
    ) -> List[Vulnerability]:
        """Generic parser for tools that output one finding per line."""
        vulns = []
        lines = self._read_lines(file_path)

        for line in lines:
            if line and not line.startswith("#"):
                vulns.append(Vulnerability(
                    severity=severity,
                    vuln_type=vuln_type,
                    url=line,
                    tool=tool,
                    details=f"{vuln_type} finding detected by {tool}",
                ))

        return vulns

    @staticmethod
    def _extract_params(url: str) -> str:
        """Extract query parameters from a URL."""
        if "?" not in url:
            return ""
        try:
            query = url.split("?", 1)[1]
            params = [p.split("=")[0] for p in query.split("&")]
            return ", ".join(params)
        except Exception:
            return ""

    @staticmethod
    def export_json(summary: ScanSummary, output_path: str):
        """Export scan results to JSON file."""
        with open(output_path, "w") as f:
            json.dump(summary.to_dict(), f, indent=2)

    @staticmethod
    def export_csv(vulnerabilities: List[Vulnerability], output_path: str):
        """Export vulnerabilities to CSV file."""
        import csv
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Severity", "Type", "URL", "Tool", "Details", "Payload", "Timestamp"
            ])
            for v in vulnerabilities:
                writer.writerow([
                    v.severity, v.vuln_type, v.url,
                    v.tool, v.details, v.payload, v.timestamp,
                ])
