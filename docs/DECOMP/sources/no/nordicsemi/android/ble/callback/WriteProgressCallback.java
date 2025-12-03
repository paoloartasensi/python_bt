package no.nordicsemi.android.ble.callback;

import android.bluetooth.BluetoothDevice;

@FunctionalInterface
/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface WriteProgressCallback {
    void onPacketSent(BluetoothDevice bluetoothDevice, byte[] bArr, int i);
}
