package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface HeartRateAlarmCallback {
    void onHeartRateAlarmReceived(final BluetoothDevice device, long stamp, boolean enabled);
}
