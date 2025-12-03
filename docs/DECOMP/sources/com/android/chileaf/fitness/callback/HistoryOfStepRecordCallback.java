package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;
import com.android.chileaf.model.HistoryOfRecord;
import java.util.List;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface HistoryOfStepRecordCallback {
    void onHistoryOfStepRecordReceived(final BluetoothDevice device, List<HistoryOfRecord> records);
}
