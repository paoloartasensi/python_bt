package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface HeartRateMaxCallback {
    void onHeartRateMaxReceived(final BluetoothDevice device, final int max);
}
