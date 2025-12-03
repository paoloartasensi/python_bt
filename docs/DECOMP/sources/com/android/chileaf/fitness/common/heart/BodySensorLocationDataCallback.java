package com.android.chileaf.fitness.common.heart;

import android.bluetooth.BluetoothDevice;
import android.os.Parcel;
import no.nordicsemi.android.ble.callback.profile.ProfileReadResponse;
import no.nordicsemi.android.ble.data.Data;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public abstract class BodySensorLocationDataCallback extends ProfileReadResponse implements BodySensorLocationCallback {
    public BodySensorLocationDataCallback() {
    }

    protected BodySensorLocationDataCallback(final Parcel in) {
        super(in);
    }

    @Override // no.nordicsemi.android.ble.response.ReadResponse, no.nordicsemi.android.ble.callback.DataReceivedCallback
    public void onDataReceived(final BluetoothDevice device, final Data data) {
        super.onDataReceived(device, data);
        if (data.size() < 1) {
            onInvalidDataReceived(device, data);
        } else {
            int sensorLocation = data.getIntValue(17, 0).intValue();
            onBodySensorLocationReceived(device, sensorLocation);
        }
    }
}
