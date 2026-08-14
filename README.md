# 🛡 VASTA — Vulnerability Assessment & Security Testing Automator

A professional bug bounty automation framework with a modern dark-themed GUI that orchestrates 7 scanning phases, auto-installs 18+ security tools, streams real-time terminal output, and presents discovered vulnerabilities in a clean dashboard.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-green)
![License](https://img.shields.io/badge/License-MIT-purple)

---

## 🎓 Academic Context

This repository is the implementation artefact for the **7005SCN Individual Research Project** (MSc Cybersecurity, Coventry University), supervised by **Dr Rochelle Sassman**. It was validated against `testfire.net` and local lab environments (DVWA, Metasploitable).

This repository is shared, per the coursework submission requirements, with the project supervisor, project coordinator, and module leader, and will remain accessible for a minimum of 3 months following thesis submission. No commits will be made to this repository after the submission date.

---

## ✨ Features

- **7-Phase Scanning Pipeline** — Subdomain enumeration → Live host probing → Endpoint discovery → Sensitive file scanning → Directory bruteforce → Vulnerability triage → Active scanning
- **18+ Security Tools** — Auto-detects and installs subfinder, assetfinder, httpx, katana, waybackurls, gf, dalfox, sqlmap, dirsearch, and 9 more
- **Professional Dark GUI** — Modern CustomTkinter interface with animated phase indicators, real-time terminal output, and a vulnerability dashboard
- **Cross-Platform** — Runs on macOS, Linux, and Windows
- **Vulnerability Dashboard** — Color-coded severity badges, filterable results table, and statistical overview
- **Export Results** — JSON and CSV export with full vulnerability details
- **Phase-Wise Execution** — Each phase feeds results into the next; pause/resume/cancel at any time

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Go runtime (for Go-based tools — auto-installed if missing)
- Git (for cloning tool repositories)

### Installation & Launch

```bash
# Clone the repository
git clone <your-repo-url> VASTA
cd VASTA

# Run VASTA (auto-installs Python dependencies)
python3 vasta.py
```

On first launch, VASTA will:
1. Show a legal disclaimer (you must confirm authorization)
2. Check which security tools are installed
3. Offer to auto-install any missing tools
4. Present the main scanning interface

---

## 📋 Scanning Phases

| Phase | Name | Tools | Description |
|-------|------|-------|-------------|
| 1 | Subdomain Enumeration | subfinder, assetfinder | Discover subdomains from multiple sources |
| 2 | Live Host Probing | httpx | Filter alive hosts on ports 80, 443, 8080, 8000, 8888 |
| 3 | Endpoint Discovery | katana, waybackurls | Crawl live hosts + fetch historical URLs |
| 4 | Sensitive File Discovery | grep, gitGraber, zip-finder | Surface JS files and sensitive extensions |
| 5 | Directory Bruteforce | dirsearch | Find hidden paths with 30+ extensions |
| 6 | Vulnerability Triage | gf | Bucket URLs by vuln type (SQLi, XSS, LFI, etc.) |
| 7 | Active Scanning | dalfox, sqlmap, + 6 more | Run targeted scanners per vulnerability class |

### Phase 7 Scanners

| # | Vulnerability | Tool |
|---|--------------|------|
| 1 | XSS | [dalfox](https://github.com/hahwul/dalfox) |
| 2 | SQL Injection | [sqlmap](https://sqlmap.org) |
| 3 | LFI | [LFI-FINDER](https://github.com/capture0x/LFI-FINDER) |
| 4 | Open Redirect | [OpenRedireX](https://github.com/devanshbatham/OpenRedireX) |
| 5 | Request Smuggling | [http-request-smuggling](https://github.com/anshumanpattnaik/http-request-smuggling) |
| 6 | Header Injection | [headi](https://github.com/mlcsec/headi) |
| 7 | CORS | [CORStest](https://github.com/RUB-NDS/CORStest) |
| 8 | Cache Poisoning | [toxicache](https://github.com/xhzeem/toxicache) |

---

## 🏗 Project Structure

```
VASTA/
├── vasta.py                  # Main entry point
├── requirements.txt          # Python dependencies
├── core/
│   ├── command_runner.py     # Async subprocess runner
│   ├── tool_manager.py       # Tool detection & auto-install
│   ├── phase_engine.py       # Phase orchestration
│   └── result_parser.py      # Scan output parser
├── gui/
│   ├── theme.py              # Color palette & styling
│   ├── app.py                # Main application window
│   ├── components/
│   │   ├── header.py         # Top bar with controls
│   │   ├── phase_panel.py    # Phase progress sidebar
│   │   ├── terminal.py       # Real-time terminal output
│   │   ├── results_view.py   # Vulnerability dashboard
│   │   ├── stats_bar.py      # Bottom statistics bar
│   │   └── tool_checker.py   # Tool install dialog
│   └── dialogs/
│       ├── disclaimer.py     # Legal disclaimer
│       └── settings.py       # Settings dialog
├── phases/
│   ├── base_phase.py         # Abstract base class
│   ├── phase1_subdomain.py   # Subdomain enumeration
│   ├── phase2_probing.py     # Live host probing
│   ├── phase3_endpoints.py   # Endpoint discovery
│   ├── phase4_sensitive.py   # Sensitive file discovery
│   ├── phase5_dirbrute.py    # Directory bruteforce
│   ├── phase6_triage.py      # gf pattern triage
│   └── phase7_scanning.py    # Active vulnerability scanning
├── tools/                    # Auto-installed git-cloned tools
└── output/                   # Scan output files
```

---

## ⚙ Configuration

Click the Settings gear icon to configure:
- **Thread count** for httpx (default: 200)
- **Crawl depth** for katana (default: 5)
- **Command timeout** (default: 300s)
- **Toggle phases** on/off individually
- **Toggle scanners** on/off in Phase 7

---

## ⚠ Legal Disclaimer

This tool is for **authorized security testing only**. You must have explicit written permission from the target organization before scanning. Unauthorized access is illegal. The developers are not responsible for misuse.

---

## 📝 License

MIT License — see LICENSE file for details.
