package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface HeartRateStatusCallback {
    void onHeartRateStatusReceived(final BluetoothDevice device, final int min, final int max, final int goal);
}
