package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface Sensor3DStatusCallback {
    void onSensor3DStatusReceived(final BluetoothDevice device, boolean enabled);
}
