package com.chileaf.cl831.sample.multi;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes3.dex */
public class DeviceItem {
    public int battery;
    public int calorie;
    public BluetoothDevice device;
    public int distance;
    public int heartRate;
    public int step;
    public String version;

    public DeviceItem(BluetoothDevice device) {
        this.device = device;
    }
}
