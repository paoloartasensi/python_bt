package no.nordicsemi.android.ble;

import android.bluetooth.BluetoothDevice;
import android.os.Handler;
import android.util.Log;
import no.nordicsemi.android.ble.callback.ClosedCallback;
import no.nordicsemi.android.ble.callback.DataReceivedCallback;
import no.nordicsemi.android.ble.callback.ReadProgressCallback;
import no.nordicsemi.android.ble.data.Data;
import no.nordicsemi.android.ble.data.DataFilter;
import no.nordicsemi.android.ble.data.DataMerger;
import no.nordicsemi.android.ble.data.DataStream;
import no.nordicsemi.android.ble.data.PacketFilter;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public class ValueChangedCallback {
    private static final String TAG = ValueChangedCallback.class.getSimpleName();
    private DataStream buffer;
    private ClosedCallback closedCallback;
    private int count = 0;
    private DataMerger dataMerger;
    private DataFilter filter;
    private CallbackHandler handler;
    private PacketFilter packetFilter;
    private ReadProgressCallback progressCallback;
    private DataReceivedCallback valueCallback;

    ValueChangedCallback(CallbackHandler handler) {
        this.handler = handler;
    }

    public ValueChangedCallback setHandler(final Handler handler) {
        this.handler = new CallbackHandler() { // from class: no.nordicsemi.android.ble.ValueChangedCallback.1
            @Override // no.nordicsemi.android.ble.CallbackHandler
            public void post(Runnable r) {
                Handler handler2 = handler;
                if (handler2 != null) {
                    handler2.post(r);
                } else {
                    r.run();
                }
            }

            @Override // no.nordicsemi.android.ble.CallbackHandler
            public void postDelayed(Runnable r, long delayMillis) {
            }

            @Override // no.nordicsemi.android.ble.CallbackHandler
            public void removeCallbacks(Runnable r) {
            }
        };
        return this;
    }

    public ValueChangedCallback with(DataReceivedCallback callback) {
        this.valueCallback = callback;
        return this;
    }

    public ValueChangedCallback filter(DataFilter filter) {
        this.filter = filter;
        return this;
    }

    public ValueChangedCallback filterPacket(PacketFilter filter) {
        this.packetFilter = filter;
        return this;
    }

    public ValueChangedCallback merge(DataMerger merger) {
        this.dataMerger = merger;
        this.progressCallback = null;
        return this;
    }

    public ValueChangedCallback merge(DataMerger merger, ReadProgressCallback callback) {
        this.dataMerger = merger;
        this.progressCallback = callback;
        return this;
    }

    public ValueChangedCallback then(ClosedCallback callback) {
        this.closedCallback = callback;
        return this;
    }

    boolean matches(byte[] packet) {
        DataFilter dataFilter = this.filter;
        return dataFilter == null || dataFilter.filter(packet);
    }

    void notifyValueChanged(final BluetoothDevice device, final byte[] value) {
        PacketFilter packetFilter;
        final DataReceivedCallback valueCallback = this.valueCallback;
        if (valueCallback == null) {
            return;
        }
        if (this.dataMerger == null && ((packetFilter = this.packetFilter) == null || packetFilter.filter(value))) {
            final Data data = new Data(value);
            this.handler.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$ValueChangedCallback$iDFr3-6QE87cWLUeUNPFplE0TFc
                @Override // java.lang.Runnable
                public final void run() {
                    ValueChangedCallback.lambda$notifyValueChanged$0(valueCallback, device, data);
                }
            });
            return;
        }
        this.handler.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$ValueChangedCallback$Abubs2xbLMwzeCQ7J-xJaz-uYeE
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$notifyValueChanged$1$ValueChangedCallback(device, value);
            }
        });
        if (this.buffer == null) {
            this.buffer = new DataStream();
        }
        DataMerger dataMerger = this.dataMerger;
        DataStream dataStream = this.buffer;
        int i = this.count;
        this.count = i + 1;
        if (dataMerger.merge(dataStream, value, i)) {
            byte[] merged = this.buffer.toByteArray();
            PacketFilter packetFilter2 = this.packetFilter;
            if (packetFilter2 == null || packetFilter2.filter(merged)) {
                final Data data2 = new Data(merged);
                this.handler.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$ValueChangedCallback$gxJaWMxOh-utzyqwoNcb6TgXgHE
                    @Override // java.lang.Runnable
                    public final void run() {
                        ValueChangedCallback.lambda$notifyValueChanged$2(valueCallback, device, data2);
                    }
                });
            }
            this.buffer = null;
            this.count = 0;
        }
    }

    static /* synthetic */ void lambda$notifyValueChanged$0(DataReceivedCallback valueCallback, BluetoothDevice device, Data data) {
        try {
            valueCallback.onDataReceived(device, data);
        } catch (Throwable t) {
            Log.e(TAG, "Exception in Value callback", t);
        }
    }

    public /* synthetic */ void lambda$notifyValueChanged$1$ValueChangedCallback(BluetoothDevice device, byte[] value) {
        ReadProgressCallback readProgressCallback = this.progressCallback;
        if (readProgressCallback != null) {
            try {
                readProgressCallback.onPacketReceived(device, value, this.count);
            } catch (Throwable t) {
                Log.e(TAG, "Exception in Progress callback", t);
            }
        }
    }

    static /* synthetic */ void lambda$notifyValueChanged$2(DataReceivedCallback valueCallback, BluetoothDevice device, Data data) {
        try {
            valueCallback.onDataReceived(device, data);
        } catch (Throwable t) {
            Log.e(TAG, "Exception in Value callback", t);
        }
    }

    void notifyClosed() {
        ClosedCallback closedCallback = this.closedCallback;
        if (closedCallback != null) {
            try {
                closedCallback.onClosed();
            } catch (Throwable t) {
                Log.e(TAG, "Exception in Closed callback", t);
            }
        }
        free();
    }

    private void free() {
        this.closedCallback = null;
        this.valueCallback = null;
        this.dataMerger = null;
        this.progressCallback = null;
        this.filter = null;
        this.packetFilter = null;
        this.buffer = null;
        this.count = 0;
    }
}
