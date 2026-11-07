# 💻 Hermes Laptop Worker Node & Master Mesh Setup

This document records the architecture and connection between the **Raspberry Pi Master Hub (`192.168.0.100`)** and the **Windows 11 Laptop Worker Node (`192.168.0.101`)**.

---

## 🏗️ Architecture Overview

```
                      +---------------------------------------+
                      |   Raspberry Pi 4 (192.168.0.100)      |
                      |   Master Hub & Autonomous Brain       |
                      +---------------------------------------+
                                          |
                +-------------------------+-------------------------+
                |                                                   |
      HTTP :8642 (Hermes Peer API)                         HTTP :8643 (Fast Worker Bridge)
                |                                                   |
                +-------------------------+-------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |   Windows 11 Laptop (192.168.0.101)   |
                      |   - Hermes Gateway Daemon (:8642)     |
                      |   - Ultra-Fast Bridge Daemon (:8643)  |
                      |   - Interactive GUI (WinSta0\Default) |
                      |   - Chrome & Screen Automation        |
                      |   - Audio Synthesis (SAPI.SpVoice)    |
                      +---------------------------------------+
```

---

## ⚡ The 5 Core Control Primitives (Raspberry Pi -> Laptop)

On the Raspberry Pi, Hermes has 5 first-class workstation tools in `/home/arush/bin/` and skill `laptop-computer-control`:

1. `laptop-status`: Reads live battery, RAM, CPU, screen resolution, and session state in <400ms.
2. `laptop-screen "<cmd>" [title]`: Launches any app or document visibly in the foreground on `WinSta0\Default` with TopMost priority.
3. `laptop-speak "<text>"`: Speaks out loud through the laptop's speakers in real time.
4. `laptop-browser "<url>"`: Launches Google Chrome on the laptop screen with specific URLs.
5. `laptop-exec "<cmd>"`: Runs any shell or PowerShell commands on the laptop and streams back output.

---

## 🔧 Service Configuration

- **Hermes Gateway Port**: TCP `8642`
- **Fast Bridge Port**: TCP `8643`
- **Authentication**: Bearer Token `sk-laptop-hermes-token-2026`
- **Startup Script**: `C:\Users\Arush\AppData\Local\hermes\gateway-service\Hermes_Gateway.cmd`
- **Auto-Start**: Windows Startup item (`Hermes_Gateway.vbs`) starts automatically on Windows user login.
