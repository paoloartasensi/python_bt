package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface BodySportHealthCallback {
    void onSportHealthReceived(final BluetoothDevice device, final int vo2Max, final int breathRate, final int emotion, final int pressure, final int stamina);
}
