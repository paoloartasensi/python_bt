package no.nordicsemi.android.ble.callback;

import android.bluetooth.BluetoothDevice;
import no.nordicsemi.android.ble.data.Data;

@FunctionalInterface
/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface DataSentCallback {
    void onDataSent(BluetoothDevice bluetoothDevice, Data data);
}
