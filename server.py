#!/usr/bin/env python3

import asyncio
import serial
import serial.tools.list_ports
import websockets
import json
import argparse
import sys
import os
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

# ── Ayarlar ───────────────────────────────────────────────
SERIAL_PORT  = "COM12"   
DEFAULT_BAUD = 115200
WS_HOST      = "127.0.0.1"
WS_PORT      = 8765
HTTP_PORT    = 8080
# ──────────────────────────────────────────────────────────

connected_clients = set()

def find_esp_port():
    """ESP32'yi otomatik bul"""
    ports = serial.tools.list_ports.comports()
    for p in ports:
        desc = (p.description or "").lower()
        if any(k in desc for k in ["cp210", "ch340", "usb serial", "uart", "esp"]):
            return p.device
    if ports:
        return ports[0].device
    return None

async def broadcast(message: str):
    """Tüm bağlı WebSocket istemcilerine gönder"""
    if connected_clients:
        await asyncio.gather(
            *[client.send(message) for client in connected_clients],
            return_exceptions=True
        )

async def serial_reader(port: str, baud: int):
    """Serial portu oku, parse et, WebSocket'e gönder"""
    print(f"[Serial] {port} portuna bağlanılıyor ({baud} baud)...")
    
    while True:
        try:
            ser = serial.Serial(port, baud, timeout=1)
            print(f"[Serial] Bağlandı: {port}")
            
            await broadcast(json.dumps({"type": "status", "serial": "connected", "port": port}))
            
            loop = asyncio.get_event_loop()
            
            while True:
                line = await loop.run_in_executor(None, ser.readline)
                if not line:
                    continue
                
                try:
                    text = line.decode("utf-8").strip()
                except UnicodeDecodeError:
                    continue
                
                if not text:
                    continue

                # SD kayıt bildirimi: SD_OK,node_id
                if text.startswith("SD_OK,"):
                    try:
                        sd_node = int(text.split(",")[1])
                        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        await broadcast(json.dumps({
                            "type":    "sd_log",
                            "node_id": sd_node,
                            "time":    now
                        }))
                        print(f"[SD] Node {sd_node} kaydedildi @ {now}")
                    except (ValueError, IndexError):
                        pass
                    continue

                # Merkez formatı: node_id,doluluk,alarm  (3 sütun)
                parts = text.split(",")
                if len(parts) != 3:
                    continue
                
                try:
                    node_id     = int(parts[0])
                    doluluk_pct = float(parts[1])
                    alarm       = int(parts[2])
                except ValueError:
                    continue

                # Geçerlilik kontrolü — bozuk paketleri reddet
                if node_id < 1 or node_id > 10:
                    print(f"[Drop] Geçersiz node_id: {node_id} (raw: {text})")
                    continue
                if doluluk_pct < -10 or doluluk_pct > 200:
                    print(f"[Drop] Geçersiz doluluk: {doluluk_pct} (raw: {text})")
                    continue

                # Yüzdeyi 0-100 arası sınırlandır
                doluluk_pct = max(0, min(100, doluluk_pct))
                
                now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                payload = json.dumps({
                    "type":        "data",
                    "node_id":     node_id,
                    "doluluk_pct": doluluk_pct,
                    "alarm":       alarm,
                    "time":        now,
                    "raw":         text
                })
                
                await broadcast(payload)
                print(f"[Data] Node {node_id} → {doluluk_pct}% alarm={alarm} @ {now}")
                
        except serial.SerialException as e:
            print(f"[Serial] Hata: {e}. 3 saniye sonra yeniden deneniyor...")
            await broadcast(json.dumps({"type": "status", "serial": "disconnected"}))
            await asyncio.sleep(3)
        except Exception as e:
            print(f"[Serial] Beklenmeyen hata: {e}")
            await asyncio.sleep(3)

async def ws_handler(websocket):
    """Yeni WebSocket bağlantısı"""
    connected_clients.add(websocket)
    addr = websocket.remote_address
    print(f"[WS] İstemci bağlandı: {addr} (toplam: {len(connected_clients)})")
    
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.discard(websocket)
        print(f"[WS] İstemci ayrıldı: {addr} (toplam: {len(connected_clients)})")

def start_http_server():
    """index.html'i servis eden basit HTTP sunucusu (ayrı thread)"""
    script_dir = os.path.dirname(os.path.abspath(__file__))

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=script_dir, **kwargs)
        def log_message(self, fmt, *args):
            pass  # HTTP loglarını sustur

    httpd = HTTPServer((WS_HOST, HTTP_PORT), Handler)
    print(f"[HTTP] Dashboard: http://{WS_HOST}:{HTTP_PORT}/index.html")
    httpd.serve_forever()

async def main(port: str, baud: int):
    # HTTP sunucusunu ayrı thread'de başlat
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    print(f"""
╔══════════════════════════════════════════╗
║   ESP32-S3 WebSocket Bridge              ║
║   Serial : {port:<30}║
║   WS     : ws://{WS_HOST}:{WS_PORT:<21}║
║   HTTP   : http://{WS_HOST}:{HTTP_PORT:<19}║
╚══════════════════════════════════════════╝
""")
    
    ws_server = await websockets.serve(ws_handler, WS_HOST, WS_PORT)
    print(f"[WS] Sunucu başladı: ws://{WS_HOST}:{WS_PORT}")
    
    await asyncio.gather(
        ws_server.wait_closed(),
        serial_reader(port, baud)
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ESP32 Serial → WebSocket Bridge")
    parser.add_argument("--port", default=None,         help="Serial port (örn: COM12 veya /dev/ttyUSB0)")
    parser.add_argument("--baud", default=DEFAULT_BAUD, type=int, help="Baud rate")
    args = parser.parse_args()

    port = args.port or SERIAL_PORT or find_esp_port()
    if not port:
        print("[Hata] Serial port bulunamadı. SERIAL_PORT sabitini veya --port argümanını kullanın.")
        sys.exit(1)

    try:
        asyncio.run(main(port, args.baud))
    except KeyboardInterrupt:
        print("\n[Çıkış] Sunucu kapatıldı.")
