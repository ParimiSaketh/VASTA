"""
VASTA Tool Manager
==================
Detects and auto-installs all 18+ external security tools.
Supports macOS, Linux, and Windows with appropriate install commands.
"""

import os
import platform
import shutil
from typing import Dict, Optional, Callable, List
from dataclasses import dataclass

from core.command_runner import CommandRunner


@dataclass
class ToolInfo:
    """Information about a security tool."""
    name: str
    description: str
    category: str  # "go", "python", "git"
    check_cmd: str  # Command to check if installed
    install_cmds: Dict[str, str]  # OS -> install command
    git_url: Optional[str] = None  # For git-cloned tools


class ToolManager:
    """Manages detection and installation of security tools."""

    TOOL_REGISTRY: Dict[str, ToolInfo] = {
        # ── Go Tools ──────────────────────────────────────────────
        "subfinder": ToolInfo(
            name="subfinder",
            description="Fast passive subdomain enumeration",
            category="go",
            check_cmd="subfinder -version",
            install_cmds={
                "darwin": "go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
                "linux": "go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
                "windows": "go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
            },
        ),
        "assetfinder": ToolInfo(
            name="assetfinder",
            description="Find domains and subdomains via various sources",
            category="go",
            check_cmd="assetfinder -h",
            install_cmds={
                "darwin": "go install -v github.com/tomnomnom/assetfinder@latest",
                "linux": "go install -v github.com/tomnomnom/assetfinder@latest",
                "windows": "go install -v github.com/tomnomnom/assetfinder@latest",
            },
        ),
        "httpx": ToolInfo(
            name="httpx",
            description="Fast HTTP probing toolkit",
            category="go",
            check_cmd="httpx -version || httpx-toolkit -version",
            install_cmds={
                "darwin": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
                "linux": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
                "windows": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
            },
        ),
        "katana": ToolInfo(
            name="katana",
            description="Web crawler for endpoint discovery",
            category="go",
            check_cmd="katana -version",
            install_cmds={
                "darwin": "go install -v github.com/projectdiscovery/katana/cmd/katana@latest",
                "linux": "go install -v github.com/projectdiscovery/katana/cmd/katana@latest",
                "windows": "go install -v github.com/projectdiscovery/katana/cmd/katana@latest",
            },
        ),
        "waybackurls": ToolInfo(
            name="waybackurls",
            description="Fetch URLs from the Wayback Machine",
            category="go",
            check_cmd="which waybackurls",
            install_cmds={
                "darwin": "go install -v github.com/tomnomnom/waybackurls@latest",
                "linux": "go install -v github.com/tomnomnom/waybackurls@latest",
                "windows": "go install -v github.com/tomnomnom/waybackurls@latest",
            },
        ),
        "gf": ToolInfo(
            name="gf",
            description="Pattern-based URL filter (grep for pentesters)",
            category="go",
            check_cmd="which gf",
            install_cmds={
                "darwin": (
                    "go install -v github.com/tomnomnom/gf@latest && "
                    "mkdir -p ~/.gf && "
                    "git clone https://github.com/1ndianl33t/Gf-Patterns.git /tmp/gf-patterns 2>/dev/null; "
                    "cp /tmp/gf-patterns/*.json ~/.gf/ 2>/dev/null; true"
                ),
                "linux": (
                    "go install -v github.com/tomnomnom/gf@latest && "
                    "mkdir -p ~/.gf && "
                    "git clone https://github.com/1ndianl33t/Gf-Patterns.git /tmp/gf-patterns 2>/dev/null; "
                    "cp /tmp/gf-patterns/*.json ~/.gf/ 2>/dev/null; true"
                ),
                "windows": "go install -v github.com/tomnomnom/gf@latest",
            },
        ),
        "dalfox": ToolInfo(
            name="dalfox",
            description="XSS vulnerability scanner",
            category="go",
            check_cmd="dalfox version",
            install_cmds={
                "darwin": "go install -v github.com/hahwul/dalfox/v2@latest",
                "linux": "go install -v github.com/hahwul/dalfox/v2@latest",
                "windows": "go install -v github.com/hahwul/dalfox/v2@latest",
            },
        ),
        "headi": ToolInfo(
            name="headi",
            description="HTTP header injection checker",
            category="go",
            check_cmd="which headi",
            install_cmds={
                "darwin": "go install -v github.com/mlcsec/headi@latest",
                "linux": "go install -v github.com/mlcsec/headi@latest",
                "windows": "go install -v github.com/mlcsec/headi@latest",
            },
        ),
        "toxicache": ToolInfo(
            name="toxicache",
            description="Web cache poisoning scanner",
            category="go",
            check_cmd="which toxicache",
            install_cmds={
                "darwin": "go install -v github.com/xhzeem/toxicache@latest",
                "linux": "go install -v github.com/xhzeem/toxicache@latest",
                "windows": "go install -v github.com/xhzeem/toxicache@latest",
            },
        ),
        # ── Python Tools ──────────────────────────────────────────
        "sqlmap": ToolInfo(
            name="sqlmap",
            description="Automatic SQL injection exploitation tool",
            category="python",
            check_cmd="sqlmap --version",
            install_cmds={
                "darwin": "pip3 install sqlmap",
                "linux": "pip3 install sqlmap",
                "windows": "pip install sqlmap",
            },
        ),
        "dirsearch": ToolInfo(
            name="dirsearch",
            description="Directory and file bruteforcer",
            category="python",
            check_cmd="dirsearch --version",
            install_cmds={
                "darwin": "pip3 install dirsearch",
                "linux": "pip3 install dirsearch",
                "windows": "pip install dirsearch",
            },
        ),
        # ── Git-cloned Tools ─────────────────────────────────────
        "LFI-FINDER": ToolInfo(
            name="LFI-FINDER",
            description="Local File Inclusion vulnerability scanner",
            category="git",
            check_cmd="",  # Check by directory existence
            install_cmds={},
            git_url="https://github.com/capture0x/LFI-FINDER.git",
        ),
        "OpenRedireX": ToolInfo(
            name="OpenRedireX",
            description="Open redirect vulnerability scanner",
            category="git",
            check_cmd="",
            install_cmds={},
            git_url="https://github.com/devanshbatham/OpenRedireX.git",
        ),
        "http-request-smuggling": ToolInfo(
            name="http-request-smuggling",
            description="HTTP request smuggling detection",
            category="git",
            check_cmd="",
            install_cmds={},
            git_url="https://github.com/anshumanpattnaik/http-request-smuggling.git",
        ),
        "CORStest": ToolInfo(
            name="CORStest",
            description="CORS misconfiguration scanner",
            category="git",
            check_cmd="",
            install_cmds={},
            git_url="https://github.com/RUB-NDS/CORStest.git",
        ),
        "gitGraber": ToolInfo(
            name="gitGraber",
            description="Monitor GitHub for leaked secrets",
            category="git",
            check_cmd="",
            install_cmds={},
            git_url="https://github.com/hisxo/gitGraber.git",
        ),
        "zip-finder": ToolInfo(
            name="zip-finder",
            description="Find exposed archive files",
            category="git",
            check_cmd="",
            install_cmds={},
            git_url="https://github.com/MuhammadWaseem29/zip-finder.git",
        ),
        "4-ZERO-3": ToolInfo(
            name="4-ZERO-3",
            description="403 bypass tool for hidden path discovery",
            category="git",
            check_cmd="",
            install_cmds={},
            git_url="https://github.com/Dheerajmadhukar/4-ZERO-3.git",
        ),
    }

    def __init__(self, project_dir: Optional[str] = None):
        self._runner = CommandRunner()
        self._system = platform.system().lower()
        if self._system not in ("darwin", "linux", "windows"):
            self._system = "linux"  # Default fallback
        self.project_dir = project_dir or os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        self.tools_dir = os.path.join(self.project_dir, "tools")

    def get_tools_dir(self) -> str:
        """Return the directory where git-cloned tools are stored."""
        os.makedirs(self.tools_dir, exist_ok=True)
        return self.tools_dir

    def get_tool_path(self, name: str) -> str:
        """Get the full path to a tool's executable or directory."""
        tool = self.TOOL_REGISTRY.get(name)
        if not tool:
            return name

        if tool.category == "git":
            return os.path.join(self.tools_dir, name)
        elif tool.category == "go":
            go_path = os.path.expanduser("~/go/bin")
            tool_path = os.path.join(go_path, name)
            if os.path.exists(tool_path):
                return tool_path
            # Fallback to which
            result = shutil.which(name)
            return result if result else name
        else:
            result = shutil.which(name)
            return result if result else name

    def check_go_installed(self) -> bool:
        """Check if Go runtime is installed."""
        _, _, rc = self._runner.run_sync("go version")
        return rc == 0

    def install_go(self, on_output: Optional[Callable] = None) -> bool:
        """Attempt to install Go runtime."""
        if on_output:
            on_output("[*] Attempting to install Go...")

        if self._system == "darwin":
            cmd = "brew install go"
        elif self._system == "linux":
            cmd = (
                "wget -q https://go.dev/dl/go1.22.0.linux-amd64.tar.gz -O /tmp/go.tar.gz && "
                "sudo tar -C /usr/local -xzf /tmp/go.tar.gz && "
                "echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> ~/.bashrc"
            )
        else:
            if on_output:
                on_output("[!] Please install Go manually from https://go.dev/dl/")
            return False

        rc = self._runner.run(cmd, on_output=on_output)
        return rc == 0

    def check_tool(self, name: str) -> bool:
        """Check if a specific tool is installed."""
        tool = self.TOOL_REGISTRY.get(name)
        if not tool:
            return False

        if tool.category == "git":
            # Check if the tool directory exists
            tool_dir = os.path.join(self.tools_dir, name)
            return os.path.isdir(tool_dir) and len(os.listdir(tool_dir)) > 0
        else:
            # Try to run the check command
            if not tool.check_cmd:
                return False
            _, _, rc = self._runner.run_sync(tool.check_cmd, timeout=10)
            return rc == 0

    def check_all_tools(self) -> Dict[str, Dict]:
        """
        Check installation status of all tools.
        
        Returns:
            Dict of tool_name -> {"installed": bool, "category": str, "description": str}
        """
        results = {}
        for name, tool in self.TOOL_REGISTRY.items():
            installed = self.check_tool(name)
            results[name] = {
                "installed": installed,
                "category": tool.category,
                "description": tool.description,
            }
        return results

    def install_tool(
        self,
        name: str,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """
        Install a specific tool.

        Args:
            name: Tool name from registry.
            on_output: Callback for installation output.

        Returns:
            True if installation succeeded.
        """
        tool = self.TOOL_REGISTRY.get(name)
        if not tool:
            if on_output:
                on_output(f"[!] Unknown tool: {name}")
            return False

        if on_output:
            on_output(f"\n[*] Installing {name}...")

        if tool.category == "git":
            return self._install_git_tool(tool, on_output)
        elif tool.category == "go":
            # Ensure Go is installed first
            if not self.check_go_installed():
                if on_output:
                    on_output("[!] Go is not installed. Installing Go first...")
                if not self.install_go(on_output):
                    if on_output:
                        on_output("[✗] Failed to install Go. Cannot install Go-based tools.")
                    return False

            cmd = tool.install_cmds.get(self._system, "")
            if not cmd:
                if on_output:
                    on_output(f"[!] No install command for {self._system}")
                return False

            rc = self._runner.run(cmd, on_output=on_output)
            success = rc == 0
            if on_output:
                status = "✓" if success else "✗"
                on_output(f"[{status}] {name} installation {'succeeded' if success else 'failed'}")
            return success
        else:
            # Python tools
            cmd = tool.install_cmds.get(self._system, "")
            if not cmd:
                if on_output:
                    on_output(f"[!] No install command for {self._system}")
                return False

            rc = self._runner.run(cmd, on_output=on_output)
            success = rc == 0
            if on_output:
                status = "✓" if success else "✗"
                on_output(f"[{status}] {name} installation {'succeeded' if success else 'failed'}")
            return success

    def _install_git_tool(
        self, tool: ToolInfo, on_output: Optional[Callable] = None
    ) -> bool:
        """Install a git-cloned tool."""
        if not tool.git_url:
            return False

        tools_dir = self.get_tools_dir()
        tool_dir = os.path.join(tools_dir, tool.name)

        if os.path.isdir(tool_dir):
            if on_output:
                on_output(f"[*] {tool.name} directory exists, pulling latest...")
            cmd = f"cd {tool_dir} && git pull"
        else:
            cmd = f"git clone {tool.git_url} {tool_dir}"

        rc = self._runner.run(cmd, on_output=on_output)

        # Install Python requirements if they exist
        req_file = os.path.join(tool_dir, "requirements.txt")
        if os.path.exists(req_file):
            if on_output:
                on_output(f"[*] Installing {tool.name} Python dependencies...")
            pip_cmd = f"pip3 install -r {req_file}"
            self._runner.run(pip_cmd, on_output=on_output)

        success = rc == 0 and os.path.isdir(tool_dir)
        if on_output:
            status = "✓" if success else "✗"
            on_output(f"[{status}] {tool.name} {'installed' if success else 'failed'}")
        return success

    def install_all_missing(
        self,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, bool]:
        """
        Install all missing tools.

        Returns:
            Dict of tool_name -> success boolean.
        """
        results = {}
        statuses = self.check_all_tools()

        missing = [name for name, info in statuses.items() if not info["installed"]]

        if not missing:
            if on_output:
                on_output("[✓] All tools are already installed!")
            return results

        if on_output:
            on_output(f"\n[*] Found {len(missing)} missing tools. Starting installation...")

        # Install Go tools first (they need Go runtime)
        go_tools = [n for n in missing if self.TOOL_REGISTRY[n].category == "go"]
        python_tools = [n for n in missing if self.TOOL_REGISTRY[n].category == "python"]
        git_tools = [n for n in missing if self.TOOL_REGISTRY[n].category == "git"]

        if go_tools and not self.check_go_installed():
            if on_output:
                on_output("\n[*] Go runtime not found. Installing Go first...")
            if not self.install_go(on_output):
                if on_output:
                    on_output("[✗] Failed to install Go. Skipping Go-based tools.")
                for name in go_tools:
                    results[name] = False
                go_tools = []

        for name in go_tools + python_tools + git_tools:
            results[name] = self.install_tool(name, on_output)

        if on_output:
            installed = sum(1 for v in results.values() if v)
            on_output(
                f"\n[*] Installation complete: {installed}/{len(results)} tools installed successfully"
            )

        return results

    def get_all_tool_names(self) -> List[str]:
        """Return list of all registered tool names."""
        return list(self.TOOL_REGISTRY.keys())

    def get_tools_by_category(self) -> Dict[str, List[str]]:
        """Return tools grouped by category."""
        categories: Dict[str, List[str]] = {}
        for name, tool in self.TOOL_REGISTRY.items():
            cat = tool.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(name)
        return categories
