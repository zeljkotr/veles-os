#!/usr/bin/env python3
"""
VELES OS Main Entry Point
"""

import sys

def main():
    print("[VELES] Starting VELES OS runtime...")

    try:
        import gi
        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk

        print("[VELES] GTK4 available.")
        from desktop.gtk.main import VELESDesktop
        app = VELESDesktop()
        app.run()
        return 0

    except ImportError:
        print("[VELES] GTK4 not available, falling back to web interface...")
        from desktop.web_init import start_web
        thread = start_web()

        if thread is None:
            print("[VELES] Desktop web interface failed to start.")
            return 1

        print("[VELES] Desktop runtime started.")
        try:
            thread.join()
        except KeyboardInterrupt:
            print("[VELES] Shutdown requested.")

        return 0

if __name__ == "__main__":
    sys.exit(main())
