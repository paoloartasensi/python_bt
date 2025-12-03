package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface AccelerometerCallback {
    void onAccelerometerReceived(final BluetoothDevice device, int x, int y, int z);
}
