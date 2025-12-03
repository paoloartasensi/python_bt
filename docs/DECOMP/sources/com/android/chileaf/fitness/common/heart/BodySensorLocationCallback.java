package com.android.chileaf.fitness.common.heart;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface BodySensorLocationCallback {
    public static final int SENSOR_LOCATION_CHEST = 1;
    public static final int SENSOR_LOCATION_EAR_LOBE = 5;
    public static final int SENSOR_LOCATION_FINGER = 3;
    public static final int SENSOR_LOCATION_FIRST = 0;
    public static final int SENSOR_LOCATION_FOOT = 6;
    public static final int SENSOR_LOCATION_HAND = 4;
    public static final int SENSOR_LOCATION_LAST = 6;
    public static final int SENSOR_LOCATION_OTHER = 0;
    public static final int SENSOR_LOCATION_WRIST = 2;

    void onBodySensorLocationReceived(final BluetoothDevice device, final int sensorLocation);
}
