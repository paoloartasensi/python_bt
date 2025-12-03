package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface TemperatureCallback {
    void onTemperatureReceived(final BluetoothDevice device, float environment, float wrist, float body);
}
