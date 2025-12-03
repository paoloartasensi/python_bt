package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;
import com.android.chileaf.model.HistoryOfStep;
import java.util.List;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface HistoryOfStepDataCallback {
    void onHistoryOfStepDataReceived(final BluetoothDevice device, List<HistoryOfStep> steps);
}
