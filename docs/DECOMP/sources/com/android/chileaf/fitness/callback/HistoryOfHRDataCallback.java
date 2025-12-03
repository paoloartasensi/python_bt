package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;
import com.android.chileaf.model.HistoryOfHeartRate;
import java.util.List;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface HistoryOfHRDataCallback {
    void onHistoryOfHRDataReceived(final BluetoothDevice device, List<HistoryOfHeartRate> heartRates);
}
