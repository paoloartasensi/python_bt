package com.android.chileaf.fitness;

import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattService;
import android.content.Context;
import android.os.Build;
import android.text.TextUtils;
import com.android.chileaf.fitness.FitnessManagerCallbacks;
import com.android.chileaf.fitness.common.battery.BatteryLevelDataCallback;
import com.android.chileaf.util.HexUtil;
import com.android.chileaf.util.LogUtil;
import java.util.List;
import java.util.UUID;
import no.nordicsemi.android.ble.BleManager;
import no.nordicsemi.android.ble.LegacyBleManager;
import no.nordicsemi.android.ble.callback.DataReceivedCallback;
import no.nordicsemi.android.ble.callback.DataSentCallback;
import no.nordicsemi.android.ble.callback.FailCallback;
import no.nordicsemi.android.ble.callback.RssiCallback;
import no.nordicsemi.android.ble.callback.SuccessCallback;
import no.nordicsemi.android.ble.data.Data;
import no.nordicsemi.android.ble.utils.ParserUtils;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public abstract class FitnessManager<T extends FitnessManagerCallbacks> extends LegacyBleManager<T> {
    protected static final String CUSTOM_CHAR_UUID = "AAE21542-71B5-42A1-8C3C-F9CF6AC969D0";
    protected static final String SPEC_CHAR_UUID = "AAE21541-71B5-42A1-8C3C-F9CF6AC969D0";
    protected boolean isContainCL833;
    private Integer mBatteryLevel;
    private BluetoothGattCharacteristic mBatteryLevelCharacteristic;
    private final DataReceivedCallback mBatteryLevelDataCallback;
    protected BluetoothGattCharacteristic mCustomRxCharacteristic;
    private final DataReceivedCallback mFirmwareCallBack;
    private String mFirmwareVersion;
    private final DataReceivedCallback mHardwareCallBack;
    private String mHardwareVersion;
    private final DataReceivedCallback mModelCallBack;
    private String mModelName;
    private BluetoothGattCharacteristic mProfileFirmwareCharacteristic;
    private BluetoothGattCharacteristic mProfileHardwareCharacteristic;
    private BluetoothGattCharacteristic mProfileModelCharacteristic;
    private BluetoothGattCharacteristic mProfileSerialCharacteristic;
    private BluetoothGattCharacteristic mProfileSoftwareCharacteristic;
    private BluetoothGattCharacteristic mProfileSystemCharacteristic;
    private BluetoothGattCharacteristic mProfileVendorCharacteristic;
    protected BluetoothGattCharacteristic mRXCharacteristic;
    private Integer mRssi;
    private final RssiCallback mRssiCallback;
    private String mSerialNumber;
    private final DataReceivedCallback mSerialNumberCallBack;
    private final DataReceivedCallback mSoftwareCallBack;
    private String mSoftwareVersion;
    private final DataReceivedCallback mSystemCallBack;
    private String mSystemId;
    protected BluetoothGattCharacteristic mTXCharacteristic;
    private final DataReceivedCallback mVendorCallBack;
    private String mVendorName;
    protected static final UUID SERVICE_UUID = UUID.fromString("AAE28F00-71B5-42A1-8C3C-F9CF6AC969D0");
    protected static final UUID RX_CHAR_UUID = UUID.fromString("AAE28F01-71B5-42A1-8C3C-F9CF6AC969D0");
    protected static final UUID TX_CHAR_UUID = UUID.fromString("AAE28F02-71B5-42A1-8C3C-F9CF6AC969D0");
    private static final UUID BATTERY_SERVICE_UUID = UUID.fromString("0000180F-0000-1000-8000-00805f9b34fb");
    private static final UUID BATTERY_LEVEL_CHARACTERISTIC_UUID = UUID.fromString("00002A19-0000-1000-8000-00805f9b34fb");
    private static final UUID PROFILE_SERVICE_UUID = UUID.fromString("0000180A-0000-1000-8000-00805f9b34fb");
    private static final UUID PROFILE_SYSTEM_CHARACTERISTIC_UUID = UUID.fromString("00002A23-0000-1000-8000-00805f9b34fb");
    private static final UUID PROFILE_MODEL_CHARACTERISTIC_UUID = UUID.fromString("00002A24-0000-1000-8000-00805f9b34fb");
    private static final UUID PROFILE_SERIAL_CHARACTERISTIC_UUID = UUID.fromString("00002A25-0000-1000-8000-00805f9b34fb");
    private static final UUID PROFILE_FIRMWARE_CHARACTERISTIC_UUID = UUID.fromString("00002A26-0000-1000-8000-00805f9b34fb");
    private static final UUID PROFILE_HARDWARE_CHARACTERISTIC_UUID = UUID.fromString("00002A27-0000-1000-8000-00805f9b34fb");
    private static final UUID PROFILE_SOFTWARE_CHARACTERISTIC_UUID = UUID.fromString("00002A28-0000-1000-8000-00805f9b34fb");
    private static final UUID PROFILE_VENDOR_CHARACTERISTIC_UUID = UUID.fromString("00002A29-0000-1000-8000-00805f9b34fb");

    public abstract void checkModel(String modelName, boolean isCL833);

    public FitnessManager(final Context context) {
        super(context);
        this.isContainCL833 = false;
        this.mRssiCallback = new RssiCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$aPdDado6CbH7ehWCTVn5mF1N_uQ
            @Override // no.nordicsemi.android.ble.callback.RssiCallback
            public final void onRssiRead(BluetoothDevice bluetoothDevice, int i) {
                this.f$0.lambda$new$0$FitnessManager(bluetoothDevice, i);
            }
        };
        this.mSystemCallBack = new DataReceivedCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$6UwmBdIqNtp7mG82vRkKYRO1-S4
            @Override // no.nordicsemi.android.ble.callback.DataReceivedCallback
            public final void onDataReceived(BluetoothDevice bluetoothDevice, Data data) {
                this.f$0.lambda$new$1$FitnessManager(bluetoothDevice, data);
            }
        };
        this.mModelCallBack = new DataReceivedCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$BdcI0uAHUoFc9bbmjiCLz_NHvh4
            @Override // no.nordicsemi.android.ble.callback.DataReceivedCallback
            public final void onDataReceived(BluetoothDevice bluetoothDevice, Data data) {
                this.f$0.lambda$new$2$FitnessManager(bluetoothDevice, data);
            }
        };
        this.mSerialNumberCallBack = new DataReceivedCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$1l1AGSGKv4uCjWKyIIUIt583c4k
            @Override // no.nordicsemi.android.ble.callback.DataReceivedCallback
            public final void onDataReceived(BluetoothDevice bluetoothDevice, Data data) {
                this.f$0.lambda$new$3$FitnessManager(bluetoothDevice, data);
            }
        };
        this.mFirmwareCallBack = new DataReceivedCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$Re7A3bQMrqEG_cLQvzqkGgQPE04
            @Override // no.nordicsemi.android.ble.callback.DataReceivedCallback
            public final void onDataReceived(BluetoothDevice bluetoothDevice, Data data) {
                this.f$0.lambda$new$4$FitnessManager(bluetoothDevice, data);
            }
        };
        this.mHardwareCallBack = new DataReceivedCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$jRSYesjZRim--gHLY7bJpVLOzD4
            @Override // no.nordicsemi.android.ble.callback.DataReceivedCallback
            public final void onDataReceived(BluetoothDevice bluetoothDevice, Data data) {
                this.f$0.lambda$new$5$FitnessManager(bluetoothDevice, data);
            }
        };
        this.mSoftwareCallBack = new DataReceivedCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$1rf3D_osDeM1zWZaqdjesIaPVjQ
            @Override // no.nordicsemi.android.ble.callback.DataReceivedCallback
            public final void onDataReceived(BluetoothDevice bluetoothDevice, Data data) {
                this.f$0.lambda$new$6$FitnessManager(bluetoothDevice, data);
            }
        };
        this.mVendorCallBack = new DataReceivedCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$1Dsddskvzgx9wXm9V3fq34C9jxg
            @Override // no.nordicsemi.android.ble.callback.DataReceivedCallback
            public final void onDataReceived(BluetoothDevice bluetoothDevice, Data data) {
                this.f$0.lambda$new$7$FitnessManager(bluetoothDevice, data);
            }
        };
        this.mBatteryLevelDataCallback = new BatteryLevelDataCallback() { // from class: com.android.chileaf.fitness.FitnessManager.2
            @Override // com.android.chileaf.fitness.common.battery.BatteryLevelCallback
            public void onBatteryLevelChanged(final BluetoothDevice device, final int batteryLevel) {
                FitnessManager.this.log(4, "Battery Level received: " + batteryLevel + "%");
                ((FitnessManagerCallbacks) FitnessManager.this.mCallbacks).onBatteryLevelChanged(device, batteryLevel);
                FitnessManager.this.mBatteryLevel = Integer.valueOf(batteryLevel);
                if (FitnessManager.this.isReadRssi()) {
                    FitnessManager.this.readRssi().with(FitnessManager.this.mRssiCallback).enqueue();
                }
            }

            @Override // no.nordicsemi.android.ble.callback.profile.ProfileReadResponse, no.nordicsemi.android.ble.callback.profile.ProfileDataCallback
            public void onInvalidDataReceived(final BluetoothDevice device, final Data data) {
                FitnessManager.this.log(5, "Invalid Battery Level data received: " + data);
            }
        };
    }

    /* JADX WARN: Multi-variable type inference failed */
    public void setManagerCallbacks(final T callbacks) {
        super.setGattCallbacks(callbacks);
        this.mCallbacks = callbacks;
    }

    @Override // no.nordicsemi.android.ble.BleManager
    protected BleManager.BleManagerGattCallback getGattCallback() {
        return new BleManager.BleManagerGattCallback() { // from class: com.android.chileaf.fitness.FitnessManager.1
            @Override // no.nordicsemi.android.ble.BleManagerHandler
            protected boolean isRequiredServiceSupported(BluetoothGatt gatt) {
                return false;
            }

            @Override // no.nordicsemi.android.ble.BleManagerHandler
            protected void onServicesInvalidated() {
            }
        };
    }

    public void setDebug(boolean debug) {
        LogUtil.setDebug(debug);
    }

    @Override // no.nordicsemi.android.ble.BleManager, no.nordicsemi.android.ble.utils.ILogger
    public void log(final int priority, final String message) {
        LogUtil.log(6, priority, message, new Object[0]);
    }

    protected byte checkSum(final byte[] data) {
        int result = 0;
        for (byte item : data) {
            result += item;
        }
        return (byte) (((-result) ^ 58) & 255);
    }

    public Integer getRssi() {
        return this.mRssi;
    }

    public Integer getBatteryLevel() {
        return this.mBatteryLevel;
    }

    public String getSystemId() {
        return this.mSystemId;
    }

    public String getModelName() {
        return this.mModelName;
    }

    public String getSerialNumber() {
        return this.mSerialNumber;
    }

    public String getFirmwareVersion() {
        return this.mFirmwareVersion;
    }

    public String getHardwareVersion() {
        return this.mHardwareVersion;
    }

    public String getSoftwareVersion() {
        return this.mSoftwareVersion;
    }

    public String getVendorName() {
        return this.mVendorName;
    }

    public boolean isReadRssi() {
        return true;
    }

    public /* synthetic */ void lambda$new$0$FitnessManager(BluetoothDevice device, int rssi) {
        ((FitnessManagerCallbacks) this.mCallbacks).onRssiRead(device, rssi);
        this.mRssi = Integer.valueOf(rssi);
    }

    public /* synthetic */ void lambda$new$1$FitnessManager(BluetoothDevice device, Data data) {
        if (data.size() > 0 && data.getValue() != null) {
            String systemId = HexUtil.byteArrayToString(data.getValue());
            if (!TextUtils.isEmpty(systemId)) {
                log(4, "System Id: " + systemId);
                ((FitnessManagerCallbacks) this.mCallbacks).onSystemId(device, systemId);
                this.mSystemId = systemId;
            }
        }
    }

    public /* synthetic */ void lambda$new$2$FitnessManager(BluetoothDevice device, Data data) {
        if (data.size() > 0 && data.getValue() != null) {
            String modelName = HexUtil.byteArrayToString(data.getValue());
            if (!TextUtils.isEmpty(modelName)) {
                log(4, "Model Name: " + modelName);
                checkModel(modelName, this.isContainCL833);
                ((FitnessManagerCallbacks) this.mCallbacks).onModelName(device, modelName);
                this.mModelName = modelName;
            }
        }
    }

    public /* synthetic */ void lambda$new$3$FitnessManager(BluetoothDevice device, Data data) {
        if (data.size() > 0 && data.getValue() != null) {
            String serialNumber = HexUtil.byteArrayToString(data.getValue());
            if (!TextUtils.isEmpty(serialNumber)) {
                log(4, "Serial Number: " + serialNumber);
                ((FitnessManagerCallbacks) this.mCallbacks).onSerialNumber(device, serialNumber);
                this.mSerialNumber = serialNumber;
            }
        }
    }

    public /* synthetic */ void lambda$new$4$FitnessManager(BluetoothDevice device, Data data) {
        if (data.size() > 0 && data.getValue() != null) {
            String firmware = HexUtil.byteArrayToString(data.getValue());
            if (!TextUtils.isEmpty(firmware)) {
                log(4, "Firmware Version: " + firmware);
                ((FitnessManagerCallbacks) this.mCallbacks).onFirmwareVersion(device, firmware);
                this.mFirmwareVersion = firmware;
            }
        }
    }

    public /* synthetic */ void lambda$new$5$FitnessManager(BluetoothDevice device, Data data) {
        if (data.size() > 0 && data.getValue() != null) {
            String value = HexUtil.byteArrayToString(data.getValue());
            if (!TextUtils.isEmpty(value)) {
                log(4, "Hardware Version: " + value);
                ((FitnessManagerCallbacks) this.mCallbacks).onHardwareVersion(device, value);
                this.mHardwareVersion = value;
            }
        }
    }

    public /* synthetic */ void lambda$new$6$FitnessManager(BluetoothDevice device, Data data) {
        if (data.size() > 0 && data.getValue() != null) {
            String value = HexUtil.byteArrayToString(data.getValue());
            if (!TextUtils.isEmpty(value)) {
                log(4, "Software Version: " + value);
                ((FitnessManagerCallbacks) this.mCallbacks).onSoftwareVersion(device, value);
                this.mSoftwareVersion = value;
            }
        }
    }

    public /* synthetic */ void lambda$new$7$FitnessManager(BluetoothDevice device, Data data) {
        if (data.size() > 0 && data.getValue() != null) {
            String value = HexUtil.byteArrayToString(data.getValue());
            if (!TextUtils.isEmpty(value)) {
                log(4, "Vendor Name: " + value);
                ((FitnessManagerCallbacks) this.mCallbacks).onVendorName(device, value);
                this.mVendorName = value;
            }
        }
    }

    public void readProfileCharacteristic() {
        if (isConnected()) {
            readCharacteristic(this.mProfileSystemCharacteristic).with(this.mSystemCallBack).fail(new FailCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$CVv7SsfA_7yp5_j8dmb3olM9tjk
                @Override // no.nordicsemi.android.ble.callback.FailCallback
                public final void onRequestFailed(BluetoothDevice bluetoothDevice, int i) {
                    this.f$0.lambda$readProfileCharacteristic$8$FitnessManager(bluetoothDevice, i);
                }
            }).enqueue();
            readCharacteristic(this.mProfileModelCharacteristic).with(this.mModelCallBack).fail(new FailCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$bkbp23U2XyW6NsSPL6a_gtuf7A8
                @Override // no.nordicsemi.android.ble.callback.FailCallback
                public final void onRequestFailed(BluetoothDevice bluetoothDevice, int i) {
                    this.f$0.lambda$readProfileCharacteristic$9$FitnessManager(bluetoothDevice, i);
                }
            }).enqueue();
            readCharacteristic(this.mProfileSerialCharacteristic).with(this.mSerialNumberCallBack).fail(new FailCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$CauT9kxFnVdIsIRVuPIu1qruPlc
                @Override // no.nordicsemi.android.ble.callback.FailCallback
                public final void onRequestFailed(BluetoothDevice bluetoothDevice, int i) {
                    this.f$0.lambda$readProfileCharacteristic$10$FitnessManager(bluetoothDevice, i);
                }
            }).enqueue();
            readCharacteristic(this.mProfileFirmwareCharacteristic).with(this.mFirmwareCallBack).fail(new FailCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$l9MwIWHyj3cmguXEpk3pnPEY2VY
                @Override // no.nordicsemi.android.ble.callback.FailCallback
                public final void onRequestFailed(BluetoothDevice bluetoothDevice, int i) {
                    this.f$0.lambda$readProfileCharacteristic$11$FitnessManager(bluetoothDevice, i);
                }
            }).enqueue();
            readCharacteristic(this.mProfileHardwareCharacteristic).with(this.mHardwareCallBack).fail(new FailCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$LMFeoCf-c6QBgPBikDMQ5vBd6jw
                @Override // no.nordicsemi.android.ble.callback.FailCallback
                public final void onRequestFailed(BluetoothDevice bluetoothDevice, int i) {
                    this.f$0.lambda$readProfileCharacteristic$12$FitnessManager(bluetoothDevice, i);
                }
            }).enqueue();
            readCharacteristic(this.mProfileSoftwareCharacteristic).with(this.mSoftwareCallBack).fail(new FailCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$er8TgCIbxxycuZ4VTVRh049EGNU
                @Override // no.nordicsemi.android.ble.callback.FailCallback
                public final void onRequestFailed(BluetoothDevice bluetoothDevice, int i) {
                    this.f$0.lambda$readProfileCharacteristic$13$FitnessManager(bluetoothDevice, i);
                }
            }).enqueue();
            readCharacteristic(this.mProfileVendorCharacteristic).with(this.mVendorCallBack).fail(new FailCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$WI-ECc3tI6-GzP71oyTp3P4c2ww
                @Override // no.nordicsemi.android.ble.callback.FailCallback
                public final void onRequestFailed(BluetoothDevice bluetoothDevice, int i) {
                    this.f$0.lambda$readProfileCharacteristic$14$FitnessManager(bluetoothDevice, i);
                }
            }).enqueue();
        }
    }

    public /* synthetic */ void lambda$readProfileCharacteristic$8$FitnessManager(BluetoothDevice device, int status) {
        log(5, "Profile system characteristic not found");
    }

    public /* synthetic */ void lambda$readProfileCharacteristic$9$FitnessManager(BluetoothDevice device, int status) {
        log(5, "Profile model characteristic not found");
    }

    public /* synthetic */ void lambda$readProfileCharacteristic$10$FitnessManager(BluetoothDevice device, int status) {
        log(5, "Profile serial characteristic not found");
    }

    public /* synthetic */ void lambda$readProfileCharacteristic$11$FitnessManager(BluetoothDevice device, int status) {
        log(5, "Profile firmware characteristic not found");
    }

    public /* synthetic */ void lambda$readProfileCharacteristic$12$FitnessManager(BluetoothDevice device, int status) {
        log(5, "Profile hardware characteristic not found");
    }

    public /* synthetic */ void lambda$readProfileCharacteristic$13$FitnessManager(BluetoothDevice device, int status) {
        log(5, "Profile software characteristic not found");
    }

    public /* synthetic */ void lambda$readProfileCharacteristic$14$FitnessManager(BluetoothDevice device, int status) {
        log(5, "Profile vendor characteristic not found");
    }

    public void readBatteryLevelCharacteristic() {
        if (isConnected()) {
            readCharacteristic(this.mBatteryLevelCharacteristic).with(this.mBatteryLevelDataCallback).fail(new FailCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$e7iVg7UEhH4etnYLUnXDA12eHS0
                @Override // no.nordicsemi.android.ble.callback.FailCallback
                public final void onRequestFailed(BluetoothDevice bluetoothDevice, int i) {
                    this.f$0.lambda$readBatteryLevelCharacteristic$15$FitnessManager(bluetoothDevice, i);
                }
            }).enqueue();
        }
    }

    public /* synthetic */ void lambda$readBatteryLevelCharacteristic$15$FitnessManager(BluetoothDevice device, int status) {
        log(5, "Battery Level characteristic not found");
    }

    public void enableBatteryLevelCharacteristicNotifications() {
        if (isConnected()) {
            setNotificationCallback(this.mBatteryLevelCharacteristic).with(this.mBatteryLevelDataCallback);
            enableNotifications(this.mBatteryLevelCharacteristic).done(new SuccessCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$7xUC-qCi5GM101dU5ZksGyY3HR0
                @Override // no.nordicsemi.android.ble.callback.SuccessCallback
                public final void onRequestCompleted(BluetoothDevice bluetoothDevice) {
                    this.f$0.lambda$enableBatteryLevelCharacteristicNotifications$16$FitnessManager(bluetoothDevice);
                }
            }).fail(new FailCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$13W7LK16mL_NBHtuLG-eUXgBHXI
                @Override // no.nordicsemi.android.ble.callback.FailCallback
                public final void onRequestFailed(BluetoothDevice bluetoothDevice, int i) {
                    this.f$0.lambda$enableBatteryLevelCharacteristicNotifications$17$FitnessManager(bluetoothDevice, i);
                }
            }).enqueue();
        }
    }

    public /* synthetic */ void lambda$enableBatteryLevelCharacteristicNotifications$16$FitnessManager(BluetoothDevice device) {
        log(3, "Battery Level notifications enabled");
    }

    public /* synthetic */ void lambda$enableBatteryLevelCharacteristicNotifications$17$FitnessManager(BluetoothDevice device, int status) {
        log(5, "Battery Level characteristic not found");
    }

    public void disableBatteryLevelCharacteristicNotifications() {
        if (isConnected()) {
            disableNotifications(this.mBatteryLevelCharacteristic).done(new SuccessCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$6-DQ8muYsbF2K80tJlc_qW75xwE
                @Override // no.nordicsemi.android.ble.callback.SuccessCallback
                public final void onRequestCompleted(BluetoothDevice bluetoothDevice) {
                    this.f$0.lambda$disableBatteryLevelCharacteristicNotifications$18$FitnessManager(bluetoothDevice);
                }
            }).enqueue();
        }
    }

    public /* synthetic */ void lambda$disableBatteryLevelCharacteristicNotifications$18$FitnessManager(BluetoothDevice device) {
        log(3, "Battery Level notifications disabled");
    }

    /* JADX INFO: Access modifiers changed from: protected */
    public abstract class FitnessManagerGattCallback extends BleManager.BleManagerGattCallback {
        protected FitnessManagerGattCallback() {
        }

        @Override // no.nordicsemi.android.ble.BleManagerHandler
        protected void initialize() {
            if (Build.VERSION.SDK_INT >= 21) {
                FitnessManager.this.requestConnectionPriority(1).enqueue();
            }
            FitnessManager.this.readProfileCharacteristic();
            FitnessManager.this.readBatteryLevelCharacteristic();
            FitnessManager.this.enableBatteryLevelCharacteristicNotifications();
        }

        /* JADX WARN: Multi-variable type inference failed */
        /* JADX WARN: Type inference failed for: r6v1 */
        /* JADX WARN: Type inference failed for: r6v10 */
        /* JADX WARN: Type inference failed for: r6v2 */
        @Override // no.nordicsemi.android.ble.BleManagerHandler
        public boolean isRequiredServiceSupported(final BluetoothGatt gatt) {
            BluetoothGattService service = gatt.getService(FitnessManager.SERVICE_UUID);
            if (service != null) {
                FitnessManager.this.mRXCharacteristic = service.getCharacteristic(FitnessManager.RX_CHAR_UUID);
                FitnessManager.this.mTXCharacteristic = service.getCharacteristic(FitnessManager.TX_CHAR_UUID);
                List<BluetoothGattCharacteristic> characteristics = service.getCharacteristics();
                for (BluetoothGattCharacteristic characteristic : characteristics) {
                    if (characteristic != null && characteristic.getUuid() != null && characteristic.getUuid().toString().equalsIgnoreCase(FitnessManager.SPEC_CHAR_UUID)) {
                        FitnessManager.this.mCustomRxCharacteristic = service.getCharacteristic(UUID.fromString(FitnessManager.CUSTOM_CHAR_UUID));
                        FitnessManager.this.isContainCL833 = true;
                    }
                }
            }
            List<BluetoothGattCharacteristic> characteristics2 = null;
            boolean writeCommand = false;
            if (FitnessManager.this.mTXCharacteristic != null) {
                int txProperties = FitnessManager.this.mTXCharacteristic.getProperties();
                characteristics2 = (txProperties & 8) > 0 ? 1 : 0;
                writeCommand = (txProperties & 4) > 0;
                if (characteristics2 != null) {
                    FitnessManager.this.mTXCharacteristic.setWriteType(2);
                    FitnessManager.this.log(3, "TXCharacteristic notifications WRITE_TYPE_DEFAULT");
                }
            }
            return (FitnessManager.this.mRXCharacteristic == null || FitnessManager.this.mTXCharacteristic == null || (!writeCommand && characteristics2 == null)) ? false : true;
        }

        @Override // no.nordicsemi.android.ble.BleManagerHandler
        protected boolean isOptionalServiceSupported(final BluetoothGatt gatt) {
            BluetoothGattService batteryService = gatt.getService(FitnessManager.BATTERY_SERVICE_UUID);
            if (batteryService != null) {
                FitnessManager.this.mBatteryLevelCharacteristic = batteryService.getCharacteristic(FitnessManager.BATTERY_LEVEL_CHARACTERISTIC_UUID);
            }
            boolean isBatteryService = FitnessManager.this.mBatteryLevelCharacteristic != null;
            BluetoothGattService profileService = gatt.getService(FitnessManager.PROFILE_SERVICE_UUID);
            if (profileService != null) {
                FitnessManager.this.mProfileSystemCharacteristic = profileService.getCharacteristic(FitnessManager.PROFILE_SYSTEM_CHARACTERISTIC_UUID);
                FitnessManager.this.mProfileModelCharacteristic = profileService.getCharacteristic(FitnessManager.PROFILE_MODEL_CHARACTERISTIC_UUID);
                FitnessManager.this.mProfileSerialCharacteristic = profileService.getCharacteristic(FitnessManager.PROFILE_SERIAL_CHARACTERISTIC_UUID);
                FitnessManager.this.mProfileFirmwareCharacteristic = profileService.getCharacteristic(FitnessManager.PROFILE_FIRMWARE_CHARACTERISTIC_UUID);
                FitnessManager.this.mProfileHardwareCharacteristic = profileService.getCharacteristic(FitnessManager.PROFILE_HARDWARE_CHARACTERISTIC_UUID);
                FitnessManager.this.mProfileSoftwareCharacteristic = profileService.getCharacteristic(FitnessManager.PROFILE_SOFTWARE_CHARACTERISTIC_UUID);
                FitnessManager.this.mProfileVendorCharacteristic = profileService.getCharacteristic(FitnessManager.PROFILE_VENDOR_CHARACTERISTIC_UUID);
            }
            boolean isProfileService = (FitnessManager.this.mProfileSystemCharacteristic == null || FitnessManager.this.mProfileModelCharacteristic == null || FitnessManager.this.mProfileSerialCharacteristic == null || FitnessManager.this.mProfileFirmwareCharacteristic == null || FitnessManager.this.mProfileHardwareCharacteristic == null || FitnessManager.this.mProfileSoftwareCharacteristic == null || FitnessManager.this.mProfileVendorCharacteristic == null) ? false : true;
            return isBatteryService && isProfileService;
        }

        @Override // no.nordicsemi.android.ble.BleManagerHandler
        protected void onDeviceDisconnected() {
            FitnessManager.this.mBatteryLevelCharacteristic = null;
            FitnessManager.this.mCustomRxCharacteristic = null;
            FitnessManager.this.mRXCharacteristic = null;
            FitnessManager.this.mTXCharacteristic = null;
            FitnessManager.this.mBatteryLevel = null;
            FitnessManager.this.isContainCL833 = false;
        }

        @Override // no.nordicsemi.android.ble.BleManagerHandler
        protected void onServicesInvalidated() {
            FitnessManager.this.mBatteryLevelCharacteristic = null;
            FitnessManager.this.mCustomRxCharacteristic = null;
            FitnessManager.this.mRXCharacteristic = null;
            FitnessManager.this.mTXCharacteristic = null;
            FitnessManager.this.mBatteryLevel = null;
            FitnessManager.this.isContainCL833 = false;
        }
    }

    public void connectDevice(BluetoothDevice device) {
        connect(device).useAutoConnect(false).enqueue();
    }

    public void disconnectDevice() {
        disconnect().enqueue();
    }

    protected void writeTxCharacteristic(final byte[] command) {
        BluetoothGattCharacteristic bluetoothGattCharacteristic;
        if (isConnected() && (bluetoothGattCharacteristic = this.mTXCharacteristic) != null) {
            writeCharacteristic(bluetoothGattCharacteristic, command).with(new DataSentCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$hOCwvpbC0Kc0iHPw50HUZtLEA3w
                @Override // no.nordicsemi.android.ble.callback.DataSentCallback
                public final void onDataSent(BluetoothDevice bluetoothDevice, Data data) {
                    this.f$0.lambda$writeTxCharacteristic$19$FitnessManager(bluetoothDevice, data);
                }
            }).done(new SuccessCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$26bhtEQVz7tSUkZ_ScNbzm7F5CQ
                @Override // no.nordicsemi.android.ble.callback.SuccessCallback
                public final void onRequestCompleted(BluetoothDevice bluetoothDevice) {
                    this.f$0.lambda$writeTxCharacteristic$20$FitnessManager(bluetoothDevice);
                }
            }).fail(new FailCallback() { // from class: com.android.chileaf.fitness.-$$Lambda$FitnessManager$-PKWcnA1dPO2pt86BZv6nr-4jaw
                @Override // no.nordicsemi.android.ble.callback.FailCallback
                public final void onRequestFailed(BluetoothDevice bluetoothDevice, int i) {
                    this.f$0.lambda$writeTxCharacteristic$21$FitnessManager(bluetoothDevice, i);
                }
            }).enqueue();
        }
    }

    public /* synthetic */ void lambda$writeTxCharacteristic$19$FitnessManager(BluetoothDevice device, Data data) {
        log(2, "Send:" + ParserUtils.parse(data.getValue()));
    }

    public /* synthetic */ void lambda$writeTxCharacteristic$20$FitnessManager(BluetoothDevice device) {
        log(3, "Tx writeCharacteristic success");
    }

    public /* synthetic */ void lambda$writeTxCharacteristic$21$FitnessManager(BluetoothDevice device, int status) {
        log(5, "Tx writeCharacteristic failure");
    }

    protected void sendCommand(final byte[] bytes) {
        sendCommand(bytes, false);
    }

    protected void sendCommand(final byte[] bytes, boolean isCheckSum) {
        byte[] command;
        if (isCheckSum) {
            byte check = checkSum(bytes);
            command = HexUtil.append(bytes, check);
        } else {
            command = bytes;
        }
        writeTxCharacteristic(command);
    }
}
