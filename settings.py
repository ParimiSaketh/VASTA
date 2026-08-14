"""
VASTA Settings Dialog
======================
Configuration options for scan parameters.
"""

import customtkinter as ctk
from typing import Dict, Optional

from gui.theme import Colors, Fonts, Dimensions, PhaseInfo


DEFAULT_SETTINGS = {
    "httpx_threads": 200,
    "katana_depth": 5,
    "command_timeout": 300,
    "output_dir": "output",
    "enabled_phases": [1, 2, 3, 4, 5, 6, 7],
    "enabled_scanners": [
        "dalfox", "sqlmap", "LFI-FINDER", "OpenRedireX",
        "http-request-smuggling", "headi", "CORStest", "toxicache",
    ],
}


class SettingsDialog(ctk.CTkToplevel):
    """Settings configuration dialog."""

    def __init__(self, master, current_settings: Optional[Dict] = None, **kwargs):
        super().__init__(master, **kwargs)

        # Fix macOS blank CTkToplevel: withdraw during setup
        self.withdraw()

        self.title("VASTA — Settings")
        self.geometry("520x620")
        self.resizable(False, False)
        self.configure(fg_color=Colors.BG_DARKEST)

        self._settings = current_settings or DEFAULT_SETTINGS.copy()
        self._result: Optional[Dict] = None

        self._build_ui()

        self.transient(master)
        self.grab_set()

        # Show the window after all widgets are built
        self.after(50, self._show_window)

    def _show_window(self):
        """Reveal the window after setup is complete."""
        try:
            if self.winfo_exists():
                self.deiconify()
                self.focus_force()
                self.lift()
        except Exception:
            pass

    def _build_ui(self):
        font_family = Fonts.get_family()

        # ── Header ──────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=Colors.BG_DARK, height=50, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="⚙ Scan Settings",
            font=(font_family, Fonts.SIZE_HEADING, "bold"),
            text_color=Colors.PRIMARY,
        )
        title.pack(side="left", padx=Dimensions.PAD_LARGE, expand=False)

        # ── Scrollable content ──────────────────────────────────
        content = ctk.CTkScrollableFrame(self, fg_color=Colors.BG_DARKEST, corner_radius=0)
        content.pack(fill="both", expand=True, padx=Dimensions.PAD_MEDIUM, pady=Dimensions.PAD_SMALL)

        # ── Performance Settings ────────────────────────────────
        self._add_section(content, "Performance")

        self._threads_entry = self._add_number_field(
            content, "httpx Threads:", self._settings["httpx_threads"], "Number of concurrent threads for HTTP probing"
        )
        self._depth_entry = self._add_number_field(
            content, "Katana Crawl Depth:", self._settings["katana_depth"], "Maximum crawl depth for endpoint discovery"
        )
        self._timeout_entry = self._add_number_field(
            content, "Command Timeout (s):", self._settings["command_timeout"], "Maximum seconds per command"
        )

        # ── Output Settings ─────────────────────────────────────
        self._add_section(content, "Output")

        self._output_entry = self._add_text_field(
            content, "Output Directory:", self._settings["output_dir"]
        )

        # ── Phase Toggles ───────────────────────────────────────
        self._add_section(content, "Phases")

        self._phase_vars = {}
        for phase in PhaseInfo.PHASES:
            var = ctk.BooleanVar(value=phase["id"] in self._settings["enabled_phases"])
            cb = ctk.CTkCheckBox(
                content,
                text=f"Phase {phase['id']}: {phase['name']}",
                font=(font_family, Fonts.SIZE_SMALL),
                text_color=Colors.TEXT_SECONDARY,
                fg_color=Colors.PRIMARY,
                hover_color=Colors.PRIMARY_DARK,
                variable=var,
            )
            cb.pack(fill="x", padx=Dimensions.PAD_SMALL, pady=2)
            self._phase_vars[phase["id"]] = var

        # ── Scanner Toggles ─────────────────────────────────────
        self._add_section(content, "Active Scanners (Phase 7)")

        scanner_names = [
            ("dalfox", "XSS Scanner"),
            ("sqlmap", "SQL Injection"),
            ("LFI-FINDER", "Local File Inclusion"),
            ("OpenRedireX", "Open Redirect"),
            ("http-request-smuggling", "Request Smuggling"),
            ("headi", "Header Injection"),
            ("CORStest", "CORS Testing"),
            ("toxicache", "Cache Poisoning"),
        ]

        self._scanner_vars = {}
        for scanner_id, scanner_name in scanner_names:
            var = ctk.BooleanVar(value=scanner_id in self._settings["enabled_scanners"])
            cb = ctk.CTkCheckBox(
                content,
                text=f"{scanner_id} — {scanner_name}",
                font=(font_family, Fonts.SIZE_SMALL),
                text_color=Colors.TEXT_SECONDARY,
                fg_color=Colors.SECONDARY,
                hover_color=Colors.SECONDARY_DARK,
                variable=var,
            )
            cb.pack(fill="x", padx=Dimensions.PAD_SMALL, pady=2)
            self._scanner_vars[scanner_id] = var

        # ── Buttons ─────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent", height=50)
        btn_frame.pack(fill="x", padx=Dimensions.PAD_MEDIUM, pady=Dimensions.PAD_MEDIUM)

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save Settings",
            font=(font_family, Fonts.SIZE_BODY, "bold"),
            fg_color=Colors.SUCCESS,
            hover_color=Colors.SUCCESS_DARK,
            text_color=Colors.TEXT_BRIGHT,
            height=40,
            corner_radius=Dimensions.RADIUS_MEDIUM,
            command=self._save,
        )
        save_btn.pack(side="left", expand=True, fill="x", padx=(0, Dimensions.PAD_SMALL))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=(font_family, Fonts.SIZE_BODY),
            fg_color=Colors.BG_LIGHT,
            hover_color=Colors.BG_HIGHLIGHT,
            text_color=Colors.TEXT_SECONDARY,
            height=40,
            corner_radius=Dimensions.RADIUS_MEDIUM,
            command=self._cancel,
            width=80,
            border_width=1,
            border_color=Colors.BORDER,
        )
        cancel_btn.pack(side="right")

    def _add_section(self, parent, title: str):
        """Add a section header."""
        font_family = Fonts.get_family()
        sep = ctk.CTkFrame(parent, height=1, fg_color=Colors.BORDER)
        sep.pack(fill="x", pady=(Dimensions.PAD_MEDIUM, Dimensions.PAD_TINY))
        lbl = ctk.CTkLabel(
            parent, text=title.upper(),
            font=(font_family, Fonts.SIZE_TINY, "bold"),
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        lbl.pack(fill="x", padx=Dimensions.PAD_SMALL, pady=(0, Dimensions.PAD_SMALL))

    def _add_number_field(self, parent, label: str, default: int, tooltip: str = "") -> ctk.CTkEntry:
        """Add a labeled number input field."""
        font_family = Fonts.get_family()
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=Dimensions.PAD_SMALL, pady=2)

        lbl = ctk.CTkLabel(
            frame, text=label,
            font=(font_family, Fonts.SIZE_SMALL),
            text_color=Colors.TEXT_SECONDARY,
            width=160, anchor="w",
        )
        lbl.pack(side="left")

        entry = ctk.CTkEntry(
            frame,
            font=(font_family, Fonts.SIZE_SMALL),
            fg_color=Colors.BG_LIGHT,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            height=30, width=100,
            corner_radius=Dimensions.RADIUS_SMALL,
        )
        entry.pack(side="left", padx=Dimensions.PAD_SMALL)
        entry.insert(0, str(default))

        if tooltip:
            tip = ctk.CTkLabel(
                frame, text=tooltip,
                font=(font_family, Fonts.SIZE_TINY),
                text_color=Colors.TEXT_MUTED,
            )
            tip.pack(side="left", padx=Dimensions.PAD_SMALL)

        return entry

    def _add_text_field(self, parent, label: str, default: str) -> ctk.CTkEntry:
        """Add a labeled text input field."""
        font_family = Fonts.get_family()
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=Dimensions.PAD_SMALL, pady=2)

        lbl = ctk.CTkLabel(
            frame, text=label,
            font=(font_family, Fonts.SIZE_SMALL),
            text_color=Colors.TEXT_SECONDARY,
            width=160, anchor="w",
        )
        lbl.pack(side="left")

        entry = ctk.CTkEntry(
            frame,
            font=(font_family, Fonts.SIZE_SMALL),
            fg_color=Colors.BG_LIGHT,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            height=30,
            corner_radius=Dimensions.RADIUS_SMALL,
        )
        entry.pack(side="left", fill="x", expand=True, padx=Dimensions.PAD_SMALL)
        entry.insert(0, default)

        return entry

    def _save(self):
        """Save settings and close."""
        try:
            self._result = {
                "httpx_threads": int(self._threads_entry.get()),
                "katana_depth": int(self._depth_entry.get()),
                "command_timeout": int(self._timeout_entry.get()),
                "output_dir": self._output_entry.get(),
                "enabled_phases": [
                    pid for pid, var in self._phase_vars.items() if var.get()
                ],
                "enabled_scanners": [
                    sid for sid, var in self._scanner_vars.items() if var.get()
                ],
            }
        except ValueError:
            self._result = self._settings
        self.grab_release()
        self.destroy()

    def _cancel(self):
        """Cancel without saving."""
        self._result = None
        self.grab_release()
        self.destroy()

    def get_result(self) -> Optional[Dict]:
        return self._result
