"""
Faulter AI -- Software Packet Builder (the actual GUI, not a script you run
for someone). This is the tool WE run, per machine, to hand a client a
scoped, encrypted, signed software packet built from the core engine.

Flow: pick a STEP file -> enter machine/client name -> Build -> watches the
real pipeline run (parse STEP -> classify components -> select formulas ->
encrypt + sign) -> writes the .enc + .lic packet to disk.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tkinter as tk
from tkinter import filedialog, messagebox

from step_parser import parse_step
from formula_selector import build_subset, FORMULAS
from crypto_core import ensure_issuer_keypair, encrypt_payload, issue_license

def resource_path(relative: str) -> str:
    """Read-only bundled resources -- works both run directly and packaged
    by PyInstaller (files land under sys._MEIPASS at runtime)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Output goes to a normal writable user location, not next to this script --
# once packaged as a signed .app, the app's own bundle directory is
# read-only, so writing output there would silently fail.
OUT_DIR = os.path.expanduser("~/Documents/Faulter Software Packets")
os.makedirs(OUT_DIR, exist_ok=True)
TWIN_VIEWER_SRC = resource_path("twin_viewer_build")  # app shell + wireframe TEMPLATE, not a pre-built app

BG = "#0d131b"
PANEL = "#141c27"
FG = "#c9d6e4"
ACCENT = "#4fc3f7"
DIM = "#6d8199"
OK = "#5ec269"
WARN = "#e0a940"


def expand_instances(components: list) -> list:
    out = []
    for c in components:
        for i in range(1, c["instances_found"] + 1):
            out.append({"name": f"{c['name']}_{i}", "type": c["type"]})
    return out


class PacketBuilderApp:
    def __init__(self, root):
        self.root = root
        self.step_path = None
        root.title("Faulter AI -- Software Packet Builder")
        root.configure(bg=BG)
        root.geometry("640x560")

        tk.Label(root, text="FAULTER AI", bg=BG, fg="#ffffff",
                 font=("Menlo", 20, "bold")).pack(pady=(22, 0))
        tk.Label(root, text="Software Packet Builder  —  powered by Yanthros Core",
                 bg=BG, fg=DIM, font=("Menlo", 11)).pack(pady=(2, 20))

        form = tk.Frame(root, bg=BG)
        form.pack(fill="x", padx=30)

        self.client_var = tk.StringVar()
        self.machine_var = tk.StringVar()
        self._field(form, "Client name", self.client_var, 0)
        self._field(form, "Machine name", self.machine_var, 1)

        tk.Frame(root, bg=BG, height=14).pack()

        upload = tk.Frame(root, bg=PANEL, highlightbackground="#1d2836", highlightthickness=1)
        upload.pack(fill="x", padx=30, pady=6)
        self.file_label = tk.Label(upload, text="No STEP file selected", bg=PANEL, fg=DIM,
                                    font=("Menlo", 11), anchor="w")
        self.file_label.pack(side="left", padx=14, pady=14, fill="x", expand=True)
        tk.Button(upload, text="Choose STEP file...", command=self.choose_file,
                  bg="#16202c", fg=FG, activebackground=ACCENT, relief="flat",
                  font=("Menlo", 10), padx=10, pady=6).pack(side="right", padx=14)

        self.build_btn = tk.Button(root, text="Build Software Packet", command=self.build,
                                    bg=ACCENT, fg="#05080d", font=("Menlo", 12, "bold"),
                                    relief="flat", padx=10, pady=10, state="disabled")
        self.build_btn.pack(fill="x", padx=30, pady=(14, 6))

        self.download_btn = tk.Button(root, text="Download Executable App...", command=self.download_executable,
                                       bg=OK, fg="#05080d", font=("Menlo", 12, "bold"),
                                       relief="flat", padx=10, pady=10, state="disabled")
        self.download_btn.pack(fill="x", padx=30, pady=(0, 10))

        log_frame = tk.Frame(root, bg=PANEL, highlightbackground="#1d2836", highlightthickness=1)
        log_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        self.log = tk.Text(log_frame, bg=PANEL, fg=FG, insertbackground=FG,
                            font=("Menlo", 10), relief="flat", padx=12, pady=10, state="disabled")
        self.log.pack(fill="both", expand=True)
        self.log.tag_config("ok", foreground=OK)
        self.log.tag_config("warn", foreground=WARN)
        self.log.tag_config("dim", foreground=DIM)
        self.log.tag_config("accent", foreground=ACCENT)

    def _field(self, parent, label, var, row):
        tk.Label(parent, text=label, bg=BG, fg=DIM, font=("Menlo", 10)).grid(
            row=row, column=0, sticky="w", pady=4)
        tk.Entry(parent, textvariable=var, bg=PANEL, fg=FG, insertbackground=FG,
                 relief="flat", font=("Menlo", 11)).grid(
            row=row, column=1, sticky="ew", padx=(10, 0), pady=4, ipady=4)
        parent.columnconfigure(1, weight=1)

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="Select assembly STEP file",
            filetypes=[("STEP files", "*.step *.stp"), ("All files", "*.*")],
        )
        if path:
            self.step_path = path
            self.file_label.config(text=os.path.basename(path), fg=FG)
            self.build_btn.config(state="normal")

    def _say(self, text, tag=None):
        self.log.config(state="normal")
        self.log.insert("end", text + "\n", tag)
        self.log.config(state="disabled")
        self.log.see("end")
        self.root.update()
        time.sleep(0.35)  # paced so each stage is actually readable

    def build(self):
        client = self.client_var.get().strip() or "(unnamed client)"
        machine = self.machine_var.get().strip() or "(unnamed machine)"
        self.build_btn.config(state="disabled")
        self.log.config(state="normal"); self.log.delete("1.0", "end"); self.log.config(state="disabled")

        try:
            self._say(f"Client: {client}   Machine: {machine}", "dim")
            self._say(f"File: {os.path.basename(self.step_path)}", "dim")
            self._say("")

            self._say("[1/5] Parsing STEP geometry...", "accent")
            parsed = parse_step(self.step_path)
            self._say(f"      root product: {parsed['root_product']}")
            self._say(f"      {parsed['unique_part_types']} unique part types, {parsed['total_instances']} instances found", "ok")

            self._say("[2/5] Classifying components...", "accent")
            components = expand_instances(parsed["components"])
            for c in components:
                self._say(f"      {c['name']:20s} -> {c['type']}")
            unclassified = [c for c in parsed["components"] if c["type"] == "unclassified"]
            if unclassified:
                self._say(f"      {len(unclassified)} part(s) unrecognized -- excluded from formula selection", "warn")

            self._say("[3/5] Selecting formulas from the core engine...", "accent")
            subset = build_subset(machine, components)
            self._say(f"      domains identified: {', '.join(subset['domains_identified'])}")
            self._say(f"      {subset['formula_count']}", "ok")

            self._say("[4/5] Building the digital model...", "accent")
            self._say(f"      {len(subset['formulas'])} formulas stacked for this machine", "ok")

            self._say("[5/5] Encrypting and signing the software packet...", "accent")
            ensure_issuer_keypair()
            os.makedirs(OUT_DIR, exist_ok=True)
            safe_name = "".join(ch if ch.isalnum() else "_" for ch in machine)[:40] or "packet"
            plaintext = json.dumps(subset, indent=2).encode()
            aes_key = os.urandom(32)
            enc_path = os.path.join(OUT_DIR, f"{safe_name}.enc")
            lic_path = os.path.join(OUT_DIR, f"{safe_name}.lic")
            with open(enc_path, "wb") as f:
                f.write(encrypt_payload(plaintext, aes_key))
            with open(lic_path, "w") as f:
                f.write(issue_license(client, machine, aes_key, valid_days=150))
            self._say(f"      -> {enc_path}", "ok")
            self._say(f"      -> {lic_path}", "ok")

            self._say("")
            self._say("DONE. Click \"Download Executable App\" below to save the", "ok")
            self._say("standalone app your client actually installs.", "ok")
            self.last_machine_name = machine
            self.download_btn.config(state="normal")
        except Exception as e:
            self._say(f"\nFAILED: {e}", "warn")
            messagebox.showerror("Build failed", str(e))
        finally:
            self.build_btn.config(state="normal")

    def download_executable(self):
        default_name = f"{self.last_machine_name} - Faulter AI.app"
        save_path = filedialog.asksaveasfilename(
            title="Save Executable App",
            initialfile=default_name,
            defaultextension=".app",
            filetypes=[("Application", "*.app")],
        )
        if not save_path:
            return  # user cancelled

        self.download_btn.config(state="disabled")
        try:
            self._say("")
            self._say("Generating the executable app for THIS machine...", "accent")
            with tempfile.TemporaryDirectory() as stage:
                # stage a fresh copy of the app shell -- this run's machine
                # name gets baked into it, nothing pre-made is reused
                app_py = os.path.join(stage, "twin_viewer_app.py")
                assets_dir = os.path.join(stage, "assets")
                shutil.copy(os.path.join(TWIN_VIEWER_SRC, "twin_viewer_app.py"), app_py)
                shutil.copytree(os.path.join(TWIN_VIEWER_SRC, "assets"), assets_dir)

                html_path = os.path.join(assets_dir, "wireframe.html")
                with open(html_path) as f:
                    html = f.read()
                html = html.replace("{{MACHINE_NAME}}", self.last_machine_name)
                with open(html_path, "w") as f:
                    f.write(html)

                self._say(f"      baked in machine name: {self.last_machine_name}")
                self._say("      running PyInstaller (this takes 10-30s)...", "dim")

                app_name = "".join(ch if ch.isalnum() or ch in " -_" else "" for ch in self.last_machine_name)[:40] or "Faulter"
                result = subprocess.run(
                    [sys.executable, "-m", "PyInstaller", "--windowed", "--noconfirm",
                     "--name", app_name, "--add-data", f"{assets_dir}:assets", app_py],
                    cwd=stage, capture_output=True, text=True,
                )
                if result.returncode != 0:
                    raise RuntimeError(result.stderr[-800:])

                built_app = os.path.join(stage, "dist", f"{app_name}.app")
                if os.path.exists(save_path):
                    shutil.rmtree(save_path)
                shutil.copytree(built_app, save_path)

            self._say(f"      -> {save_path}", "ok")
            self._say("DONE. Fully independent -- double-click to open.", "ok")
            messagebox.showinfo("Saved", f"Saved to:\n{save_path}\n\nDouble-click it to open -- fully independent of this builder.")
        except Exception as e:
            self._say(f"\nFAILED to build executable: {e}", "warn")
            messagebox.showerror("Build failed", str(e))
        finally:
            self.download_btn.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    app = PacketBuilderApp(root)
    root.mainloop()
