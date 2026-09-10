"""
VASTA Results View
===================
Tabbed vulnerability results dashboard with overview, vulns, subdomains, endpoints.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, List, Dict

from gui.theme import Colors, Fonts, Dimensions, Icons


class StatCard(ctk.CTkFrame):
    """Summary statistic card for the overview tab."""

    def __init__(self, master, icon: str, label: str, value: str = "0", color: str = Colors.PRIMARY, **kwargs):
        super().__init__(master, fg_color=Colors.BG_MEDIUM, corner_radius=Dimensions.RADIUS_LARGE, **kwargs)

        font_family = Fonts.get_family()

        self._icon_label = ctk.CTkLabel(
            self, text=icon, font=(font_family, Fonts.SIZE_TITLE),
        )
        self._icon_label.pack(pady=(Dimensions.PAD_MEDIUM, 0))

        self._value_label = ctk.CTkLabel(
            self, text=value,
            font=(font_family, 28, "bold"),
            text_color=color,
        )
        self._value_label.pack(pady=(Dimensions.PAD_TINY, 0))

        self._name_label = ctk.CTkLabel(
            self, text=label,
            font=(font_family, Fonts.SIZE_SMALL),
            text_color=Colors.TEXT_SECONDARY,
        )
        self._name_label.pack(pady=(0, Dimensions.PAD_MEDIUM))

    def set_value(self, value):
        self._value_label.configure(text=str(value))


class VulnRow(ctk.CTkFrame):
    """Single vulnerability row in the table."""

    SEVERITY_COLORS = {
        "critical": Colors.SEVERITY_CRITICAL,
        "high": Colors.SEVERITY_HIGH,
        "medium": Colors.SEVERITY_MEDIUM,
        "low": Colors.SEVERITY_LOW,
        "info": Colors.SEVERITY_INFO,
    }

    SEVERITY_ICONS = {
        "critical": Icons.CRITICAL,
        "high": Icons.HIGH,
        "medium": Icons.MEDIUM,
        "low": Icons.LOW,
        "info": Icons.INFO_BADGE,
    }

    def __init__(self, master, severity: str, vuln_type: str, url: str, tool: str, details: str = "", **kwargs):
        super().__init__(master, fg_color=Colors.BG_MEDIUM, corner_radius=Dimensions.RADIUS_SMALL, **kwargs)

        font_family = Fonts.get_family()
        sev_color = self.SEVERITY_COLORS.get(severity.lower(), Colors.TEXT_MUTED)
        sev_icon = self.SEVERITY_ICONS.get(severity.lower(), "")

        self.grid_columnconfigure(2, weight=1)

        # Severity badge
        sev_badge = ctk.CTkLabel(
            self,
            text=f"{sev_icon} {severity.upper()}",
            font=(font_family, Fonts.SIZE_TINY, "bold"),
            text_color=sev_color,
            width=90,
            anchor="w",
        )
        sev_badge.grid(row=0, column=0, padx=Dimensions.PAD_SMALL, pady=Dimensions.PAD_SMALL, sticky="w")

        # Vuln type
        type_label = ctk.CTkLabel(
            self,
            text=vuln_type,
            font=(font_family, Fonts.SIZE_SMALL, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            width=100,
            anchor="w",
        )
        type_label.grid(row=0, column=1, padx=Dimensions.PAD_TINY, pady=Dimensions.PAD_SMALL, sticky="w")

        # URL (truncated)
        display_url = url[:80] + "..." if len(url) > 80 else url
        url_label = ctk.CTkLabel(
            self,
            text=display_url,
            font=(Fonts.get_mono_family(), Fonts.SIZE_TINY),
            text_color=Colors.PRIMARY_LIGHT,
            anchor="w",
        )
        url_label.grid(row=0, column=2, padx=Dimensions.PAD_TINY, pady=Dimensions.PAD_SMALL, sticky="ew")

        # Tool
        tool_label = ctk.CTkLabel(
            self,
            text=tool,
            font=(font_family, Fonts.SIZE_TINY),
            text_color=Colors.TEXT_MUTED,
            width=80,
            anchor="e",
        )
        tool_label.grid(row=0, column=3, padx=Dimensions.PAD_SMALL, pady=Dimensions.PAD_SMALL, sticky="e")

        # Details row (expandable)
        if details:
            details_label = ctk.CTkLabel(
                self,
                text=f"  ↳ {details[:120]}",
                font=(font_family, Fonts.SIZE_TINY),
                text_color=Colors.TEXT_MUTED,
                anchor="w",
            )
            details_label.grid(row=1, column=0, columnspan=4, padx=Dimensions.PAD_MEDIUM, pady=(0, Dimensions.PAD_SMALL), sticky="w")

        # Hover effect
        self.bind("<Enter>", lambda e: self.configure(fg_color=Colors.BG_HIGHLIGHT))
        self.bind("<Leave>", lambda e: self.configure(fg_color=Colors.BG_MEDIUM))


class ScrollableList(ctk.CTkScrollableFrame):
    """Scrollable list for subdomains, endpoints, etc."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=Colors.BG_DARK, corner_radius=0, **kwargs)
        self._items: List[ctk.CTkLabel] = []
        self._font = (Fonts.get_mono_family(), Fonts.SIZE_TINY)

    def add_items(self, items: List[str]):
        """Add items to the list."""
        for item in items:
            label = ctk.CTkLabel(
                self,
                text=item,
                font=self._font,
                text_color=Colors.TEXT_SECONDARY,
                anchor="w",
            )
            label.pack(fill="x", padx=Dimensions.PAD_SMALL, pady=1)
            self._items.append(label)

    def set_items(self, items: List[str]):
        """Replace all items."""
        self.clear()
        self.add_items(items)

    def clear(self):
        """Remove all items."""
        for item in self._items:
            item.destroy()
        self._items.clear()

    def get_count(self) -> int:
        return len(self._items)


class ResultsView(ctk.CTkFrame):
    """Tabbed results dashboard showing scan findings."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=Colors.BG_DARKEST, corner_radius=Dimensions.RADIUS_MEDIUM, **kwargs)
        self._vuln_rows: List[VulnRow] = []
        self._build_ui()

    def _build_ui(self):
        font_family = Fonts.get_family()

        # ── Tabview ──────────────────────────────────────────────
        self._tabs = ctk.CTkTabview(
            self,
            fg_color=Colors.BG_DARKEST,
            segmented_button_fg_color=Colors.BG_DARK,
            segmented_button_selected_color=Colors.SECONDARY,
            segmented_button_selected_hover_color=Colors.SECONDARY_DARK,
            segmented_button_unselected_color=Colors.BG_DARK,
            segmented_button_unselected_hover_color=Colors.BG_LIGHT,
            text_color=Colors.TEXT_PRIMARY,
            text_color_disabled=Colors.TEXT_MUTED,
            corner_radius=Dimensions.RADIUS_MEDIUM,
        )
        self._tabs.pack(fill="both", expand=True, padx=Dimensions.PAD_TINY, pady=Dimensions.PAD_TINY)

        # Create tabs
        overview_tab = self._tabs.add("📊 Overview")
        vulns_tab = self._tabs.add("🐛 Vulnerabilities")
        subs_tab = self._tabs.add("🌐 Subdomains")
        endpoints_tab = self._tabs.add("🔗 Endpoints")
        sensitive_tab = self._tabs.add("📂 Sensitive Files")

        # ── Overview Tab ─────────────────────────────────────────
        self._build_overview(overview_tab)

        # ── Vulnerabilities Tab ──────────────────────────────────
        self._build_vulns_tab(vulns_tab)

        # ── List Tabs ────────────────────────────────────────────
        self._subdomains_list = ScrollableList(subs_tab)
        self._subdomains_list.pack(fill="both", expand=True)

        self._endpoints_list = ScrollableList(endpoints_tab)
        self._endpoints_list.pack(fill="both", expand=True)

        self._sensitive_list = ScrollableList(sensitive_tab)
        self._sensitive_list.pack(fill="both", expand=True)

    def _build_overview(self, parent):
        """Build the overview statistics tab."""
        font_family = Fonts.get_family()

        # Title
        title = ctk.CTkLabel(
            parent,
            text="Scan Summary",
            font=(font_family, Fonts.SIZE_HEADING, "bold"),
            text_color=Colors.TEXT_PRIMARY,
        )
        title.pack(pady=(Dimensions.PAD_LARGE, Dimensions.PAD_MEDIUM))

        # Stats cards grid
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack(fill="x", padx=Dimensions.PAD_LARGE, pady=Dimensions.PAD_MEDIUM)
        for i in range(6):
            cards_frame.grid_columnconfigure(i, weight=1)

        self._stat_cards = {}

        card_configs = [
            ("subdomains", "🌐", "Subdomains", Colors.PRIMARY),
            ("alive_hosts", "📡", "Alive Hosts", Colors.SUCCESS),
            ("endpoints", "🔗", "Endpoints", Colors.SECONDARY),
            ("js_files", "📜", "JS Files", Colors.WARNING),
            ("sensitive", "🔒", "Sensitive", Colors.ERROR),
            ("vulns", "🐛", "Vulnerabilities", Colors.SEVERITY_CRITICAL),
        ]

        for idx, (key, icon, label, color) in enumerate(card_configs):
            card = StatCard(cards_frame, icon=icon, label=label, color=color)
            card.grid(row=0, column=idx, padx=Dimensions.PAD_SMALL, pady=Dimensions.PAD_SMALL, sticky="nsew")
            self._stat_cards[key] = card

        # Severity breakdown
        sev_frame = ctk.CTkFrame(parent, fg_color=Colors.BG_MEDIUM, corner_radius=Dimensions.RADIUS_LARGE)
        sev_frame.pack(fill="x", padx=Dimensions.PAD_LARGE, pady=Dimensions.PAD_MEDIUM)

        sev_title = ctk.CTkLabel(
            sev_frame,
            text="Severity Breakdown",
            font=(font_family, Fonts.SIZE_BODY, "bold"),
            text_color=Colors.TEXT_PRIMARY,
        )
        sev_title.pack(pady=(Dimensions.PAD_MEDIUM, Dimensions.PAD_SMALL))

        sev_row = ctk.CTkFrame(sev_frame, fg_color="transparent")
        sev_row.pack(fill="x", padx=Dimensions.PAD_LARGE, pady=(0, Dimensions.PAD_MEDIUM))

        self._severity_labels = {}
        for sev, color in [
            ("critical", Colors.SEVERITY_CRITICAL),
            ("high", Colors.SEVERITY_HIGH),
            ("medium", Colors.SEVERITY_MEDIUM),
            ("low", Colors.SEVERITY_LOW),
            ("info", Colors.SEVERITY_INFO),
        ]:
            frame = ctk.CTkFrame(sev_row, fg_color="transparent")
            frame.pack(side="left", expand=True)
            val = ctk.CTkLabel(frame, text="0", font=(font_family, Fonts.SIZE_HEADING, "bold"), text_color=color)
            val.pack()
            lbl = ctk.CTkLabel(frame, text=sev.upper(), font=(font_family, Fonts.SIZE_TINY), text_color=Colors.TEXT_MUTED)
            lbl.pack()
            self._severity_labels[sev] = val

    def _build_vulns_tab(self, parent):
        """Build the vulnerabilities list tab."""
        font_family = Fonts.get_family()

        # Header row
        header = ctk.CTkFrame(parent, fg_color=Colors.BG_DARK, height=30)
        header.pack(fill="x", padx=0, pady=(0, 2))
        header.pack_propagate(False)
        header.grid_columnconfigure(2, weight=1)

        for idx, (text, width) in enumerate([
            ("SEVERITY", 90), ("TYPE", 100), ("URL", 200), ("TOOL", 80),
        ]):
            lbl = ctk.CTkLabel(
                header, text=text,
                font=(font_family, Fonts.SIZE_TINY, "bold"),
                text_color=Colors.TEXT_MUTED,
                width=width,
                anchor="w",
            )
            lbl.grid(row=0, column=idx, padx=Dimensions.PAD_SMALL, sticky="w" if idx != 3 else "e")

        # Scrollable vulnerability list
        self._vulns_scroll = ctk.CTkScrollableFrame(
            parent, fg_color=Colors.BG_DARKEST, corner_radius=0,
        )
        self._vulns_scroll.pack(fill="both", expand=True)

        # Empty state
        self._empty_label = ctk.CTkLabel(
            self._vulns_scroll,
            text="No vulnerabilities found yet.\nStart a scan to discover security issues.",
            font=(font_family, Fonts.SIZE_BODY),
            text_color=Colors.TEXT_MUTED,
            justify="center",
        )
        self._empty_label.pack(pady=Dimensions.PAD_SECTION)

    # ── Public Methods ──────────────────────────────────────────

    def add_vulnerability(self, severity: str, vuln_type: str, url: str, tool: str, details: str = ""):
        """Add a vulnerability to the results."""
        # Remove empty state label
        if self._empty_label and self._empty_label.winfo_exists():
            self._empty_label.destroy()
            self._empty_label = None

        row = VulnRow(
            self._vulns_scroll,
            severity=severity,
            vuln_type=vuln_type,
            url=url,
            tool=tool,
            details=details,
        )
        row.pack(fill="x", padx=Dimensions.PAD_TINY, pady=2)
        self._vuln_rows.append(row)

    def update_stats(self, stats_dict: Dict):
        """Update overview statistics cards."""
        mapping = {
            "subdomains": "subdomains",
            "alive_hosts": "alive_hosts",
            "endpoints": "endpoints",
            "js_files": "js_files",
            "sensitive_files": "sensitive",
            "vulnerabilities": "vulns",
        }
        for key, card_key in mapping.items():
            if key in stats_dict and card_key in self._stat_cards:
                self._stat_cards[card_key].set_value(stats_dict[key])

    def update_severity_counts(self, counts: Dict[str, int]):
        """Update the severity breakdown display."""
        for sev, label in self._severity_labels.items():
            count = counts.get(sev, 0)
            label.configure(text=str(count))

    def add_subdomains(self, subdomain_list: List[str]):
        """Add subdomains to the subdomains tab."""
        self._subdomains_list.add_items(subdomain_list)

    def add_endpoints(self, endpoint_list: List[str]):
        """Add endpoints to the endpoints tab."""
        self._endpoints_list.add_items(endpoint_list)

    def add_sensitive_files(self, files_list: List[str]):
        """Add sensitive files to the sensitive files tab."""
        self._sensitive_list.add_items(files_list)

    def clear(self):
        """Clear all results."""
        for row in self._vuln_rows:
            row.destroy()
        self._vuln_rows.clear()

        self._subdomains_list.clear()
        self._endpoints_list.clear()
        self._sensitive_list.clear()

        for card in self._stat_cards.values():
            card.set_value("0")

        for label in self._severity_labels.values():
            label.configure(text="0")
