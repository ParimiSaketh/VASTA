"""
VASTA Header Bar
=================
Top bar with logo, target input, action buttons, and elapsed time.
"""

import customtkinter as ctk
from typing import Optional, Callable

from gui.theme import Colors, Fonts, Dimensions, Icons


class HeaderBar(ctk.CTkFrame):
    """Top header bar with target input and scan controls."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            height=Dimensions.HEADER_HEIGHT,
            fg_color=Colors.BG_DARK,
            corner_radius=0,
            **kwargs,
        )

        self.on_start: Optional[Callable] = None
        self.on_pause: Optional[Callable] = None
        self.on_stop: Optional[Callable] = None
        self.on_export: Optional[Callable] = None
        self.on_manual_test: Optional[Callable] = None

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(2, weight=1)  # Target input expands

        font_family = Fonts.get_family()

        # ── Logo / App Name ─────────────────────────────────────
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=(Dimensions.PAD_LARGE, Dimensions.PAD_SMALL), pady=Dimensions.PAD_MEDIUM, sticky="w")

        self._logo_label = ctk.CTkLabel(
            logo_frame,
            text=f"{Icons.SHIELD} VASTA",
            font=(font_family, Fonts.SIZE_TITLE, "bold"),
            text_color=Colors.PRIMARY,
        )
        self._logo_label.pack(anchor="w")

        self._subtitle = ctk.CTkLabel(
            logo_frame,
            text="Vulnerability Assessment & Security Testing Automator",
            font=(font_family, Fonts.SIZE_TINY),
            text_color=Colors.TEXT_MUTED,
        )
        self._subtitle.pack(anchor="w")

        # ── Separator ───────────────────────────────────────────
        sep = ctk.CTkFrame(self, width=2, fg_color=Colors.BORDER, corner_radius=1)
        sep.grid(row=0, column=1, padx=Dimensions.PAD_SMALL, pady=Dimensions.PAD_MEDIUM, sticky="ns")

        # ── Target Input ────────────────────────────────────────
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=0, column=2, padx=Dimensions.PAD_MEDIUM, pady=Dimensions.PAD_MEDIUM, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)

        target_label = ctk.CTkLabel(
            input_frame,
            text=f"{Icons.TARGET} Target:",
            font=(font_family, Fonts.SIZE_BODY, "bold"),
            text_color=Colors.TEXT_SECONDARY,
        )
        target_label.grid(row=0, column=0, padx=(0, Dimensions.PAD_SMALL))

        self._target_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter target domain (e.g., example.com)",
            height=Dimensions.INPUT_HEIGHT,
            font=(font_family, Fonts.SIZE_BODY),
            fg_color=Colors.BG_LIGHT,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_MUTED,
            corner_radius=Dimensions.RADIUS_MEDIUM,
            border_width=1,
        )
        self._target_entry.grid(row=0, column=1, sticky="ew", padx=(0, Dimensions.PAD_SMALL))
        self._target_entry.bind("<Return>", lambda e: self._on_start_click())

        # ── Action Buttons ──────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=0, column=3, padx=(0, Dimensions.PAD_MEDIUM), pady=Dimensions.PAD_MEDIUM, sticky="e")

        self._start_btn = ctk.CTkButton(
            btn_frame,
            text=f"{Icons.PLAY} Start Scan",
            font=(font_family, Fonts.SIZE_BODY, "bold"),
            fg_color=Colors.SUCCESS,
            hover_color=Colors.SUCCESS_DARK,
            text_color=Colors.TEXT_BRIGHT,
            height=Dimensions.BUTTON_HEIGHT,
            corner_radius=Dimensions.RADIUS_MEDIUM,
            command=self._on_start_click,
            width=120,
        )
        self._start_btn.pack(side="left", padx=(0, Dimensions.PAD_TINY))

        self._pause_btn = ctk.CTkButton(
            btn_frame,
            text=f"{Icons.PAUSE} Pause",
            font=(font_family, Fonts.SIZE_BODY),
            fg_color=Colors.WARNING,
            hover_color=Colors.WARNING_DARK,
            text_color=Colors.BG_DARKEST,
            height=Dimensions.BUTTON_HEIGHT,
            corner_radius=Dimensions.RADIUS_MEDIUM,
            command=self._on_pause_click,
            state="disabled",
            width=90,
        )
        self._pause_btn.pack(side="left", padx=(0, Dimensions.PAD_TINY))

        self._stop_btn = ctk.CTkButton(
            btn_frame,
            text=f"{Icons.STOP} Stop",
            font=(font_family, Fonts.SIZE_BODY),
            fg_color=Colors.ERROR,
            hover_color=Colors.ERROR_DARK,
            text_color=Colors.TEXT_BRIGHT,
            height=Dimensions.BUTTON_HEIGHT,
            corner_radius=Dimensions.RADIUS_MEDIUM,
            command=self._on_stop_click,
            state="disabled",
            width=80,
        )
        self._stop_btn.pack(side="left", padx=(0, Dimensions.PAD_TINY))

        self._export_btn = ctk.CTkButton(
            btn_frame,
            text=f"{Icons.EXPORT} Export",
            font=(font_family, Fonts.SIZE_BODY),
            fg_color=Colors.BG_LIGHT,
            hover_color=Colors.BG_HIGHLIGHT,
            text_color=Colors.TEXT_SECONDARY,
            height=Dimensions.BUTTON_HEIGHT,
            corner_radius=Dimensions.RADIUS_MEDIUM,
            command=self._on_export_click,
            border_width=1,
            border_color=Colors.BORDER,
            width=90,
        )
        self._export_btn.pack(side="left", padx=(0, Dimensions.PAD_MEDIUM))

        # ── Elapsed Time ────────────────────────────────────────
        self._time_label = ctk.CTkLabel(
            btn_frame,
            text="00:00:00",
            font=(Fonts.get_mono_family(), Fonts.SIZE_BODY),
            text_color=Colors.TEXT_MUTED,
            width=70,
        )
        self._time_label.pack(side="left")

    # ── Public Methods ──────────────────────────────────────────

    def get_target(self) -> str:
        """Return the entered target domain."""
        return self._target_entry.get().strip()

    def set_scanning_state(self, is_scanning: bool):
        """Update button states when scan starts/stops."""
        if is_scanning:
            self._start_btn.configure(state="disabled")
            self._pause_btn.configure(state="normal")
            self._stop_btn.configure(state="normal")
            self._target_entry.configure(state="disabled")
        else:
            self._start_btn.configure(state="normal")
            self._pause_btn.configure(state="disabled")
            self._stop_btn.configure(state="disabled")
            self._target_entry.configure(state="normal")

    def set_paused_state(self, is_paused: bool):
        """Update pause button text."""
        if is_paused:
            self._pause_btn.configure(text=f"{Icons.PLAY} Resume")
        else:
            self._pause_btn.configure(text=f"{Icons.PAUSE} Pause")

    def update_elapsed_time(self, seconds: int):
        """Update the elapsed time display."""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        self._time_label.configure(text=f"{h:02d}:{m:02d}:{s:02d}")

    # ── Event Handlers ──────────────────────────────────────────

    def _on_start_click(self):
        if self.on_start:
            self.on_start()

    def _on_pause_click(self):
        if self.on_pause:
            self.on_pause()

    def _on_stop_click(self):
        if self.on_stop:
            self.on_stop()

    def _on_export_click(self):
        if self.on_export:
            self.on_export()

    def _on_manual_test_click(self):
        if self.on_manual_test:
            self.on_manual_test()
