package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;
import com.android.chileaf.fitness.FitnessManagerCallbacks;
import com.android.chileaf.fitness.common.heart.BodySensorLocationCallback;
import com.android.chileaf.fitness.common.heart.HeartRateMeasurementCallback;
import java.util.List;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface WearManagerCallbacks extends FitnessManagerCallbacks, BodySensorLocationCallback, HeartRateMeasurementCallback, BodySportCallback, BluetoothStatusCallback {
    @Override // com.android.chileaf.fitness.callback.BluetoothStatusCallback
    void onBluetoothStatusReceived(final BluetoothDevice device, boolean enabled);

    @Override // com.android.chileaf.fitness.common.heart.BodySensorLocationCallback
    void onBodySensorLocationReceived(final BluetoothDevice device, final int sensorLocation);

    @Override // com.android.chileaf.fitness.common.heart.HeartRateMeasurementCallback
    void onHeartRateMeasurementReceived(final BluetoothDevice device, final int heartRate, final Boolean contactDetected, final Integer energyExpanded, final List<Integer> rrIntervals);

    @Override // com.android.chileaf.fitness.callback.BodySportCallback
    void onSportReceived(final BluetoothDevice device, final int step, final int distance, final int calorie);

    /* renamed from: com.android.chileaf.fitness.callback.WearManagerCallbacks$-CC, reason: invalid class name */
    public final /* synthetic */ class CC {
        public static void $default$onBodySensorLocationReceived(WearManagerCallbacks _this, BluetoothDevice device, int sensorLocation) {
        }

        public static void $default$onHeartRateMeasurementReceived(WearManagerCallbacks _this, BluetoothDevice device, int heartRate, Boolean contactDetected, Integer energyExpanded, List list) {
        }

        public static void $default$onSportReceived(WearManagerCallbacks _this, BluetoothDevice device, int step, int distance, int calorie) {
        }

        public static void $default$onBluetoothStatusReceived(WearManagerCallbacks _this, BluetoothDevice device, boolean enabled) {
        }
    }
}
