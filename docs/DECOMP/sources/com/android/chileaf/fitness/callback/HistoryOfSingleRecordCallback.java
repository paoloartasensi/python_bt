package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface HistoryOfSingleRecordCallback {
    void onHistorySingleRecordReceived(final BluetoothDevice device, final long stamp, final long step, final long distance, final long calorie);
}
