#!/usr/bin/env python3
"""
Scanner BLE Universale
Scansiona TUTTI i dispositivi Bluetooth Low Energy nelle vicinanze
"""
import asyncio
from bleak import BleakScanner
from datetime import datetime


async def scan_all_devices():
    print("\n" + "="*70)
    print("🔵 SCANNER BLE UNIVERSALE")
    print("="*70)
    print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🔍 Scansione in corso (20 secondi)...")
    print("   Accendi/muovi i dispositivi BLE che vuoi trovare\n")
    
    devices_found = {}
    
    def detection_callback(device, advertisement_data):
        """Callback chiamato per ogni dispositivo trovato"""
        addr = device.address
        if addr not in devices_found:
            name = device.name or advertisement_data.local_name or "(senza nome)"
            rssi = advertisement_data.rssi
            devices_found[addr] = {
                'name': name,
                'rssi': rssi,
                'adv': advertisement_data
            }
            print(f"   📡 Trovato: {name} [{addr}] RSSI: {rssi} dBm")
    
    # Crea scanner con callback
    scanner = BleakScanner(detection_callback=detection_callback)
    
    try:
        await scanner.start()
        await asyncio.sleep(20)  # Scansione per 20 secondi
        await scanner.stop()
    except Exception as e:
        print(f"\n❌ Errore durante scansione: {e}")
        return
    
    # Riepilogo finale
    print("\n" + "="*70)
    print(f"📊 RIEPILOGO: {len(devices_found)} dispositivi trovati")
    print("="*70)
    
    if not devices_found:
        print("\n❌ Nessun dispositivo BLE rilevato!")
        print("\n🔧 Possibili soluzioni:")
        print("   1. Verifica permessi: Impostazioni → Privacy → Bluetooth")
        print("   2. Aggiungi Terminal.app alle app autorizzate")
        print("   3. Riavvia il Bluetooth (spegni e riaccendi)")
        print("   4. Riavvia il Mac")
    else:
        # Ordina per RSSI (segnale più forte prima)
        sorted_devices = sorted(devices_found.items(), 
                               key=lambda x: x[1]['rssi'], 
                               reverse=True)
        
        print(f"\n{'Nome':<30} {'Indirizzo':<20} {'RSSI':<10} {'Servizi'}")
        print("-"*70)
        
        for addr, info in sorted_devices:
            name = info['name'][:28] if len(info['name']) > 28 else info['name']
            rssi = f"{info['rssi']} dBm"
            
            # Conta servizi
            services = info['adv'].service_uuids or []
            svc_count = f"{len(services)} servizi" if services else "-"
            
            print(f"{name:<30} {addr:<20} {rssi:<10} {svc_count}")
        
        # Cerca dispositivi CL837/CL831
        cl_devices = [d for d in devices_found.values() 
                      if d['name'] and ('CL837' in d['name'] or 'CL831' in d['name'])]
        
        if cl_devices:
            print(f"\n🎯 Trovato dispositivo CL837/CL831!")
            print("   Puoi eseguire: python sleep/sleep.py")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(scan_all_devices())
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrotto dall'utente")
    except Exception as e:
        print(f"\n❌ Errore: {e}")
