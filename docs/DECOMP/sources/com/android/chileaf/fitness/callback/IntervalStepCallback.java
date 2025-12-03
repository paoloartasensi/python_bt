package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;
import com.android.chileaf.model.IntervalStep;
import java.util.List;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface IntervalStepCallback {
    void onIntervalStepReceived(final BluetoothDevice device, List<IntervalStep> steps);
}
