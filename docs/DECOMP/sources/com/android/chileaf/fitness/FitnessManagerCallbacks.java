package com.android.chileaf.fitness;

import android.bluetooth.BluetoothDevice;
import com.android.chileaf.fitness.common.battery.BatteryLevelCallback;
import com.android.chileaf.fitness.common.profile.ProfileCallback;
import no.nordicsemi.android.ble.BleManagerCallbacks;
import no.nordicsemi.android.ble.callback.RssiCallback;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface FitnessManagerCallbacks extends BleManagerCallbacks, RssiCallback, BatteryLevelCallback, ProfileCallback {
    @Override // com.android.chileaf.fitness.common.battery.BatteryLevelCallback
    void onBatteryLevelChanged(final BluetoothDevice device, final int batteryLevel);

    @Override // no.nordicsemi.android.ble.BleManagerCallbacks
    @Deprecated
    void onBatteryValueReceived(final BluetoothDevice device, final int value);

    @Override // no.nordicsemi.android.ble.BleManagerCallbacks
    void onBonded(final BluetoothDevice device);

    @Override // no.nordicsemi.android.ble.BleManagerCallbacks
    void onBondingFailed(final BluetoothDevice device);

    @Override // no.nordicsemi.android.ble.BleManagerCallbacks
    void onBondingRequired(final BluetoothDevice device);

    @Override // no.nordicsemi.android.ble.BleManagerCallbacks
    void onDeviceConnected(final BluetoothDevice device);

    @Override // no.nordicsemi.android.ble.BleManagerCallbacks
    void onDeviceConnecting(final BluetoothDevice device);

    @Override // no.nordicsemi.android.ble.BleManagerCallbacks
    void onDeviceDisconnected(final BluetoothDevice device);

    @Override // no.nordicsemi.android.ble.BleManagerCallbacks
    void onDeviceDisconnecting(final BluetoothDevice device);

    @Override // no.nordicsemi.android.ble.BleManagerCallbacks
    void onDeviceNotSupported(final BluetoothDevice device);

    @Override // no.nordicsemi.android.ble.BleManagerCallbacks
    void onDeviceReady(final BluetoothDevice device);

    @Override // no.nordicsemi.android.ble.BleManagerCallbacks
    void onError(final BluetoothDevice device, final String message, final int errorCode);

    @Override // com.android.chileaf.fitness.common.profile.ProfileCallback
    void onFirmwareVersion(final BluetoothDevice device, final String firmware);

    @Override // com.android.chileaf.fitness.common.profile.ProfileCallback
    void onHardwareVersion(final BluetoothDevice device, final String hardware);

    @Override // no.nordicsemi.android.ble.BleManagerCallbacks
    void onLinkLossOccurred(final BluetoothDevice device);

    @Override // com.android.chileaf.fitness.common.profile.ProfileCallback
    void onModelName(final BluetoothDevice device, final String modelName);

    @Override // no.nordicsemi.android.ble.callback.RssiCallback
    void onRssiRead(final BluetoothDevice device, final int rssi);

    @Override // com.android.chileaf.fitness.common.profile.ProfileCallback
    void onSerialNumber(final BluetoothDevice device, final String serialNumber);

    @Override // no.nordicsemi.android.ble.BleManagerCallbacks
    void onServicesDiscovered(final BluetoothDevice device, final boolean optionalServicesFound);

    @Override // com.android.chileaf.fitness.common.profile.ProfileCallback
    void onSoftwareVersion(final BluetoothDevice device, final String software);

    @Override // com.android.chileaf.fitness.common.profile.ProfileCallback
    void onSystemId(final BluetoothDevice device, final String systemId);

    @Override // com.android.chileaf.fitness.common.profile.ProfileCallback
    void onVendorName(final BluetoothDevice device, final String vendorName);

    @Override // no.nordicsemi.android.ble.BleManagerCallbacks
    @Deprecated
    boolean shouldEnableBatteryLevelNotifications(final BluetoothDevice device);

    /* renamed from: com.android.chileaf.fitness.FitnessManagerCallbacks$-CC, reason: invalid class name */
    public final /* synthetic */ class CC {
        public static void $default$onDeviceConnecting(FitnessManagerCallbacks _this, BluetoothDevice device) {
        }

        public static void $default$onDeviceDisconnecting(FitnessManagerCallbacks _this, BluetoothDevice device) {
        }

        public static void $default$onLinkLossOccurred(FitnessManagerCallbacks _this, BluetoothDevice device) {
        }

        public static void $default$onServicesDiscovered(FitnessManagerCallbacks _this, BluetoothDevice device, boolean optionalServicesFound) {
        }

        public static void $default$onDeviceReady(FitnessManagerCallbacks _this, BluetoothDevice device) {
        }

        @Deprecated
        public static boolean $default$shouldEnableBatteryLevelNotifications(FitnessManagerCallbacks _this, BluetoothDevice device) {
            return false;
        }

        @Deprecated
        public static void $default$onBatteryValueReceived(FitnessManagerCallbacks _this, BluetoothDevice device, int value) {
        }

        public static void $default$onBondingRequired(FitnessManagerCallbacks _this, BluetoothDevice device) {
        }

        public static void $default$onBonded(FitnessManagerCallbacks _this, BluetoothDevice device) {
        }

        public static void $default$onBondingFailed(FitnessManagerCallbacks _this, BluetoothDevice device) {
        }

        public static void $default$onError(FitnessManagerCallbacks _this, BluetoothDevice device, String message, int errorCode) {
        }

        public static void $default$onDeviceNotSupported(FitnessManagerCallbacks _this, BluetoothDevice device) {
        }

        public static void $default$onRssiRead(FitnessManagerCallbacks _this, BluetoothDevice device, int rssi) {
        }

        public static void $default$onBatteryLevelChanged(FitnessManagerCallbacks _this, BluetoothDevice device, int batteryLevel) {
        }

        public static void $default$onSystemId(FitnessManagerCallbacks _this, BluetoothDevice device, String systemId) {
        }

        public static void $default$onModelName(FitnessManagerCallbacks _this, BluetoothDevice device, String modelName) {
        }

        public static void $default$onSerialNumber(FitnessManagerCallbacks _this, BluetoothDevice device, String serialNumber) {
        }

        public static void $default$onFirmwareVersion(FitnessManagerCallbacks _this, BluetoothDevice device, String firmware) {
        }

        public static void $default$onHardwareVersion(FitnessManagerCallbacks _this, BluetoothDevice device, String hardware) {
        }

        public static void $default$onSoftwareVersion(FitnessManagerCallbacks _this, BluetoothDevice device, String software) {
        }

        public static void $default$onVendorName(FitnessManagerCallbacks _this, BluetoothDevice device, String vendorName) {
        }
    }
}
