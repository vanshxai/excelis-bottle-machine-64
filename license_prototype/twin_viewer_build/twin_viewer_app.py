"""
Faulter AI -- Twin Viewer (the "Executable File" piece).

This is NOT a pre-made app. A fresh copy of this template + a
machine-specific wireframe.html gets staged and packaged (PyInstaller)
by the Software Packet Builder itself, every time someone runs it
against a real assembly file -- see packet_builder_app.py's
download_executable(). This file should never be built/shipped by hand.

Uses pywebview so the 3D wireframe renders INSIDE this app's own native
window -- not by shelling out to the system browser.
"""
import os
import sys
import webview


def resource_path(relative: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


if __name__ == "__main__":
    html_path = resource_path("assets/wireframe.html")
    webview.create_window("Faulter AI", html_path, width=1180, height=860, min_size=(800, 600))
    webview.start()
