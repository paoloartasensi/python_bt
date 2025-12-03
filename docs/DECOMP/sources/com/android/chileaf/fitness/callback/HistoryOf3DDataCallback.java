package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;
import com.android.chileaf.model.HistoryOf3D;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface HistoryOf3DDataCallback {
    void onHistoryOf3DDataReceived(final BluetoothDevice device, HistoryOf3D history, boolean finish);
}
