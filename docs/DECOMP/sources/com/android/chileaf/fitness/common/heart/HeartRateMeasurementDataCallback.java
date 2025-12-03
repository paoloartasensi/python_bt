package com.android.chileaf.fitness.common.heart;

import android.bluetooth.BluetoothDevice;
import android.os.Parcel;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import no.nordicsemi.android.ble.callback.profile.ProfileReadResponse;
import no.nordicsemi.android.ble.data.Data;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public abstract class HeartRateMeasurementDataCallback extends ProfileReadResponse implements HeartRateMeasurementCallback {
    public HeartRateMeasurementDataCallback() {
    }

    protected HeartRateMeasurementDataCallback(final Parcel in) {
        super(in);
    }

    @Override // no.nordicsemi.android.ble.response.ReadResponse, no.nordicsemi.android.ble.callback.DataReceivedCallback
    public void onDataReceived(final BluetoothDevice device, final Data data) {
        List<Integer> intervals;
        super.onDataReceived(device, data);
        if (data.size() >= 2) {
            int flags = data.getIntValue(17, 0).intValue();
            int hearRateType = (flags & 1) != 0 ? 18 : 17;
            int sensorContactStatus = (flags & 6) >> 1;
            boolean sensorContactSupported = sensorContactStatus == 2 || sensorContactStatus == 3;
            boolean sensorContactDetected = sensorContactStatus == 3;
            boolean energyExpandedPresent = (flags & 8) != 0;
            boolean rrIntervalsPresent = (flags & 16) != 0;
            int offset = 0 + 1;
            if (data.size() < (hearRateType & 15) + 1 + (energyExpandedPresent ? 2 : 0) + (rrIntervalsPresent ? 2 : 0)) {
                onInvalidDataReceived(device, data);
                return;
            }
            Boolean sensorContact = sensorContactSupported ? Boolean.valueOf(sensorContactDetected) : null;
            int heartRate = data.getIntValue(hearRateType, offset).intValue();
            int offset2 = offset + (hearRateType & 15);
            Integer energyExpanded = null;
            if (energyExpandedPresent) {
                energyExpanded = data.getIntValue(18, offset2);
                offset2 += 2;
            }
            if (!rrIntervalsPresent) {
                intervals = null;
            } else {
                int count = (data.size() - offset2) / 2;
                List<Integer> intervals2 = new ArrayList<>(count);
                int i = 0;
                while (i < count) {
                    intervals2.add(data.getIntValue(18, offset2));
                    offset2 += 2;
                    i++;
                    hearRateType = hearRateType;
                }
                List<Integer> rrIntervals = Collections.unmodifiableList(intervals2);
                intervals = rrIntervals;
            }
            onHeartRateMeasurementReceived(device, heartRate, sensorContact, energyExpanded, intervals);
            return;
        }
        onInvalidDataReceived(device, data);
    }
}
