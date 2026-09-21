# Specification: Phase 16 — Tailscale Remote Connectivity

## 1. Scope & Objectives
Configure and establish secure remote access between the mobile device (Android) and the backend laptop via Tailscale's encrypted mesh VPN (WireGuard), allowing full functionality of the personal assistant over cellular mobile data without opening public router ports or exposing sensitive services to the public internet.

### Problem Definition
In development and local testing, the mobile app communicates with FastAPI via local Wi-Fi LAN IP (`192.168.40.15:8000`). However, when the user leaves the home Wi-Fi or uses mobile cellular data (4G/5G), the local LAN IP is unreachable. Exposing the backend port publicly via port-forwarding on a residential router poses significant security hazards (DDoS, port scanning, credential stuffing). Tailscale provides an encrypted, authenticated point-to-point overlay network (CGNAT `100.64.0.0/10`) that works transparently across NATs and firewalls.

### Non-Goals
- Opening router public WAN ports (Port Forwarding / DMZ).
- Using public reverse proxies (ngrok, cloudflare tunnels with public URLs) that expose internal endpoints without device-level mutual authentication.

---

## 2. System Topology & Flow

```
[ ANDROID PHONE (Mobile Data: 4G / 5G / LTE) ]
       │
       ▼ (Tailscale App: Connected)
[ TAILSCALE OVERLAY NETWORK (WireGuard Mesh: 100.x.y.z) ]
       │
       ▼ (Zero Public Ports / End-to-End Encrypted)
[ LAPTOP (Windows) - TAILSCALE ADAPTER: 100.x.y.w ]
       │
       ▼ (Bound to 0.0.0.0:8000)
[ FASTAPI BACKEND (Uvicorn) ]
       │
       ├─► /health
       ├─► /chat
       ├─► /db/status
       └─► /webhooks/bank
```

---

## 3. Contracts & Technical Requirements

### A. Network & Host Binding Contract
- **Backend Host Binding**: `backend/app/core/config.py` MUST maintain `HOST = "0.0.0.0"`.
  - Binding to `0.0.0.0` ensures the socket automatically listens on loopback (`127.0.0.1`), Wi-Fi adapter (`192.168.x.x`), and Tailscale adapter (`100.x.y.z`).
- **Windows Firewall Rule**:
  - Inbound rule allowing TCP port 8000 for private and domain network profiles, or specifically scoped to the Tailscale network interface / CGNAT range (`100.64.0.0/10`).
- **Security Invariant**:
  - No UPnP, no router WAN port mapping, no public IP binding.

### B. Mobile App Client Contract
- **URL Configuration (`src/config/index.ts` & `mobile/src/config/index.ts`)**:
  - Define `DEFAULT_TAILSCALE_IP` alongside `DEFAULT_LAN_IP`.
  - Provide quick-switch helpers for the active backend base URL.
- **Diagnostic Screen (`ConnectionDiagnosticScreen.tsx`)**:
  - Add single-tap presets:
    - `[🏠 Wi-Fi Local]` (`http://192.168.40.15:8000`)
    - `[🔒 Tailscale]` (`http://100.x.y.z:8000`)
  - Persist the selected URL in `AsyncStorage` (`STORAGE_KEYS.BACKEND_URL`).
  - Run the 3-step end-to-end diagnostic suite (Backend Liveness, DB Status, LLM Chat) across the Tailscale link to prove zero-regression connectivity.

---

## 4. Acceptance Criteria & Scenarios (Gherkin)

### Scenario 1: Tailscale Node Registration & IP Assignment
- **Given** Tailscale is installed and authenticated on both the Windows laptop and the Android phone
- **When** the Tailscale service is started on both devices
- **Then** both devices appear in the user's Tailscale Admin Console and receive dedicated 100.x.y.z IPv4 addresses
- **And** the laptop's Tailscale IP responds to ICMP ping from the phone's Tailscale client.

### Scenario 2: Backend Accessibility over Mobile Data
- **Given** the mobile phone has Wi-Fi turned OFF and Mobile Data (4G/5G) turned ON
- **And** the Tailscale VPN toggle is active on the mobile phone
- **When** the phone sends an HTTP GET request to `http://<laptop-tailscale-ip>:8000/health`
- **Then** the backend responds with HTTP 200 `{"status": "ok"}` without any Wi-Fi connection.

### Scenario 3: In-App Diagnostics & Feature Execution over Tailscale
- **Given** the mobile app is opened on the phone with cellular data and Tailscale active
- **When** the user taps the `[🔒 Tailscale]` preset in `ConnectionDiagnosticScreen` and runs full diagnostics
- **Then** all three tests (Backend, Database, Agent Chat) pass with green checks and measured latency
- **And** the user can send voice/text messages to the Secretary and Financial agents with full response delivery.

---

## 5. Impacted Components

1. **Host Setup**:
   - Install Tailscale on Windows host (`winget install Tailscale.Tailscale`).
   - Configure Windows Defender Firewall rule for port 8000.
2. **Mobile Configuration**:
   - `src/config/index.ts` & `mobile/src/config/index.ts`: Add Tailscale configuration constants.
   - `src/screens/ConnectionDiagnosticScreen.tsx` & `mobile/src/screens/ConnectionDiagnosticScreen.tsx`: Add quick switch buttons for LAN vs Tailscale.
3. **Helper Tooling**:
   - `backend/check_tailscale.py` (or powershell script): Diagnostic script to check Tailscale IP, verify binding, and test local accessibility.
4. **Documentation**:
   - `AGENTS.md` and walkthrough updates.
