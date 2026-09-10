"""
VASTA Stats Bar
================
Bottom statistics bar with live counters and phase progress.
"""

import customtkinter as ctk
from typing import Dict

from gui.theme import Colors, Fonts, Dimensions


class StatsBar(ctk.CTkFrame):
    """Bottom bar showing live scan statistics."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            height=Dimensions.STATS_BAR_HEIGHT,
            fg_color=Colors.BG_DARK,
            corner_radius=0,
            **kwargs,
        )
        self.pack_propagate(False)
        self._stat_labels: Dict[str, ctk.CTkLabel] = {}
        self._build_ui()

    def _build_ui(self):
        font_family = Fonts.get_family()

        # ── Left side: stat counters ──────────────────────────────
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(side="left", fill="y", padx=Dimensions.PAD_MEDIUM)

        stat_configs = [
            ("subdomains", "🌐 Subdomains:", "0", Colors.PRIMARY),
            ("alive_hosts", "📡 Alive:", "0", Colors.SUCCESS),
            ("endpoints", "🔗 Endpoints:", "0", Colors.SECONDARY_LIGHT),
            ("js_files", "📜 JS:", "0", Colors.WARNING),
            ("sensitive", "🔒 Sensitive:", "0", Colors.TEXT_SECONDARY),
            ("vulns", "🐛 Vulns:", "0", Colors.ERROR),
        ]

        for key, label_text, default_val, color in stat_configs:
            # Container
            item = ctk.CTkFrame(stats_frame, fg_color="transparent")
            item.pack(side="left", padx=(0, Dimensions.PAD_LARGE))

            # Label
            lbl = ctk.CTkLabel(
                item,
                text=label_text,
                font=(font_family, Fonts.SIZE_TINY),
                text_color=Colors.TEXT_MUTED,
            )
            lbl.pack(side="left")

            # Value
            val = ctk.CTkLabel(
                item,
                text=default_val,
                font=(font_family, Fonts.SIZE_SMALL, "bold"),
                text_color=color,
            )
            val.pack(side="left", padx=(Dimensions.PAD_TINY, 0))

            self._stat_labels[key] = val

        # ── Right side: phase info ───────────────────────────────
        phase_frame = ctk.CTkFrame(self, fg_color="transparent")
        phase_frame.pack(side="right", fill="y", padx=Dimensions.PAD_MEDIUM)

        self._phase_label = ctk.CTkLabel(
            phase_frame,
            text="Ready to scan",
            font=(font_family, Fonts.SIZE_SMALL),
            text_color=Colors.TEXT_MUTED,
        )
        self._phase_label.pack(side="right")

    # ── Public Methods ──────────────────────────────────────────

    def update_stat(self, name: str, value):
        """Update a specific stat counter."""
        label = self._stat_labels.get(name)
        if label:
            label.configure(text=str(value))

    def set_phase_info(self, phase_name: str, progress_text: str = ""):
        """Update the current phase display."""
        text = f"⟳ {phase_name}"
        if progress_text:
            text += f" — {progress_text}"
        self._phase_label.configure(text=text, text_color=Colors.PRIMARY)

    def set_complete(self):
        """Show scan complete state."""
        self._phase_label.configure(text="✓ Scan Complete", text_color=Colors.SUCCESS)

    def set_cancelled(self):
        """Show scan cancelled state."""
        self._phase_label.configure(text="■ Scan Cancelled", text_color=Colors.WARNING)

    def reset(self):
        """Reset all stats to zero."""
        for label in self._stat_labels.values():
            label.configure(text="0")
        self._phase_label.configure(text="Ready to scan", text_color=Colors.TEXT_MUTED)
