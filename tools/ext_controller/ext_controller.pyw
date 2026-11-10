#!/usr/bin/env python3
"""
EXT Controller — External Background Process & Windows Startup Manager
Author: Arush Sengar (Omni Homelab & Workstation Controller)
Enables 1-click detection, inspection, termination, and autostart lockout
for external background tools, rogue daemons (Hermes, OmniRoute, Node/Python background jobs),
and 3rd-party startup software.
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

import psutil
try:
    import winreg
except ImportError:
    winreg = None

# Colors & Theming (Modern Slate Dark Theme)
BG_DARK = "#0f172a"        # Slate 900
BG_PANEL = "#1e293b"       # Slate 800
BG_HOVER = "#334155"       # Slate 700
BORDER_COLOR = "#475569"   # Slate 600
TEXT_MAIN = "#f8fafc"      # Slate 50
TEXT_MUTED = "#94a3b8"     # Slate 400
ACCENT_BLUE = "#38bdf8"    # Sky 400
ACCENT_GREEN = "#10b981"   # Emerald 500
ACCENT_RED = "#ef4444"     # Rose 500
ACCENT_ORANGE = "#f59e0b"  # Amber 500
FONT_FAMILY = "Segoe UI"

STARTUP_USER = Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup"
STARTUP_USER_DISABLED = Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup_Disabled"
STARTUP_COMMON = Path(os.environ.get("PROGRAMDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup"
STARTUP_COMMON_DISABLED = Path(os.environ.get("PROGRAMDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup_Disabled"

SYSTEM_PROC_NAMES = {
    "system", "system idle process", "registry", "smss.exe", "csrss.exe", "wininit.exe",
    "services.exe", "lsass.exe", "svchost.exe", "fontdrvhost.exe", "dwm.exe", "explorer.exe",
    "taskhostw.exe", "runtimebroker.exe", "searchhost.exe", "shellexperiencehost.exe",
    "startmenuexperiencehost.exe", "sihost.exe", "ctfmon.exe", "conhost.exe", "spoolsv.exe",
    "dashost.exe", "securityhealthservice.exe", "sgrmbroker.exe", "searchindexer.exe",
    "audiodg.exe", "smartscreen.exe", "wudfhost.exe", "compattelrunner.exe", "textinputhost.exe",
    "lockapp.exe", "useroobebroker.exe", "dllhost.exe", "wmiapsrv.exe", "msmpeng.exe", "nissrv.exe"
}

KNOWN_EXTERNAL_KEYWORDS = [
    "hermes", "omniroute", "ghost", "netcut", "anydesk", "lghub", "memreduct",
    "discord", "roblox", "steam", "wispr", "gemini", "asc", "iobit", "python", "node"
]


class ExtControllerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EXT Controller — Process & Autostart Manager")
        self.root.geometry("1100x720")
        self.root.minsize(920, 600)
        self.root.configure(bg=BG_DARK)

        # Style Configuration
        self.setup_styles()

        # Data Caches
        self.processes = []
        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.filter_var = tk.StringVar(value="external")
        self.search_var = tk.StringVar(value="")
        self.search_var.trace_add("write", lambda *args: self.filter_and_render_processes())

        # Header Banner
        self.build_header()

        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(6, 8))

        # Tab 1: Running Processes
        self.tab_proc = ttk.Frame(self.notebook, style="Dark.TFrame")
        self.notebook.add(self.tab_proc, text="  ⚡ Background & External Processes  ")
        self.build_processes_tab()

        # Tab 2: Windows Startup Manager
        self.tab_startup = ttk.Frame(self.notebook, style="Dark.TFrame")
        self.notebook.add(self.tab_startup, text="  🚀 Windows Startup Manager  ")
        self.build_startup_tab()

        # Tab 3: Open Network Ports
        self.tab_ports = ttk.Frame(self.notebook, style="Dark.TFrame")
        self.notebook.add(self.tab_ports, text="  🌐 Active Network Ports  ")
        self.build_ports_tab()

        # Bottom Status Bar
        self.build_status_bar()

        # Initial Load
        self.refresh_all()
        self.schedule_auto_refresh()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Dark.TFrame", background=BG_DARK)
        style.configure("Panel.TFrame", background=BG_PANEL)

        style.configure(
            "TNotebook",
            background=BG_DARK,
            borderwidth=0
        )
        style.configure(
            "TNotebook.Tab",
            background=BG_PANEL,
            foreground=TEXT_MUTED,
            font=(FONT_FAMILY, 10, "bold"),
            padding=[16, 7],
            borderwidth=0
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", BG_HOVER), ("active", BORDER_COLOR)],
            foreground=[("selected", ACCENT_BLUE), ("active", TEXT_MAIN)]
        )

        style.configure(
            "Treeview",
            background=BG_PANEL,
            foreground=TEXT_MAIN,
            fieldbackground=BG_PANEL,
            rowheight=28,
            font=(FONT_FAMILY, 9),
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background=BG_HOVER,
            foreground=TEXT_MAIN,
            font=(FONT_FAMILY, 9, "bold"),
            padding=6,
            relief="flat"
        )
        style.map(
            "Treeview",
            background=[("selected", "#1e3a8a")],
            foreground=[("selected", "#ffffff")]
        )
        style.map(
            "Treeview.Heading",
            background=[("active", BORDER_COLOR)]
        )

    def build_header(self):
        header_frame = tk.Frame(self.root, bg=BG_PANEL, height=56)
        header_frame.pack(fill="x", padx=14, pady=(12, 6))

        title_lbl = tk.Label(
            header_frame,
            text="⚡ EXT Controller",
            font=(FONT_FAMILY, 15, "bold"),
            fg=ACCENT_BLUE,
            bg=BG_PANEL
        )
        title_lbl.pack(side="left", padx=14, pady=10)

        subtitle_lbl = tk.Label(
            header_frame,
            text="Identify, End Task & Lockout Rogue Background Tools & Autostart Daemons",
            font=(FONT_FAMILY, 9),
            fg=TEXT_MUTED,
            bg=BG_PANEL
        )
        subtitle_lbl.pack(side="left", pady=12)

        # Quick Kill-Switch Buttons in Header
        kill_hermes_btn = tk.Button(
            header_frame,
            text="🛑 Stop All Hermes & Omni",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#ffffff",
            bg=ACCENT_RED,
            activebackground="#b91c1c",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.kill_all_hermes
        )
        kill_hermes_btn.pack(side="right", padx=(6, 14), pady=10)

        lock_startup_btn = tk.Button(
            header_frame,
            text="🚫 Disable Hermes Autostart",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#ffffff",
            bg=ACCENT_ORANGE,
            activebackground="#d97706",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.disable_all_hermes_startup
        )
        lock_startup_btn.pack(side="right", padx=6, pady=10)

    # -------------------------------------------------------------
    # TAB 1: RUNNING PROCESSES
    # -------------------------------------------------------------
    def build_processes_tab(self):
        # Controls Bar
        ctrl_frame = tk.Frame(self.tab_proc, bg=BG_DARK)
        ctrl_frame.pack(fill="x", pady=(8, 6))

        # Search Bar
        tk.Label(ctrl_frame, text="🔍 Search:", font=(FONT_FAMILY, 9, "bold"), fg=TEXT_MUTED, bg=BG_DARK).pack(side="left")
        search_entry = tk.Entry(
            ctrl_frame,
            textvariable=self.search_var,
            font=(FONT_FAMILY, 9),
            bg=BG_PANEL,
            fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN,
            relief="flat",
            width=24
        )
        search_entry.pack(side="left", padx=(6, 14), ipady=3)

        # Filter Options
        tk.Label(ctrl_frame, text="Filter:", font=(FONT_FAMILY, 9, "bold"), fg=TEXT_MUTED, bg=BG_DARK).pack(side="left")
        filter_cb = ttk.Combobox(
            ctrl_frame,
            textvariable=self.filter_var,
            values=[
                "external",
                "hermes_only",
                "high_ram",
                "all"
            ],
            state="readonly",
            width=18
        )
        filter_cb.pack(side="left", padx=(6, 14))
        filter_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_and_render_processes())

        # Auto-refresh checkbox
        chk_auto = tk.Checkbutton(
            ctrl_frame,
            text="Live Auto-Refresh (3s)",
            variable=self.auto_refresh_var,
            font=(FONT_FAMILY, 9),
            fg=TEXT_MAIN,
            bg=BG_DARK,
            selectcolor=BG_PANEL,
            activebackground=BG_DARK,
            activeforeground=TEXT_MAIN
        )
        chk_auto.pack(side="left", padx=10)

        # Action Buttons
        btn_refresh = tk.Button(
            ctrl_frame,
            text="🔄 Refresh",
            font=(FONT_FAMILY, 9, "bold"),
            fg=TEXT_MAIN,
            bg=BG_HOVER,
            activebackground=BORDER_COLOR,
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.refresh_processes
        )
        btn_refresh.pack(side="right", padx=(6, 0))

        btn_end = tk.Button(
            ctrl_frame,
            text="🛑 End Task",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#ffffff",
            bg=ACCENT_RED,
            activebackground="#b91c1c",
            relief="flat",
            padx=14,
            pady=3,
            cursor="hand2",
            command=self.kill_selected_process
        )
        btn_end.pack(side="right", padx=6)

        # Process Treeview Table
        tree_container = tk.Frame(self.tab_proc, bg=BG_PANEL)
        tree_container.pack(fill="both", expand=True)

        cols = ("category", "name", "pid", "ram", "cpu", "path", "cmdline")
        self.proc_tree = ttk.Treeview(tree_container, columns=cols, show="headings", selectmode="browse")

        self.proc_tree.heading("category", text="Category")
        self.proc_tree.heading("name", text="Process Name")
        self.proc_tree.heading("pid", text="PID")
        self.proc_tree.heading("ram", text="RAM (MB)")
        self.proc_tree.heading("cpu", text="CPU %")
        self.proc_tree.heading("path", text="Executable Path")
        self.proc_tree.heading("cmdline", text="Command Line")

        self.proc_tree.column("category", width=130, anchor="w")
        self.proc_tree.column("name", width=170, anchor="w")
        self.proc_tree.column("pid", width=70, anchor="center")
        self.proc_tree.column("ram", width=90, anchor="e")
        self.proc_tree.column("cpu", width=70, anchor="e")
        self.proc_tree.column("path", width=260, anchor="w")
        self.proc_tree.column("cmdline", width=340, anchor="w")

        # Scrollbar
        sb_y = ttk.Scrollbar(tree_container, orient="vertical", command=self.proc_tree.yview)
        self.proc_tree.configure(yscrollcommand=sb_y.set)
        self.proc_tree.pack(side="left", fill="both", expand=True)
        sb_y.pack(side="right", fill="y")

        # Treeview Tag Styling for Colors
        self.proc_tree.tag_configure("hermes", foreground=ACCENT_RED, background="#2d1217")
        self.proc_tree.tag_configure("external", foreground=ACCENT_ORANGE, background=BG_PANEL)
        self.proc_tree.tag_configure("runtime", foreground=ACCENT_BLUE, background=BG_PANEL)
        self.proc_tree.tag_configure("system", foreground=TEXT_MUTED, background=BG_PANEL)

        # Double click to kill
        self.proc_tree.bind("<Double-1>", lambda e: self.kill_selected_process())

    # -------------------------------------------------------------
    # TAB 2: STARTUP MANAGER
    # -------------------------------------------------------------
    def build_startup_tab(self):
        ctrl_frame = tk.Frame(self.tab_startup, bg=BG_DARK)
        ctrl_frame.pack(fill="x", pady=(8, 6))

        tk.Label(
            ctrl_frame,
            text="Manage all items that launch automatically when Windows boots or logs in.",
            font=(FONT_FAMILY, 9),
            fg=TEXT_MUTED,
            bg=BG_DARK
        ).pack(side="left")

        btn_toggle = tk.Button(
            ctrl_frame,
            text="⚡ Toggle Enable / Disable",
            font=(FONT_FAMILY, 9, "bold"),
            fg=TEXT_MAIN,
            bg=ACCENT_BLUE,
            activebackground="#0284c7",
            relief="flat",
            padx=12,
            pady=3,
            cursor="hand2",
            command=self.toggle_selected_startup_item
        )
        btn_toggle.pack(side="right", padx=(6, 0))

        btn_refresh_st = tk.Button(
            ctrl_frame,
            text="🔄 Refresh",
            font=(FONT_FAMILY, 9, "bold"),
            fg=TEXT_MAIN,
            bg=BG_HOVER,
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.refresh_startup_items
        )
        btn_refresh_st.pack(side="right", padx=6)

        # Startup Treeview Table
        tree_container = tk.Frame(self.tab_startup, bg=BG_PANEL)
        tree_container.pack(fill="both", expand=True)

        cols = ("status", "name", "location", "command")
        self.startup_tree = ttk.Treeview(tree_container, columns=cols, show="headings", selectmode="browse")

        self.startup_tree.heading("status", text="Status")
        self.startup_tree.heading("name", text="Program / Script Name")
        self.startup_tree.heading("location", text="Registry / Folder Location")
        self.startup_tree.heading("command", text="Command / Target Path")

        self.startup_tree.column("status", width=110, anchor="center")
        self.startup_tree.column("name", width=220, anchor="w")
        self.startup_tree.column("location", width=240, anchor="w")
        self.startup_tree.column("command", width=480, anchor="w")

        sb_y = ttk.Scrollbar(tree_container, orient="vertical", command=self.startup_tree.yview)
        self.startup_tree.configure(yscrollcommand=sb_y.set)
        self.startup_tree.pack(side="left", fill="both", expand=True)
        sb_y.pack(side="right", fill="y")

        self.startup_tree.tag_configure("active", foreground=ACCENT_GREEN)
        self.startup_tree.tag_configure("disabled", foreground=TEXT_MUTED)
        self.startup_tree.tag_configure("danger", foreground=ACCENT_RED)

    # -------------------------------------------------------------
    # TAB 3: NETWORK PORTS
    # -------------------------------------------------------------
    def build_ports_tab(self):
        ctrl_frame = tk.Frame(self.tab_ports, bg=BG_DARK)
        ctrl_frame.pack(fill="x", pady=(8, 6))

        tk.Label(
            ctrl_frame,
            text="Inspect listening TCP/UDP ports to catch background servers & hidden proxies.",
            font=(FONT_FAMILY, 9),
            fg=TEXT_MUTED,
            bg=BG_DARK
        ).pack(side="left")

        btn_kill_port = tk.Button(
            ctrl_frame,
            text="🛑 Kill Process on Selected Port",
            font=(FONT_FAMILY, 9, "bold"),
            fg="#ffffff",
            bg=ACCENT_RED,
            activebackground="#b91c1c",
            relief="flat",
            padx=12,
            pady=3,
            cursor="hand2",
            command=self.kill_selected_port_process
        )
        btn_kill_port.pack(side="right", padx=(6, 0))

        btn_refresh_p = tk.Button(
            ctrl_frame,
            text="🔄 Refresh",
            font=(FONT_FAMILY, 9, "bold"),
            fg=TEXT_MAIN,
            bg=BG_HOVER,
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.refresh_ports
        )
        btn_refresh_p.pack(side="right", padx=6)

        tree_container = tk.Frame(self.tab_ports, bg=BG_PANEL)
        tree_container.pack(fill="both", expand=True)

        cols = ("port", "protocol", "pid", "name", "address", "path")
        self.ports_tree = ttk.Treeview(tree_container, columns=cols, show="headings", selectmode="browse")

        self.ports_tree.heading("port", text="Port")
        self.ports_tree.heading("protocol", text="Proto")
        self.ports_tree.heading("pid", text="PID")
        self.ports_tree.heading("name", text="Process Name")
        self.ports_tree.heading("address", text="Local IP Address")
        self.ports_tree.heading("path", text="Executable Path")

        self.ports_tree.column("port", width=90, anchor="center")
        self.ports_tree.column("protocol", width=70, anchor="center")
        self.ports_tree.column("pid", width=80, anchor="center")
        self.ports_tree.column("name", width=180, anchor="w")
        self.ports_tree.column("address", width=150, anchor="w")
        self.ports_tree.column("path", width=460, anchor="w")

        sb_y = ttk.Scrollbar(tree_container, orient="vertical", command=self.ports_tree.yview)
        self.ports_tree.configure(yscrollcommand=sb_y.set)
        self.ports_tree.pack(side="left", fill="both", expand=True)
        sb_y.pack(side="right", fill="y")

    # -------------------------------------------------------------
    # STATUS BAR
    # -------------------------------------------------------------
    def build_status_bar(self):
        self.status_bar = tk.Frame(self.root, bg=BG_PANEL, height=26)
        self.status_bar.pack(fill="x", side="bottom")

        self.status_lbl = tk.Label(
            self.status_bar,
            text="Ready. Initializing scan...",
            font=(FONT_FAMILY, 9),
            fg=TEXT_MUTED,
            bg=BG_PANEL
        )
        self.status_lbl.pack(side="left", padx=14, pady=3)

        self.ram_lbl = tk.Label(
            self.status_bar,
            text="RAM: --",
            font=(FONT_FAMILY, 9),
            fg=TEXT_MUTED,
            bg=BG_PANEL
        )
        self.ram_lbl.pack(side="right", padx=14, pady=3)

    # -------------------------------------------------------------
    # SCANNING & REFRESH LOGIC
    # -------------------------------------------------------------
    def refresh_all(self):
        self.refresh_processes()
        self.refresh_startup_items()
        self.refresh_ports()

    def schedule_auto_refresh(self):
        if self.auto_refresh_var.get():
            self.refresh_processes()
        self.root.after(3000, self.schedule_auto_refresh)

    def refresh_processes(self):
        """Scans all running processes and categorizes them."""
        procs = []
        try:
            for p in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'memory_info', 'cpu_percent']):
                try:
                    info = p.info
                    name = info.get('name') or "Unknown"
                    pid = info.get('pid') or 0
                    exe = info.get('exe') or ""
                    cmd_list = info.get('cmdline') or []
                    cmdline = " ".join(cmd_list) if cmd_list else ""
                    mem_mb = (info.get('memory_info').rss / (1024 * 1024)) if info.get('memory_info') else 0
                    cpu = info.get('cpu_percent') or 0.0

                    lower_name = name.lower()
                    lower_cmd = cmdline.lower()
                    lower_exe = exe.lower()

                    # Categorize
                    is_hermes = (
                        "hermes" in lower_name or "omniroute" in lower_name or
                        "hermes" in lower_cmd or "omniroute" in lower_cmd or
                        ".hermes" in lower_cmd or ".hermes" in lower_exe or
                        "hermes_pc_hub" in lower_cmd
                    )

                    is_system = lower_name in SYSTEM_PROC_NAMES or r"\windows\system32" in lower_exe

                    is_known_external = any(k in lower_name or k in lower_cmd for k in KNOWN_EXTERNAL_KEYWORDS)

                    is_runtime = lower_name in ["python.exe", "pythonw.exe", "node.exe", "pwsh.exe"]

                    if is_hermes:
                        category = "🔴 HERMES / OMNI"
                        tag = "hermes"
                    elif is_known_external:
                        category = "🟠 EXTERNAL TOOL"
                        tag = "external"
                    elif is_runtime:
                        category = "🟡 RUNTIME / SCRIPT"
                        tag = "runtime"
                    elif is_system:
                        category = "⚪ WINDOWS SYSTEM"
                        tag = "system"
                    else:
                        category = "USER APPLICATION"
                        tag = "external"

                    procs.append({
                        "category": category,
                        "tag": tag,
                        "name": name,
                        "pid": pid,
                        "ram": mem_mb,
                        "cpu": cpu,
                        "path": exe,
                        "cmdline": cmdline,
                        "is_hermes": is_hermes,
                        "is_system": is_system
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.set_status(f"Process scan error: {e}")

        # Sort by RAM descending
        procs.sort(key=lambda x: x["ram"], reverse=True)
        self.processes = procs
        self.filter_and_render_processes()

    def filter_and_render_processes(self):
        """Renders filtered processes into the Treeview table."""
        # Clear existing
        for item in self.proc_tree.get_children():
            self.proc_tree.delete(item)

        flt = self.filter_var.get()
        search = self.search_var.get().strip().lower()

        count = 0
        total_ram = 0

        for p in self.processes:
            # Apply Filter
            if flt == "hermes_only" and not p["is_hermes"]:
                continue
            if flt == "external" and p["is_system"]:
                continue
            if flt == "high_ram" and p["ram"] < 100.0:
                continue

            # Apply Search
            if search:
                haystack = f"{p['name']} {p['pid']} {p['path']} {p['cmdline']}".lower()
                if search not in haystack:
                    continue

            count += 1
            total_ram += p["ram"]

            self.proc_tree.insert(
                "",
                "end",
                iid=str(p["pid"]),
                values=(
                    p["category"],
                    p["name"],
                    p["pid"],
                    f"{p['ram']:.1f}",
                    f"{p['cpu']:.1f}",
                    p["path"],
                    p["cmdline"]
                ),
                tags=(p["tag"],)
            )

        vmem = psutil.virtual_memory()
        self.ram_lbl.config(text=f"Total RAM: {vmem.used // (1024*1024)}MB / {vmem.total // (1024*1024)}MB ({vmem.percent}%)")
        self.set_status(f"Displaying {count} processes ({total_ram:.1f} MB tracked) | Filter: {flt.upper()}")

    # -------------------------------------------------------------
    # KILLING PROCESSES
    # -------------------------------------------------------------
    def kill_selected_process(self):
        selected = self.proc_tree.selection()
        if not selected:
            messagebox.showinfo("Select Process", "Please click on a process from the table first.")
            return

        pid_str = selected[0]
        try:
            pid = int(pid_str)
        except ValueError:
            return

        proc_item = next((p for p in self.processes if p["pid"] == pid), None)
        pname = proc_item["name"] if proc_item else f"PID {pid}"

        confirm = messagebox.askyesno(
            "Confirm End Task",
            f"Are you sure you want to terminate:\n\n{pname} (PID: {pid})?"
        )
        if not confirm:
            return

        try:
            p = psutil.Process(pid)
            p.kill()
            self.set_status(f"✅ Successfully terminated {pname} (PID {pid})")
        except Exception as e:
            # Fallback to taskkill /F
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            self.set_status(f"Dispatched taskkill for PID {pid}")

        time.sleep(0.3)
        self.refresh_processes()

    def kill_all_hermes(self):
        """Immediately terminates all Hermes, OmniRoute, and associated rogue daemons."""
        killed = []
        for p in self.processes:
            if p["is_hermes"]:
                try:
                    proc = psutil.Process(p["pid"])
                    proc.kill()
                    killed.append(f"{p['name']} ({p['pid']})")
                except Exception:
                    subprocess.run(["taskkill", "/F", "/PID", str(p["pid"])], capture_output=True)
                    killed.append(f"{p['name']} ({p['pid']})")

        if killed:
            messagebox.showinfo("Hermes Services Stopped", f"Terminated {len(killed)} Hermes/Omni processes:\n\n" + "\n".join(killed))
        else:
            messagebox.showinfo("Hermes Status", "No active Hermes or Omni processes found running on desktop.")
        self.refresh_processes()

    # -------------------------------------------------------------
    # STARTUP ITEMS SCAN & MANAGEMENT
    # -------------------------------------------------------------
    def refresh_startup_items(self):
        for item in self.startup_tree.get_children():
            self.startup_tree.delete(item)

        items = []

        # 1. User Startup Folder (Active)
        if STARTUP_USER.exists():
            for f in STARTUP_USER.iterdir():
                if f.is_file() and not f.name.startswith("desktop.ini"):
                    items.append({
                        "name": f.name,
                        "location": "Startup Folder (User)",
                        "path": str(f),
                        "status": "ACTIVE",
                        "tag": "danger" if "hermes" in f.name.lower() or "omni" in f.name.lower() else "active",
                        "type": "file"
                    })

        # 2. User Startup Folder (Disabled)
        if STARTUP_USER_DISABLED.exists():
            for f in STARTUP_USER_DISABLED.iterdir():
                if f.is_file() and not f.name.startswith("desktop.ini"):
                    items.append({
                        "name": f.name,
                        "location": "Startup_Disabled (User)",
                        "path": str(f),
                        "status": "DISABLED",
                        "tag": "disabled",
                        "type": "file_disabled"
                    })

        # 3. All Users Startup Folder
        if STARTUP_COMMON.exists():
            for f in STARTUP_COMMON.iterdir():
                if f.is_file() and not f.name.startswith("desktop.ini"):
                    items.append({
                        "name": f.name,
                        "location": "Startup Folder (All Users)",
                        "path": str(f),
                        "status": "ACTIVE",
                        "tag": "active",
                        "type": "file"
                    })

        # 4. Registry HKCU Run
        if winreg:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        val_name, val_data, _ = winreg.EnumValue(key, i)
                        is_disabled = val_name.startswith("_DISABLED_")
                        clean_name = val_name.replace("_DISABLED_", "")
                        items.append({
                            "name": clean_name,
                            "location": "Registry (HKCU Run)",
                            "path": val_data,
                            "status": "DISABLED" if is_disabled else "ACTIVE",
                            "tag": "disabled" if is_disabled else "active",
                            "type": "reg_hkcu",
                            "raw_name": val_name
                        })
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except Exception:
                pass

        # Populate table
        for idx, itm in enumerate(items):
            self.startup_tree.insert(
                "",
                "end",
                iid=f"st_{idx}",
                values=(
                    itm["status"],
                    itm["name"],
                    itm["location"],
                    itm["path"]
                ),
                tags=(itm["tag"],)
            )

        self._cached_startup_items = items

    def toggle_selected_startup_item(self):
        sel = self.startup_tree.selection()
        if not sel:
            messagebox.showinfo("Select Item", "Please click on a startup entry to enable/disable.")
            return

        idx = int(sel[0].replace("st_", ""))
        item = self._cached_startup_items[idx]

        src_path = Path(item["path"])
        itype = item["type"]

        if itype == "file":
            # Disable by moving to Startup_Disabled
            dest_dir = STARTUP_USER_DISABLED
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / src_path.name
            try:
                shutil.move(str(src_path), str(dest_file))
                messagebox.showinfo("Disabled", f"Disabled '{item['name']}' from autostart.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to disable: {e}")

        elif itype == "file_disabled":
            # Enable by moving back to Startup
            dest_dir = STARTUP_USER
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / src_path.name
            try:
                shutil.move(str(src_path), str(dest_file))
                messagebox.showinfo("Enabled", f"Enabled '{item['name']}' for autostart.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to enable: {e}")

        elif itype == "reg_hkcu":
            raw_name = item["raw_name"]
            is_currently_disabled = raw_name.startswith("_DISABLED_")
            new_name = raw_name.replace("_DISABLED_", "") if is_currently_disabled else f"_DISABLED_{raw_name}"

            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, raw_name)
                winreg.SetValueEx(key, new_name, 0, winreg.REG_SZ, item["path"])
                winreg.CloseKey(key)
                action = "Enabled" if is_currently_disabled else "Disabled"
                messagebox.showinfo(action, f"{action} registry startup entry for '{item['name']}'.")
            except Exception as e:
                messagebox.showerror("Error", f"Registry update failed: {e}")

        self.refresh_startup_items()

    def disable_all_hermes_startup(self):
        """Moves any Hermes or Omni scripts out of Startup into Startup_Disabled."""
        STARTUP_USER_DISABLED.mkdir(parents=True, exist_ok=True)
        count = 0
        if STARTUP_USER.exists():
            for f in STARTUP_USER.iterdir():
                if ("hermes" in f.name.lower() or "omni" in f.name.lower()) and f.is_file():
                    try:
                        shutil.move(str(f), str(STARTUP_USER_DISABLED / f.name))
                        count += 1
                    except Exception:
                        pass

        messagebox.showinfo(
            "Autostart Lockout",
            f"Locked out {count} Hermes/Omni startup scripts.\nThey will NOT execute when desktop starts up."
        )
        self.refresh_startup_items()

    # -------------------------------------------------------------
    # NETWORK PORTS MANAGEMENT
    # -------------------------------------------------------------
    def refresh_ports(self):
        for item in self.ports_tree.get_children():
            self.ports_tree.delete(item)

        port_records = []
        try:
            conns = psutil.net_connections(kind='inet')
            for c in conns:
                if c.status == psutil.CONN_LISTEN:
                    pid = c.pid or 0
                    pname = "Unknown"
                    pexe = ""
                    if pid:
                        try:
                            p = psutil.Process(pid)
                            pname = p.name()
                            pexe = p.exe()
                        except Exception:
                            pass
                    port_records.append({
                        "port": c.laddr.port,
                        "proto": "TCP" if c.type == 1 else "UDP",
                        "pid": pid,
                        "name": pname,
                        "address": c.laddr.ip,
                        "path": pexe
                    })
        except Exception as e:
            self.set_status(f"Port scan error: {e}")

        port_records.sort(key=lambda x: x["port"])
        self._cached_ports = port_records

        for idx, r in enumerate(port_records):
            self.ports_tree.insert(
                "",
                "end",
                iid=f"port_{idx}",
                values=(
                    r["port"],
                    r["proto"],
                    r["pid"],
                    r["name"],
                    r["address"],
                    r["path"]
                )
            )

    def kill_selected_port_process(self):
        sel = self.ports_tree.selection()
        if not sel:
            messagebox.showinfo("Select Port", "Please select a port from the table first.")
            return

        idx = int(sel[0].replace("port_", ""))
        rec = self._cached_ports[idx]
        pid = rec["pid"]
        if not pid:
            messagebox.showwarning("System Process", "This port belongs to a kernel/system process that cannot be killed.")
            return

        confirm = messagebox.askyesno(
            "Kill Process on Port",
            f"Terminate process '{rec['name']}' (PID: {pid}) listening on port {rec['port']}?"
        )
        if confirm:
            try:
                psutil.Process(pid).kill()
                messagebox.showinfo("Terminated", f"Process on port {rec['port']} terminated.")
            except Exception as e:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            self.refresh_ports()
            self.refresh_processes()

    def set_status(self, msg: str):
        self.status_lbl.config(text=f"[{time.strftime('%H:%M:%S')}] {msg}")


def main():
    root = tk.Tk()
    app = ExtControllerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

