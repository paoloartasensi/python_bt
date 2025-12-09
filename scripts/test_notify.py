"""
Test Notify - Sottoscrivi a TUTTE le caratteristiche notify e stampa i dati
Per trovare quale caratteristica è l'accelerometro
"""

import asyncio
from bleak import BleakClient, BleakScanner
import struct


# UUID delle caratteristiche notify trovate su VITRO
NOTIFY_CHARS = [
    "0000ae02-0000-1000-8000-00805f9b34fb",  # Vendor ae00 service
    "0000ae42-0000-1000-8000-00805f9b34fb",  # Vendor ae40 service
    "f0020002-0451-4000-b000-000000000000",  # f002 service
    "f0030002-0451-4000-b000-000000000000",  # f003 service
    "f0080002-0451-4000-b000-000000000000",  # f008 service
    "0000fec8-0000-1000-8000-00805f9b34fb",  # fee7 service (indicate)
    "0000fea1-0000-1000-8000-00805f9b34fb",  # fee7 service
]


def parse_accel_data(data):
    """Prova a interpretare i dati come accelerometro"""
    try:
        # Prova vari formati comuni per accelerometro
        formats = [
            ('3 float (12 bytes)', '<fff', 12),      # 3 float little-endian
            ('3 int16 (6 bytes)', '<hhh', 6),        # 3 int16 little-endian
            ('3 int16 BE (6 bytes)', '>hhh', 6),     # 3 int16 big-endian
            ('6 int16 (12 bytes)', '<hhhhhh', 12),   # 6 int16 (accel + gyro?)
        ]
        
        for name, fmt, size in formats:
            if len(data) == size:
                values = struct.unpack(fmt, data)
                return f"{name}: {values}"
        
        # Se non matcha, stampa hex
        return f"HEX ({len(data)} bytes): {data.hex()}"
    except:
        return f"RAW ({len(data)} bytes): {data.hex()}"


async def notification_handler(uuid):
    """Crea un handler per le notifiche di una caratteristica specifica"""
    def handler(sender, data):
        parsed = parse_accel_data(data)
        print(f"📡 {uuid[:8]}... | {parsed}")
    return handler


async def test_all_notify(device_address="47:7C:8E:41:C6:34"):
    """Connetti e sottoscrivi a tutte le caratteristiche notify"""
    print("=" * 80)
    print("🔵 TEST NOTIFY - Trova l'accelerometro")
    print("=" * 80)
    print(f"🔗 Connessione a {device_address}...\n")
    
    async with BleakClient(device_address, timeout=15.0) as client:
        if not client.is_connected:
            print("❌ Connessione fallita")
            return
        
        print("✅ Connesso!\n")
        print("📋 Sottoscrizione alle caratteristiche notify:")
        print("-" * 80)
        
        # Sottoscrivi a tutte le notify
        subscribed = []
        for uuid in NOTIFY_CHARS:
            try:
                handler = await notification_handler(uuid)
                await client.start_notify(uuid, handler)
                print(f"✅ Sottoscritto a {uuid}")
                subscribed.append(uuid)
            except Exception as e:
                print(f"⚠️  Impossibile sottoscrivere a {uuid}: {str(e)[:50]}")
        
        if not subscribed:
            print("\n❌ Nessuna sottoscrizione riuscita")
            return
        
        print("\n" + "=" * 80)
        print("📡 RICEZIONE DATI (premi Ctrl+C per fermare)")
        print("=" * 80)
        print("Cerca pattern tipo: (X, Y, Z) con valori ~±1.0g quando fermo")
        print("o valori ~±2000 se sono int16 raw\n")
        
        # Ricevi dati per 30 secondi
        try:
            await asyncio.sleep(30)
        except KeyboardInterrupt:
            print("\n\n⏸️  Interrotto dall'utente")
        
        # Unsubscribe
        print("\n" + "=" * 80)
        print("🛑 Chiusura sottoscrizioni...")
        for uuid in subscribed:
            try:
                await client.stop_notify(uuid)
            except:
                pass
        
        print("✅ Disconnesso")


async def find_device():
    """Cerca il dispositivo VITRO"""
    print("🔍 Ricerca VITRO...")
    devices = await BleakScanner.discover(timeout=10.0)
    
    for device in devices:
        if device.name and "VITRO" in device.name.upper():
            print(f"✅ Trovato: {device.name} ({device.address})")
            return device.address
    
    # Se non trovato, usa l'indirizzo hardcoded
    print("⚠️  VITRO non trovato, uso indirizzo salvato")
    return "47:7C:8E:41:C6:34"


async def main():
    device_address = await find_device()
    await test_all_notify(device_address)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Programma terminato")
