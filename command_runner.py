"""
VASTA Command Runner
====================
Wraps subprocess.Popen for real-time output streaming with cross-platform support.
Handles process management, cancellation, and thread-safe output delivery.
"""

import subprocess
import threading
import platform
import signal
import os
import queue
from typing import Callable, Optional, Tuple


class CommandRunner:
    """Runs shell commands with real-time output streaming."""

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._cancelled = False
        self._output_queue: queue.Queue = queue.Queue()

    @staticmethod
    def _is_windows() -> bool:
        return platform.system() == "Windows"

    def run(
        self,
        cmd: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        env: Optional[dict] = None,
        on_output: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[int], None]] = None,
    ) -> int:
        """
        Run a command with real-time output streaming.

        Args:
            cmd: Shell command string to execute.
            cwd: Working directory for the command.
            timeout: Maximum seconds to wait (None = no limit).
            env: Environment variables dict (merged with os.environ).
            on_output: Callback for each output line.
            on_complete: Callback when command finishes, receives return code.

        Returns:
            Process return code.
        """
        self._cancelled = False

        # Build environment
        run_env = os.environ.copy()
        # Ensure Go binaries are in PATH
        go_path = os.path.expanduser("~/go/bin")
        if go_path not in run_env.get("PATH", ""):
            run_env["PATH"] = go_path + os.pathsep + run_env.get("PATH", "")
        if env:
            run_env.update(env)

        # Cross-platform shell setup
        if self._is_windows():
            shell_cmd = ["cmd", "/c", cmd]
            kwargs = {
                "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP,
            }
        else:
            shell_cmd = ["bash", "-c", cmd]
            kwargs = {
                "preexec_fn": os.setsid,
            }

        try:
            self._process = subprocess.Popen(
                shell_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=cwd,
                env=run_env,
                bufsize=1,
                universal_newlines=True,
                **kwargs,
            )

            # Read output in a thread to avoid blocking
            def _read_output():
                try:
                    for line in iter(self._process.stdout.readline, ""):
                        if self._cancelled:
                            break
                        stripped = line.rstrip("\n\r")
                        if on_output:
                            on_output(stripped)
                        self._output_queue.put(stripped)
                except (ValueError, OSError):
                    pass  # Process stdout was closed
                finally:
                    if self._process.stdout:
                        self._process.stdout.close()

            reader_thread = threading.Thread(target=_read_output, daemon=True)
            reader_thread.start()

            # Wait for completion with optional timeout
            try:
                return_code = self._process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self._kill_process()
                return_code = -1
                if on_output:
                    on_output(f"[TIMEOUT] Command timed out after {timeout}s")

            reader_thread.join(timeout=5)

            if on_complete:
                on_complete(return_code)

            return return_code

        except FileNotFoundError as e:
            error_msg = f"[ERROR] Command not found: {e}"
            if on_output:
                on_output(error_msg)
            if on_complete:
                on_complete(-1)
            return -1
        except Exception as e:
            error_msg = f"[ERROR] Failed to run command: {e}"
            if on_output:
                on_output(error_msg)
            if on_complete:
                on_complete(-1)
            return -1
        finally:
            self._process = None

    def run_sync(
        self, cmd: str, cwd: Optional[str] = None, timeout: Optional[int] = 30
    ) -> Tuple[str, str, int]:
        """
        Run a command synchronously and return output.

        Returns:
            Tuple of (stdout, stderr, return_code).
        """
        run_env = os.environ.copy()
        go_path = os.path.expanduser("~/go/bin")
        if go_path not in run_env.get("PATH", ""):
            run_env["PATH"] = go_path + os.pathsep + run_env.get("PATH", "")

        try:
            if self._is_windows():
                shell_cmd = ["cmd", "/c", cmd]
            else:
                shell_cmd = ["bash", "-c", cmd]

            result = subprocess.run(
                shell_cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                env=run_env,
                timeout=timeout,
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", f"Command timed out after {timeout}s", -1
        except FileNotFoundError as e:
            return "", f"Command not found: {e}", -1
        except Exception as e:
            return "", f"Error: {e}", -1

    def cancel(self):
        """Cancel the currently running command."""
        self._cancelled = True
        self._kill_process()

    def _kill_process(self):
        """Kill the running process and its children."""
        if self._process is None:
            return

        try:
            if self._is_windows():
                # Windows: use taskkill to kill process tree
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self._process.pid)],
                    capture_output=True,
                )
            else:
                # Unix: kill the process group
                try:
                    os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass
                # Force kill after a moment if still alive
                try:
                    self._process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
        except Exception:
            # Last resort
            try:
                self._process.kill()
            except Exception:
                pass

    @property
    def is_running(self) -> bool:
        """Check if a command is currently running."""
        return self._process is not None and self._process.poll() is None
