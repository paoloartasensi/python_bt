package no.nordicsemi.android.ble.observer;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface ServerObserver {
    void onDeviceConnectedToServer(BluetoothDevice bluetoothDevice);

    void onDeviceDisconnectedFromServer(BluetoothDevice bluetoothDevice);

    void onServerReady();
}
