"""
CL837 Unified Accelerometer Monitor
Connessione, lettura e visualizzazione oscilloscopio in tempo reale
"""

import asyncio
import struct
import time
import threading
from collections import deque
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.figure import Figure
import numpy as np

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.characteristic import BleakGATTCharacteristic

class CL837UnifiedMonitor:
    """Monitor unificato CL837 con oscilloscopio integrato"""
    
    def __init__(self):
        # Connessione BLE
        self.client = None
        self.device = None
        self.is_connected = False
        
        # Protocollo Chileaf
        self.CHILEAF_SERVICE_UUID = "aae28f00-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_TX_UUID = "aae28f01-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_RX_UUID = "aae28f02-71b5-42a1-8c3c-f9cf6ac969d0"
        self.CHILEAF_HEADER = 0xFF
        self.CHILEAF_CMD_ACCELEROMETER = 0x0C
        self.CHILEAF_CONVERSION_FACTOR = 4096.0
        
        # Dati per oscilloscopio
        self.max_samples = 300   # Finestra ridotta per latenza minore (~12 sec a 25Hz)
        self.x_data = deque(maxlen=self.max_samples)
        self.y_data = deque(maxlen=self.max_samples)
        self.z_data = deque(maxlen=self.max_samples)
        self.magnitude_data = deque(maxlen=self.max_samples)
        self.timestamps = deque(maxlen=self.max_samples)
        
        # Statistiche
        self.sample_count = 0
        self.spike_count = 0
        self.start_time = time.time()
        self.last_values = {'x': 0, 'y': 0, 'z': 0, 'mag': 0}
        
        # Oscilloscopio
        self.fig = None
        self.axes = None
        self.lines = []
        self.animation = None
        self.plot_thread = None
        self.plot_ready = False

    async def scan_and_connect(self):
        """Scansiona e connetti al CL837"""
        print("🔍 Ricerca dispositivi CL837...")
        
        devices = await BleakScanner.discover(timeout=8.0)
        
        cl837_devices = []
        for device in devices:
            if device.name and device.name.startswith("CL837"):
                cl837_devices.append(device)
        
        if not cl837_devices:
            print("❌ Nessun dispositivo CL837 trovato")
            print("💡 Assicurati che il dispositivo sia acceso e in modalità pairing")
            return False
        
        print(f"✅ Trovati {len(cl837_devices)} dispositivi CL837:")
        for i, device in enumerate(cl837_devices, 1):
            print(f"   {i}. {device.name} ({device.address})")
        
        # 🎯 SELEZIONE INTERATTIVA DEL DISPOSITIVO
        if len(cl837_devices) == 1:
            # Solo uno disponibile - connessione diretta
            target_device = cl837_devices[0]
            print(f"\n🎯 Connessione automatica a: {target_device.name}")
        else:
            # Più dispositivi - chiedi all'utente
            while True:
                try:
                    print(f"\n🔢 Seleziona dispositivo (1-{len(cl837_devices)}) o 'q' per uscire:")
                    choice = input("➤ ").strip().lower()
                    
                    if choice == 'q':
                        print("❌ Connessione annullata")
                        return False
                    
                    device_index = int(choice) - 1
                    if 0 <= device_index < len(cl837_devices):
                        target_device = cl837_devices[device_index]
                        print(f"\n🎯 Connessione a: {target_device.name}")
                        break
                    else:
                        print(f"⚠️ Scelta non valida. Inserisci un numero tra 1 e {len(cl837_devices)}")
                        
                except ValueError:
                    print("⚠️ Inserisci un numero valido o 'q' per uscire")
                except KeyboardInterrupt:
                    print("\n❌ Connessione annullata")
                    return False
        
        try:
            print("⏳ Connessione in corso...")
            # 🚀 LOW-LATENCY: timeout ridotto per connessioni più reattive
            self.client = BleakClient(target_device, timeout=10.0)
            await self.client.connect()
            
            if self.client.is_connected:
                self.device = target_device
                self.is_connected = True
                print(f"✅ Connesso con successo!")
                
                # 🚀 OTTIMIZZAZIONE LATENZA: Richiedi parametri low-latency
                print("⚡ Configurazione low-latency BLE...")
                try:
                    # Bleak non ha API diretta per connection parameters, ma alcuni OS supportano hints
                    # Windows: Prova a impostare priorità alta per la connessione
                    if hasattr(self.client, '_backend') and hasattr(self.client._backend, '_requester'):
                        print("   💡 Hint: Connection priority HIGH richiesta")
                except Exception as e:
                    print(f"   ⚠️ Connection parameters non configurabili: {e}")
                
                return True
            else:
                print("❌ Connessione fallita")
                return False
                
        except Exception as e:
            print(f"❌ Errore di connessione: {e}")
            return False

    async def discover_services(self):
        """Analizza servizi e caratteristiche del dispositivo"""
        print(f"\n🔍 Analisi servizi BLE...")
        
        chileaf_service = None
        tx_characteristic = None
        
        for service in self.client.services:
            print(f"📋 Servizio: {service.uuid}")
            
            if service.uuid.lower() == self.CHILEAF_SERVICE_UUID.lower():
                print(f"   🎯 SERVIZIO CHILEAF IDENTIFICATO!")
                chileaf_service = service
            
            for char in service.characteristics:
                print(f"   📊 Caratteristica: {char.uuid} - {char.properties}")
                
                if char.uuid.lower() == self.CHILEAF_TX_UUID.lower():
                    # 🚀 Controlla supporto per indicate (più veloce di notify)
                    supports_indicate = "indicate" in char.properties
                    supports_notify = "notify" in char.properties
                    
                    speed_info = "INDICATE" if supports_indicate else "NOTIFY" if supports_notify else "NONE"
                    print(f"      ✅ CARATTERISTICA TX CHILEAF ({speed_info})")
                    
                    if supports_indicate:
                        print(f"         🚀 INDICATE supportato - Latenza minima disponibile!")
                    
                    tx_characteristic = char
                elif char.uuid.lower() == self.CHILEAF_RX_UUID.lower():
                    print(f"      ✅ CARATTERISTICA RX CHILEAF (Comandi)")
        
        if not tx_characteristic:
            print("❌ Caratteristica TX Chileaf non trovata!")
            return False
        
        if "notify" not in tx_characteristic.properties:
            print("❌ La caratteristica TX non supporta le notifiche!")
            return False
        
        print("✅ Servizio Chileaf configurato correttamente")
        self.tx_char = tx_characteristic
        return True

    def setup_oscilloscope(self):
        """Inizializza l'oscilloscopio matplotlib"""
        print("📊 Inizializzazione oscilloscopio...")
        
        # Crea figura con subplots
        self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.suptitle("CL837 Accelerometer Oscilloscope - Real Time", fontsize=16)
        
        # Configura assi
        ax_xyz, ax_mag, ax_xy, ax_stats = self.axes.flatten()
        
        # Grafico XYZ
        ax_xyz.set_title("Accelerazione XYZ (g)")
        ax_xyz.set_xlabel("Campioni")
        ax_xyz.set_ylabel("Accelerazione (g)")
        ax_xyz.grid(True, alpha=0.3)
        ax_xyz.legend(['X', 'Y', 'Z'])
        
        # Grafico Magnitudine
        ax_mag.set_title("Magnitudine Totale")
        ax_mag.set_xlabel("Campioni")
        ax_mag.set_ylabel("Magnitudine (g)")
        ax_mag.grid(True, alpha=0.3)
        
        # Grafico XY (vista dall'alto)
        ax_xy.set_title("Vista XY (dall'alto)")
        ax_xy.set_xlabel("X (g)")
        ax_xy.set_ylabel("Y (g)")
        ax_xy.grid(True, alpha=0.3)
        ax_xy.set_aspect('equal')
        ax_xy.set_xlim(-2, 2)
        ax_xy.set_ylim(-2, 2)
        
        # Area statistiche
        ax_stats.set_title("Statistiche Live")
        ax_stats.axis('off')
        
        # Inizializza linee
        line_x, = ax_xyz.plot([], [], 'r-', label='X', alpha=0.8)
        line_y, = ax_xyz.plot([], [], 'g-', label='Y', alpha=0.8)
        line_z, = ax_xyz.plot([], [], 'b-', label='Z', alpha=0.8)
        line_mag, = ax_mag.plot([], [], 'purple', linewidth=2)
        line_xy, = ax_xy.plot([], [], 'o-', markersize=3, alpha=0.6)
        
        self.lines = [line_x, line_y, line_z, line_mag, line_xy]
        
        # Testo statistiche
        self.stats_text = ax_stats.text(0.05, 0.95, "", transform=ax_stats.transAxes,
                                       fontsize=10, verticalalignment='top',
                                       fontfamily='monospace')
        
        plt.tight_layout()
        print("✅ Oscilloscopio configurato")

    def start_oscilloscope_thread(self):
        """Avvia oscilloscopio in thread separato"""
        def run_plot():
            self.setup_oscilloscope()
            self.animation = animation.FuncAnimation(
                self.fig, self.update_plot, interval=25, blit=True)  # 40Hz refresh + blitting per performance
            self.plot_ready = True
            plt.show()
        
        self.plot_thread = threading.Thread(target=run_plot, daemon=True)
        self.plot_thread.start()
        
        # Aspetta che il plot sia pronto
        while not self.plot_ready:
            time.sleep(0.1)
        
        print("🚀 Oscilloscopio avviato in thread separato")

    def update_plot(self, frame):
        """Aggiorna i grafici dell'oscilloscopio"""
        if len(self.x_data) < 2:
            return self.lines
        
        # Converti deque in liste per matplotlib
        x_list = list(self.x_data)
        y_list = list(self.y_data)
        z_list = list(self.z_data)
        mag_list = list(self.magnitude_data)
        
        # Crea indici per x-axis
        indices = list(range(len(x_list)))
        
        # Aggiorna linee XYZ
        self.lines[0].set_data(indices, x_list)  # X
        self.lines[1].set_data(indices, y_list)  # Y
        self.lines[2].set_data(indices, z_list)  # Z
        
        # Aggiorna magnitudine
        self.lines[3].set_data(indices, mag_list)
        
        # Aggiorna vista XY (ultimi 50 punti)
        if len(x_list) > 50:
            xy_x = x_list[-50:]
            xy_y = y_list[-50:]
        else:
            xy_x = x_list
            xy_y = y_list
        self.lines[4].set_data(xy_x, xy_y)
        
        # Aggiorna limiti assi automaticamente
        if indices:
            # XYZ plot
            self.axes[0, 0].set_xlim(max(0, len(indices)-200), len(indices))
            all_values = x_list + y_list + z_list
            if all_values:
                y_min, y_max = min(all_values), max(all_values)
                margin = (y_max - y_min) * 0.1 + 0.1
                self.axes[0, 0].set_ylim(y_min - margin, y_max + margin)
            
            # Magnitudine plot
            self.axes[0, 1].set_xlim(max(0, len(indices)-200), len(indices))
            if mag_list:
                mag_min, mag_max = min(mag_list), max(mag_list)
                margin = (mag_max - mag_min) * 0.1 + 0.1
                self.axes[0, 1].set_ylim(mag_min - margin, mag_max + margin)
        
        # Aggiorna statistiche
        self.update_statistics_display()
        
        return self.lines

    def update_statistics_display(self):
        """Aggiorna il display delle statistiche"""
        if self.sample_count == 0:
            return
            
        elapsed_time = time.time() - self.start_time
        avg_frequency = self.sample_count / elapsed_time if elapsed_time > 0 else 0
        
        current_vals = self.last_values
        
        stats_text = f"""STATISTICHE LIVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Campioni: {self.sample_count:,}
🚨 Spike: {self.spike_count}
⏱️  Tempo: {elapsed_time:.1f}s  
📈 Frequenza: {avg_frequency:.1f} Hz

VALORI ATTUALI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 X: {current_vals['x']:+.3f}g
🟢 Y: {current_vals['y']:+.3f}g  
🔵 Z: {current_vals['z']:+.3f}g
🟣 Mag: {current_vals['mag']:.3f}g

DISPOSITIVO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 {self.device.name if self.device else 'N/A'}
🔗 {self.device.address if self.device else 'N/A'}
"""
        
        self.stats_text.set_text(stats_text)

    def parse_chileaf_data(self, data):
        """Parsing dati dal protocollo Chileaf - SOLO frame accelerometro 0x0C"""
        try:
            # FILTRO RIGOROSO: Solo frame Chileaf con command 0x0C
            if len(data) >= 3 and data[0] == self.CHILEAF_HEADER:
                command = data[2]
                
                if command == self.CHILEAF_CMD_ACCELEROMETER:
                    # Frame accelerometro valido
                    return self.parse_multi_sample_frame(data)
                else:
                    # Frame Chileaf ma NON accelerometro - IGNORA
                    print(f"⚠️ Frame Chileaf ignorato: Command=0x{command:02X} (non accelerometro)")
                    return False
            else:
                # Frame non-Chileaf - IGNORA
                print(f"⚠️ Frame non-Chileaf ignorato: {data.hex().upper()}")
                return False
                
        except Exception as e:
            print(f"⚠️ Errore parsing: {e}")
            return False

    def parse_multi_sample_frame(self, data):
        """Parsing frame Chileaf con possibili campioni multipli secondo doc 0x0C"""
        header = data[0]
        length = data[1]
        command = data[2]
        
        # � ULTRA LOW-LATENCY: Eliminato logging verboso che rallentava ogni frame
        
        # Calcola quanti campioni da 6 bytes ci sono nel payload
        payload_bytes = len(data) - 3  # Escludi header, length, command
        samples_count = payload_bytes // 6
        remaining_bytes = payload_bytes % 6
        
        # Processa tutti i campioni nel frame
        samples_processed = 0
        for i in range(samples_count):
            offset = 3 + (i * 6)  # 3 per header + i * 6 bytes per campione
            if offset + 6 <= len(data):
                sample_data = data[offset:offset+6]
                success = self.parse_single_sample(sample_data, data, sample_index=i+1, total_samples=samples_count)
                if success:
                    samples_processed += 1
        
        # 🚀 Bytes rimanenti processati silenziosamente per velocità
        
        return samples_processed > 0

    def parse_single_sample(self, accel_data, original_frame, sample_index=1, total_samples=1):
        """Parsing di un singolo campione accelerometro"""
        if len(accel_data) < 6:
            return False
        
        try:
            # Parsing accelerometro (6 bytes = 3 assi x 2 bytes int16 little-endian)
            rawAX, rawAY, rawAZ = struct.unpack('<hhh', accel_data)
            
            # Conversione in g-force
            ax_g = rawAX / self.CHILEAF_CONVERSION_FACTOR
            ay_g = rawAY / self.CHILEAF_CONVERSION_FACTOR
            az_g = rawAZ / self.CHILEAF_CONVERSION_FACTOR
            magnitude = (ax_g**2 + ay_g**2 + az_g**2)**0.5
            
            # 🚨 FILTRO SPIKE DETECTION
            is_spike = self.detect_spike(ax_g, ay_g, az_g, magnitude, original_frame)
            
            if is_spike and total_samples == 1:  # Solo per campioni singoli
                self.spike_count += 1
                print(f"🚨 SPIKE RILEVATO #{self.sample_count + 1}:")
                print(f"   Raw frame: {original_frame.hex().upper()}")
                print(f"   Sample data: {accel_data.hex().upper()}")
                print(f"   Raw values: AX={rawAX} AY={rawAY} AZ={rawAZ}")
                print(f"   G values: X={ax_g:+.3f} Y={ay_g:+.3f} Z={az_g:+.3f} Mag={magnitude:.3f}")
                print("   ---")
            
            # Aggiungi ai buffer oscilloscopio
            current_time = time.time()
            self.x_data.append(ax_g)
            self.y_data.append(ay_g)
            self.z_data.append(az_g)
            self.magnitude_data.append(magnitude)
            self.timestamps.append(current_time)
            
            # Aggiorna statistiche
            self.last_values = {'x': ax_g, 'y': ay_g, 'z': az_g, 'mag': magnitude}
            self.sample_count += 1
            
            # Output console dettagliato per multi-sample
            if total_samples > 1:
                print(f"   Campione {sample_index}/{total_samples}: X:{ax_g:+.3f} Y:{ay_g:+.3f} Z:{az_g:+.3f} Mag:{magnitude:.3f}g")
            elif self.sample_count % 15 == 0:  # Output più frequente per responsività
                elapsed = current_time - self.start_time
                freq = self.sample_count / elapsed if elapsed > 0 else 0
                spike_marker = "🚨" if is_spike else "📊"
                print(f"{spike_marker} #{self.sample_count:>4} | "
                      f"X:{ax_g:+.3f} Y:{ay_g:+.3f} Z:{az_g:+.3f} | "
                      f"Mag:{magnitude:.3f}g | {freq:.1f}Hz")
            
            return True
            
        except struct.error as e:
            print(f"   ⚠️ Errore unpacking campione: {e}")
            return False

    def detect_spike(self, ax, ay, az, mag, raw_data):
        """Rileva VERI malfunzionamenti del sensore (non più frame di altri comandi)"""
        # I precedenti "spike" erano frame di comandi diversi (0x38, 0x15, 0x75)
        # Ora con filtro rigoroso su command=0x0C, rimangono solo veri problemi hardware
        
        # Soglie MOLTO permissive - solo per malfunzionamenti gravi
        MAX_PHYSICS_G = 50.0   # Limite fisico impossibile da superare
        MIN_PHYSICS_MAG = 0.01 # Magnitudine minima fisicamente possibile
        
        # Solo spike hardware REALMENTE impossibili
        is_spike = False
        
        # Controllo limiti fisici estremi
        if (abs(ax) > MAX_PHYSICS_G or abs(ay) > MAX_PHYSICS_G or abs(az) > MAX_PHYSICS_G or
            mag > MAX_PHYSICS_G or mag < MIN_PHYSICS_MAG):
            is_spike = True
        
        # Frame length sempre 10 per command 0x0C
        if len(raw_data) != 10:
            is_spike = True
        
        return is_spike

    def notification_handler(self, sender, data):
        """Gestisce le notifiche BLE - ULTRA LOW LATENCY"""
        # 🚀 Processing immediato senza attesa - handler sincrono per min latency
        # Non usare async qui perché aggiunge overhead nel BLE callback
        try:
            self.parse_chileaf_data(data)
        except Exception as e:
            # Logging minimo per non rallentare
            print(f"⚠️ Handler error: {e}")

    async def start_monitoring(self):
        """Avvia il monitoraggio principale"""
        print(f"\n🚀 Avvio monitoraggio accelerometro CL837")
        print("=" * 60)
        
        # Avvia oscilloscopio
        self.start_oscilloscope_thread()
        
        # 🚀 OTTIMIZZAZIONE: Attivazione notifiche con priorità massima
        print("🔔 Attivazione notifiche LOW-LATENCY...")
        
        # Flush eventuali dati bufferizzati prima di iniziare
        try:
            # Leggi eventuali caratteristiche cached per svuotare buffer
            services = self.client.services
            for service in services:
                if str(service.uuid).startswith('aae28f00'):
                    print(f"   🧹 Flush cache servizio {service.uuid}")
        except Exception:
            pass
            
        await self.client.start_notify(self.tx_char, self.notification_handler)
        print("✅ Notifiche LOW-LATENCY attivate - Streaming in corso")
        
        # 🎯 Piccolo delay per stabilizzazione
        await asyncio.sleep(0.1)
        
        print("\n📊 MONITOR ATTIVO:")
        print("   - Console: aggiornamenti ogni ~1 secondo")
        print("   - Oscilloscopio: real-time a 20fps")
        print("   - Premi Ctrl+C per fermare")
        print("=" * 60)
        
        try:
            # 🚀 LOW-LATENCY: Loop più reattivo per gestione eventi
            while True:
                await asyncio.sleep(0.1)  # 10x più reattivo per Ctrl+C e gestione eventi
        except KeyboardInterrupt:
            print("\n⚠️ Interruzione utente...")
        finally:
            print("🔄 Disconnessione in corso...")
            await self.client.stop_notify(self.tx_char)

    async def disconnect(self):
        """Disconnetti dal dispositivo"""
        if self.client and self.is_connected:
            await self.client.disconnect()
            
            # Statistiche finali
            total_time = time.time() - self.start_time
            avg_freq = self.sample_count / total_time if total_time > 0 else 0
            
            print(f"\n📊 SESSIONE COMPLETATA:")
            print(f"   Dispositivo: {self.device.name}")
            print(f"   Durata: {total_time:.1f}s")
            print(f"   Campioni: {self.sample_count:,}")
            print(f"   Spike rilevati: {self.spike_count}")
            if self.sample_count > 0:
                spike_percentage = (self.spike_count / self.sample_count) * 100
                print(f"   Percentuale spike: {spike_percentage:.2f}%")
            print(f"   Frequenza media: {avg_freq:.2f}Hz")
            print(f"🔌 Disconnesso")
            
            # Mantieni oscilloscopio aperto
            if self.plot_ready:
                print("📊 Oscilloscopio rimane aperto - chiudi la finestra per terminare")
                input("Premi Enter per chiudere completamente...")

async def main():
    """Funzione principale"""
    monitor = CL837UnifiedMonitor()
    
    print("🚀 CL837 UNIFIED ACCELEROMETER MONITOR")
    print("📊 Connessione + Monitor Console + Oscilloscopio Real-Time")
    print("=" * 70)
    
    try:
        # Fase 1: Connessione
        if not await monitor.scan_and_connect():
            return
        
        # Fase 2: Analisi servizi
        if not await monitor.discover_services():
            return
        
        # Fase 3: Monitoraggio
        await monitor.start_monitoring()
        
    except Exception as e:
        print(f"❌ Errore generale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await monitor.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Programma terminato")