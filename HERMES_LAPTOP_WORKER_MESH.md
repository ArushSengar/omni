# 🌐 Hermes Master-Worker Mesh Architecture
**Raspberry Pi 4 (Master Node) ↔ Windows 11 Laptop (Worker Node)**

---

## 📌 Architecture Overview

```
                      +---------------------------------------+
                      |       Raspberry Pi 4 (Master)         |
                      |           192.168.0.100               |
                      |                                       |
                      |  - Omni Master Hub (:8000)            |
                      |  - OmniRoute AI Router (:20128)       |
                      |  - 24/7 System Cron & Sentinels       |
                      |  - Master Hermes Agent                |
                      +-------------------+-------------------+
                                          |
                        Hermes Bot-to-Bot Peer Protocol
                           (TCP :8642 + Bearer Auth)
                                          |
                      +-------------------v-------------------+
                      |      Windows 11 Laptop (Worker)       |
                      |           192.168.0.101               |
                      |                                       |
                      |  - Hermes Gateway Daemon (:8642)      |
                      |  - Local Execution Tools & Terminal   |
                      |  - Computer Use (cua-driver)          |
                      |  - High-Performance Workload Runner   |
                      +---------------------------------------+
```

---

## 🚀 Key Capabilities

1. **24/7 Autonomous Control**:
   - The Raspberry Pi remains powered on 24/7 as the coordinator, scheduler, and central intelligence gateway.
   - When heavy tasks, desktop automation, or Windows-specific jobs need to be run, the Pi delegates them to the Laptop Worker Node.

2. **Native Hermes Peer Protocol (`hermes peer`)**:
   - Bot-to-Bot DM turns: `hermes peer dm laptop "<instruction>"`
   - Long-running async execution: `echo "<task>" | hermes peer run laptop`
   - Real-time status checks: `hermes peer status laptop <run_id>`

3. **Omni Master Hub Dashboard Integration**:
   - Single-pane view at `http://192.168.0.100:8000`.
   - **Laptop Worker Node Card**: Real-time status, health ping, and connectivity metrics.
   - **Command & Task Dispatcher**: 1-click execution console for instant dispatch to the Windows laptop.

4. **Zero-Paid AI Inference Routing**:
   - Both the Pi Master and Laptop Worker query OmniRoute on `http://192.168.0.100:20128/v1`.
   - Models: `hermes-brain` (Claude 3.7 Sonnet) and `hermes-fast` (Gemini 2.5 Flash).
   - Zero API subscription fees.

---

## 🔧 Worker Node Service Configuration

- **API Server Port**: TCP `8642`
- **Authentication**: Bearer Token stored in `~/.hermes/.env` (`API_SERVER_KEY`)
- **Startup Script**: `C:\Users\Arush\AppData\Local\hermes\gateway-service\Hermes_Gateway.cmd`
- **Auto-Start**: Windows Startup item (`Hermes_Gateway.vbs`) starts automatically on Windows user login.
