package com.android.chileaf.fitness.common.profile;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface ProfileCallback {
    void onFirmwareVersion(final BluetoothDevice device, final String firmware);

    void onHardwareVersion(final BluetoothDevice device, final String hardware);

    void onModelName(final BluetoothDevice device, final String modelName);

    void onSerialNumber(final BluetoothDevice device, final String serialNumber);

    void onSoftwareVersion(final BluetoothDevice device, final String software);

    void onSystemId(final BluetoothDevice device, final String systemId);

    void onVendorName(final BluetoothDevice device, final String vendorName);
}
