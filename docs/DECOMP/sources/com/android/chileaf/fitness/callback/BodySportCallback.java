package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface BodySportCallback {
    void onSportReceived(final BluetoothDevice device, final int step, final int distance, final int calorie);
}
