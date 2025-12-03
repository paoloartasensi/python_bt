package no.nordicsemi.android.ble.callback;

import android.bluetooth.BluetoothDevice;

@FunctionalInterface
/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface ConnectionParametersUpdatedCallback {
    void onConnectionUpdated(BluetoothDevice bluetoothDevice, int i, int i2, int i3);
}
