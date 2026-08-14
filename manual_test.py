"""
VASTA Manual Test Dialog
=========================
Lets users run individual security tools against a specific target URL.
Shows all 8 scanning tools with descriptions, accepts a target, and streams
output to the main terminal.
"""

import customtkinter as ctk
import threading
import shutil
from typing import Optional, Callable

from gui.theme import Colors, Fonts, Dimensions
from core.command_runner import CommandRunner


# ── Tool Definitions ──────────────────────────────────────────────────

MANUAL_TOOLS = [
    {
        "name": "dalfox",
        "display": "DalFox",
        "icon": "🦊",
        "description": "XSS (Cross-Site Scripting) scanner",
        "severity": "HIGH",
        "category": "XSS",
        "url": "https://github.com/hahwul/dalfox",
        "cmd": "dalfox url {target} --silence",
        "needs_url": True,
    },
    {
        "name": "sqlmap",
        "display": "SQLMap",
        "icon": "💉",
        "description": "SQL Injection detection & exploitation",
        "severity": "CRITICAL",
        "category": "SQLi",
        "url": "https://github.com/sqlmapproject/sqlmap",
        "cmd": "sqlmap -u \"{target}\" --batch --random-agent --level 1 --risk 1",
        "needs_url": True,
    },
    {
        "name": "python3",
        "display": "LFI-FINDER",
        "icon": "📂",
        "description": "Local File Inclusion vulnerability scanner",
        "severity": "HIGH",
        "category": "LFI",
        "url": "https://github.com/capture0x/LFI-FINDER",
        "cmd": "python3 ~/LFI-FINDER/lfi_finder.py -u \"{target}\"",
        "check_name": "LFI-FINDER",
        "needs_url": True,
    },
    {
        "name": "python3",
        "display": "OpenRedireX",
        "icon": "🔀",
        "description": "Open Redirect vulnerability scanner",
        "severity": "MEDIUM",
        "category": "Redirect",
        "url": "https://github.com/devanshbatham/OpenRedireX",
        "cmd": "echo \"{target}\" | python3 ~/OpenRedireX/openredirex.py",
        "check_name": "OpenRedireX",
        "needs_url": True,
    },
    {
        "name": "python3",
        "display": "HTTP-Smuggling",
        "icon": "📦",
        "description": "HTTP Request Smuggling detector",
        "severity": "HIGH",
        "category": "Smuggling",
        "url": "https://github.com/anshumanpattnaik/http-request-smuggling",
        "cmd": "python3 ~/http-request-smuggling/smuggler.py -u \"{target}\"",
        "check_name": "http-request-smuggling",
        "needs_url": True,
    },
    {
        "name": "headi",
        "display": "Headi",
        "icon": "🎯",
        "description": "Header injection vulnerability checker",
        "severity": "MEDIUM",
        "category": "Header Injection",
        "url": "https://github.com/mlcsec/headi",
        "cmd": "headi -u \"{target}\"",
        "needs_url": True,
    },
    {
        "name": "python3",
        "display": "CORStest",
        "icon": "🌐",
        "description": "CORS misconfiguration scanner",
        "severity": "MEDIUM",
        "category": "CORS",
        "url": "https://github.com/RUB-NDS/CORStest",
        "cmd": "python3 ~/CORStest/corstest.py \"{target}\"",
        "check_name": "CORStest",
        "needs_url": True,
    },
    {
        "name": "python3",
        "display": "Toxicache",
        "icon": "☠️",
        "description": "Web cache poisoning vulnerability scanner",
        "severity": "HIGH",
        "category": "Cache Poisoning",
        "url": "https://github.com/xhzeem/toxicache",
        "cmd": "python3 ~/toxicache/toxicache.py -u \"{target}\"",
        "check_name": "toxicache",
        "needs_url": True,
    },
]


# ── Severity Colors ───────────────────────────────────────────────────

SEVERITY_COLORS = {
    "CRITICAL": "#FF1744",
    "HIGH": "#FF6D00",
    "MEDIUM": "#FFD600",
}


class ManualTestDialog(ctk.CTkToplevel):
    """Dialog for running individual security tools against a target."""

    def __init__(self, master, on_output: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(master, **kwargs)

        self._on_output = on_output
        self._runner: Optional[CommandRunner] = None
        self._selected_tool: Optional[dict] = None
        self._tool_cards = []

        # Fix macOS blank CTkToplevel
        self.withdraw()

        self.title("VASTA — Manual Tool Testing")
        self.geometry("750x700")
        self.resizable(True, True)
        self.minsize(650, 550)
        self.configure(fg_color=Colors.BG_DARKEST)

        self._build_ui()

        # Show after building
        self.after(100, self.deiconify)
        self.after(150, self.focus_force)
        self.after(200, self.grab_set)

    def _build_ui(self):
        font_family = Fonts.get_family()

        # ── Header ────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=Colors.PRIMARY, corner_radius=0, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="🔧  Manual Tool Testing",
            font=(font_family, 22, "bold"),
            text_color=Colors.TEXT_BRIGHT,
        ).pack(side="left", padx=Dimensions.PAD_LARGE, pady=Dimensions.PAD_MEDIUM)

        ctk.CTkLabel(
            header,
            text="Select a tool and provide a target URL",
            font=(font_family, Fonts.SIZE_SMALL),
            text_color="#FFFFFFCC",
        ).pack(side="right", padx=Dimensions.PAD_LARGE)

        # ── Target Input Area ─────────────────────────────────────
        target_frame = ctk.CTkFrame(self, fg_color=Colors.BG_DARK, corner_radius=0)
        target_frame.pack(fill="x", padx=0, pady=0)

        inner_target = ctk.CTkFrame(target_frame, fg_color="transparent")
        inner_target.pack(fill="x", padx=Dimensions.PAD_LARGE, pady=Dimensions.PAD_MEDIUM)
        inner_target.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            inner_target,
            text="🎯 Target URL:",
            font=(font_family, Fonts.SIZE_BODY, "bold"),
            text_color=Colors.TEXT_SECONDARY,
        ).grid(row=0, column=0, padx=(0, Dimensions.PAD_SMALL))

        self._target_entry = ctk.CTkEntry(
            inner_target,
            placeholder_text="e.g., http://testfire.net/search.jsp?query=test",
            height=40,
            font=(font_family, Fonts.SIZE_BODY),
            fg_color=Colors.BG_LIGHT,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_MUTED,
            corner_radius=Dimensions.RADIUS_MEDIUM,
            border_width=1,
        )
        self._target_entry.grid(row=0, column=1, sticky="ew", padx=(0, Dimensions.PAD_SMALL))

        self._run_btn = ctk.CTkButton(
            inner_target,
            text="▶  Run Tool",
            font=(font_family, Fonts.SIZE_BODY, "bold"),
            fg_color=Colors.SUCCESS,
            hover_color=Colors.SUCCESS_DARK,
            text_color=Colors.TEXT_BRIGHT,
            height=40,
            width=120,
            corner_radius=Dimensions.RADIUS_MEDIUM,
            command=self._run_selected_tool,
            state="disabled",
        )
        self._run_btn.grid(row=0, column=2, padx=(0, Dimensions.PAD_TINY))

        self._stop_btn = ctk.CTkButton(
            inner_target,
            text="■  Stop",
            font=(font_family, Fonts.SIZE_BODY),
            fg_color=Colors.ERROR,
            hover_color=Colors.ERROR_DARK,
            text_color=Colors.TEXT_BRIGHT,
            height=40,
            width=80,
            corner_radius=Dimensions.RADIUS_MEDIUM,
            command=self._stop_tool,
            state="disabled",
        )
        self._stop_btn.grid(row=0, column=3)

        # Selected tool indicator
        self._selected_label = ctk.CTkLabel(
            target_frame,
            text="  ← Select a tool below to get started",
            font=(font_family, Fonts.SIZE_SMALL),
            text_color=Colors.TEXT_MUTED,
        )
        self._selected_label.pack(padx=Dimensions.PAD_LARGE, pady=(0, Dimensions.PAD_SMALL), anchor="w")

        # ── Tool Grid (scrollable) ────────────────────────────────
        tools_header = ctk.CTkFrame(self, fg_color="transparent")
        tools_header.pack(fill="x", padx=Dimensions.PAD_LARGE, pady=(Dimensions.PAD_MEDIUM, Dimensions.PAD_TINY))

        ctk.CTkLabel(
            tools_header,
            text="AVAILABLE TOOLS",
            font=(font_family, Fonts.SIZE_SMALL, "bold"),
            text_color=Colors.TEXT_MUTED,
        ).pack(side="left")

        ctk.CTkLabel(
            tools_header,
            text=f"{len(MANUAL_TOOLS)} tools",
            font=(font_family, Fonts.SIZE_TINY),
            text_color=Colors.TEXT_MUTED,
        ).pack(side="right")

        # Scrollable tool cards container
        self._tools_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=Colors.BG_LIGHT,
            scrollbar_button_hover_color=Colors.PRIMARY,
        )
        self._tools_scroll.pack(fill="both", expand=True, padx=Dimensions.PAD_MEDIUM, pady=(0, Dimensions.PAD_MEDIUM))
        self._tools_scroll.grid_columnconfigure(0, weight=1)
        self._tools_scroll.grid_columnconfigure(1, weight=1)

        # Create tool cards in a 2-column grid
        for idx, tool in enumerate(MANUAL_TOOLS):
            card = self._create_tool_card(self._tools_scroll, tool, idx)
            row = idx // 2
            col = idx % 2
            card.grid(row=row, column=col, padx=Dimensions.PAD_TINY, pady=Dimensions.PAD_TINY, sticky="nsew")
            self._tool_cards.append(card)

    def _create_tool_card(self, parent, tool: dict, index: int) -> ctk.CTkFrame:
        """Create a clickable tool card."""
        font_family = Fonts.get_family()
        severity_color = SEVERITY_COLORS.get(tool["severity"], Colors.TEXT_MUTED)

        card = ctk.CTkFrame(
            parent,
            fg_color=Colors.BG_DARK,
            corner_radius=Dimensions.RADIUS_MEDIUM,
            border_width=1,
            border_color=Colors.BORDER,
            cursor="hand2",
        )
        card.grid_columnconfigure(1, weight=1)

        # Tool icon
        icon_label = ctk.CTkLabel(
            card,
            text=tool["icon"],
            font=(font_family, 28),
            width=45,
        )
        icon_label.grid(row=0, column=0, rowspan=2, padx=(Dimensions.PAD_SMALL, Dimensions.PAD_TINY), pady=Dimensions.PAD_SMALL)

        # Tool name
        name_label = ctk.CTkLabel(
            card,
            text=tool["display"],
            font=(font_family, Fonts.SIZE_BODY, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        name_label.grid(row=0, column=1, sticky="w", padx=(0, Dimensions.PAD_SMALL), pady=(Dimensions.PAD_SMALL, 0))

        # Description
        desc_label = ctk.CTkLabel(
            card,
            text=tool["description"],
            font=(font_family, Fonts.SIZE_TINY),
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        desc_label.grid(row=1, column=1, sticky="w", padx=(0, Dimensions.PAD_SMALL), pady=(0, Dimensions.PAD_SMALL))

        # Severity badge
        badge = ctk.CTkLabel(
            card,
            text=tool["severity"],
            font=(font_family, 9, "bold"),
            text_color=severity_color,
            fg_color=Colors.BG_DARKEST,
            corner_radius=4,
            width=55,
            height=20,
        )
        badge.grid(row=0, column=2, padx=Dimensions.PAD_SMALL, pady=(Dimensions.PAD_SMALL, 0), sticky="ne")

        # Bind click to all widgets in the card
        def _select(event=None, t=tool, c=card):
            self._select_tool(t, c)

        for widget in [card, icon_label, name_label, desc_label, badge]:
            widget.bind("<Button-1>", _select)

        # Hover effect
        def _hover_enter(event=None, c=card):
            if self._selected_tool != tool:
                c.configure(border_color=Colors.PRIMARY)

        def _hover_leave(event=None, c=card, t=tool):
            if self._selected_tool != t:
                c.configure(border_color=Colors.BORDER)

        for widget in [card, icon_label, name_label, desc_label, badge]:
            widget.bind("<Enter>", _hover_enter)
            widget.bind("<Leave>", _hover_leave)

        # Store reference
        card._tool_data = tool
        return card

    def _select_tool(self, tool: dict, card: ctk.CTkFrame):
        """Handle tool selection."""
        self._selected_tool = tool

        # Reset all card borders
        for c in self._tool_cards:
            c.configure(border_color=Colors.BORDER, fg_color=Colors.BG_DARK)

        # Highlight selected
        card.configure(border_color=Colors.PRIMARY, fg_color=Colors.PRIMARY_MUTED)

        # Update label and enable run
        severity_color = SEVERITY_COLORS.get(tool["severity"], Colors.TEXT_MUTED)
        self._selected_label.configure(
            text=f"  ✓ Selected: {tool['icon']} {tool['display']} — {tool['description']}",
            text_color=Colors.PRIMARY,
        )
        self._run_btn.configure(state="normal")
        self._target_entry.focus_set()

    def _run_selected_tool(self):
        """Run the selected tool against the target."""
        if not self._selected_tool:
            return

        target = self._target_entry.get().strip()
        if not target:
            self._selected_label.configure(
                text="  ⚠ Please enter a target URL first!",
                text_color=Colors.WARNING,
            )
            return

        tool = self._selected_tool
        cmd = tool["cmd"].format(target=target)

        # Check tool availability
        check_name = tool.get("check_name", tool["name"])
        if tool["name"] != "python3" and not shutil.which(tool["name"]):
            self._emit(f"\n[ERROR] {tool['display']} is not installed!")
            self._emit(f"Install it from: {tool['url']}")
            return

        # Update UI state
        self._run_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._selected_label.configure(
            text=f"  ⏳ Running {tool['display']}...",
            text_color=Colors.WARNING,
        )

        # Emit tool banner to terminal
        self._emit(f"\n{'═' * 55}")
        self._emit(f"  {tool['icon']}  MANUAL TEST: {tool['display'].upper()}")
        self._emit(f"  Category: {tool['category']} | Severity: {tool['severity']}")
        self._emit(f"  Target:   {target}")
        self._emit(f"{'═' * 55}")

        # Run in background thread
        self._runner = CommandRunner()

        def _run():
            rc = self._runner.run(
                cmd,
                on_output=lambda line: self._emit(f"  {line}"),
            )
            # Update UI from main thread
            self.after(0, lambda _rc=rc: self._on_tool_complete(_rc))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def _stop_tool(self):
        """Stop the currently running tool."""
        if self._runner:
            self._runner.cancel()
            self._emit("\n  [■] Tool execution stopped by user")

    def _on_tool_complete(self, return_code: int):
        """Called when tool finishes."""
        self._run_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")

        tool = self._selected_tool
        if return_code == 0:
            self._emit(f"\n  [✓] {tool['display']} completed successfully")
            self._selected_label.configure(
                text=f"  ✓ {tool['display']} completed! Select another tool or re-run.",
                text_color=Colors.SUCCESS,
            )
        else:
            self._emit(f"\n  [✗] {tool['display']} exited with code {return_code}")
            self._selected_label.configure(
                text=f"  ✗ {tool['display']} exited with code {return_code}",
                text_color=Colors.ERROR,
            )

    def _emit(self, text: str):
        """Send output to the main terminal."""
        if self._on_output:
            self._on_output(text)

    def _cancel_all_after(self):
        """Cancel all pending Tcl 'after' events on this window."""
        try:
            after_ids = self.tk.call('after', 'info')
            if after_ids:
                for after_id in self.tk.splitlist(after_ids):
                    try:
                        self.tk.call('after', 'cancel', after_id)
                    except Exception:
                        pass
        except Exception:
            pass

    def destroy(self):
        """Clean up before destroying."""
        if self._runner and self._runner.is_running:
            self._runner.cancel()
        self.grab_release()
        self._cancel_all_after()
        super().destroy()
