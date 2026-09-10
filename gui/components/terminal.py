"""
VASTA Terminal View
====================
Real-time terminal output with color-coded output and search.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional

from gui.theme import Colors, Fonts, Dimensions, Icons


class TerminalView(ctk.CTkFrame):
    """Terminal-like output display with real-time streaming."""

    MAX_LINES = Dimensions.TERMINAL_MAX_LINES

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=Colors.TERMINAL_BG, corner_radius=Dimensions.RADIUS_MEDIUM, **kwargs)
        self._auto_scroll = True
        self._line_count = 0
        self._build_ui()

    def _build_ui(self):
        font_family = Fonts.get_family()
        mono_family = Fonts.get_mono_family()

        # ── Top toolbar ──────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color=Colors.BG_DARK, height=36, corner_radius=0)
        toolbar.pack(fill="x", padx=0, pady=0)
        toolbar.pack_propagate(False)

        term_label = ctk.CTkLabel(
            toolbar,
            text=f"{Icons.TERMINAL} Live Output",
            font=(font_family, Fonts.SIZE_SMALL, "bold"),
            text_color=Colors.TEXT_SECONDARY,
        )
        term_label.pack(side="left", padx=Dimensions.PAD_MEDIUM)

        # Clear button
        clear_btn = ctk.CTkButton(
            toolbar,
            text="Clear",
            font=(font_family, Fonts.SIZE_TINY),
            fg_color=Colors.BG_LIGHT,
            hover_color=Colors.BG_HIGHLIGHT,
            text_color=Colors.TEXT_MUTED,
            height=24,
            width=50,
            corner_radius=Dimensions.RADIUS_SMALL,
            command=self.clear,
        )
        clear_btn.pack(side="right", padx=Dimensions.PAD_SMALL)

        # Copy button
        copy_btn = ctk.CTkButton(
            toolbar,
            text=f"{Icons.COPY} Copy",
            font=(font_family, Fonts.SIZE_TINY),
            fg_color=Colors.BG_LIGHT,
            hover_color=Colors.BG_HIGHLIGHT,
            text_color=Colors.TEXT_MUTED,
            height=24,
            width=60,
            corner_radius=Dimensions.RADIUS_SMALL,
            command=self._copy_all,
        )
        copy_btn.pack(side="right", padx=(0, Dimensions.PAD_TINY))

        # Search
        self._search_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text=f"{Icons.SEARCH} Search...",
            font=(font_family, Fonts.SIZE_TINY),
            fg_color=Colors.BG_LIGHT,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_MUTED,
            height=24,
            width=160,
            corner_radius=Dimensions.RADIUS_SMALL,
            border_width=1,
        )
        self._search_entry.pack(side="right", padx=Dimensions.PAD_SMALL)
        self._search_entry.bind("<Return>", lambda e: self.search(self._search_entry.get()))

        # Auto-scroll indicator
        self._scroll_label = ctk.CTkLabel(
            toolbar,
            text="↓ Auto-scroll",
            font=(font_family, Fonts.SIZE_TINY),
            text_color=Colors.SUCCESS,
        )
        self._scroll_label.pack(side="right", padx=Dimensions.PAD_SMALL)

        # ── Text area ────────────────────────────────────────────
        self._textbox = tk.Text(
            self,
            bg=Colors.TERMINAL_BG,
            fg=Colors.TERMINAL_TEXT,
            font=(mono_family, Fonts.SIZE_TERMINAL),
            insertbackground=Colors.TERMINAL_BG,  # Hide cursor
            selectbackground=Colors.BG_HIGHLIGHT,
            selectforeground=Colors.TEXT_BRIGHT,
            relief="flat",
            padx=Dimensions.PAD_MEDIUM,
            pady=Dimensions.PAD_SMALL,
            wrap="word",
            state="normal",
            cursor="xterm",
            borderwidth=0,
            highlightthickness=0,
        )
        self._textbox.pack(fill="both", expand=True, padx=Dimensions.PAD_TINY, pady=(0, Dimensions.PAD_TINY))

        # Scrollbar
        scrollbar = ctk.CTkScrollbar(self._textbox, command=self._textbox.yview)
        scrollbar.pack(side="right", fill="y")
        self._textbox.configure(yscrollcommand=scrollbar.set)

        # Configure text tags for colors
        self._textbox.tag_configure("command", foreground=Colors.TERMINAL_COMMAND)
        self._textbox.tag_configure("output", foreground=Colors.TERMINAL_TEXT)
        self._textbox.tag_configure("success", foreground=Colors.TERMINAL_SUCCESS)
        self._textbox.tag_configure("error", foreground=Colors.TERMINAL_ERROR)
        self._textbox.tag_configure("warning", foreground=Colors.TERMINAL_WARNING)
        self._textbox.tag_configure("phase", foreground=Colors.TERMINAL_PROMPT, font=(mono_family, Fonts.SIZE_TERMINAL, "bold"))
        self._textbox.tag_configure("highlight", background=Colors.WARNING, foreground=Colors.BG_DARKEST)
        self._textbox.tag_configure("info", foreground=Colors.INFO)

        # Block all keyboard input EXCEPT copy shortcuts and selection
        def _block_input(event):
            # Allow Ctrl+C (copy), Ctrl+A (select all), arrow keys, and mouse selection
            if event.state & 0x4:  # Ctrl key held
                if event.keysym.lower() in ('c', 'a'):
                    return  # Allow copy and select-all
            # Allow navigation keys
            if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Home', 'End',
                                'Prior', 'Next'):  # Prior=PageUp, Next=PageDown
                return
            return "break"  # Block everything else (typing, pasting, deleting)

        self._textbox.bind("<Key>", _block_input)

        # Right-click context menu for copy
        self._context_menu = tk.Menu(self._textbox, tearoff=0,
                                     bg=Colors.BG_DARK, fg=Colors.TEXT_PRIMARY,
                                     activebackground=Colors.PRIMARY,
                                     activeforeground=Colors.TEXT_BRIGHT)
        self._context_menu.add_command(label="Copy", command=self._copy_selection)
        self._context_menu.add_command(label="Copy All", command=self._copy_all)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="Select All", command=self._select_all)

        self._textbox.bind("<Button-3>", self._show_context_menu)

        # Scroll detection
        self._textbox.bind("<MouseWheel>", self._on_scroll)
        self._textbox.bind("<Button-4>", self._on_scroll)
        self._textbox.bind("<Button-5>", self._on_scroll)

    # ── Public Methods ──────────────────────────────────────────

    def append_output(self, text: str, tag: str = "output"):
        """Append a line of text with the specified color tag."""
        # Auto-detect tag from content
        if tag == "output":
            tag = self._detect_tag(text)

        self._textbox.insert("end", text + "\n", tag)
        self._line_count += 1

        # Trim if over limit
        if self._line_count > self.MAX_LINES:
            trim = self._line_count - self.MAX_LINES
            self._textbox.delete("1.0", f"{trim + 1}.0")
            self._line_count = self.MAX_LINES

        if self._auto_scroll:
            self._textbox.see("end")

    def append_command(self, cmd: str):
        """Append a command line in command style."""
        self.append_output(f"❯ {cmd}", "command")

    def append_phase_header(self, phase_name: str):
        """Append a phase section header."""
        self.append_output(f"\n{'━' * 50}", "phase")
        self.append_output(f"  {phase_name}", "phase")
        self.append_output(f"{'━' * 50}", "phase")

    def clear(self):
        """Clear all terminal output."""
        self._textbox.delete("1.0", "end")
        self._line_count = 0

    def search(self, query: str):
        """Highlight matching text in the terminal."""
        # Remove previous highlights
        self._textbox.tag_remove("highlight", "1.0", "end")

        if not query:
            return

        start = "1.0"
        while True:
            pos = self._textbox.search(query, start, stopindex="end", nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self._textbox.tag_add("highlight", pos, end)
            start = end

        # Scroll to first match
        first = self._textbox.tag_ranges("highlight")
        if first:
            self._textbox.see(first[0])

    def get_all_text(self) -> str:
        """Return all terminal text."""
        return self._textbox.get("1.0", "end-1c")

    # ── Private Methods ─────────────────────────────────────────

    def _detect_tag(self, text: str) -> str:
        """Auto-detect the appropriate tag based on content."""
        lower = text.lower()
        if text.strip().startswith("❯") or text.strip().startswith(">"):
            return "command"
        elif "[✓]" in text or "[+]" in text or "success" in lower or "found" in lower:
            return "success"
        elif "[✗]" in text or "[error]" in lower or "error" in lower or "failed" in lower:
            return "error"
        elif "[!]" in text or "[warning]" in lower or "warning" in lower or "skipped" in lower:
            return "warning"
        elif "━" in text or "═" in text or "─" in text or "phase" in lower:
            return "phase"
        elif "[*]" in text or "[info]" in lower:
            return "info"
        return "output"

    def _on_scroll(self, event=None):
        """Handle scroll events to toggle auto-scroll."""
        # If user scrolls up, disable auto-scroll
        self._auto_scroll = False
        self._scroll_label.configure(text="↑ Scroll locked", text_color=Colors.WARNING)

        # Re-enable if scrolled to bottom
        self.after(100, self._check_scroll_position)

    def _check_scroll_position(self):
        """Check if scrolled to bottom to re-enable auto-scroll."""
        try:
            yview = self._textbox.yview()
            if yview[1] >= 0.99:
                self._auto_scroll = True
                self._scroll_label.configure(text="↓ Auto-scroll", text_color=Colors.SUCCESS)
        except Exception:
            pass

    def _copy_all(self):
        """Copy all terminal text to clipboard."""
        try:
            text = self.get_all_text()
            self.clipboard_clear()
            self.clipboard_append(text)
        except Exception:
            pass

    def _copy_selection(self):
        """Copy selected text to clipboard."""
        try:
            if self._textbox.tag_ranges("sel"):
                text = self._textbox.get("sel.first", "sel.last")
                self.clipboard_clear()
                self.clipboard_append(text)
        except Exception:
            pass

    def _select_all(self):
        """Select all terminal text."""
        self._textbox.tag_add("sel", "1.0", "end")

    def _show_context_menu(self, event):
        """Show right-click context menu."""
        try:
            self._context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._context_menu.grab_release()
