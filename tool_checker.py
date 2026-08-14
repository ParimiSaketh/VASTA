"""
VASTA Tool Checker Dialog
==========================
Modal showing tool installation status with auto-install capability.
"""

import customtkinter as ctk
import threading
from typing import Optional, Callable, Dict

from gui.theme import Colors, Fonts, Dimensions


class ToolCheckerDialog(ctk.CTkToplevel):
    """Dialog for checking and installing required tools."""

    def __init__(self, master, tool_manager=None, **kwargs):
        super().__init__(master, **kwargs)

        # Fix macOS blank CTkToplevel: withdraw during setup
        self.withdraw()

        self.title("VASTA — Tool Status Check")
        self.geometry("700x600")
        self.resizable(False, False)
        self.configure(fg_color=Colors.BG_DARKEST)

        self._tool_manager = tool_manager
        self._tool_rows: Dict[str, dict] = {}
        self._result = False  # True if user proceeds

        self._build_ui()

        # Center on parent
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
                # Auto-check tools after window is visible
                if self._tool_manager:
                    self.after(300, self._check_tools)
        except Exception:
            pass

    def _build_ui(self):
        font_family = Fonts.get_family()

        # ── Header ──────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=Colors.BG_DARK, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="⚙ Tool Status Check",
            font=(font_family, Fonts.SIZE_HEADING, "bold"),
            text_color=Colors.PRIMARY,
        )
        title.pack(side="left", padx=Dimensions.PAD_LARGE, pady=Dimensions.PAD_MEDIUM)

        self._summary_label = ctk.CTkLabel(
            header,
            text="Checking tools...",
            font=(font_family, Fonts.SIZE_SMALL),
            text_color=Colors.TEXT_MUTED,
        )
        self._summary_label.pack(side="right", padx=Dimensions.PAD_LARGE)

        # ── Tool List ───────────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=Colors.BG_DARKEST,
            corner_radius=0,
        )
        self._scroll.pack(fill="both", expand=True, padx=Dimensions.PAD_MEDIUM, pady=Dimensions.PAD_SMALL)

        # ── Progress Area ───────────────────────────────────────
        self._progress_frame = ctk.CTkFrame(self, fg_color=Colors.BG_DARK, height=80)
        self._progress_frame.pack(fill="x", padx=Dimensions.PAD_MEDIUM, pady=(0, Dimensions.PAD_SMALL))

        self._progress_label = ctk.CTkLabel(
            self._progress_frame,
            text="",
            font=(Fonts.get_mono_family(), Fonts.SIZE_TINY),
            text_color=Colors.TEXT_MUTED,
            wraplength=650,
            justify="left",
        )
        self._progress_label.pack(padx=Dimensions.PAD_MEDIUM, pady=Dimensions.PAD_SMALL, anchor="w")

        self._progress_bar = ctk.CTkProgressBar(
            self._progress_frame,
            fg_color=Colors.BG_MEDIUM,
            progress_color=Colors.PRIMARY,
            height=6,
        )
        self._progress_bar.pack(fill="x", padx=Dimensions.PAD_MEDIUM, pady=(0, Dimensions.PAD_SMALL))
        self._progress_bar.set(0)

        # ── Buttons ─────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent", height=50)
        btn_frame.pack(fill="x", padx=Dimensions.PAD_MEDIUM, pady=Dimensions.PAD_MEDIUM)

        self._install_btn = ctk.CTkButton(
            btn_frame,
            text="⬇ Install All Missing",
            font=(font_family, Fonts.SIZE_BODY, "bold"),
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_DARK,
            text_color=Colors.BG_DARKEST,
            height=40,
            corner_radius=Dimensions.RADIUS_MEDIUM,
            command=self._install_missing,
            width=200,
        )
        self._install_btn.pack(side="left", padx=(0, Dimensions.PAD_MEDIUM))

        self._skip_btn = ctk.CTkButton(
            btn_frame,
            text="Skip & Continue →",
            font=(font_family, Fonts.SIZE_BODY),
            fg_color=Colors.BG_LIGHT,
            hover_color=Colors.BG_HIGHLIGHT,
            text_color=Colors.TEXT_SECONDARY,
            height=40,
            corner_radius=Dimensions.RADIUS_MEDIUM,
            command=self._skip,
            border_width=1,
            border_color=Colors.BORDER,
            width=150,
        )
        self._skip_btn.pack(side="right")

    def _add_tool_row(self, name: str, category: str, description: str, installed: bool):
        """Add a tool row to the list."""
        font_family = Fonts.get_family()

        row = ctk.CTkFrame(self._scroll, fg_color=Colors.BG_MEDIUM, corner_radius=Dimensions.RADIUS_SMALL)
        row.pack(fill="x", pady=2)
        row.grid_columnconfigure(1, weight=1)

        # Status icon
        status_text = "✅" if installed else "❌"
        status_color = Colors.SUCCESS if installed else Colors.ERROR
        status_lbl = ctk.CTkLabel(
            row, text=status_text, font=(font_family, Fonts.SIZE_BODY), width=30,
        )
        status_lbl.grid(row=0, column=0, padx=Dimensions.PAD_SMALL, pady=Dimensions.PAD_TINY)

        # Tool info
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="w", padx=0, pady=Dimensions.PAD_TINY)

        name_lbl = ctk.CTkLabel(
            info_frame, text=name,
            font=(font_family, Fonts.SIZE_SMALL, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        name_lbl.pack(anchor="w")

        desc_lbl = ctk.CTkLabel(
            info_frame, text=description,
            font=(font_family, Fonts.SIZE_TINY),
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        desc_lbl.pack(anchor="w")

        # Category badge
        cat_colors = {
            "go": Colors.PRIMARY,
            "python": Colors.WARNING,
            "git": Colors.SECONDARY_LIGHT,
        }
        cat_lbl = ctk.CTkLabel(
            row, text=category.upper(),
            font=(font_family, Fonts.SIZE_TINY, "bold"),
            text_color=cat_colors.get(category, Colors.TEXT_MUTED),
            width=60,
        )
        cat_lbl.grid(row=0, column=2, padx=Dimensions.PAD_SMALL, pady=Dimensions.PAD_TINY)

        self._tool_rows[name] = {
            "row": row,
            "status_label": status_lbl,
            "installed": installed,
        }

    def _check_tools(self):
        """Check all tool installation statuses."""
        if not self._tool_manager:
            return

        statuses = self._tool_manager.check_all_tools()
        installed_count = 0
        total = len(statuses)

        for name, info in statuses.items():
            self._add_tool_row(
                name=name,
                category=info["category"],
                description=info["description"],
                installed=info["installed"],
            )
            if info["installed"]:
                installed_count += 1

        status_color = Colors.SUCCESS if installed_count == total else Colors.WARNING
        self._summary_label.configure(
            text=f"{installed_count}/{total} tools installed",
            text_color=status_color,
        )

        if installed_count == total:
            self._install_btn.configure(state="disabled", text="✓ All Installed")

    def set_tool_status(self, tool_name: str, installed: bool, version: str = ""):
        """Update a specific tool's status."""
        row_info = self._tool_rows.get(tool_name)
        if row_info:
            row_info["status_label"].configure(text="✅" if installed else "❌")
            row_info["installed"] = installed

    def set_install_progress(self, tool_name: str, progress_text: str):
        """Update the install progress display."""
        self._progress_label.configure(text=f"[{tool_name}] {progress_text}")

    def _install_missing(self):
        """Install all missing tools in a background thread."""
        if not self._tool_manager:
            return

        self._install_btn.configure(state="disabled", text="Installing...")
        self._skip_btn.configure(state="disabled")

        def _do_install():
            total_tools = len(self._tool_rows)
            installed = 0

            def on_output(text):
                self.after(0, lambda: self._progress_label.configure(text=text[-80:] if len(text) > 80 else text))

            results = self._tool_manager.install_all_missing(on_output=on_output)

            # Re-check all tools
            statuses = self._tool_manager.check_all_tools()
            installed_count = sum(1 for v in statuses.values() if v["installed"])

            def _update_ui():
                for name, info in statuses.items():
                    self.set_tool_status(name, info["installed"])

                self._summary_label.configure(
                    text=f"{installed_count}/{total_tools} tools installed",
                    text_color=Colors.SUCCESS if installed_count == total_tools else Colors.WARNING,
                )
                self._progress_label.configure(text="Installation complete!")
                self._progress_bar.set(1.0)
                self._install_btn.configure(text="✓ Done")
                self._skip_btn.configure(state="normal", text="Continue →")

            self.after(0, _update_ui)

        thread = threading.Thread(target=_do_install, daemon=True)
        thread.start()

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

    def _skip(self):
        """Skip tool check and continue."""
        self._result = True
        self.grab_release()
        self._cancel_all_after()
        self.destroy()

    def get_result(self) -> bool:
        return self._result
