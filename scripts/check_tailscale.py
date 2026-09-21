"""
Personal Assistant AI - Tailscale Connectivity & Diagnostics Tool (Phase 16)
Validates Tailscale installation, extracts assigned 100.x.y.z IP, checks socket binding on 0.0.0.0:8000,
and verifies endpoint accessibility over the Tailscale interface.
"""

import subprocess
import socket
import sys
import json
import urllib.request
import urllib.error
import re
import os

def run_cmd(cmd: list) -> tuple[int, str]:
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        return res.returncode, res.stdout.strip()
    except Exception as e:
        return -1, str(e)

def find_tailscale_exe() -> str:
    # Check PATH
    code, out = run_cmd(["where", "tailscale"])
    if code == 0 and out:
        return out.splitlines()[0]
    
    # Check default install paths on Windows
    paths = [
        r"C:\Program Files\Tailscale\tailscale.exe",
        r"C:\Program Files (x86)\Tailscale\tailscale.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Tailscale\tailscale.exe")
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return ""

def get_tailscale_ip(tailscale_exe: str) -> str:
    if tailscale_exe:
        code, out = run_cmd([tailscale_exe, "ip", "-4"])
        if code == 0 and out:
            # First line is usually the ipv4
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("100."):
                    return line

    # Fallback to ipconfig
    code, out = run_cmd(["ipconfig"])
    if code == 0:
        lines = out.splitlines()
        in_tailscale = False
        for line in lines:
            if "tailscale" in line.lower():
                in_tailscale = True
            elif in_tailscale and "IPv4" in line:
                m = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
                if m:
                    return m.group(1)
            elif in_tailscale and line.strip() == "":
                in_tailscale = False
    return ""

def check_backend_socket(port: int = 8000) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.5)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except Exception:
        return False

def test_health_endpoint(ip: str, port: int = 8000) -> tuple[bool, str]:
    url = f"http://{ip}:{port}/health"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TailscaleCheck/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = resp.read().decode("utf-8")
            return True, data
    except urllib.error.URLError as e:
        return False, str(e.reason)
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print(" [TAILSCALE] Diagnóstico de Conectividad Remota - Fase 16")
    print("=" * 60)

    # 1. Check Tailscale CLI / Service
    ts_exe = find_tailscale_exe()
    if not ts_exe:
        print("[!] Tailscale no parece estar en PATH ni en Program Files.")
        print("    Asegúrate de haber completado la instalación de Tailscale.")
    else:
        print(f"[OK] Tailscale CLI encontrado: {ts_exe}")

    # 2. Extract Tailscale IP
    ts_ip = get_tailscale_ip(ts_exe)
    if ts_ip:
        print(f"[OK] IP de Tailscale de esta Laptop: {ts_ip}")
    else:
        print("[!] No se detectó una IP de Tailscale activa (rango 100.x.y.z).")
        print("    Verifica que Tailscale esté iniciado y con sesión activa (Connected).")

    # 3. Status of Peers
    if ts_exe:
        code, status_out = run_cmd([ts_exe, "status"])
        if code == 0:
            print("\n--- Nodos en tu red Tailnet ---")
            for line in status_out.splitlines()[:10]:
                print(f"  {line}")
            print("--------------------------------")
        else:
            print(f"[!] tailscale status devolvió código {code}: {status_out}")

    # 4. Check Backend process
    backend_running = check_backend_socket(8000)
    print("\n--- Estado del Backend (FastAPI / Uvicorn) ---")
    if backend_running:
        print("[OK] Backend escuchando en puerto 8000.")
        if ts_ip:
            ok, msg = test_health_endpoint(ts_ip, 8000)
            if ok:
                print(f"[OK] Acceso exitoso a http://{ts_ip}:8000/health:")
                print(f"     Respuesta: {msg}")
            else:
                print(f"[!] No se pudo conectar a través de la IP de Tailscale ({ts_ip}:8000): {msg}")
                print("    Verifica el Firewall de Windows en el puerto 8000.")
    else:
        print("[INFO] El backend FastAPI no está corriendo actualmente en el puerto 8000.")
        print("       Inícialo con: python run.py")

    print("=" * 60)
    if ts_ip:
        print("CONFIGURACIÓN LISTA PARA EL MÓVIL:")
        print(f"  URL Backend: http://{ts_ip}:8000")
        print(f"  Health check: http://{ts_ip}:8000/health")
        print("=" * 60)

if __name__ == "__main__":
    main()
