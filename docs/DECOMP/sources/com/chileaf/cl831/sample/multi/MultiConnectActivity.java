package com.chileaf.cl831.sample.multi;

import android.bluetooth.BluetoothDevice;
import android.content.DialogInterface;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import androidx.appcompat.app.AlertDialog;
import androidx.recyclerview.widget.DefaultItemAnimator;
import androidx.recyclerview.widget.DividerItemDecoration;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.android.chileaf.WearManager;
import com.android.chileaf.fitness.FitnessManager;
import com.android.chileaf.fitness.FitnessManagerCallbacks;
import com.android.chileaf.fitness.callback.WearManagerCallbacks;
import com.chad.library.adapter.base.BaseQuickAdapter;
import com.chad.library.adapter.base.listener.OnItemChildClickListener;
import com.chileaf.cl831.sample.BaseActivity;
import com.chileaf.cl831.sample.BuildConfig;
import com.chileaf.cl831.sample.R;
import com.chileaf.cl831.sample.ScannerFragment;
import com.hjq.permissions.OnPermissionCallback;
import com.hjq.permissions.XXPermissions;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import no.nordicsemi.android.ble.callback.FailCallback;
import timber.log.Timber;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes3.dex */
public class MultiConnectActivity extends BaseActivity implements ScannerFragment.OnDeviceSelectedListener, WearManagerCallbacks {
    private Button mBtnConnect;
    private RecyclerView mRvDevice;
    private final List<BluetoothDevice> mManagedDevices = new ArrayList();
    private final HashMap<BluetoothDevice, FitnessManager<WearManagerCallbacks>> mBleManagers = new HashMap<>();
    private final DeviceAdapter mAdapter = new DeviceAdapter();

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public /* synthetic */ void onBatteryValueReceived(BluetoothDevice bluetoothDevice, int i) {
        FitnessManagerCallbacks.CC.$default$onBatteryValueReceived(this, bluetoothDevice, i);
    }

    @Override // com.android.chileaf.fitness.callback.WearManagerCallbacks, com.android.chileaf.fitness.callback.BluetoothStatusCallback
    public /* synthetic */ void onBluetoothStatusReceived(BluetoothDevice bluetoothDevice, boolean z) {
        WearManagerCallbacks.CC.$default$onBluetoothStatusReceived(this, bluetoothDevice, z);
    }

    @Override // com.android.chileaf.fitness.callback.WearManagerCallbacks, com.android.chileaf.fitness.common.heart.BodySensorLocationCallback
    public /* synthetic */ void onBodySensorLocationReceived(BluetoothDevice bluetoothDevice, int i) {
        WearManagerCallbacks.CC.$default$onBodySensorLocationReceived(this, bluetoothDevice, i);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public /* synthetic */ void onBonded(BluetoothDevice bluetoothDevice) {
        FitnessManagerCallbacks.CC.$default$onBonded(this, bluetoothDevice);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public /* synthetic */ void onBondingFailed(BluetoothDevice bluetoothDevice) {
        FitnessManagerCallbacks.CC.$default$onBondingFailed(this, bluetoothDevice);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public /* synthetic */ void onBondingRequired(BluetoothDevice bluetoothDevice) {
        FitnessManagerCallbacks.CC.$default$onBondingRequired(this, bluetoothDevice);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public /* synthetic */ void onDeviceConnecting(BluetoothDevice bluetoothDevice) {
        FitnessManagerCallbacks.CC.$default$onDeviceConnecting(this, bluetoothDevice);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public /* synthetic */ void onDeviceDisconnecting(BluetoothDevice bluetoothDevice) {
        FitnessManagerCallbacks.CC.$default$onDeviceDisconnecting(this, bluetoothDevice);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public /* synthetic */ void onDeviceReady(BluetoothDevice bluetoothDevice) {
        FitnessManagerCallbacks.CC.$default$onDeviceReady(this, bluetoothDevice);
    }

    @Override // com.chileaf.cl831.sample.ScannerFragment.OnDeviceSelectedListener
    public /* synthetic */ void onDialogCanceled() {
        ScannerFragment.OnDeviceSelectedListener.CC.$default$onDialogCanceled(this);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, com.android.chileaf.fitness.common.profile.ProfileCallback
    public /* synthetic */ void onFirmwareVersion(BluetoothDevice bluetoothDevice, String str) {
        FitnessManagerCallbacks.CC.$default$onFirmwareVersion(this, bluetoothDevice, str);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, com.android.chileaf.fitness.common.profile.ProfileCallback
    public /* synthetic */ void onHardwareVersion(BluetoothDevice bluetoothDevice, String str) {
        FitnessManagerCallbacks.CC.$default$onHardwareVersion(this, bluetoothDevice, str);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, com.android.chileaf.fitness.common.profile.ProfileCallback
    public /* synthetic */ void onModelName(BluetoothDevice bluetoothDevice, String str) {
        FitnessManagerCallbacks.CC.$default$onModelName(this, bluetoothDevice, str);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.callback.RssiCallback
    public /* synthetic */ void onRssiRead(BluetoothDevice bluetoothDevice, int i) {
        FitnessManagerCallbacks.CC.$default$onRssiRead(this, bluetoothDevice, i);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, com.android.chileaf.fitness.common.profile.ProfileCallback
    public /* synthetic */ void onSerialNumber(BluetoothDevice bluetoothDevice, String str) {
        FitnessManagerCallbacks.CC.$default$onSerialNumber(this, bluetoothDevice, str);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public /* synthetic */ void onServicesDiscovered(BluetoothDevice bluetoothDevice, boolean z) {
        FitnessManagerCallbacks.CC.$default$onServicesDiscovered(this, bluetoothDevice, z);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, com.android.chileaf.fitness.common.profile.ProfileCallback
    public /* synthetic */ void onSystemId(BluetoothDevice bluetoothDevice, String str) {
        FitnessManagerCallbacks.CC.$default$onSystemId(this, bluetoothDevice, str);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, com.android.chileaf.fitness.common.profile.ProfileCallback
    public /* synthetic */ void onVendorName(BluetoothDevice bluetoothDevice, String str) {
        FitnessManagerCallbacks.CC.$default$onVendorName(this, bluetoothDevice, str);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public /* synthetic */ boolean shouldEnableBatteryLevelNotifications(BluetoothDevice bluetoothDevice) {
        return FitnessManagerCallbacks.CC.$default$shouldEnableBatteryLevelNotifications(this, bluetoothDevice);
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected int layoutId() {
        return R.layout.activity_multi_connect;
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initView() {
        this.mBtnConnect = (Button) findViewById(R.id.btn_connect);
        RecyclerView recyclerView = (RecyclerView) findViewById(R.id.rv_device);
        this.mRvDevice = recyclerView;
        recyclerView.addItemDecoration(new DividerItemDecoration(this, 1));
        this.mRvDevice.setLayoutManager(new LinearLayoutManager(this));
        this.mRvDevice.setItemAnimator(new DefaultItemAnimator());
        this.mRvDevice.setHasFixedSize(true);
        this.mAdapter.setOnItemChildClickListener(new OnItemChildClickListener() { // from class: com.chileaf.cl831.sample.multi.-$$Lambda$MultiConnectActivity$aGDGx5HLwCiZiNeVbmU9BFjH2do
            @Override // com.chad.library.adapter.base.listener.OnItemChildClickListener
            public final void onItemChildClick(BaseQuickAdapter baseQuickAdapter, View view, int i) {
                this.f$0.lambda$initView$0$MultiConnectActivity(baseQuickAdapter, view, i);
            }
        });
        this.mRvDevice.setAdapter(this.mAdapter);
        this.mBtnConnect.setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.multi.-$$Lambda$MultiConnectActivity$ZVurvD-pJB4irIuANSSMqanIYIk
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$1$MultiConnectActivity(view);
            }
        });
    }

    public /* synthetic */ void lambda$initView$0$MultiConnectActivity(BaseQuickAdapter adapter, View view, int position) {
        DeviceItem item = this.mAdapter.getItem(position);
        if (item != null) {
            disconnect(item.device);
        }
    }

    public /* synthetic */ void lambda$initView$1$MultiConnectActivity(View view) {
        if (isBLEEnabled()) {
            showDeviceScanningDialog();
        } else {
            showBLEDialog();
        }
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initData(Bundle savedInstanceState) {
        isBLESupported();
        if (!isBLEEnabled()) {
            showBLEDialog();
        }
    }

    public WearManager getWearManager(final BluetoothDevice device) {
        return (WearManager) this.mBleManagers.get(device);
    }

    public List<BluetoothDevice> getConnectedDevices() {
        List<BluetoothDevice> list = new ArrayList<>();
        for (BluetoothDevice device : this.mManagedDevices) {
            WearManager manager = getWearManager(device);
            if (manager != null && manager.isConnected()) {
                list.add(device);
            }
        }
        return Collections.unmodifiableList(list);
    }

    public void connect(final BluetoothDevice device) {
        FitnessManager<WearManagerCallbacks> manager = this.mBleManagers.get(device);
        if (manager == null) {
            manager = new WearManager(this);
        }
        this.mBleManagers.put(device, manager);
        manager.setManagerCallbacks(this);
        manager.setDebug(BuildConfig.DEBUG);
        if (!this.mManagedDevices.contains(device)) {
            this.mManagedDevices.add(device);
        }
        Timber.v("Connect:%s %s %s", device.getName(), device.getAddress(), manager.toString());
        manager.connect(device).retry(2, 100).useAutoConnect(false).timeout(10000L).fail(new FailCallback() { // from class: com.chileaf.cl831.sample.multi.-$$Lambda$MultiConnectActivity$MVNDJIvDv3uY8wSiGAWzUTEY6LQ
            @Override // no.nordicsemi.android.ble.callback.FailCallback
            public final void onRequestFailed(BluetoothDevice bluetoothDevice, int i) {
                this.f$0.lambda$connect$2$MultiConnectActivity(device, bluetoothDevice, i);
            }
        }).enqueue();
    }

    public /* synthetic */ void lambda$connect$2$MultiConnectActivity(BluetoothDevice device, BluetoothDevice d, int status) {
        this.mManagedDevices.remove(device);
        this.mBleManagers.remove(device);
    }

    public final void disconnect(final BluetoothDevice device) {
        WearManager manager = getWearManager(device);
        if (manager != null) {
            manager.disconnect().enqueue();
        }
    }

    public final void disconnectAll() {
        for (BluetoothDevice device : getConnectedDevices()) {
            disconnect(device);
        }
    }

    public final boolean isConnected(final BluetoothDevice device) {
        WearManager manager = getWearManager(device);
        return manager != null && manager.isConnected();
    }

    public final boolean isReady(final BluetoothDevice device) {
        WearManager manager = getWearManager(device);
        return manager != null && manager.isReady();
    }

    public final int getConnectionState(final BluetoothDevice device) {
        WearManager manager = getWearManager(device);
        if (manager != null) {
            return manager.getConnectionState();
        }
        return 0;
    }

    private void showDeviceScanningDialog() {
        if (isLocationEnabled(this)) {
            XXPermissions.with(this).permission(getPermissions()).request(new AnonymousClass1());
        } else {
            new AlertDialog.Builder(this).setTitle(getString(R.string.location_permission_title)).setMessage(getString(R.string.location_permission_info)).setPositiveButton("OK", new DialogInterface.OnClickListener() { // from class: com.chileaf.cl831.sample.multi.-$$Lambda$MultiConnectActivity$LMqqUH-qGq91zZifHISKGWDjPDg
                @Override // android.content.DialogInterface.OnClickListener
                public final void onClick(DialogInterface dialogInterface, int i) {
                    this.f$0.lambda$showDeviceScanningDialog$3$MultiConnectActivity(dialogInterface, i);
                }
            }).setNegativeButton("Cancel", (DialogInterface.OnClickListener) null).show();
        }
    }

    /* renamed from: com.chileaf.cl831.sample.multi.MultiConnectActivity$1, reason: invalid class name */
    class AnonymousClass1 implements OnPermissionCallback {
        AnonymousClass1() {
        }

        @Override // com.hjq.permissions.OnPermissionCallback
        public void onGranted(List<String> permissions, boolean allGranted) {
            if (!allGranted) {
                MultiConnectActivity.this.showToast("permission is denied");
            } else {
                MultiConnectActivity.this.runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.multi.-$$Lambda$MultiConnectActivity$1$Daf6EwsgX9j7p02n3Loj9vt_I-Y
                    @Override // java.lang.Runnable
                    public final void run() {
                        this.f$0.lambda$onGranted$0$MultiConnectActivity$1();
                    }
                });
            }
        }

        public /* synthetic */ void lambda$onGranted$0$MultiConnectActivity$1() {
            ScannerFragment dialog = ScannerFragment.getInstance();
            dialog.show(MultiConnectActivity.this.getSupportFragmentManager(), "scan_fragment");
        }

        @Override // com.hjq.permissions.OnPermissionCallback
        public void onDenied(List<String> permissions, boolean doNotAskAgain) {
            if (!doNotAskAgain) {
                MultiConnectActivity.this.showToast("permission is denied");
            } else {
                new AlertDialog.Builder(MultiConnectActivity.this).setTitle(MultiConnectActivity.this.getString(R.string.permission_required)).setMessage(MultiConnectActivity.this.getString(R.string.permission_location_info)).setPositiveButton(MultiConnectActivity.this.getString(R.string.yes), new DialogInterface.OnClickListener() { // from class: com.chileaf.cl831.sample.multi.-$$Lambda$MultiConnectActivity$1$KzwAH-GZxE3sZ4KUWzualPBN7IQ
                    @Override // android.content.DialogInterface.OnClickListener
                    public final void onClick(DialogInterface dialogInterface, int i) {
                        this.f$0.lambda$onDenied$1$MultiConnectActivity$1(dialogInterface, i);
                    }
                }).setNegativeButton(MultiConnectActivity.this.getString(R.string.f5no), (DialogInterface.OnClickListener) null).show();
            }
        }

        public /* synthetic */ void lambda$onDenied$1$MultiConnectActivity$1(DialogInterface dialog, int which) {
            MultiConnectActivity.this.onPermissionSettings();
        }
    }

    public /* synthetic */ void lambda$showDeviceScanningDialog$3$MultiConnectActivity(DialogInterface dialog, int which) {
        onEnableLocation();
    }

    @Override // com.chileaf.cl831.sample.ScannerFragment.OnDeviceSelectedListener
    public void onDeviceSelected(BluetoothDevice device, String name) {
        showToast("Connect " + device.getName());
        connect(device);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public void onError(BluetoothDevice device, String message, int errorCode) {
        Timber.e("onError: (" + errorCode + ")", new Object[0]);
        showToast(message + " (" + errorCode + ")");
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public void onDeviceNotSupported(BluetoothDevice device) {
        showToast(getString(R.string.not_supported));
    }

    public /* synthetic */ void lambda$onSoftwareVersion$4$MultiConnectActivity(BluetoothDevice device, String software) {
        this.mAdapter.onSoftwareVersion(device, software);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, com.android.chileaf.fitness.common.profile.ProfileCallback
    public void onSoftwareVersion(final BluetoothDevice device, final String software) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.multi.-$$Lambda$MultiConnectActivity$ClpOZdgxmAWY2RFmHTL6cqWgTu8
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onSoftwareVersion$4$MultiConnectActivity(device, software);
            }
        });
    }

    public /* synthetic */ void lambda$onBatteryLevelChanged$5$MultiConnectActivity(BluetoothDevice device, int batteryLevel) {
        this.mAdapter.onBatteryLevelChanged(device, batteryLevel);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, com.android.chileaf.fitness.common.battery.BatteryLevelCallback
    public void onBatteryLevelChanged(final BluetoothDevice device, final int batteryLevel) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.multi.-$$Lambda$MultiConnectActivity$ro4f_ImXrsbVwcqdQQk_pcUaxJM
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onBatteryLevelChanged$5$MultiConnectActivity(device, batteryLevel);
            }
        });
    }

    public /* synthetic */ void lambda$onHeartRateMeasurementReceived$6$MultiConnectActivity(BluetoothDevice device, int heartRate) {
        this.mAdapter.onHeartRateMeasurementReceived(device, heartRate);
    }

    @Override // com.android.chileaf.fitness.callback.WearManagerCallbacks, com.android.chileaf.fitness.common.heart.HeartRateMeasurementCallback
    public void onHeartRateMeasurementReceived(final BluetoothDevice device, final int heartRate, Boolean contactDetected, Integer energyExpanded, List<Integer> rrIntervals) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.multi.-$$Lambda$MultiConnectActivity$3fnrabNAT_gEWuhsp-ibptjQwzg
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onHeartRateMeasurementReceived$6$MultiConnectActivity(device, heartRate);
            }
        });
    }

    public /* synthetic */ void lambda$onSportReceived$7$MultiConnectActivity(BluetoothDevice device, int step, int distance, int calorie) {
        this.mAdapter.onSportReceived(device, step, distance, calorie);
    }

    @Override // com.android.chileaf.fitness.callback.WearManagerCallbacks, com.android.chileaf.fitness.callback.BodySportCallback
    public void onSportReceived(final BluetoothDevice device, final int step, final int distance, final int calorie) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.multi.-$$Lambda$MultiConnectActivity$-J9fLF95n-67LmzhQAjZq8MPgMo
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onSportReceived$7$MultiConnectActivity(device, step, distance, calorie);
            }
        });
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public void onDeviceConnected(final BluetoothDevice device) {
        showToast("Add " + device.getName());
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.multi.-$$Lambda$MultiConnectActivity$S_HsD_v18rzkTiIlQn-btXtrO6c
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onDeviceConnected$8$MultiConnectActivity(device);
            }
        });
    }

    public /* synthetic */ void lambda$onDeviceConnected$8$MultiConnectActivity(BluetoothDevice device) {
        this.mAdapter.addDevice(new DeviceItem(device));
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public void onDeviceDisconnected(final BluetoothDevice device) {
        showToast("Remove " + device.getName());
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.multi.-$$Lambda$MultiConnectActivity$3yHGuupIPqYbGXMzCPhI3s4LPYs
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onDeviceDisconnected$9$MultiConnectActivity(device);
            }
        });
    }

    public /* synthetic */ void lambda$onDeviceDisconnected$9$MultiConnectActivity(BluetoothDevice device) {
        this.mAdapter.removeDevice(device);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public void onLinkLossOccurred(final BluetoothDevice device) {
        showToast("LinkLoss " + device.getName());
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.multi.-$$Lambda$MultiConnectActivity$Zrx2bbzOzrc5y92l_FeVcumqteg
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onLinkLossOccurred$10$MultiConnectActivity(device);
            }
        });
    }

    public /* synthetic */ void lambda$onLinkLossOccurred$10$MultiConnectActivity(BluetoothDevice device) {
        this.mAdapter.removeDevice(device);
    }

    @Override // androidx.activity.ComponentActivity, android.app.Activity
    public void onBackPressed() {
        disconnectAll();
        super.onBackPressed();
    }
}
