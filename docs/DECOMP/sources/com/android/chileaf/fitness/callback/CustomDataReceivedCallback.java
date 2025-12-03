package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface CustomDataReceivedCallback {
    void onDataReceived(final BluetoothDevice device, final byte[] data);
}
