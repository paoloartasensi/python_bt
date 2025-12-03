package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;
import com.android.chileaf.model.HistoryOfRespiratoryRate;
import java.util.List;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface HistoryOfRRDataCallback {
    void onHistoryOfRRDataReceived(final BluetoothDevice device, List<HistoryOfRespiratoryRate> respiratoryRates);
}
