package com.android.chileaf.fitness.common;

import android.bluetooth.BluetoothDevice;
import android.os.Parcel;
import java.util.Calendar;
import no.nordicsemi.android.ble.callback.profile.ProfileReadResponse;
import no.nordicsemi.android.ble.data.Data;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public abstract class DateTimeDataCallback extends ProfileReadResponse implements DateTimeCallback {
    public DateTimeDataCallback() {
    }

    protected DateTimeDataCallback(final Parcel in) {
        super(in);
    }

    @Override // no.nordicsemi.android.ble.response.ReadResponse, no.nordicsemi.android.ble.callback.DataReceivedCallback
    public void onDataReceived(final BluetoothDevice device, final Data data) {
        super.onDataReceived(device, data);
        Calendar calendar = readDateTime(data, 0);
        if (calendar == null) {
            onInvalidDataReceived(device, data);
        } else {
            onDateTimeReceived(device, calendar);
        }
    }

    public static Calendar readDateTime(final Data data, final int offset) {
        if (data.size() < offset + 7) {
            return null;
        }
        Calendar calendar = Calendar.getInstance();
        int year = data.getIntValue(18, offset).intValue();
        int month = data.getIntValue(17, offset + 2).intValue();
        int day = data.getIntValue(17, offset + 3).intValue();
        if (year > 0) {
            calendar.set(1, year);
        } else {
            calendar.clear(1);
        }
        if (month > 0) {
            calendar.set(2, month - 1);
        } else {
            calendar.clear(2);
        }
        if (day > 0) {
            calendar.set(5, day);
        } else {
            calendar.clear(5);
        }
        calendar.set(11, data.getIntValue(17, offset + 4).intValue());
        calendar.set(12, data.getIntValue(17, offset + 5).intValue());
        calendar.set(13, data.getIntValue(17, offset + 6).intValue());
        calendar.set(14, 0);
        return calendar;
    }
}
