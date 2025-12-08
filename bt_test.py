#!/usr/bin/env python3
"""Test diagnostico Bluetooth"""
import asyncio
from bleak import BleakScanner

async def test():
    print("Test 1: Verifica inizializzazione scanner...")
    try:
        scanner = BleakScanner()
        print("✅ Scanner inizializzato correttamente")
    except Exception as e:
        print(f"❌ Errore inizializzazione: {e}")
        return
    
    print("\nTest 2: Scansione estesa (15 secondi)...")
    print("   👉 Muovi/tocca il dispositivo CL837 se lo hai vicino\n")
    
    try:
        devices = await BleakScanner.discover(timeout=15.0, return_adv=True)
        
        print(f"\n📊 Trovati {len(devices)} dispositivi:\n")
        
        if len(devices) == 0:
            print("❌ NESSUN dispositivo BLE rilevato!")
            print("\nPossibili cause:")
            print("  1. Nessun dispositivo BLE attivo nelle vicinanze")
            print("  2. Permessi Bluetooth non concessi a Terminal/VS Code")
            print("  3. Problema hardware Bluetooth")
            print("\n👉 Vai in: Impostazioni Sistema → Privacy e Sicurezza → Bluetooth")
            print("   e assicurati che Terminal sia autorizzato")
        else:
            for addr, (device, adv) in devices.items():
                name = device.name or adv.local_name or "(senza nome)"
                print(f"  • {name}")
                print(f"    Indirizzo: {addr}")
                print(f"    RSSI: {adv.rssi} dBm")
                print()
                
    except Exception as e:
        print(f"❌ Errore durante scansione: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
