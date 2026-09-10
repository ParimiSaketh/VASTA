"""
VASTA Main Application
=======================
Assembles all GUI components and wires up the scanning pipeline.
"""

import customtkinter as ctk
import os
import sys
import threading
import json
import time
from tkinter import filedialog, messagebox
from typing import Optional, Dict

from gui.theme import Colors, Fonts, Dimensions
from gui.components.header import HeaderBar
from gui.components.phase_panel import PhasePanel
from gui.components.terminal import TerminalView
from gui.components.results_view import ResultsView
from gui.components.stats_bar import StatsBar
from gui.components.tool_checker import ToolCheckerDialog
from gui.dialogs.disclaimer import DisclaimerDialog
from gui.dialogs.settings import SettingsDialog, DEFAULT_SETTINGS
from gui.dialogs.manual_test import ManualTestDialog

from core.phase_engine import PhaseEngine
from core.tool_manager import ToolManager
from core.result_parser import ResultParser, ScanSummary

from phases.phase1_subdomain import SubdomainPhase
from phases.phase2_probing import ProbingPhase
from phases.phase3_endpoints import EndpointPhase
from phases.phase4_sensitive import SensitivePhase
from phases.phase5_dirbrute import DirBrutePhase
from phases.phase6_triage import TriagePhase
from phases.phase7_scanning import ScanningPhase


class VASTAApp(ctk.CTk):
    """Main VASTA application window."""

    def __init__(self):
        # Configure appearance BEFORE creating window
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        super().__init__()

        # Window setup
        self.title("VASTA — Vulnerability Assessment & Security Testing Automator")
        self.geometry(f"{Dimensions.WINDOW_DEFAULT_WIDTH}x{Dimensions.WINDOW_DEFAULT_HEIGHT}")
        self.minsize(Dimensions.WINDOW_MIN_WIDTH, Dimensions.WINDOW_MIN_HEIGHT)
        self.configure(fg_color=Colors.BG_DARKEST)

        # State
        self._project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._engine: Optional[PhaseEngine] = None
        self._tool_manager = ToolManager(project_dir=self._project_dir)
        self._parser = ResultParser()
        self._scan_summary = ScanSummary()
        self._settings = DEFAULT_SETTINGS.copy()
        self._scan_start_time = 0.0
        self._elapsed_timer_id = None
        self._is_paused = False

        # Build UI
        self._build_layout()

        # Wire up callbacks
        self._connect_signals()

        # Show disclaimer on startup
        self.after(500, self._show_startup_flow)

    def _build_layout(self):
        """Build the main application layout."""
        # Grid configuration
        self.grid_rowconfigure(1, weight=1)  # Main content expands
        self.grid_columnconfigure(1, weight=1)  # Center content expands

        # ── Top: Header Bar ─────────────────────────────────────
        self._header = HeaderBar(self)
        self._header.grid(row=0, column=0, columnspan=2, sticky="ew")

        # ── Left: Phase Panel ───────────────────────────────────
        self._phase_panel = PhasePanel(self)
        self._phase_panel.grid(row=1, column=0, sticky="ns", padx=0, pady=0)
        self._phase_panel.grid_propagate(False)
        self._phase_panel.configure(width=Dimensions.SIDEBAR_WIDTH)

        # ── Center: Tabbed content (Terminal + Results) ─────────
        center_frame = ctk.CTkFrame(self, fg_color=Colors.BG_DARKEST, corner_radius=0)
        center_frame.grid(row=1, column=1, sticky="nsew", padx=Dimensions.PAD_TINY, pady=Dimensions.PAD_TINY)
        center_frame.grid_rowconfigure(0, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)

        self._center_tabs = ctk.CTkTabview(
            center_frame,
            fg_color=Colors.BG_DARKEST,
            segmented_button_fg_color=Colors.BG_DARK,
            segmented_button_selected_color=Colors.PRIMARY,
            segmented_button_selected_hover_color=Colors.PRIMARY_DARK,
            segmented_button_unselected_color=Colors.BG_DARK,
            segmented_button_unselected_hover_color=Colors.BG_LIGHT,
            text_color=Colors.TEXT_BRIGHT,
            text_color_disabled=Colors.TEXT_MUTED,
            corner_radius=Dimensions.RADIUS_MEDIUM,
        )
        self._center_tabs.grid(row=0, column=0, sticky="nsew")

        terminal_tab = self._center_tabs.add("❯ Live Terminal")
        results_tab = self._center_tabs.add("📊 Results Dashboard")

        # Terminal
        terminal_tab.grid_rowconfigure(0, weight=1)
        terminal_tab.grid_columnconfigure(0, weight=1)
        self._terminal = TerminalView(terminal_tab)
        self._terminal.grid(row=0, column=0, sticky="nsew")

        # Results
        results_tab.grid_rowconfigure(0, weight=1)
        results_tab.grid_columnconfigure(0, weight=1)
        self._results = ResultsView(results_tab)
        self._results.grid(row=0, column=0, sticky="nsew")

        # ── Bottom: Stats Bar ───────────────────────────────────
        self._stats_bar = StatsBar(self)
        self._stats_bar.grid(row=2, column=0, columnspan=2, sticky="ew")

    def _connect_signals(self):
        """Wire up UI callbacks."""
        self._header.on_start = self._on_start_scan
        self._header.on_pause = self._on_pause_scan
        self._header.on_stop = self._on_stop_scan
        self._header.on_export = self._on_export
        self._header.on_manual_test = self._on_manual_test
        self._phase_panel.set_on_phase_click(self._on_phase_click)

    # ── Startup Flow ────────────────────────────────────────────

    def _show_startup_flow(self):
        """Show disclaimer, then tool checker on startup."""
        # Force render the main window first
        self.update_idletasks()
        self.update()
        self.after(200, self._show_disclaimer)

    def _show_disclaimer(self):
        """Show the legal disclaimer dialog."""
        self.update()
        dialog = DisclaimerDialog(self)
        # Force the dialog to render on macOS
        dialog.update_idletasks()
        dialog.update()
        dialog.focus_force()
        dialog.lift()

        self.wait_window(dialog)

        if not dialog.accepted:
            self.destroy()
            sys.exit(0)

        # After disclaimer, check tools
        self.after(300, self._show_tool_checker)

    def _show_tool_checker(self):
        """Show the tool installation checker dialog."""
        self.update()
        dialog = ToolCheckerDialog(self, tool_manager=self._tool_manager)
        # Force the dialog to render on macOS
        dialog.update_idletasks()
        dialog.update()
        dialog.focus_force()
        dialog.lift()

        self.wait_window(dialog)

        # Welcome message in terminal
        self._terminal.append_output(
            f"\n{'═' * 50}\n"
            f"  🛡  Welcome to VASTA\n"
            f"  Enter a target domain and click Start Scan\n"
            f"{'═' * 50}\n",
            "phase"
        )

    # ── Scan Control ────────────────────────────────────────────

    def _on_start_scan(self):
        """Start the scanning pipeline."""
        target = self._header.get_target()
        if not target:
            messagebox.showwarning(
                "No Target",
                "Please enter a target domain (e.g., example.com)",
            )
            return

        # Validate domain format (basic check)
        if " " in target or not ("." in target or "localhost" in target):
            messagebox.showwarning(
                "Invalid Target",
                "Please enter a valid domain name (e.g., example.com)",
            )
            return

        # Reset state
        self._scan_summary = ScanSummary()
        self._terminal.clear()
        self._results.clear()
        self._phase_panel.reset()
        self._stats_bar.reset()
        self._is_paused = False

        # Create output directory
        output_base = os.path.join(
            self._project_dir,
            self._settings.get("output_dir", "output"),
        )
        os.makedirs(output_base, exist_ok=True)

        # Create phase instances
        phases = [
            SubdomainPhase(),
            ProbingPhase(),
            EndpointPhase(),
            SensitivePhase(),
            TriagePhase(),       # Phase 5: Vuln Triage
            DirBrutePhase(),     # Phase 6: Dir Brute
            ScanningPhase(),
        ]

        # Create engine
        self._engine = PhaseEngine(phases, output_base=output_base)
        self._engine.on_phase_start = self._handle_phase_start
        self._engine.on_phase_complete = self._handle_phase_complete
        self._engine.on_output = self._handle_output
        self._engine.on_error = self._handle_error
        self._engine.on_scan_complete = self._handle_scan_complete
        self._engine.on_vulnerability = self._handle_vulnerability

        # Update UI state
        self._header.set_scanning_state(True)
        self._stats_bar.set_phase_info("Starting scan...")

        # Switch to terminal tab
        self._center_tabs.set("❯ Live Terminal")

        # Start elapsed timer
        self._scan_start_time = time.time()
        self._update_elapsed_time()

        # Start the engine
        enabled = self._settings.get("enabled_phases", [1, 2, 3, 4, 5, 6, 7])
        self._engine.start(target, enabled_phases=enabled)

    def _on_pause_scan(self):
        """Pause or resume the scan."""
        if not self._engine:
            return

        if self._is_paused:
            self._engine.resume()
            self._is_paused = False
            self._header.set_paused_state(False)
        else:
            self._engine.pause()
            self._is_paused = True
            self._header.set_paused_state(True)

    def _on_stop_scan(self):
        """Stop the current scan."""
        if not self._engine:
            return

        confirm = messagebox.askyesno(
            "Stop Scan",
            "Are you sure you want to stop the current scan?",
        )
        if confirm:
            self._engine.cancel()

    def _on_export(self):
        """Export scan results."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ],
            title="Export Results",
        )
        if not file_path:
            return

        try:
            if file_path.endswith(".csv"):
                ResultParser.export_csv(self._scan_summary.vulnerabilities, file_path)
            else:
                ResultParser.export_json(self._scan_summary, file_path)

            messagebox.showinfo("Export Complete", f"Results exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")

    def _on_manual_test(self):
        """Open the manual tool testing dialog."""
        # Switch to Live Terminal tab to show output
        self._center_tabs.set("❯ Live Terminal")

        def _on_tool_output(text):
            """Receive output from manual tool — route to terminal."""
            self.after(0, lambda t=text: self._terminal.append_output(t))

        dialog = ManualTestDialog(self, on_output=_on_tool_output)
        dialog.wait_window()

    def _on_phase_click(self, phase_id: int):
        """Handle phase panel click — switch to results view."""
        self._center_tabs.set("📊 Results Dashboard")

    # ── Engine Callbacks (called from background thread) ────────

    def _handle_phase_start(self, phase_id: int, phase_name: str):
        """Called when a phase starts."""
        pid = phase_id
        pname = phase_name
        self.after(0, lambda _pid=pid: self._phase_panel.set_phase_status(_pid, "running"))
        self.after(0, lambda _pn=pname: self._stats_bar.set_phase_info(_pn))
        self.after(0, lambda _pid=pid, _pn=pname: self._terminal.append_phase_header(
            f"Phase {_pid}: {_pn}"
        ))

    def _handle_phase_complete(self, phase_id: int, result):
        """Called when a phase completes."""
        # Capture values by binding to local variables
        _pid = phase_id
        _result = result

        def _update(_pid=_pid, _result=_result):
            if _result.success:
                self._phase_panel.set_phase_status(_pid, "complete")

                # Show any warnings/errors even when successful
                if _result.errors:
                    warn_text = "; ".join(_result.errors)
                    self._phase_panel.set_phase_stats(_pid, f"⚠ {warn_text[:40]}")

                # Update stats based on phase results
                stats = _result.stats
                if "subdomains" in stats:
                    self._scan_summary.total_subdomains = stats["subdomains"]
                    self._stats_bar.update_stat("subdomains", stats["subdomains"])
                    self._phase_panel.set_phase_stats(_pid, f"{stats['subdomains']} subdomains")
                if "alive_hosts" in stats:
                    self._scan_summary.alive_hosts = stats["alive_hosts"]
                    self._stats_bar.update_stat("alive_hosts", stats["alive_hosts"])
                    self._phase_panel.set_phase_stats(_pid, f"{stats['alive_hosts']} alive")
                if "endpoints" in stats:
                    self._scan_summary.total_endpoints = stats["endpoints"]
                    self._stats_bar.update_stat("endpoints", stats["endpoints"])
                    self._phase_panel.set_phase_stats(_pid, f"{stats['endpoints']} URLs")
                if "js_files" in stats:
                    self._scan_summary.js_files = stats.get("js_files", 0)
                    self._stats_bar.update_stat("js_files", stats.get("js_files", 0))
                if "sensitive_files" in stats:
                    self._scan_summary.sensitive_files = stats.get("sensitive_files", 0)
                    self._stats_bar.update_stat("sensitive", stats.get("sensitive_files", 0))
                if "js_files" in stats or "sensitive_files" in stats:
                    total = stats.get("js_files", 0) + stats.get("sensitive_files", 0)
                    self._phase_panel.set_phase_stats(_pid, f"{total} files")
                if "dirs_found" in stats:
                    self._scan_summary.dirs_found = stats["dirs_found"]
                    self._phase_panel.set_phase_stats(_pid, f"{stats['dirs_found']} paths")

                # Gf triage stats
                triage_total = sum(v for k, v in stats.items() if k.endswith("_urls"))
                if triage_total > 0:
                    self._phase_panel.set_phase_stats(_pid, f"{triage_total} patterns")

                # Vulnerability stats from scanning
                vuln_total = sum(v for k, v in stats.items() if k.endswith("_vulns"))
                if vuln_total > 0:
                    self._phase_panel.set_phase_stats(_pid, f"{vuln_total} vulns found")

                # Load results into the results view for list-based phases
                self._load_phase_results(_pid, _result)

                # Update results overview
                self._results.update_stats({
                    "subdomains": self._scan_summary.total_subdomains,
                    "alive_hosts": self._scan_summary.alive_hosts,
                    "endpoints": self._scan_summary.total_endpoints,
                    "js_files": self._scan_summary.js_files,
                    "sensitive_files": self._scan_summary.sensitive_files,
                    "vulnerabilities": len(self._scan_summary.vulnerabilities),
                })
            else:
                self._phase_panel.set_phase_status(_pid, "error")
                errors = "; ".join(_result.errors) if _result.errors else "Failed"
                self._phase_panel.set_phase_stats(_pid, errors[:30])

        self.after(0, _update)

    def _handle_output(self, phase_id: int, text: str):
        """Called for each output line from the engine."""
        # Use default arg binding (t=text) to capture the current value.
        # Without this, the lambda closure captures by reference and
        # text may change before the lambda is invoked by after().
        self.after(0, lambda t=text: self._terminal.append_output(t))

    def _handle_error(self, phase_id: int, error: str):
        """Called when a phase encounters an error."""
        self.after(0, lambda e=error: self._terminal.append_output(f"[ERROR] {e}", "error"))

    def _handle_scan_complete(self, results: Dict):
        """Called when the entire scan pipeline finishes."""
        def _update():
            self._header.set_scanning_state(False)

            if results.get("cancelled"):
                self._stats_bar.set_cancelled()
            else:
                self._stats_bar.set_complete()

            # Stop elapsed timer
            if self._elapsed_timer_id:
                self.after_cancel(self._elapsed_timer_id)
                self._elapsed_timer_id = None

            # Switch to results
            self._center_tabs.set("📊 Results Dashboard")

            # Update severity counts
            self._results.update_severity_counts(
                self._scan_summary.severity_counts
            )

        self.after(0, _update)

    def _handle_vulnerability(self, vuln):
        """Called when a vulnerability is discovered."""
        _vuln = vuln
        def _update(_v=_vuln):
            self._scan_summary.vulnerabilities.append(_v)
            self._results.add_vulnerability(
                severity=_v.severity,
                vuln_type=_v.vuln_type,
                url=_v.url,
                tool=_v.tool,
                details=_v.details,
            )
            self._stats_bar.update_stat("vulns", len(self._scan_summary.vulnerabilities))

            # Update severity counts
            self._results.update_severity_counts(
                self._scan_summary.severity_counts
            )

        self.after(0, _update)

    # ── Helpers ─────────────────────────────────────────────────

    def _load_phase_results(self, phase_id: int, result):
        """Load phase output files into the results view."""
        try:
            if phase_id == 1 and "all_subdomains" in result.output_files:
                subs, _ = self._parser.parse_subdomains(result.output_files["all_subdomains"])
                if subs:
                    self._results.add_subdomains(subs[:5000])  # Limit for UI performance

            elif phase_id == 3 and "mainurls" in result.output_files:
                urls, _ = self._parser.parse_endpoints(result.output_files["mainurls"])
                if urls:
                    self._results.add_endpoints(urls[:5000])

            elif phase_id == 4:
                sensitive = []
                for key in ["js_files", "sensitive_files"]:
                    if key in result.output_files:
                        items, _ = self._parser.parse_sensitive_files(result.output_files[key])
                        sensitive.extend(items)
                if sensitive:
                    self._results.add_sensitive_files(sensitive[:5000])

        except Exception as e:
            self._terminal.append_output(f"[!] Error loading results: {e}", "warning")

    def _update_elapsed_time(self):
        """Update the elapsed time counter every second."""
        try:
            if self._engine and self._engine.is_running:
                elapsed = int(time.time() - self._scan_start_time)
                self._header.update_elapsed_time(elapsed)
                self._elapsed_timer_id = self.after(1000, self._update_elapsed_time)
        except Exception:
            pass  # Widget may be destroyed

    def destroy(self):
        """Clean up ALL pending callbacks before destroying the window."""
        # Cancel any running scan
        if self._engine and self._engine.is_running:
            try:
                self._engine.cancel()
            except Exception:
                pass

        # Cancel ALL pending Tcl 'after' events (including CTk internal ones)
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

        super().destroy()

    def report_callback_exception(self, exc_type, exc_value, exc_tb):
        """Suppress harmless Tcl 'invalid command name' errors on exit."""
        import traceback
        err_msg = str(exc_value)
        # These are harmless after-script errors during window teardown
        if "invalid command name" in err_msg:
            return
        # Print any real errors
        traceback.print_exception(exc_type, exc_value, exc_tb)

    def run(self):
        """Start the application main loop."""
        self.mainloop()
