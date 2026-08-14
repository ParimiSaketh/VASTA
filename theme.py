"""
VASTA Theme Configuration
=========================
Centralized color palette, fonts, and styling constants for the entire application.
Uses a dark cyberpunk-inspired theme with deep purples and cyan accents.
"""


class Colors:
    """Application color palette."""
    
    # Base backgrounds
    BG_DARKEST = "#0a0a0f"       # Main window background
    BG_DARK = "#12121a"          # Panel backgrounds
    BG_MEDIUM = "#1a1a2e"        # Card backgrounds
    BG_LIGHT = "#242440"         # Input backgrounds, hover states
    BG_HIGHLIGHT = "#2d2d50"     # Selected/active items
    
    # Primary accent — Electric Cyan
    PRIMARY = "#00d4ff"
    PRIMARY_DARK = "#0099cc"
    PRIMARY_LIGHT = "#66e5ff"
    PRIMARY_MUTED = "#1a3a4a"    # For subtle highlights
    
    # Secondary accent — Vivid Purple
    SECONDARY = "#7c3aed"
    SECONDARY_DARK = "#5b21b6"
    SECONDARY_LIGHT = "#a78bfa"
    
    # Gradient endpoints
    GRADIENT_START = "#7c3aed"
    GRADIENT_END = "#00d4ff"
    
    # Text colors
    TEXT_PRIMARY = "#e8e8f0"
    TEXT_SECONDARY = "#9898b0"
    TEXT_MUTED = "#606080"
    TEXT_BRIGHT = "#ffffff"
    
    # Status colors
    SUCCESS = "#10b981"
    SUCCESS_DARK = "#065f46"
    WARNING = "#f59e0b"
    WARNING_DARK = "#78350f"
    ERROR = "#ef4444"
    ERROR_DARK = "#7f1d1d"
    INFO = "#3b82f6"
    INFO_DARK = "#1e3a5f"
    
    # Severity colors (for vulnerabilities)
    SEVERITY_CRITICAL = "#ff1744"
    SEVERITY_HIGH = "#ff6d00"
    SEVERITY_MEDIUM = "#ffd600"
    SEVERITY_LOW = "#00e676"
    SEVERITY_INFO = "#448aff"
    
    # Terminal colors
    TERMINAL_BG = "#0d0d14"
    TERMINAL_TEXT = "#c8c8d8"
    TERMINAL_COMMAND = "#00d4ff"
    TERMINAL_SUCCESS = "#10b981"
    TERMINAL_ERROR = "#ef4444"
    TERMINAL_WARNING = "#f59e0b"
    TERMINAL_PROMPT = "#7c3aed"
    
    # Border / Separator
    BORDER = "#2a2a45"
    BORDER_LIGHT = "#3a3a5a"
    BORDER_ACCENT = "#7c3aed"
    
    # Phase status colors
    PHASE_PENDING = "#606080"
    PHASE_RUNNING = "#00d4ff"
    PHASE_COMPLETE = "#10b981"
    PHASE_ERROR = "#ef4444"
    PHASE_SKIPPED = "#f59e0b"


class Fonts:
    """Font configurations."""
    
    # Font families
    FAMILY_PRIMARY = "Segoe UI"    # Windows
    FAMILY_MAC = "SF Pro Display"  # macOS
    FAMILY_LINUX = "Ubuntu"        # Linux
    FAMILY_MONO = "Cascadia Code"  # Monospace
    FAMILY_MONO_MAC = "SF Mono"
    FAMILY_MONO_LINUX = "Ubuntu Mono"
    FAMILY_FALLBACK = "Helvetica"
    FAMILY_MONO_FALLBACK = "Courier"
    
    # Sizes
    SIZE_TITLE = 24
    SIZE_HEADING = 18
    SIZE_SUBHEADING = 14
    SIZE_BODY = 13
    SIZE_SMALL = 11
    SIZE_TINY = 9
    SIZE_TERMINAL = 12
    
    @classmethod
    def get_family(cls):
        """Get the best available font family for the current OS."""
        import platform
        system = platform.system()
        if system == "Darwin":
            return cls.FAMILY_MAC
        elif system == "Windows":
            return cls.FAMILY_PRIMARY
        else:
            return cls.FAMILY_LINUX
    
    @classmethod
    def get_mono_family(cls):
        """Get the best available monospace font for the current OS."""
        import platform
        system = platform.system()
        if system == "Darwin":
            return cls.FAMILY_MONO_MAC
        elif system == "Windows":
            return cls.FAMILY_MONO
        else:
            return cls.FAMILY_MONO_LINUX


class Dimensions:
    """Layout dimensions and spacing."""
    
    # Window
    WINDOW_MIN_WIDTH = 1200
    WINDOW_MIN_HEIGHT = 750
    WINDOW_DEFAULT_WIDTH = 1400
    WINDOW_DEFAULT_HEIGHT = 850
    
    # Sidebar
    SIDEBAR_WIDTH = 300
    
    # Spacing
    PAD_TINY = 4
    PAD_SMALL = 8
    PAD_MEDIUM = 12
    PAD_LARGE = 16
    PAD_XLARGE = 24
    PAD_SECTION = 32
    
    # Border radius
    RADIUS_SMALL = 4
    RADIUS_MEDIUM = 8
    RADIUS_LARGE = 12
    RADIUS_XLARGE = 16
    
    # Component heights
    HEADER_HEIGHT = 70
    STATS_BAR_HEIGHT = 45
    BUTTON_HEIGHT = 36
    INPUT_HEIGHT = 40
    
    # Terminal
    TERMINAL_MAX_LINES = 5000


class Icons:
    """Unicode icons used throughout the app."""
    
    # Phase status
    PENDING = "○"
    RUNNING = "◉"
    COMPLETE = "✓"
    ERROR = "✗"
    SKIPPED = "⊘"
    
    # Navigation
    ARROW_RIGHT = "→"
    ARROW_DOWN = "↓"
    
    # Actions
    PLAY = "▶"
    PAUSE = "⏸"
    STOP = "■"
    EXPORT = "⤓"
    SETTINGS = "⚙"
    SEARCH = "⌕"
    COPY = "⧉"
    REFRESH = "⟳"
    
    # Categories
    SHIELD = "🛡"
    BUG = "🐛"
    GLOBE = "🌐"
    LOCK = "🔒"
    WARNING = "⚠"
    FIRE = "🔥"
    TARGET = "◎"
    TERMINAL = "❯"
    
    # Severity
    CRITICAL = "🔴"
    HIGH = "🟠"
    MEDIUM = "🟡"
    LOW = "🟢"
    INFO_BADGE = "🔵"


class PhaseInfo:
    """Phase metadata."""
    
    PHASES = [
        {
            "id": 1,
            "name": "Subdomain Enumeration",
            "short": "Subdomains",
            "description": "Discover subdomains using subfinder & assetfinder",
            "icon": "🌐",
            "tools": ["subfinder", "assetfinder"],
        },
        {
            "id": 2,
            "name": "Live Host Probing",
            "short": "Live Hosts",
            "description": "Filter hosts that respond on ports 80, 443, 8080, 8000, 8888",
            "icon": "📡",
            "tools": ["httpx"],
        },
        {
            "id": 3,
            "name": "Endpoint Discovery",
            "short": "Endpoints",
            "description": "Crawl live hosts and pull historical URLs",
            "icon": "🔗",
            "tools": ["katana", "waybackurls"],
        },
        {
            "id": 4,
            "name": "Sensitive File Discovery",
            "short": "Sensitive Files",
            "description": "Surface JS files and exposed sensitive extensions",
            "icon": "📂",
            "tools": ["gitGraber", "zip-finder", "4-ZERO-3"],
        },
        {
            "id": 5,
            "name": "Vulnerability Triage",
            "short": "Vuln Triage",
            "description": "Bucket URLs by likely vuln class using gf patterns",
            "icon": "🔍",
            "tools": ["gf"],
        },
        {
            "id": 6,
            "name": "Directory Bruteforce",
            "short": "Dir Brute",
            "description": "Find hidden files/paths not caught by crawling",
            "icon": "📁",
            "tools": ["dirsearch"],
        },
        {
            "id": 7,
            "name": "Active Scanning",
            "short": "Active Scan",
            "description": "Run targeted scanners against each bucketed list",
            "icon": "🚀",
            "tools": ["dalfox", "sqlmap", "LFI-FINDER", "OpenRedireX",
                      "http-request-smuggling", "headi", "CORStest", "toxicache"],
        },
    ]
