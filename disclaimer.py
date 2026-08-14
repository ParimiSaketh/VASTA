"""
VASTA Disclaimer Dialog
========================
Legal disclaimer shown on startup requiring user acknowledgment.
"""

import customtkinter as ctk

from gui.theme import Colors, Fonts, Dimensions


DISCLAIMER_TEXT = """
⚠️  LEGAL DISCLAIMER  ⚠️

VASTA is a security testing automation tool designed for authorized 
penetration testing and bug bounty hunting ONLY.

By using this tool, you acknowledge and agree that:

1. You have EXPLICIT WRITTEN AUTHORIZATION from the target 
   organization to perform security testing.

2. You will NOT use this tool against systems, networks, or 
   applications without proper authorization.

3. Unauthorized access to computer systems is ILLEGAL in most 
   jurisdictions and can result in criminal prosecution.

4. The developers of VASTA are NOT responsible for any misuse, 
   damage, or legal consequences resulting from the use of this tool.

5. You understand that active scanning tools may cause disruption 
   to target systems and accept full responsibility.

6. All findings must be reported responsibly through the 
   appropriate channels.

USE THIS TOOL RESPONSIBLY AND ETHICALLY.
"""


class DisclaimerDialog(ctk.CTkToplevel):
    """Legal disclaimer dialog requiring user confirmation."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Fix macOS blank CTkToplevel: withdraw during setup
        self.withdraw()

        self.title("VASTA — Legal Disclaimer")
        self.geometry("550x650")
        self.resizable(False, False)
        self.configure(fg_color=Colors.BG_DARKEST)

        self._accepted = False

        self._build_ui()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_exit)

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
        except Exception:
            pass

    def _build_ui(self):
        font_family = Fonts.get_family()

        # ── Warning Header ──────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=Colors.ERROR_DARK, height=50, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        warning_label = ctk.CTkLabel(
            header,
            text="⚠  IMPORTANT: Read Before Proceeding",
            font=(font_family, Fonts.SIZE_SUBHEADING, "bold"),
            text_color=Colors.WARNING,
        )
        warning_label.pack(expand=True)

        # ── Disclaimer Text ─────────────────────────────────────
        text_frame = ctk.CTkFrame(self, fg_color=Colors.BG_DARK, corner_radius=Dimensions.RADIUS_MEDIUM)
        text_frame.pack(fill="both", expand=True, padx=Dimensions.PAD_LARGE, pady=Dimensions.PAD_MEDIUM)

        text_label = ctk.CTkLabel(
            text_frame,
            text=DISCLAIMER_TEXT.strip(),
            font=(font_family, Fonts.SIZE_SMALL),
            text_color=Colors.TEXT_SECONDARY,
            justify="left",
            wraplength=470,
        )
        text_label.pack(padx=Dimensions.PAD_MEDIUM, pady=Dimensions.PAD_MEDIUM)

        # ── Checkbox ────────────────────────────────────────────
        self._agree_var = ctk.BooleanVar(value=False)
        self._agree_check = ctk.CTkCheckBox(
            self,
            text="I confirm I have authorization to scan the target",
            font=(font_family, Fonts.SIZE_BODY, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_DARK,
            checkmark_color=Colors.BG_DARKEST,
            variable=self._agree_var,
            command=self._on_checkbox_change,
        )
        self._agree_check.pack(padx=Dimensions.PAD_LARGE, pady=(0, Dimensions.PAD_MEDIUM))

        # ── Buttons ─────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent", height=70)
        btn_frame.pack(fill="x", padx=Dimensions.PAD_LARGE, pady=(Dimensions.PAD_MEDIUM, Dimensions.PAD_LARGE))
        btn_frame.pack_propagate(False)

        self._accept_btn = ctk.CTkButton(
            btn_frame,
            text="✓  Accept & Continue",
            font=(font_family, 16, "bold"),
            fg_color=Colors.SUCCESS,
            hover_color=Colors.SUCCESS_DARK,
            text_color=Colors.TEXT_BRIGHT,
            height=55,
            corner_radius=Dimensions.RADIUS_MEDIUM,
            command=self._on_accept,
            state="disabled",
        )
        self._accept_btn.pack(side="left", expand=True, fill="both", padx=(0, Dimensions.PAD_MEDIUM))

        exit_btn = ctk.CTkButton(
            btn_frame,
            text="✕  Exit",
            font=(font_family, 16, "bold"),
            fg_color=Colors.ERROR,
            hover_color=Colors.ERROR_DARK,
            text_color=Colors.TEXT_BRIGHT,
            height=55,
            corner_radius=Dimensions.RADIUS_MEDIUM,
            command=self._on_exit,
            width=120,
        )
        exit_btn.pack(side="right", fill="y")

    def _on_checkbox_change(self):
        """Enable/disable accept button based on checkbox."""
        if self._agree_var.get():
            self._accept_btn.configure(state="normal")
        else:
            self._accept_btn.configure(state="disabled")

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

    def _on_accept(self):
        """User accepted the disclaimer."""
        self._accepted = True
        self.grab_release()
        self._cancel_all_after()
        self.destroy()

    def _on_exit(self):
        """User declined — exit the application."""
        self._accepted = False
        self.grab_release()
        self._cancel_all_after()
        self.destroy()

    @property
    def accepted(self) -> bool:
        return self._accepted
