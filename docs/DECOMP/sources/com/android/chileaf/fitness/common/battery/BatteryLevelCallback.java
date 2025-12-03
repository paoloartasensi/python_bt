package com.android.chileaf.fitness.common.battery;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface BatteryLevelCallback {
    void onBatteryLevelChanged(final BluetoothDevice device, final int batteryLevel);
}
