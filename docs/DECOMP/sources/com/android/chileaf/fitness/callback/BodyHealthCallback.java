package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface BodyHealthCallback {
    void onHealthReceived(final BluetoothDevice device, final int vo2Max, final int breathRate, final int emotionLevel, final int stressPercent, final int stamina, final float tp, final float lf, final float hf);
}
