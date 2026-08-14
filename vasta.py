#!/usr/bin/env python3
"""VASTA — Vulnerability Assessment & Security Testing Automator"""
import sys
import os

# Silence macOS Tk deprecation warning
os.environ["TK_SILENCE_DEPRECATION"] = "1"

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: VASTA requires Python 3.8 or higher")
        sys.exit(1)

    # Check and install customtkinter if needed
    try:
        import customtkinter
    except ImportError:
        print("Installing required dependencies...")
        os.system(f"{sys.executable} -m pip install customtkinter Pillow")
        import customtkinter

    # Set dark mode BEFORE any window is created
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")

    from gui.app import VASTAApp
    app = VASTAApp()
    app.run()


if __name__ == '__main__':
    main()
