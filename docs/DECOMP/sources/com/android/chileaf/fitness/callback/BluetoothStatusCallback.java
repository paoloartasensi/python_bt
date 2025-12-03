package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface BluetoothStatusCallback {
    void onBluetoothStatusReceived(final BluetoothDevice device, boolean enabled);
}
