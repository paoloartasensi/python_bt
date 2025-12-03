package com.android.chileaf.fitness.common.battery;

import android.bluetooth.BluetoothDevice;
import android.os.Parcel;
import no.nordicsemi.android.ble.callback.profile.ProfileReadResponse;
import no.nordicsemi.android.ble.data.Data;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public abstract class BatteryLevelDataCallback extends ProfileReadResponse implements BatteryLevelCallback {
    public BatteryLevelDataCallback() {
    }

    protected BatteryLevelDataCallback(final Parcel in) {
        super(in);
    }

    @Override // no.nordicsemi.android.ble.response.ReadResponse, no.nordicsemi.android.ble.callback.DataReceivedCallback
    public void onDataReceived(final BluetoothDevice device, final Data data) {
        int batteryLevel;
        super.onDataReceived(device, data);
        if (data.size() == 1 && (batteryLevel = data.getIntValue(17, 0).intValue()) >= 0 && batteryLevel <= 100) {
            onBatteryLevelChanged(device, batteryLevel);
        } else {
            onInvalidDataReceived(device, data);
        }
    }
}
