package com.android.chileaf.fitness.common;

import android.bluetooth.BluetoothDevice;
import java.util.Calendar;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface DateTimeCallback {
    void onDateTimeReceived(final BluetoothDevice device, final Calendar calendar);
}
