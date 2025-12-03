package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;
import com.android.chileaf.model.HistoryOfSport;
import java.util.List;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface HistoryOfSportCallback {
    void onHistoryOfSportReceived(final BluetoothDevice device, List<HistoryOfSport> sports);
}
