package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;
import com.android.chileaf.model.HistorySleep;
import java.util.List;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface HistoryOfSleepCallback {
    void onHistoryOfSleepReceived(final BluetoothDevice device, List<HistorySleep> sleeps);
}
