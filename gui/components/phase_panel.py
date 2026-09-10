"""
VASTA Phase Panel
==================
Left sidebar showing all 7 phases with live status indicators.
"""

import customtkinter as ctk
from typing import Optional, Callable, Dict

from gui.theme import Colors, Fonts, Dimensions, Icons, PhaseInfo


class PhaseCard(ctk.CTkFrame):
    """Individual phase card in the sidebar."""

    STATUS_CONFIG = {
        "pending": {"icon": Icons.PENDING, "color": Colors.PHASE_PENDING, "bg": "transparent"},
        "running": {"icon": Icons.RUNNING, "color": Colors.PHASE_RUNNING, "bg": Colors.PRIMARY_MUTED},
        "complete": {"icon": Icons.COMPLETE, "color": Colors.PHASE_COMPLETE, "bg": "transparent"},
        "error": {"icon": Icons.ERROR, "color": Colors.PHASE_ERROR, "bg": Colors.ERROR_DARK},
        "skipped": {"icon": Icons.SKIPPED, "color": Colors.PHASE_SKIPPED, "bg": "transparent"},
    }

    def __init__(self, master, phase_data: dict, on_click: Optional[Callable] = None, **kwargs):
        super().__init__(
            master,
            fg_color="transparent",
            corner_radius=Dimensions.RADIUS_MEDIUM,
            cursor="hand2",
            **kwargs,
        )
        self.phase_id = phase_data["id"]
        self._phase_data = phase_data
        self._on_click = on_click
        self._status = "pending"
        self._anim_frame = 0

        font_family = Fonts.get_family()

        # Layout
        self.grid_columnconfigure(1, weight=1)

        # Status icon
        self._status_icon = ctk.CTkLabel(
            self,
            text=Icons.PENDING,
            font=(font_family, Fonts.SIZE_HEADING),
            text_color=Colors.PHASE_PENDING,
            width=30,
        )
        self._status_icon.grid(row=0, column=0, rowspan=2, padx=(Dimensions.PAD_SMALL, Dimensions.PAD_TINY), pady=Dimensions.PAD_SMALL)

        # Phase name
        self._name_label = ctk.CTkLabel(
            self,
            text=f"{phase_data['icon']} Phase {phase_data['id']}: {phase_data['short']}",
            font=(font_family, Fonts.SIZE_SMALL, "bold"),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        )
        self._name_label.grid(row=0, column=1, sticky="w", padx=0, pady=(Dimensions.PAD_SMALL, 0))

        # Stats / description
        self._stats_label = ctk.CTkLabel(
            self,
            text=phase_data["description"][:45],
            font=(font_family, Fonts.SIZE_TINY),
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        self._stats_label.grid(row=1, column=1, sticky="w", padx=0, pady=(0, Dimensions.PAD_SMALL))

        # Bind click events
        for widget in [self, self._status_icon, self._name_label, self._stats_label]:
            widget.bind("<Button-1>", self._handle_click)
            widget.bind("<Enter>", self._on_hover_enter)
            widget.bind("<Leave>", self._on_hover_leave)

    def set_status(self, status: str):
        """Update phase status visual."""
        self._status = status
        config = self.STATUS_CONFIG.get(status, self.STATUS_CONFIG["pending"])
        self._status_icon.configure(text=config["icon"], text_color=config["color"])

        bg = config["bg"]
        self.configure(fg_color=bg)

        if status == "running":
            self._name_label.configure(text_color=Colors.PRIMARY)
            self._start_running_animation()
        elif status == "complete":
            self._name_label.configure(text_color=Colors.SUCCESS)
        elif status == "error":
            self._name_label.configure(text_color=Colors.ERROR)
        else:
            self._name_label.configure(text_color=Colors.TEXT_SECONDARY)

    def set_stats(self, stats_text: str):
        """Update the stats display text."""
        self._stats_label.configure(text=stats_text, text_color=Colors.TEXT_SECONDARY)

    def _start_running_animation(self):
        """Animate the running status icon."""
        if self._status != "running":
            return
        dots = ["◐", "◓", "◑", "◒"]
        self._anim_frame = (self._anim_frame + 1) % len(dots)
        self._status_icon.configure(text=dots[self._anim_frame])
        self.after(300, self._start_running_animation)

    def _handle_click(self, event=None):
        if self._on_click:
            self._on_click(self.phase_id)

    def _on_hover_enter(self, event=None):
        if self._status not in ("running",):
            self.configure(fg_color=Colors.BG_LIGHT)

    def _on_hover_leave(self, event=None):
        if self._status == "running":
            self.configure(fg_color=Colors.PRIMARY_MUTED)
        elif self._status == "error":
            self.configure(fg_color=Colors.ERROR_DARK)
        else:
            self.configure(fg_color="transparent")


class PhasePanel(ctk.CTkFrame):
    """Left sidebar showing all scan phases with status."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            width=Dimensions.SIDEBAR_WIDTH,
            fg_color=Colors.BG_DARK,
            corner_radius=0,
            **kwargs,
        )
        self._on_phase_click: Optional[Callable] = None
        self._phase_cards: Dict[int, PhaseCard] = {}
        self._build_ui()

    def _build_ui(self):
        font_family = Fonts.get_family()

        # Header
        header = ctk.CTkLabel(
            self,
            text="SCAN PHASES",
            font=(font_family, Fonts.SIZE_SMALL, "bold"),
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        header.pack(padx=Dimensions.PAD_LARGE, pady=(Dimensions.PAD_LARGE, Dimensions.PAD_SMALL), anchor="w")

        # Separator
        sep = ctk.CTkFrame(self, height=1, fg_color=Colors.BORDER)
        sep.pack(fill="x", padx=Dimensions.PAD_MEDIUM, pady=(0, Dimensions.PAD_SMALL))

        # Scrollable container for phase cards
        self._scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=Colors.BG_LIGHT,
            scrollbar_button_hover_color=Colors.PRIMARY,
        )
        self._scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Phase cards inside the scrollable frame
        for phase_data in PhaseInfo.PHASES:
            card = PhaseCard(
                self._scroll_frame,
                phase_data=phase_data,
                on_click=self._handle_phase_click,
            )
            card.pack(fill="x", padx=Dimensions.PAD_SMALL, pady=Dimensions.PAD_TINY)
            self._phase_cards[phase_data["id"]] = card

    def set_phase_status(self, phase_id: int, status: str):
        """Update a phase's status indicator."""
        card = self._phase_cards.get(phase_id)
        if card:
            card.set_status(status)

    def set_phase_stats(self, phase_id: int, stats_text: str):
        """Update a phase's statistics text."""
        card = self._phase_cards.get(phase_id)
        if card:
            card.set_stats(stats_text)

    def set_on_phase_click(self, callback: Callable):
        """Set the callback for phase card clicks."""
        self._on_phase_click = callback

    def reset(self):
        """Reset all phases to pending state."""
        for phase_data in PhaseInfo.PHASES:
            pid = phase_data["id"]
            self.set_phase_status(pid, "pending")
            card = self._phase_cards.get(pid)
            if card:
                card.set_stats(phase_data["description"][:45])

    def _handle_phase_click(self, phase_id: int):
        if self._on_phase_click:
            self._on_phase_click(phase_id)
