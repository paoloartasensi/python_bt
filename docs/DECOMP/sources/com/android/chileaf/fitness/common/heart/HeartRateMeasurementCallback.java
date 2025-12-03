package com.android.chileaf.fitness.common.heart;

import android.bluetooth.BluetoothDevice;
import java.util.List;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface HeartRateMeasurementCallback {
    void onHeartRateMeasurementReceived(final BluetoothDevice device, final int heartRate, final Boolean contactDetected, final Integer energyExpanded, final List<Integer> rrIntervals);
}
