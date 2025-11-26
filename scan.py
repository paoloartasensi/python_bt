"""
Bluetooth Device Scanner and Service Explorer
Scansiona dispositivi Bluetooth, effettua pairing e mostra servizi/caratteristiche
"""

import asyncio
from bleak import BleakScanner, BleakClient
import sys


async def scan_devices():
    """Scansiona tutti i dispositivi Bluetooth disponibili"""
    print("🔍 Scansione dispositivi Bluetooth in corso...")
    print("=" * 80)
    
    devices = await BleakScanner.discover(timeout=10.0)
    
    if not devices:
        print("❌ Nessun dispositivo trovato")
        return None
    
    print(f"\n✅ Trovati {len(devices)} dispositivi:\n")
    
    device_list = []
    for idx, device in enumerate(devices, 1):
        name = device.name if device.name else "Unknown"
        address = device.address
        rssi = device.rssi if hasattr(device, 'rssi') else "N/A"
        
        print(f"{idx:2d}. {name:30s} | {address:20s} | RSSI: {rssi}")
        device_list.append(device)
    
    print("=" * 80)
    return device_list


async def explore_services(device):
    """Esplora servizi e caratteristiche di un dispositivo"""
    print(f"\n🔗 Connessione a {device.name} ({device.address})...")
    
    try:
        async with BleakClient(device.address, timeout=15.0) as client:
            if not client.is_connected:
                print("❌ Impossibile connettersi al dispositivo")
                return
            
            print(f"✅ Connesso a {device.name}\n")
            print("=" * 80)
            print("📋 SERVIZI E CARATTERISTICHE")
            print("=" * 80)
            
            services = client.services
            
            for service in services:
                print(f"\n🔹 SERVICE: {service.uuid}")
                print(f"   Description: {service.description}")
                
                for char in service.characteristics:
                    properties = ", ".join(char.properties)
                    print(f"\n   ├─ CHARACTERISTIC: {char.uuid}")
                    print(f"   │  Description: {char.description}")
                    print(f"   │  Properties: {properties}")
                    print(f"   │  Handle: {char.handle}")
                    
                    # Mostra descriptors se presenti
                    if char.descriptors:
                        for desc in char.descriptors:
                            print(f"   │  └─ Descriptor: {desc.uuid} (Handle: {desc.handle})")
                    
                    # Prova a leggere il valore se la caratteristica è readable
                    if "read" in char.properties:
                        try:
                            value = await client.read_gatt_char(char.uuid)
                            print(f"   │  Value: {value.hex()} ({len(value)} bytes)")
                        except Exception as e:
                            print(f"   │  Value: [Cannot read: {str(e)[:40]}]")
            
            print("\n" + "=" * 80)
            print(f"✅ Esplorazione completata per {device.name}")
            print("=" * 80)
            
    except asyncio.TimeoutError:
        print("❌ Timeout durante la connessione")
    except Exception as e:
        print(f"❌ Errore: {e}")


async def main():
    """Funzione principale"""
    print("\n" + "=" * 80)
    print("🔵 BLUETOOTH DEVICE SCANNER & SERVICE EXPLORER")
    print("=" * 80 + "\n")
    
    # Scansiona dispositivi
    devices = await scan_devices()
    
    if not devices:
        return
    
    # Chiedi all'utente quale dispositivo esplorare
    print("\n💡 Inserisci il numero del dispositivo da esplorare (0 per uscire):")
    
    try:
        choice = input("Numero: ").strip()
        
        if choice == "0":
            print("👋 Uscita...")
            return
        
        device_num = int(choice)
        
        if device_num < 1 or device_num > len(devices):
            print("❌ Numero non valido")
            return
        
        selected_device = devices[device_num - 1]
        
        # Esplora servizi e caratteristiche
        await explore_services(selected_device)
        
    except ValueError:
        print("❌ Input non valido")
    except KeyboardInterrupt:
        print("\n\n👋 Interrotto dall'utente")
    except Exception as e:
        print(f"❌ Errore: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Programma terminato")
        sys.exit(0)
