package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface BloodOxygenCallback {
    void onBloodOxygenReceived(final BluetoothDevice device, int bSwitch, String value, int gesture, int piValue, int Onwrist);
}
