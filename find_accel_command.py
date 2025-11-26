"""
Trova il comando corretto per attivare l'accelerometro
Prova diversi comandi su tutte le caratteristiche write
"""

import asyncio
from bleak import BleakClient, BleakScanner
import struct


# Caratteristiche WRITE per inviare comandi
WRITE_CHARS = {
    "ae01": "0000ae01-0000-1000-8000-00805f9b34fb",  # Vendor ae00 service
    "ae41": "0000ae41-0000-1000-8000-00805f9b34fb",  # Vendor ae40 service
    "f002": "f0020003-0451-4000-b000-000000000000",  # f002 service
    "f003": "f0030003-0451-4000-b000-000000000000",  # f003 service
    "f008": "f0080003-0451-4000-b000-000000000000",  # f008 service
}

# Caratteristiche NOTIFY per ricevere dati
NOTIFY_CHARS = {
    "ae02": "0000ae02-0000-1000-8000-00805f9b34fb",
    "ae42": "0000ae42-0000-1000-8000-00805f9b34fb",
    "f002": "f0020002-0451-4000-b000-000000000000",
    "f003": "f0030002-0451-4000-b000-000000000000",
    "f008": "f0080002-0451-4000-b000-000000000000",
}

# Comandi tipici per START accelerometro
START_COMMANDS = [
    ("Chileaf accel 0xFF 0x0C", bytes([0xFF, 0x0C])),  # PRIORITÀ 1
    ("Chileaf accel extended", bytes([0xFF, 0x0C, 0x01])),
    ("Simple 0x01", bytes([0x01])),
    ("Double 0x01", bytes([0x01, 0x01])),
    ("Start with header", bytes([0x11, 0x01, 0x01])),
    ("Cmd 0x02, sensor 0x01", bytes([0x02, 0x01])),
    ("Cmd 0x03, sensor 0x01", bytes([0x03, 0x01])),
    ("Enable all sensors", bytes([0x01, 0xFF])),
    ("Start stream", bytes([0xAA, 0x01])),
    ("Nordic start", bytes([0x01, 0x00, 0x01])),
    ("TI start", bytes([0x55, 0x01])),
    ("Full enable", bytes([0x01, 0x01, 0x01])),
]

# Counter per notifiche ricevute
notification_count = {}
received_data = {}


def notification_handler(uuid_short):
    """Crea handler per notifiche"""
    def handler(sender, data):
        if uuid_short not in notification_count:
            notification_count[uuid_short] = 0
            received_data[uuid_short] = []
        
        notification_count[uuid_short] += 1
        received_data[uuid_short].append(data)
        
        # Mostra solo prime 3 notifiche per non intasare
        if notification_count[uuid_short] <= 3:
            # Prova a parsare come accelerometro
            parsed = parse_accel(data)
            print(f"  📡 {uuid_short}: {parsed}")
    
    return handler


def parse_accel(data):
    """Prova a interpretare come dati accelerometro"""
    try:
        if len(data) == 6:  # 3x int16
            x, y, z = struct.unpack('<hhh', data)
            return f"3x int16: X={x:5d} Y={y:5d} Z={z:5d}"
        elif len(data) == 12:  # 3x float
            x, y, z = struct.unpack('<fff', data)
            return f"3x float: X={x:6.3f} Y={y:6.3f} Z={z:6.3f}"
        else:
            return f"HEX ({len(data)}B): {data.hex()}"
    except:
        return f"RAW ({len(data)}B): {data.hex()}"


async def test_commands(device_address="47:7C:8E:41:C6:34"):
    """Testa tutti i comandi su tutte le caratteristiche write"""
    print("=" * 80)
    print("🔍 RICERCA COMANDO START ACCELEROMETRO")
    print("=" * 80)
    print(f"🔗 Connessione a {device_address}...\n")
    
    async with BleakClient(device_address, timeout=15.0) as client:
        if not client.is_connected:
            print("❌ Connessione fallita")
            return
        
        print("✅ Connesso!\n")
        
        # Sottoscrivi a tutte le notify
        print("📋 Sottoscrizione a tutte le notify...")
        for name, uuid in NOTIFY_CHARS.items():
            try:
                await client.start_notify(uuid, notification_handler(name))
                print(f"  ✅ {name}: {uuid[:8]}...")
            except Exception as e:
                print(f"  ⚠️  {name}: {str(e)[:40]}")
        
        print("\n" + "=" * 80)
        print("🧪 TEST COMANDI")
        print("=" * 80)
        
        # Prova ogni comando su ogni caratteristica write
        for cmd_name, cmd_bytes in START_COMMANDS:
            print(f"\n🔧 Comando: {cmd_name} = {cmd_bytes.hex().upper()}")
            
            for write_name, write_uuid in WRITE_CHARS.items():
                try:
                    # Reset counters
                    notification_count.clear()
                    received_data.clear()
                    
                    # Invia comando
                    print(f"\n  → Invio a {write_name} ({write_uuid[:8]}...)...")
                    await client.write_gatt_char(write_uuid, cmd_bytes, response=False)
                    
                    # Aspetta 2 secondi per vedere se arrivano dati
                    await asyncio.sleep(2)
                    
                    # Verifica se sono arrivate notifiche
                    if notification_count:
                        print(f"\n  🎉 SUCCESSO! Ricevute notifiche:")
                        for notify_name, count in notification_count.items():
                            print(f"    ✅ {notify_name}: {count} pacchetti")
                        
                        print(f"\n  ⭐ COMANDO TROVATO!")
                        print(f"     Write UUID: {write_uuid}")
                        print(f"     Comando: {cmd_bytes.hex().upper()}")
                        print(f"     Notify UUID(s): {', '.join(notification_count.keys())}")
                        
                        # Mostra sample dei dati
                        for notify_name, packets in received_data.items():
                            if packets:
                                print(f"\n  📊 Sample dati da {notify_name}:")
                                for i, pkt in enumerate(packets[:3]):
                                    print(f"     {i+1}. {parse_accel(pkt)}")
                        
                        return  # Trovato! Esci
                    else:
                        print("    ❌ Nessuna risposta")
                    
                except Exception as e:
                    print(f"    ⚠️  Errore: {str(e)[:50]}")
        
        print("\n" + "=" * 80)
        print("❌ Nessun comando ha funzionato")
        print("=" * 80)
        
        # Unsubscribe
        for name, uuid in NOTIFY_CHARS.items():
            try:
                await client.stop_notify(uuid)
            except:
                pass


async def main():
    print("\n🔍 Ricerca VITRO...")
    devices = await BleakScanner.discover(timeout=10.0)
    
    device_address = None
    for device in devices:
        if device.name and "VITRO" in device.name.upper():
            print(f"✅ Trovato: {device.name} ({device.address})\n")
            device_address = device.address
            break
    
    if not device_address:
        print("⚠️  VITRO non trovato, uso indirizzo salvato\n")
        device_address = "47:7C:8E:41:C6:34"
    
    await test_commands(device_address)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrotto dall'utente")
