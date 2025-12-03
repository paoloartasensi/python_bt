package com.android.chileaf;

import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattService;
import android.content.Context;
import android.os.ParcelUuid;
import android.text.TextUtils;
import com.android.chileaf.fitness.FitnessManager;
import com.android.chileaf.fitness.callback.AccelerometerCallback;
import com.android.chileaf.fitness.callback.BloodOxygenCallback;
import com.android.chileaf.fitness.callback.BluetoothStatusCallback;
import com.android.chileaf.fitness.callback.BodyHealthCallback;
import com.android.chileaf.fitness.callback.BodySportCallback;
import com.android.chileaf.fitness.callback.BodySportHealthCallback;
import com.android.chileaf.fitness.callback.CustomDataReceivedCallback;
import com.android.chileaf.fitness.callback.HeartRateAlarmCallback;
import com.android.chileaf.fitness.callback.HeartRateMaxCallback;
import com.android.chileaf.fitness.callback.HeartRateStatusCallback;
import com.android.chileaf.fitness.callback.HistoryOf3DDataCallback;
import com.android.chileaf.fitness.callback.HistoryOfHRDataCallback;
import com.android.chileaf.fitness.callback.HistoryOfHRRecordCallback;
import com.android.chileaf.fitness.callback.HistoryOfRRDataCallback;
import com.android.chileaf.fitness.callback.HistoryOfRRRecordCallback;
import com.android.chileaf.fitness.callback.HistoryOfSingleRecordCallback;
import com.android.chileaf.fitness.callback.HistoryOfSleepCallback;
import com.android.chileaf.fitness.callback.HistoryOfSportCallback;
import com.android.chileaf.fitness.callback.HistoryOfStepDataCallback;
import com.android.chileaf.fitness.callback.HistoryOfStepRecordCallback;
import com.android.chileaf.fitness.callback.IntervalStepCallback;
import com.android.chileaf.fitness.callback.Sensor3DFrequencyCallback;
import com.android.chileaf.fitness.callback.Sensor3DStatusCallback;
import com.android.chileaf.fitness.callback.Sensor6DFrequencyCallback;
import com.android.chileaf.fitness.callback.Sensor6DRawDataCallback;
import com.android.chileaf.fitness.callback.SingleTapRecordCallback;
import com.android.chileaf.fitness.callback.TemperatureCallback;
import com.android.chileaf.fitness.callback.UserInfoCallback;
import com.android.chileaf.fitness.callback.WearManagerCallbacks;
import com.android.chileaf.fitness.callback.WearReceivedDataCallback;
import com.android.chileaf.fitness.common.FilterScanCallback;
import com.android.chileaf.fitness.common.heart.BodySensorLocationDataCallback;
import com.android.chileaf.fitness.common.heart.HeartRateMeasurementCallback;
import com.android.chileaf.fitness.common.heart.HeartRateMeasurementDataCallback;
import com.android.chileaf.fitness.common.parser.BodySensorLocationParser;
import com.android.chileaf.fitness.common.parser.HeartRateMeasurementParser;
import com.android.chileaf.model.HistoryOf3D;
import com.android.chileaf.model.HistoryOfHeartRate;
import com.android.chileaf.model.HistoryOfRecord;
import com.android.chileaf.model.HistoryOfRespiratoryRate;
import com.android.chileaf.model.HistoryOfSport;
import com.android.chileaf.model.HistoryOfStep;
import com.android.chileaf.model.HistorySleep;
import com.android.chileaf.model.IntervalStep;
import com.android.chileaf.util.DateUtil;
import com.android.chileaf.util.HexUtil;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import no.nordicsemi.android.ble.BleManager;
import no.nordicsemi.android.ble.callback.DataReceivedCallback;
import no.nordicsemi.android.ble.callback.FailCallback;
import no.nordicsemi.android.ble.callback.SuccessCallback;
import no.nordicsemi.android.ble.data.Data;
import no.nordicsemi.android.support.v18.scanner.BluetoothLeScannerCompat;
import no.nordicsemi.android.support.v18.scanner.ScanCallback;
import no.nordicsemi.android.support.v18.scanner.ScanFilter;
import no.nordicsemi.android.support.v18.scanner.ScanResult;
import no.nordicsemi.android.support.v18.scanner.ScanSettings;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public class WearManager extends FitnessManager<WearManagerCallbacks> {
    private AccelerometerCallback mAccelerometerCallback;
    private BloodOxygenCallback mBloodOxygenCallback;
    private BluetoothStatusCallback mBluetoothStatusCallback;
    private BodyHealthCallback mBodyHealthCallback;
    private BluetoothGattCharacteristic mBodySensorLocationCharacteristic;
    private final BodySensorLocationDataCallback mBodySensorLocationDataCallback;
    private BodySportCallback mBodySportCallback;
    private BodySportHealthCallback mBodySportHealthCallback;
    private CustomDataReceivedCallback mCustomDataReceivedCallback;
    private String[] mFilterNames;
    private HeartRateAlarmCallback mHeartRateAlarmCallback;
    private BluetoothGattCharacteristic mHeartRateCharacteristic;
    private HeartRateMaxCallback mHeartRateMaxCallback;
    private final HeartRateMeasurementDataCallback mHeartRateMeasureDataCallback;
    private HeartRateMeasurementCallback mHeartRateMeasurementCallback;
    private HeartRateStatusCallback mHeartRateStatusCallback;
    private HistoryOf3DDataCallback mHistoryOf3DDataCallback;
    private HistoryOfHRDataCallback mHistoryOfHRDataCallback;
    private HistoryOfHRRecordCallback mHistoryOfHRRecordCallback;
    private HistoryOfRRDataCallback mHistoryOfRRDataCallback;
    private HistoryOfRRRecordCallback mHistoryOfRRRecordCallback;
    private HistoryOfSingleRecordCallback mHistoryOfSingleRecordCallback;
    private HistoryOfSleepCallback mHistoryOfSleepCallback;
    private HistoryOfSportCallback mHistoryOfSportCallback;
    private HistoryOfStepDataCallback mHistoryOfStepDataCallback;
    private HistoryOfStepRecordCallback mHistoryOfStepRecordCallback;
    private IntervalStepCallback mIntervalStepsCallback;
    private final WearReceivedDataCallback mReceivedDataCallback;
    private WearScanCallback mScanCallback;
    private Sensor3DFrequencyCallback mSensor3DFrequencyCallback;
    private Sensor3DStatusCallback mSensor3DStatusCallback;
    private Sensor6DFrequencyCallback mSensor6DFrequencyCallback;
    private Sensor6DRawDataCallback mSensor6DRawDataCallback;
    private SingleTapRecordCallback mSingleTapRecordCallback;
    private TemperatureCallback mTemperatureCallback;
    private UserInfoCallback mUserInfoCallback;
    private static final UUID HR_SERVICE_UUID = UUID.fromString("0000180D-0000-1000-8000-00805f9b34fb");
    private static final UUID BODY_SENSOR_LOCATION_CHARACTERISTIC_UUID = UUID.fromString("00002A38-0000-1000-8000-00805f9b34fb");
    private static final UUID HEART_RATE_MEASUREMENT_CHARACTERISTIC_UUID = UUID.fromString("00002A37-0000-1000-8000-00805f9b34fb");
    private static final String[] MODE_NAMES = {"CL831", "CL880N"};
    private static WearManager managerInstance = null;

    public static synchronized WearManager getInstance(final Context context) {
        if (managerInstance == null) {
            managerInstance = new WearManager(context);
        }
        return managerInstance;
    }

    public WearManager(final Context context) {
        super(context);
        this.mFilterNames = null;
        this.mBodySensorLocationDataCallback = new BodySensorLocationDataCallback() { // from class: com.android.chileaf.WearManager.1
            @Override // com.android.chileaf.fitness.common.heart.BodySensorLocationCallback
            public void onBodySensorLocationReceived(final BluetoothDevice device, final int sensorLocation) {
                ((WearManagerCallbacks) WearManager.this.mCallbacks).onBodySensorLocationReceived(device, sensorLocation);
            }

            @Override // com.android.chileaf.fitness.common.heart.BodySensorLocationDataCallback, no.nordicsemi.android.ble.response.ReadResponse, no.nordicsemi.android.ble.callback.DataReceivedCallback
            public void onDataReceived(final BluetoothDevice device, final Data data) {
                WearManager.this.log(3, String.format("%s received", BodySensorLocationParser.parse(data)));
                super.onDataReceived(device, data);
            }
        };
        this.mHeartRateMeasureDataCallback = new HeartRateMeasurementDataCallback() { // from class: com.android.chileaf.WearManager.2
            @Override // com.android.chileaf.fitness.common.heart.HeartRateMeasurementCallback
            public void onHeartRateMeasurementReceived(BluetoothDevice device, int heartRate, Boolean contactDetected, Integer energyExpanded, List<Integer> rrIntervals) {
                ((WearManagerCallbacks) WearManager.this.mCallbacks).onHeartRateMeasurementReceived(device, heartRate, contactDetected, energyExpanded, rrIntervals);
                if (WearManager.this.mHeartRateMeasurementCallback != null) {
                    WearManager.this.mHeartRateMeasurementCallback.onHeartRateMeasurementReceived(device, heartRate, contactDetected, energyExpanded, rrIntervals);
                }
            }

            @Override // com.android.chileaf.fitness.common.heart.HeartRateMeasurementDataCallback, no.nordicsemi.android.ble.response.ReadResponse, no.nordicsemi.android.ble.callback.DataReceivedCallback
            public void onDataReceived(final BluetoothDevice device, final Data data) {
                WearManager.this.log(3, HeartRateMeasurementParser.parse(data) + " received");
                super.onDataReceived(device, data);
            }
        };
        this.mReceivedDataCallback = new WearReceivedDataCallback() { // from class: com.android.chileaf.WearManager.3
            @Override // com.android.chileaf.fitness.callback.BodySportCallback
            public void onSportReceived(BluetoothDevice device, int step, int distance, int calorie) {
                ((WearManagerCallbacks) WearManager.this.mCallbacks).onSportReceived(device, step, distance, calorie);
                if (WearManager.this.mBodySportCallback != null) {
                    WearManager.this.mBodySportCallback.onSportReceived(device, step, distance, calorie);
                }
            }

            @Override // com.android.chileaf.fitness.callback.BodyHealthCallback
            public void onHealthReceived(BluetoothDevice device, int vo2Max, int breathRate, int emotionLevel, int stressPercent, int stamina, float tp, float lf, float hf) {
                if (WearManager.this.mBodyHealthCallback != null) {
                    WearManager.this.mBodyHealthCallback.onHealthReceived(device, vo2Max, breathRate, emotionLevel, stressPercent, stamina, tp, lf, hf);
                }
            }

            @Override // com.android.chileaf.fitness.callback.HistoryOfStepRecordCallback
            public void onHistoryOfStepRecordReceived(BluetoothDevice device, List<HistoryOfRecord> records) {
                if (WearManager.this.mHistoryOfStepRecordCallback != null) {
                    WearManager.this.mHistoryOfStepRecordCallback.onHistoryOfStepRecordReceived(device, records);
                }
            }

            @Override // com.android.chileaf.fitness.callback.HistoryOfStepDataCallback
            public void onHistoryOfStepDataReceived(BluetoothDevice device, List<HistoryOfStep> steps) {
                if (WearManager.this.mHistoryOfStepDataCallback != null) {
                    WearManager.this.mHistoryOfStepDataCallback.onHistoryOfStepDataReceived(device, steps);
                }
            }

            @Override // com.android.chileaf.fitness.callback.BodySportHealthCallback
            public void onSportHealthReceived(BluetoothDevice device, int vo2Max, int breathRate, int emotion, int pressure, int stamina) {
                if (WearManager.this.mBodySportHealthCallback != null) {
                    WearManager.this.mBodySportHealthCallback.onSportHealthReceived(device, vo2Max, breathRate, emotion, pressure, stamina);
                }
            }

            @Override // com.android.chileaf.fitness.callback.BluetoothStatusCallback
            public void onBluetoothStatusReceived(BluetoothDevice device, boolean enabled) {
                ((WearManagerCallbacks) WearManager.this.mCallbacks).onBluetoothStatusReceived(device, enabled);
                if (WearManager.this.mBluetoothStatusCallback != null) {
                    WearManager.this.mBluetoothStatusCallback.onBluetoothStatusReceived(device, enabled);
                }
            }

            @Override // com.android.chileaf.fitness.callback.UserInfoCallback
            public void onUserInfoReceived(BluetoothDevice device, int age, int sex, int weight, int height, long userId) {
                if (WearManager.this.mUserInfoCallback != null) {
                    WearManager.this.mUserInfoCallback.onUserInfoReceived(device, age, sex, weight, height, userId);
                }
            }

            @Override // com.android.chileaf.fitness.callback.HistoryOfSportCallback
            public void onHistoryOfSportReceived(BluetoothDevice device, List<HistoryOfSport> sports) {
                if (WearManager.this.mHistoryOfSportCallback != null) {
                    WearManager.this.mHistoryOfSportCallback.onHistoryOfSportReceived(device, sports);
                }
            }

            @Override // com.android.chileaf.fitness.callback.HistoryOfHRRecordCallback
            public void onHistoryOfHRRecordReceived(BluetoothDevice device, List<HistoryOfRecord> records) {
                if (WearManager.this.mHistoryOfHRRecordCallback != null) {
                    WearManager.this.mHistoryOfHRRecordCallback.onHistoryOfHRRecordReceived(device, records);
                }
            }

            @Override // com.android.chileaf.fitness.callback.HistoryOfHRDataCallback
            public void onHistoryOfHRDataReceived(BluetoothDevice device, List<HistoryOfHeartRate> heartRates) {
                if (WearManager.this.mHistoryOfHRDataCallback != null) {
                    WearManager.this.mHistoryOfHRDataCallback.onHistoryOfHRDataReceived(device, heartRates);
                }
            }

            @Override // com.android.chileaf.fitness.callback.HistoryOfRRRecordCallback
            public void onHistoryOfRRRecordReceived(BluetoothDevice device, List<HistoryOfRecord> records) {
                if (WearManager.this.mHistoryOfRRRecordCallback != null) {
                    WearManager.this.mHistoryOfRRRecordCallback.onHistoryOfRRRecordReceived(device, records);
                }
            }

            @Override // com.android.chileaf.fitness.callback.HistoryOfRRDataCallback
            public void onHistoryOfRRDataReceived(BluetoothDevice device, List<HistoryOfRespiratoryRate> respiratoryRates) {
                if (WearManager.this.mHistoryOfRRDataCallback != null) {
                    WearManager.this.mHistoryOfRRDataCallback.onHistoryOfRRDataReceived(device, respiratoryRates);
                }
            }

            @Override // com.android.chileaf.fitness.callback.IntervalStepCallback
            public void onIntervalStepReceived(BluetoothDevice device, List<IntervalStep> steps) {
                if (WearManager.this.mIntervalStepsCallback != null) {
                    WearManager.this.mIntervalStepsCallback.onIntervalStepReceived(device, steps);
                }
            }

            @Override // com.android.chileaf.fitness.callback.SingleTapRecordCallback
            public void onSingleTapRecordReceived(BluetoothDevice device, List<HistoryOfRecord> records) {
                if (WearManager.this.mSingleTapRecordCallback != null) {
                    WearManager.this.mSingleTapRecordCallback.onSingleTapRecordReceived(device, records);
                }
            }

            @Override // com.android.chileaf.fitness.callback.HeartRateStatusCallback
            public void onHeartRateStatusReceived(BluetoothDevice device, int min, int max, int goal) {
                if (WearManager.this.mHeartRateStatusCallback != null) {
                    WearManager.this.mHeartRateStatusCallback.onHeartRateStatusReceived(device, min, max, goal);
                }
            }

            @Override // com.android.chileaf.fitness.callback.HistoryOf3DDataCallback
            public void onHistoryOf3DDataReceived(BluetoothDevice device, HistoryOf3D history, boolean finish) {
                if (WearManager.this.mHistoryOf3DDataCallback != null) {
                    WearManager.this.mHistoryOf3DDataCallback.onHistoryOf3DDataReceived(device, history, finish);
                }
            }

            @Override // com.android.chileaf.fitness.callback.BloodOxygenCallback
            public void onBloodOxygenReceived(BluetoothDevice device, int bSwitch, String value, int gesture, int piValue, int onwrist) {
                if (WearManager.this.mBloodOxygenCallback != null) {
                    WearManager.this.mBloodOxygenCallback.onBloodOxygenReceived(device, bSwitch, value, gesture, piValue, onwrist);
                }
            }

            @Override // com.android.chileaf.fitness.callback.TemperatureCallback
            public void onTemperatureReceived(BluetoothDevice device, float environment, float wrist, float body) {
                if (WearManager.this.mTemperatureCallback != null) {
                    WearManager.this.mTemperatureCallback.onTemperatureReceived(device, environment, wrist, body);
                }
            }

            @Override // com.android.chileaf.fitness.callback.HistoryOfSingleRecordCallback
            public void onHistorySingleRecordReceived(BluetoothDevice device, long stamp, long step, long distance, long calorie) {
                if (WearManager.this.mHistoryOfSingleRecordCallback != null) {
                    WearManager.this.mHistoryOfSingleRecordCallback.onHistorySingleRecordReceived(device, stamp, step, distance, calorie);
                }
            }

            @Override // com.android.chileaf.fitness.callback.HeartRateAlarmCallback
            public void onHeartRateAlarmReceived(BluetoothDevice device, long stamp, boolean enabled) {
                if (WearManager.this.mHeartRateAlarmCallback != null) {
                    WearManager.this.mHeartRateAlarmCallback.onHeartRateAlarmReceived(device, stamp, enabled);
                }
            }

            @Override // com.android.chileaf.fitness.callback.AccelerometerCallback
            public void onAccelerometerReceived(BluetoothDevice device, int x, int y, int z) {
                if (WearManager.this.mAccelerometerCallback != null) {
                    WearManager.this.mAccelerometerCallback.onAccelerometerReceived(device, x, y, z);
                }
            }

            @Override // com.android.chileaf.fitness.callback.HeartRateMaxCallback
            public void onHeartRateMaxReceived(BluetoothDevice device, int max) {
                if (WearManager.this.mHeartRateMaxCallback != null) {
                    WearManager.this.mHeartRateMaxCallback.onHeartRateMaxReceived(device, max);
                }
            }

            @Override // com.android.chileaf.fitness.callback.HistoryOfSleepCallback
            public void onHistoryOfSleepReceived(BluetoothDevice device, List<HistorySleep> sleeps) {
                if (WearManager.this.mHistoryOfSleepCallback != null) {
                    WearManager.this.mHistoryOfSleepCallback.onHistoryOfSleepReceived(device, sleeps);
                }
            }

            @Override // com.android.chileaf.fitness.callback.Sensor3DFrequencyCallback
            public void onSensor3DFrequencyReceived(BluetoothDevice device, int frequency) {
                if (WearManager.this.mSensor3DFrequencyCallback != null) {
                    WearManager.this.mSensor3DFrequencyCallback.onSensor3DFrequencyReceived(device, frequency);
                }
            }

            @Override // com.android.chileaf.fitness.callback.Sensor3DStatusCallback
            public void onSensor3DStatusReceived(BluetoothDevice device, boolean enabled) {
                if (WearManager.this.mSensor3DStatusCallback != null) {
                    WearManager.this.mSensor3DStatusCallback.onSensor3DStatusReceived(device, enabled);
                }
            }

            @Override // com.android.chileaf.fitness.callback.Sensor6DFrequencyCallback
            public void onSensor6DFrequencyReceived(BluetoothDevice device, int sensor) {
                if (WearManager.this.mSensor6DFrequencyCallback != null) {
                    WearManager.this.mSensor6DFrequencyCallback.onSensor6DFrequencyReceived(device, sensor);
                }
            }

            @Override // com.android.chileaf.fitness.callback.Sensor6DRawDataCallback
            public void onSensor6DRawDataReceived(BluetoothDevice device, long utc, int sequence, int gyroscopeX, int gyroscopeY, int gyroscopeZ, int accelerometerX, int accelerometerY, int accelerometerZ) {
                if (WearManager.this.mSensor6DRawDataCallback != null) {
                    WearManager.this.mSensor6DRawDataCallback.onSensor6DRawDataReceived(device, utc, sequence, gyroscopeX, gyroscopeY, gyroscopeZ, accelerometerX, accelerometerY, accelerometerZ);
                }
            }
        };
    }

    @Override // com.android.chileaf.fitness.FitnessManager
    public void checkModel(String modelName, boolean isCL833) {
        boolean cl833 = checkMode(modelName);
        this.mReceivedDataCallback.setCL833(cl833 && isCL833);
        log(3, String.format("Check modelName:%s isCL833:%s", modelName, Boolean.valueOf(isCL833)));
    }

    private boolean checkMode(String name) {
        for (String device : MODE_NAMES) {
            if (device.equalsIgnoreCase(name)) {
                return true;
            }
        }
        return false;
    }

    @Override // com.android.chileaf.fitness.FitnessManager, no.nordicsemi.android.ble.BleManager
    protected BleManager.BleManagerGattCallback getGattCallback() {
        return new WearManagerGattCallback();
    }

    private final class WearScanCallback extends ScanCallback {
        private final FilterScanCallback mCallback;

        private WearScanCallback(FilterScanCallback callback) {
            this.mCallback = callback;
        }

        private boolean matchDeviceName(BluetoothDevice device) {
            String name;
            if (WearManager.this.mFilterNames == null) {
                return true;
            }
            if (device != null && (name = device.getName()) != null && !TextUtils.isEmpty(name)) {
                for (String filterName : WearManager.this.mFilterNames) {
                    if (name.contains(filterName)) {
                        return true;
                    }
                }
            }
            return false;
        }

        @Override // no.nordicsemi.android.support.v18.scanner.ScanCallback
        public void onScanResult(int callbackType, ScanResult result) {
            super.onScanResult(callbackType, result);
            FilterScanCallback filterScanCallback = this.mCallback;
            if (filterScanCallback != null) {
                filterScanCallback.onScanResult(callbackType, result);
            }
        }

        @Override // no.nordicsemi.android.support.v18.scanner.ScanCallback
        public void onBatchScanResults(List<ScanResult> results) {
            List<ScanResult> scanDevices = new ArrayList<>();
            for (ScanResult result : results) {
                BluetoothDevice device = result.getDevice();
                if (matchDeviceName(device)) {
                    scanDevices.add(result);
                }
            }
            FilterScanCallback filterScanCallback = this.mCallback;
            if (filterScanCallback != null) {
                filterScanCallback.onBatchScanResults(results);
                this.mCallback.onFilterScanResults(scanDevices);
            }
        }

        @Override // no.nordicsemi.android.support.v18.scanner.ScanCallback
        public void onScanFailed(int errorCode) {
            super.onScanFailed(errorCode);
            FilterScanCallback filterScanCallback = this.mCallback;
            if (filterScanCallback != null) {
                filterScanCallback.onScanFailed(errorCode);
            }
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    final class WearManagerGattCallback extends FitnessManager<WearManagerCallbacks>.FitnessManagerGattCallback {
        private WearManagerGattCallback() {
            super();
        }

        @Override // com.android.chileaf.fitness.FitnessManager.FitnessManagerGattCallback, no.nordicsemi.android.ble.BleManagerHandler
        protected void initialize() {
            super.initialize();
            WearManager wearManager = WearManager.this;
            wearManager.readCharacteristic(wearManager.mBodySensorLocationCharacteristic).with((DataReceivedCallback) WearManager.this.mBodySensorLocationDataCallback).fail(new FailCallback() { // from class: com.android.chileaf.-$$Lambda$WearManager$WearManagerGattCallback$LBWa6RfMf2LrxSuy5hCgi1wYTBc
                @Override // no.nordicsemi.android.ble.callback.FailCallback
                public final void onRequestFailed(BluetoothDevice bluetoothDevice, int i) {
                    this.f$0.lambda$initialize$0$WearManager$WearManagerGattCallback(bluetoothDevice, i);
                }
            }).enqueue();
            WearManager wearManager2 = WearManager.this;
            wearManager2.setNotificationCallback(wearManager2.mHeartRateCharacteristic).with(WearManager.this.mHeartRateMeasureDataCallback);
            WearManager wearManager3 = WearManager.this;
            wearManager3.enableNotifications(wearManager3.mHeartRateCharacteristic).enqueue();
            WearManager wearManager4 = WearManager.this;
            wearManager4.setNotificationCallback(wearManager4.mRXCharacteristic).with(WearManager.this.mReceivedDataCallback);
            WearManager wearManager5 = WearManager.this;
            wearManager5.enableNotifications(wearManager5.mRXCharacteristic).done(new SuccessCallback() { // from class: com.android.chileaf.-$$Lambda$WearManager$WearManagerGattCallback$kaQ8yCm6Xyo1TD1O7aRUtcM6XdU
                @Override // no.nordicsemi.android.ble.callback.SuccessCallback
                public final void onRequestCompleted(BluetoothDevice bluetoothDevice) {
                    this.f$0.lambda$initialize$1$WearManager$WearManagerGattCallback(bluetoothDevice);
                }
            }).fail(new FailCallback() { // from class: com.android.chileaf.-$$Lambda$WearManager$WearManagerGattCallback$4_WG7TNlt3VvhBe4ICwIlUuh7Z0
                @Override // no.nordicsemi.android.ble.callback.FailCallback
                public final void onRequestFailed(BluetoothDevice bluetoothDevice, int i) {
                    this.f$0.lambda$initialize$2$WearManager$WearManagerGattCallback(bluetoothDevice, i);
                }
            }).enqueue();
            if (WearManager.this.mCustomRxCharacteristic != null) {
                WearManager wearManager6 = WearManager.this;
                wearManager6.setNotificationCallback(wearManager6.mCustomRxCharacteristic).with(new DataReceivedCallback() { // from class: com.android.chileaf.-$$Lambda$WearManager$WearManagerGattCallback$I1gw52-6JZv6T-5oT-nJ0tOeMaQ
                    @Override // no.nordicsemi.android.ble.callback.DataReceivedCallback
                    public final void onDataReceived(BluetoothDevice bluetoothDevice, Data data) {
                        this.f$0.lambda$initialize$3$WearManager$WearManagerGattCallback(bluetoothDevice, data);
                    }
                });
                WearManager wearManager7 = WearManager.this;
                wearManager7.enableNotifications(wearManager7.mCustomRxCharacteristic).enqueue();
            }
        }

        public /* synthetic */ void lambda$initialize$0$WearManager$WearManagerGattCallback(BluetoothDevice device, int status) {
            WearManager.this.log(5, "Body Sensor Location characteristic not found");
        }

        public /* synthetic */ void lambda$initialize$1$WearManager$WearManagerGattCallback(BluetoothDevice device) {
            WearManager.this.log(3, "Rx notifications enabled");
        }

        public /* synthetic */ void lambda$initialize$2$WearManager$WearManagerGattCallback(BluetoothDevice device, int status) {
            WearManager.this.log(5, "Rx characteristic not found");
        }

        public /* synthetic */ void lambda$initialize$3$WearManager$WearManagerGattCallback(BluetoothDevice device, Data data) {
            if (WearManager.this.mCustomDataReceivedCallback != null) {
                WearManager.this.mCustomDataReceivedCallback.onDataReceived(device, data.getValue());
            }
        }

        @Override // com.android.chileaf.fitness.FitnessManager.FitnessManagerGattCallback, no.nordicsemi.android.ble.BleManagerHandler
        public boolean isRequiredServiceSupported(BluetoothGatt gatt) {
            super.isRequiredServiceSupported(gatt);
            BluetoothGattService hrService = gatt.getService(WearManager.HR_SERVICE_UUID);
            if (hrService != null) {
                WearManager.this.mHeartRateCharacteristic = hrService.getCharacteristic(WearManager.HEART_RATE_MEASUREMENT_CHARACTERISTIC_UUID);
            }
            return WearManager.this.mHeartRateCharacteristic != null;
        }

        @Override // com.android.chileaf.fitness.FitnessManager.FitnessManagerGattCallback, no.nordicsemi.android.ble.BleManagerHandler
        protected boolean isOptionalServiceSupported(final BluetoothGatt gatt) {
            super.isOptionalServiceSupported(gatt);
            BluetoothGattService service = gatt.getService(WearManager.HR_SERVICE_UUID);
            if (service != null) {
                WearManager.this.mBodySensorLocationCharacteristic = service.getCharacteristic(WearManager.BODY_SENSOR_LOCATION_CHARACTERISTIC_UUID);
            }
            return WearManager.this.mBodySensorLocationCharacteristic != null;
        }

        @Override // no.nordicsemi.android.ble.BleManagerHandler
        protected void onDeviceReady() {
            super.onDeviceReady();
            WearManager.this.setUTCTime();
        }

        @Override // com.android.chileaf.fitness.FitnessManager.FitnessManagerGattCallback, no.nordicsemi.android.ble.BleManagerHandler
        protected void onDeviceDisconnected() {
            super.onDeviceDisconnected();
            WearManager.this.mBodySensorLocationCharacteristic = null;
            WearManager.this.mHeartRateCharacteristic = null;
            WearManager.this.mReceivedDataCallback.setCL833(false);
        }

        @Override // com.android.chileaf.fitness.FitnessManager.FitnessManagerGattCallback, no.nordicsemi.android.ble.BleManagerHandler
        protected void onServicesInvalidated() {
            super.onServicesInvalidated();
            WearManager.this.mBodySensorLocationCharacteristic = null;
            WearManager.this.mHeartRateCharacteristic = null;
            WearManager.this.mReceivedDataCallback.setCL833(false);
        }
    }

    public void addBodySportCallback(final BodySportCallback callback) {
        this.mBodySportCallback = callback;
    }

    public void addBodyHealthCallback(final BodyHealthCallback callback) {
        this.mBodyHealthCallback = callback;
    }

    public void addHeartRateMeasurementCallback(final HeartRateMeasurementCallback callback) {
        this.mHeartRateMeasurementCallback = callback;
    }

    public void setBluetoothStatusCallback(BluetoothStatusCallback callback) {
        this.mBluetoothStatusCallback = callback;
    }

    public void addUserInfoCallback(final UserInfoCallback callback) {
        this.mUserInfoCallback = callback;
    }

    public void addHistoryOfSportCallback(final HistoryOfSportCallback callback) {
        this.mHistoryOfSportCallback = callback;
    }

    public void addHistoryOfHRRecordCallback(final HistoryOfHRRecordCallback callback) {
        this.mHistoryOfHRRecordCallback = callback;
    }

    public void addHistoryOfHRDataCallback(final HistoryOfHRDataCallback callback) {
        this.mHistoryOfHRDataCallback = callback;
    }

    public void addHistoryOfRRRecordCallback(final HistoryOfRRRecordCallback callback) {
        this.mHistoryOfRRRecordCallback = callback;
    }

    public void addHistoryOfRRDataCallback(final HistoryOfRRDataCallback callback) {
        this.mHistoryOfRRDataCallback = callback;
    }

    public void addIntervalStepCallback(final IntervalStepCallback callback) {
        this.mIntervalStepsCallback = callback;
    }

    public void addSingleTapRecordCallback(final SingleTapRecordCallback callback) {
        this.mSingleTapRecordCallback = callback;
    }

    public void addHistoryOf3DDataCallback(final HistoryOf3DDataCallback callback) {
        this.mHistoryOf3DDataCallback = callback;
    }

    public void addHeartRateStatusCallback(HeartRateStatusCallback callback) {
        this.mHeartRateStatusCallback = callback;
    }

    public void addBloodOxygenCallback(final BloodOxygenCallback callback) {
        this.mBloodOxygenCallback = callback;
    }

    public void addTemperatureCallback(final TemperatureCallback callback) {
        this.mTemperatureCallback = callback;
    }

    public void addHistoryOfSingleRecordCallback(final HistoryOfSingleRecordCallback callback) {
        this.mHistoryOfSingleRecordCallback = callback;
    }

    public void addHeartRateAlarmCallback(HeartRateAlarmCallback callback) {
        this.mHeartRateAlarmCallback = callback;
    }

    public void addAccelerometerCallback(final AccelerometerCallback callback) {
        this.mAccelerometerCallback = callback;
    }

    public void addHeartRateMaxCallback(HeartRateMaxCallback callback) {
        this.mHeartRateMaxCallback = callback;
    }

    public void addHistoryOfSleepCallback(HistoryOfSleepCallback callback) {
        this.mHistoryOfSleepCallback = callback;
    }

    public void addSensor3DFrequencyCallback(Sensor3DFrequencyCallback callback) {
        this.mSensor3DFrequencyCallback = callback;
    }

    public void addSensor3DStatusCallback(Sensor3DStatusCallback callback) {
        this.mSensor3DStatusCallback = callback;
    }

    public void addSensor6DFrequencyCallback(final Sensor6DFrequencyCallback callback) {
        this.mSensor6DFrequencyCallback = callback;
    }

    public void addSensor6DRawDataCallback(final Sensor6DRawDataCallback callback) {
        this.mSensor6DRawDataCallback = callback;
    }

    public void addBodySportHealthCallback(final BodySportHealthCallback callback) {
        this.mBodySportHealthCallback = callback;
    }

    public void addHistoryOfStepRecordCallback(final HistoryOfStepRecordCallback callback) {
        this.mHistoryOfStepRecordCallback = callback;
    }

    public void addHistoryOfStepDataCallback(final HistoryOfStepDataCallback callback) {
        this.mHistoryOfStepDataCallback = callback;
    }

    public void setFilterNames(String... filterNames) {
        this.mFilterNames = filterNames;
    }

    public void startScan(final FilterScanCallback callback) {
        this.mScanCallback = new WearScanCallback(callback);
        BluetoothLeScannerCompat scanner = BluetoothLeScannerCompat.getScanner();
        ScanSettings settings = new ScanSettings.Builder().setLegacy(false).setReportDelay(1000L).setUseHardwareBatchingIfSupported(false).setScanMode(2).build();
        List<ScanFilter> filters = new ArrayList<>();
        ParcelUuid uuid = new ParcelUuid(HR_SERVICE_UUID);
        filters.add(new ScanFilter.Builder().setServiceUuid(uuid).build());
        scanner.startScan(filters, settings, this.mScanCallback);
    }

    public void stopScan() {
        if (this.mScanCallback != null) {
            BluetoothLeScannerCompat scanner = BluetoothLeScannerCompat.getScanner();
            scanner.stopScan(this.mScanCallback);
        }
    }

    private void sendCommand(final byte cmd, final int... values) {
        byte[] header;
        if (values != null) {
            int len = values.length + 4;
            byte[] header2 = HexUtil.compose(255, len, cmd);
            byte[] bytes = HexUtil.compose(values);
            header = HexUtil.append(header2, bytes);
        } else {
            header = HexUtil.compose(255, 4, cmd);
        }
        byte check = checkSum(header);
        byte[] command = HexUtil.append(header, check);
        writeTxCharacteristic(command);
    }

    protected int[] utc2Bytes(final long stamp) {
        int[] utcArray = {(int) (stamp >> 24), (int) (stamp >> 16), (int) (stamp >> 8), (int) stamp};
        return utcArray;
    }

    public void setUTCTime() {
        setUTCTime(DateUtil.getZoneUTC());
    }

    public void setUTCTime(final long stamp) {
        sendCommand((byte) 8, utc2Bytes(stamp));
    }

    public void shutdown() {
        sendCommand((byte) -15, 0);
    }

    public void restoration() {
        sendCommand((byte) -13, 0);
    }

    public void setBluetoothDisabled() {
        sendCommand((byte) 63, 2);
    }

    public void getHistoryOfSport() {
        this.mReceivedDataCallback.clearType(2);
        sendCommand((byte) 22, 0);
    }

    public void getHistoryOfHRRecord() {
        this.mReceivedDataCallback.clearType(4);
        sendCommand((byte) 33, 0);
    }

    public void getHistoryOfHRData(final long stamp) {
        this.mReceivedDataCallback.clearType(6);
        sendCommand((byte) 34, HexUtil.append(1, utc2Bytes(stamp)));
    }

    public void getHistoryOfRRRecord() {
        this.mReceivedDataCallback.clearType(8);
        sendCommand((byte) 36, new int[0]);
    }

    public void getHistoryOfRRData(final long stamp) {
        this.mReceivedDataCallback.clearType(16);
        sendCommand((byte) 37, HexUtil.append(1, utc2Bytes(stamp)));
    }

    public void getHistoryOfStepRecord() {
        this.mReceivedDataCallback.clearType(32);
        sendCommand((byte) -112, new int[0]);
    }

    public void getHistoryOfStepData(final long stamp) {
        this.mReceivedDataCallback.clearType(34);
        sendCommand((byte) -111, HexUtil.append(1, utc2Bytes(stamp)));
    }

    public void getIntervalSteps() {
        this.mReceivedDataCallback.clearType(18);
        sendCommand((byte) 64, 0);
    }

    public void getSingleTapRecords() {
        this.mReceivedDataCallback.clearType(20);
        sendCommand((byte) 66, 0);
    }

    public void getHistoryOfSleep() {
        this.mReceivedDataCallback.clearType(22);
        sendCommand((byte) 5, 2);
    }

    public void getUserInfo() {
        sendCommand((byte) 3, 0);
    }

    public void setUserInfo(final int age, final int sex, final int weight, final int height, final long userId) {
        int[] command = {(byte) age, (byte) sex, (byte) weight, (byte) height, (byte) ((userId >> 32) & 255), (byte) ((userId >> 24) & 255), (byte) ((userId >> 16) & 255), (byte) ((userId >> 8) & 255), (byte) (255 & userId)};
        sendCommand((byte) 4, command);
    }

    public void getHeartRateStatus() {
        sendCommand((byte) 70, 0);
    }

    public void setHeartRateStatus(int min, int max, int goal) {
        sendCommand((byte) 70, 1, (byte) min, (byte) max, (byte) goal);
    }

    public void setHeartRateMax(int max) {
        sendCommand((byte) 116, 0, 6, (byte) max);
    }

    public void getHeartRateMax() {
        sendCommand((byte) 117, 0, 6);
    }

    public void setBloodOxygen(final int mode) {
        int[] command = {(byte) mode, 0};
        sendCommand((byte) 55, command);
    }

    public void setHeartRateAlarm(boolean z) {
        sendCommand((byte) 87, z ? 1 : 0);
    }

    public void getHeartRateAlarm() {
        sendCommand((byte) 91, 0);
    }

    public void getHistoryOfSingleRecord(final long stamp) {
        sendCommand((byte) 73, utc2Bytes(stamp));
    }

    public void set3DFrequency(int frequency) {
        sendCommand((byte) 116, 0, 11, (byte) frequency);
    }

    public void get3DFrequency() {
        sendCommand((byte) 117, 0, 11);
    }

    public void set3DEnabled(boolean z) {
        sendCommand((byte) 116, 0, 12, z ? 1 : 0);
    }

    public void get3DStatus() {
        sendCommand((byte) 117, 0, 12);
    }

    public void get6DFrequency() {
        sendCommand((byte) 97, 0);
    }

    public void set6DFrequency(int frequency) {
        sendCommand((byte) 98, frequency);
    }

    public void setCustomDataReceivedCallback(CustomDataReceivedCallback customDataReceivedCallback) {
        this.mCustomDataReceivedCallback = customDataReceivedCallback;
    }

    public void getHistoryOf3D() {
        sendCommand((byte) 119, 0);
    }

    public String dfuMode() {
        String address = getDFUAddress();
        byte[] command = new byte[4];
        command[0] = -1;
        command[1] = 4;
        command[2] = 39;
        command[3] = checkSum(command);
        writeTxCharacteristic(command);
        return address;
    }

    private String getDFUAddress() {
        BluetoothDevice device = getBluetoothDevice();
        if (device == null) {
            return null;
        }
        String deviceAddress = device.getAddress();
        String firstBytes = deviceAddress.substring(0, 15);
        String lastByte = deviceAddress.substring(15);
        String lastByteIncremented = String.format(Locale.US, "%02X", Integer.valueOf((Integer.valueOf(lastByte, 16).intValue() + 1) & 255));
        return firstBytes + lastByteIncremented;
    }
}
