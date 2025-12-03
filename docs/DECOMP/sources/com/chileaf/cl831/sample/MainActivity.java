package com.chileaf.cl831.sample;

import android.bluetooth.BluetoothDevice;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.View;
import android.widget.Button;
import android.widget.CompoundButton;
import android.widget.EditText;
import android.widget.TextView;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.widget.AppCompatEditText;
import androidx.appcompat.widget.SwitchCompat;
import com.android.chileaf.fitness.FitnessManagerCallbacks;
import com.android.chileaf.fitness.callback.AccelerometerCallback;
import com.android.chileaf.fitness.callback.BodyHealthCallback;
import com.android.chileaf.fitness.callback.CustomDataReceivedCallback;
import com.android.chileaf.fitness.callback.HeartRateAlarmCallback;
import com.android.chileaf.fitness.callback.HeartRateMaxCallback;
import com.android.chileaf.fitness.callback.HeartRateStatusCallback;
import com.android.chileaf.fitness.callback.Sensor3DFrequencyCallback;
import com.android.chileaf.fitness.callback.Sensor3DStatusCallback;
import com.android.chileaf.fitness.callback.Sensor6DFrequencyCallback;
import com.android.chileaf.fitness.callback.Sensor6DRawDataCallback;
import com.android.chileaf.fitness.callback.WearManagerCallbacks;
import com.android.chileaf.util.HexUtil;
import com.chileaf.cl831.sample.ScannerFragment;
import com.chileaf.cl831.sample.dfu.DfuActivity;
import com.chileaf.cl831.sample.multi.MultiConnectActivity;
import com.hjq.permissions.OnPermissionCallback;
import com.hjq.permissions.XXPermissions;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import timber.log.Timber;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class MainActivity extends BaseActivity implements ScannerFragment.OnDeviceSelectedListener, WearManagerCallbacks {
    private Button mBtnConnect;
    private EditText mEtGoal;
    private EditText mEtHRMax;
    private EditText mEtMax;
    private EditText mEtMin;
    private TextView mTv3DFrequency;
    private TextView mTv3DStatus;
    private TextView mTv6DFrequency;
    private TextView mTv6DRawData;
    private TextView mTvAccelerometer;
    private TextView mTvBattery;
    private TextView mTvDeviceName;
    private TextView mTvHRAlertStatus;
    private TextView mTvHRMax;
    private TextView mTvHRStatus;
    private TextView mTvHealth;
    private TextView mTvHeartRate;
    private TextView mTvReceivedData;
    private TextView mTvRssi;
    private TextView mTvSDKVersion;
    private TextView mTvSport;
    private TextView mTvVersion;
    private boolean mDeviceConnected = false;
    private final SimpleDateFormat mDateFormat = new SimpleDateFormat("yy-MM-dd HH:mm:ss", Locale.getDefault());
    private final Map<Integer, String> mFrequency3DMap = new HashMap();
    private final Map<Integer, String> mFrequency6DMap = new HashMap();

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
        return R.layout.activity_main;
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initView() {
        this.mTvDeviceName = (TextView) findViewById(R.id.tv_device_name);
        TextView textView = (TextView) findViewById(R.id.tv_sdk_version);
        this.mTvSDKVersion = textView;
        textView.setText("SDK Version: v3.0.4");
        this.mTvAccelerometer = (TextView) findViewById(R.id.tv_accelerometer);
        this.mTvRssi = (TextView) findViewById(R.id.tv_rssi);
        this.mTvVersion = (TextView) findViewById(R.id.tv_version);
        this.mTvBattery = (TextView) findViewById(R.id.tv_battery);
        this.mTvSport = (TextView) findViewById(R.id.tv_sport);
        this.mTvHeartRate = (TextView) findViewById(R.id.tv_hr);
        this.mTvReceivedData = (TextView) findViewById(R.id.tv_received);
        this.mTvHRStatus = (TextView) findViewById(R.id.tv_heart_rate);
        this.mTvHRAlertStatus = (TextView) findViewById(R.id.tv_hr_alert_status);
        this.mTvHRMax = (TextView) findViewById(R.id.tv_hr_max);
        this.mTv3DFrequency = (TextView) findViewById(R.id.tv_3d_frequency);
        this.mTv3DStatus = (TextView) findViewById(R.id.tv_3d_status);
        this.mEtMin = (EditText) findViewById(R.id.et_min);
        this.mEtMax = (EditText) findViewById(R.id.et_max);
        this.mEtGoal = (EditText) findViewById(R.id.et_goal);
        this.mEtHRMax = (EditText) findViewById(R.id.et_hr_max);
        this.mTvHealth = (TextView) findViewById(R.id.tv_health);
        this.mTv6DFrequency = (TextView) findViewById(R.id.tv_6d_frequency);
        this.mTv6DRawData = (TextView) findViewById(R.id.tv_6d_data);
        this.mBtnConnect = (Button) findViewById(R.id.btn_connect);
        findViewById(R.id.btn_multi).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$sVrImcXlqfrU9ycmGKWOgr6cyXE
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$0$MainActivity(view);
            }
        });
        findViewById(R.id.btn_sport_health).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$CjokEupc9pkLbMOXPPl8O-zfRyQ
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$1$MainActivity(view);
            }
        });
        findViewById(R.id.btn_heart_rate).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$oYzVbP7e7ZvfXhj-C4gp9jxvjDY
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$2$MainActivity(view);
            }
        });
        findViewById(R.id.btn_user_info).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$Chlb_Ha6JiDU_222vYO1_qMLprI
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$3$MainActivity(view);
            }
        });
        findViewById(R.id.btn_restoration).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$kDC3HqrmkjclT7Ec7H5U3L73-oM
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$4$MainActivity(view);
            }
        });
        findViewById(R.id.btn_dfu).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$tnXzxt2rARb3d4lOXz4M-FnQn68
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$5$MainActivity(view);
            }
        });
        findViewById(R.id.btn_history_sport).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$R2w7CQv5aWK-sM5mSZ9p7PsyIY8
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$6$MainActivity(view);
            }
        });
        findViewById(R.id.btn_history_heart).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$04n6jIw3lb-4JX7bygb0JW3I7PI
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$7$MainActivity(view);
            }
        });
        findViewById(R.id.btn_history_rr).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$BJ3ni7cUkiapKNds722rDRyPvYc
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$8$MainActivity(view);
            }
        });
        findViewById(R.id.btn_history_step).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$2-nTfXmDdQzoqlsa2JCCG1LnTh4
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$9$MainActivity(view);
            }
        });
        findViewById(R.id.btn_interval).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$Pl9NXZDqMj1dS4uAXY22LfBVV7o
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$10$MainActivity(view);
            }
        });
        findViewById(R.id.btn_single).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$bY2Ifbqp4V4EeVedS5296WwvdsU
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$11$MainActivity(view);
            }
        });
        findViewById(R.id.btn_3d).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$lnakfSNKGsdXPgN-SNthDXUNmqU
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$12$MainActivity(view);
            }
        });
        findViewById(R.id.btn_hr_setting).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$R13TlsBVDc2sM21VVtlC7MFsPiw
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$13$MainActivity(view);
            }
        });
        findViewById(R.id.btn_shut_down).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$ukdHToug7bn4vKAcRoBmEZErD78
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$14$MainActivity(view);
            }
        });
        findViewById(R.id.btn_blood_oxygen).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$5rXlcI2hmrErsS1qB2ukVVOmId4
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$15$MainActivity(view);
            }
        });
        findViewById(R.id.btn_temperature).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$H0jP2Q0hnf1KZLPA1QUF0X-WExk
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$16$MainActivity(view);
            }
        });
        SwitchCompat swAlarm = (SwitchCompat) findViewById(R.id.sw_alarm);
        swAlarm.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() { // from class: com.chileaf.cl831.sample.MainActivity.1
            @Override // android.widget.CompoundButton.OnCheckedChangeListener
            public void onCheckedChanged(CompoundButton buttonView, boolean isChecked) {
                MainActivity.this.mManager.setHeartRateAlarm(isChecked);
                MainActivity mainActivity = MainActivity.this;
                mainActivity.showToast(mainActivity.getAlarm(isChecked));
            }
        });
        findViewById(R.id.btn_hr_alert).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$OmK5wcZcoM3bgTCLiq_wetzqWbk
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$17$MainActivity(view);
            }
        });
        findViewById(R.id.btn_hr_max).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$LrIn5M4dV-TO_GLwivwEK0cxmSU
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$18$MainActivity(view);
            }
        });
        findViewById(R.id.btn_get_hr_max).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$HotWVZJU9Z9IZGyEm4x-yMOjqkM
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$19$MainActivity(view);
            }
        });
        findViewById(R.id.btn_get_sleep_data).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$V-pc8K21LJePX9Lo-E3RZDa97rY
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$20$MainActivity(view);
            }
        });
        findViewById(R.id.btn_3d_frequency).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$uOwYfuTw9UPxUetfSlYyK0C1LTU
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$21$MainActivity(view);
            }
        });
        findViewById(R.id.btn_3d_0).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$UdRmVusOfCPicn0vyLX9dyYkUAU
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$22$MainActivity(view);
            }
        });
        findViewById(R.id.btn_3d_1).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$ATRy0grQSltC9b6CQRXPMBurRMI
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$23$MainActivity(view);
            }
        });
        findViewById(R.id.btn_3d_2).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$-SVtyr2QziX2G26lBXxZ0wwiDEk
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$24$MainActivity(view);
            }
        });
        findViewById(R.id.btn_3d_3).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$O8yVVl0dhzc_wO0orWSC86W9UEs
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$25$MainActivity(view);
            }
        });
        findViewById(R.id.btn_3d_4).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$IhdVde60cuSUKOlNJhoApjNe5Dk
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$26$MainActivity(view);
            }
        });
        findViewById(R.id.btn_6d_frequency).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$XFhUZfs7NaBWk0aQyiPGghwyzUY
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$27$MainActivity(view);
            }
        });
        findViewById(R.id.btn_6d_0).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$G0fPzKDPZDsgtwgc8e92IiDkxUA
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$28$MainActivity(view);
            }
        });
        findViewById(R.id.btn_6d_1).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$eAOAyP8wN99_rx-Qwkb64bssS1Y
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$29$MainActivity(view);
            }
        });
        findViewById(R.id.btn_6d_2).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$taKAeTpjUfoxv6xs5fpryskZLKk
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$30$MainActivity(view);
            }
        });
        findViewById(R.id.btn_6d_3).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$iACLNdo8uYj2dcO7EtcZygegql8
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$31$MainActivity(view);
            }
        });
        SwitchCompat sw3dStatus = (SwitchCompat) findViewById(R.id.sw_3d_status);
        sw3dStatus.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() { // from class: com.chileaf.cl831.sample.MainActivity.2
            @Override // android.widget.CompoundButton.OnCheckedChangeListener
            public void onCheckedChanged(CompoundButton buttonView, boolean isChecked) {
                MainActivity.this.mManager.set3DEnabled(isChecked);
                MainActivity mainActivity = MainActivity.this;
                mainActivity.showToast(mainActivity.get3DStatus(isChecked));
            }
        });
        findViewById(R.id.btn_3d_status).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$STefBwB6IreEtIlxKt36otT5y8A
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$32$MainActivity(view);
            }
        });
        final AppCompatEditText etFilter = (AppCompatEditText) findViewById(R.id.et_filter);
        this.mBtnConnect.setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$p7CyU7jaJiABi_fGOVa9bhv83WQ
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$33$MainActivity(etFilter, view);
            }
        });
    }

    public /* synthetic */ void lambda$initView$0$MainActivity(View view) {
        startActivity(new Intent(this, (Class<?>) MultiConnectActivity.class));
    }

    public /* synthetic */ void lambda$initView$1$MainActivity(View view) {
        startActivity(new Intent(this, (Class<?>) SportHealthActivity.class));
    }

    public /* synthetic */ void lambda$initView$2$MainActivity(View view) {
        this.mManager.getHeartRateStatus();
    }

    public /* synthetic */ void lambda$initView$3$MainActivity(View view) {
        startActivity(new Intent(this, (Class<?>) UserInfoActivity.class));
    }

    public /* synthetic */ void lambda$initView$4$MainActivity(View view) {
        this.mManager.restoration();
    }

    public /* synthetic */ void lambda$initView$5$MainActivity(View view) {
        if (!this.mManager.isConnected()) {
            showToast("请先连接设备");
        } else {
            startActivity(new Intent(this, (Class<?>) DfuActivity.class));
        }
    }

    public /* synthetic */ void lambda$initView$6$MainActivity(View view) {
        launchHistory(2);
    }

    public /* synthetic */ void lambda$initView$7$MainActivity(View view) {
        launchHistory(4);
    }

    public /* synthetic */ void lambda$initView$8$MainActivity(View view) {
        launchHistory(6);
    }

    public /* synthetic */ void lambda$initView$9$MainActivity(View view) {
        launchHistory(20);
    }

    public /* synthetic */ void lambda$initView$10$MainActivity(View view) {
        launchHistory(8);
    }

    public /* synthetic */ void lambda$initView$11$MainActivity(View view) {
        launchHistory(16);
    }

    public /* synthetic */ void lambda$initView$12$MainActivity(View view) {
        launchHistory(18);
    }

    public /* synthetic */ void lambda$initView$13$MainActivity(View view) {
        int min = getValue(this.mEtMin);
        int max = getValue(this.mEtMax);
        int goal = getValue(this.mEtGoal);
        this.mManager.setHeartRateStatus(min, max, goal);
    }

    public /* synthetic */ void lambda$initView$14$MainActivity(View view) {
        this.mManager.shutdown();
    }

    public /* synthetic */ void lambda$initView$15$MainActivity(View view) {
        startActivity(new Intent(this, (Class<?>) BloodOxygenActivity.class));
    }

    public /* synthetic */ void lambda$initView$16$MainActivity(View view) {
        startActivity(new Intent(this, (Class<?>) TemperatureActivity.class));
    }

    public /* synthetic */ void lambda$initView$17$MainActivity(View v) {
        this.mManager.getHeartRateAlarm();
    }

    public /* synthetic */ void lambda$initView$18$MainActivity(View view) {
        int max = getValue(this.mEtHRMax);
        this.mManager.setHeartRateMax(max);
    }

    public /* synthetic */ void lambda$initView$19$MainActivity(View v) {
        this.mManager.getHeartRateMax();
    }

    public /* synthetic */ void lambda$initView$20$MainActivity(View view) {
        startActivity(new Intent(this, (Class<?>) HistorySleepActivity.class));
    }

    public /* synthetic */ void lambda$initView$21$MainActivity(View v) {
        this.mManager.get3DFrequency();
    }

    public /* synthetic */ void lambda$initView$22$MainActivity(View v) {
        this.mManager.set3DFrequency(0);
    }

    public /* synthetic */ void lambda$initView$23$MainActivity(View v) {
        this.mManager.set3DFrequency(1);
    }

    public /* synthetic */ void lambda$initView$24$MainActivity(View v) {
        this.mManager.set3DFrequency(2);
    }

    public /* synthetic */ void lambda$initView$25$MainActivity(View v) {
        this.mManager.set3DFrequency(3);
    }

    public /* synthetic */ void lambda$initView$26$MainActivity(View v) {
        this.mManager.set3DFrequency(4);
    }

    public /* synthetic */ void lambda$initView$27$MainActivity(View view) {
        this.mManager.get6DFrequency();
    }

    public /* synthetic */ void lambda$initView$28$MainActivity(View view) {
        this.mManager.set6DFrequency(0);
    }

    public /* synthetic */ void lambda$initView$29$MainActivity(View view) {
        this.mManager.set6DFrequency(1);
    }

    public /* synthetic */ void lambda$initView$30$MainActivity(View view) {
        this.mManager.set6DFrequency(2);
    }

    public /* synthetic */ void lambda$initView$31$MainActivity(View view) {
        this.mManager.set6DFrequency(3);
    }

    public /* synthetic */ void lambda$initView$32$MainActivity(View v) {
        this.mManager.get3DStatus();
    }

    public /* synthetic */ void lambda$initView$33$MainActivity(AppCompatEditText etFilter, View view) {
        String filter = etFilter.getText().toString();
        if (!TextUtils.isEmpty(filter)) {
            this.mManager.setFilterNames(filter);
        } else {
            this.mManager.setFilterNames((String[]) null);
        }
        if (isBLEEnabled()) {
            if (!this.mDeviceConnected) {
                showDeviceScanningDialog();
                return;
            } else {
                this.mManager.disconnectDevice();
                return;
            }
        }
        showBLEDialog();
    }

    private int getValue(EditText view) {
        String value = view.getText().toString();
        if (value.isEmpty()) {
            return 0;
        }
        return Integer.parseInt(value);
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initData(Bundle savedInstanceState) {
        isBLESupported();
        if (!isBLEEnabled()) {
            showBLEDialog();
        }
        this.mFrequency3DMap.put(0, "25HZ");
        this.mFrequency3DMap.put(1, "50HZ");
        this.mFrequency3DMap.put(2, "100HZ");
        this.mFrequency3DMap.put(3, "200HZ");
        this.mFrequency3DMap.put(4, "400HZ");
        this.mFrequency6DMap.put(0, "26HZ");
        this.mFrequency6DMap.put(1, "52HZ");
        this.mFrequency6DMap.put(2, "104HZ");
        this.mFrequency6DMap.put(3, "208HZ");
        this.mManager.setManagerCallbacks(this);
        this.mManager.addAccelerometerCallback(new AccelerometerCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$93GTuAvd3g2NLEUqpvp1DWOReWs
            @Override // com.android.chileaf.fitness.callback.AccelerometerCallback
            public final void onAccelerometerReceived(BluetoothDevice bluetoothDevice, int i, int i2, int i3) {
                this.f$0.lambda$initData$35$MainActivity(bluetoothDevice, i, i2, i3);
            }
        });
        this.mManager.addHeartRateStatusCallback(new HeartRateStatusCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$Ee6yiDry_cvNUqs2_WH4CqqbnA8
            @Override // com.android.chileaf.fitness.callback.HeartRateStatusCallback
            public final void onHeartRateStatusReceived(BluetoothDevice bluetoothDevice, int i, int i2, int i3) {
                this.f$0.lambda$initData$37$MainActivity(bluetoothDevice, i, i2, i3);
            }
        });
        this.mManager.setCustomDataReceivedCallback(new CustomDataReceivedCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$uzoPmTaNJN2KHCDiSbr5Q9Ju-2Y
            @Override // com.android.chileaf.fitness.callback.CustomDataReceivedCallback
            public final void onDataReceived(BluetoothDevice bluetoothDevice, byte[] bArr) {
                this.f$0.lambda$initData$39$MainActivity(bluetoothDevice, bArr);
            }
        });
        this.mManager.addHeartRateAlarmCallback(new HeartRateAlarmCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$6TRJwQK660qs0bhmarkbaiNCayE
            @Override // com.android.chileaf.fitness.callback.HeartRateAlarmCallback
            public final void onHeartRateAlarmReceived(BluetoothDevice bluetoothDevice, long j, boolean z) {
                this.f$0.lambda$initData$41$MainActivity(bluetoothDevice, j, z);
            }
        });
        this.mManager.addHeartRateMaxCallback(new HeartRateMaxCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$xPO007mPCdt3qktsjIF1NIVrTQQ
            @Override // com.android.chileaf.fitness.callback.HeartRateMaxCallback
            public final void onHeartRateMaxReceived(BluetoothDevice bluetoothDevice, int i) {
                this.f$0.lambda$initData$43$MainActivity(bluetoothDevice, i);
            }
        });
        this.mManager.addSensor3DFrequencyCallback(new Sensor3DFrequencyCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$rfOI0YFqOpw5KZGR-w0SEzirF-k
            @Override // com.android.chileaf.fitness.callback.Sensor3DFrequencyCallback
            public final void onSensor3DFrequencyReceived(BluetoothDevice bluetoothDevice, int i) {
                this.f$0.lambda$initData$45$MainActivity(bluetoothDevice, i);
            }
        });
        this.mManager.addSensor3DStatusCallback(new Sensor3DStatusCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$VDy2N8KEliG0-wkuTQcoyTqnEYU
            @Override // com.android.chileaf.fitness.callback.Sensor3DStatusCallback
            public final void onSensor3DStatusReceived(BluetoothDevice bluetoothDevice, boolean z) {
                this.f$0.lambda$initData$47$MainActivity(bluetoothDevice, z);
            }
        });
        this.mManager.addBodyHealthCallback(new AnonymousClass3());
        this.mManager.addSensor6DFrequencyCallback(new AnonymousClass4());
        this.mManager.addSensor6DRawDataCallback(new AnonymousClass5());
    }

    public /* synthetic */ void lambda$initData$34$MainActivity(int x, int y, int z) {
        this.mTvAccelerometer.setText(getString(R.string.accelerometer, new Object[]{Integer.valueOf(x), Integer.valueOf(y), Integer.valueOf(z)}));
    }

    public /* synthetic */ void lambda$initData$35$MainActivity(BluetoothDevice device, final int x, final int y, final int z) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$dGhSZlnBlKtMddtpLfVlHhsAHdU
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$34$MainActivity(x, y, z);
            }
        });
    }

    public /* synthetic */ void lambda$initData$36$MainActivity(int min, int max, int goal) {
        this.mTvHRStatus.setText("HR Status Min:" + min + " Max:" + max + " Goal:" + goal);
    }

    public /* synthetic */ void lambda$initData$37$MainActivity(BluetoothDevice device, final int min, final int max, final int goal) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$MNF_c8164kuVk2JZgy3WrHP0-14
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$36$MainActivity(min, max, goal);
            }
        });
    }

    public /* synthetic */ void lambda$initData$38$MainActivity(byte[] data) {
        this.mTvReceivedData.setText("Received data:" + HexUtil.bytes2HexString(data));
    }

    public /* synthetic */ void lambda$initData$39$MainActivity(BluetoothDevice device, final byte[] data) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$IqG2TisNsYAWJP5F9IfxLI5BW6I
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$38$MainActivity(data);
            }
        });
    }

    public /* synthetic */ void lambda$initData$41$MainActivity(BluetoothDevice device, final long stamp, final boolean enabled) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$My9PtjK25NCHVWCpehTPix7ACYI
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$40$MainActivity(enabled, stamp);
            }
        });
    }

    public /* synthetic */ void lambda$initData$40$MainActivity(boolean enabled, long stamp) {
        String status = getAlarm(enabled);
        this.mTvHRAlertStatus.setText("HR Alarm:" + status + " \n(" + this.mDateFormat.format(new Date(stamp)) + ")");
    }

    public /* synthetic */ void lambda$initData$42$MainActivity(int max) {
        this.mTvHRMax.setText("HeartRate Max:" + max);
    }

    public /* synthetic */ void lambda$initData$43$MainActivity(BluetoothDevice device, final int max) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$vN32OE_3PxGK0IhINw4cF6jdtX0
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$42$MainActivity(max);
            }
        });
    }

    public /* synthetic */ void lambda$initData$44$MainActivity(int frequency) {
        this.mTv3DFrequency.setText("3D Frequency:" + this.mFrequency3DMap.get(Integer.valueOf(frequency)));
    }

    public /* synthetic */ void lambda$initData$45$MainActivity(BluetoothDevice device, final int frequency) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$9Oiu6Ro5R1SHkcOOT033kdnWG-4
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$44$MainActivity(frequency);
            }
        });
    }

    /* renamed from: com.chileaf.cl831.sample.MainActivity$3, reason: invalid class name */
    class AnonymousClass3 implements BodyHealthCallback {
        AnonymousClass3() {
        }

        public /* synthetic */ void lambda$onHealthReceived$0$MainActivity$3(int vo2Max, int breathRate, int emotionLevel, int stressPercent, int stamina, float tp, float lf, float hf) {
            MainActivity.this.mTvHealth.setText("Health vo2Max:" + vo2Max + " breathRate:" + breathRate + " emotionLevel:" + MainActivity.this.getEmotion(emotionLevel) + " stressPercent:" + stressPercent + "% stamina:" + MainActivity.this.getStamina(stamina) + " \nTP:" + tp + " LF:" + lf + " HF:" + hf);
        }

        @Override // com.android.chileaf.fitness.callback.BodyHealthCallback
        public void onHealthReceived(BluetoothDevice device, final int vo2Max, final int breathRate, final int emotionLevel, final int stressPercent, final int stamina, final float tp, final float lf, final float hf) {
            MainActivity.this.runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$3$hnTzVl4zW7keWMwjTUlcFCidyIo
                @Override // java.lang.Runnable
                public final void run() {
                    this.f$0.lambda$onHealthReceived$0$MainActivity$3(vo2Max, breathRate, emotionLevel, stressPercent, stamina, tp, lf, hf);
                }
            });
        }
    }

    public /* synthetic */ void lambda$initData$46$MainActivity(boolean enabled) {
        TextView textView = this.mTv3DStatus;
        StringBuilder sb = new StringBuilder();
        sb.append("3D Status:");
        sb.append(enabled ? "Enabled" : "Disabled");
        textView.setText(sb.toString());
    }

    public /* synthetic */ void lambda$initData$47$MainActivity(BluetoothDevice device, final boolean enabled) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$tKRNdSlzrWcFVohXeC2e8qI9bVM
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$46$MainActivity(enabled);
            }
        });
    }

    /* renamed from: com.chileaf.cl831.sample.MainActivity$4, reason: invalid class name */
    class AnonymousClass4 implements Sensor6DFrequencyCallback {
        AnonymousClass4() {
        }

        public /* synthetic */ void lambda$onSensor6DFrequencyReceived$0$MainActivity$4(int frequency) {
            MainActivity.this.mTv6DFrequency.setText("6D Frequency:" + ((String) MainActivity.this.mFrequency6DMap.get(Integer.valueOf(frequency))));
        }

        @Override // com.android.chileaf.fitness.callback.Sensor6DFrequencyCallback
        public void onSensor6DFrequencyReceived(BluetoothDevice device, final int frequency) {
            MainActivity.this.runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$4$LHva5Zdu44WvA_rAADQsFwfZJI4
                @Override // java.lang.Runnable
                public final void run() {
                    this.f$0.lambda$onSensor6DFrequencyReceived$0$MainActivity$4(frequency);
                }
            });
        }
    }

    /* renamed from: com.chileaf.cl831.sample.MainActivity$5, reason: invalid class name */
    class AnonymousClass5 implements Sensor6DRawDataCallback {
        AnonymousClass5() {
        }

        @Override // com.android.chileaf.fitness.callback.Sensor6DRawDataCallback
        public void onSensor6DRawDataReceived(BluetoothDevice device, final long utc, final int sequence, final int gyroscopeX, final int gyroscopeY, final int gyroscopeZ, final int accelerometerX, final int accelerometerY, final int accelerometerZ) {
            MainActivity.this.runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$5$xviwFRgC9nuOjGjmJY94A4pXDHk
                @Override // java.lang.Runnable
                public final void run() {
                    this.f$0.lambda$onSensor6DRawDataReceived$0$MainActivity$5(utc, sequence, gyroscopeX, gyroscopeY, gyroscopeZ, accelerometerX, accelerometerY, accelerometerZ);
                }
            });
        }

        public /* synthetic */ void lambda$onSensor6DRawDataReceived$0$MainActivity$5(long utc, int sequence, int gyroscopeX, int gyroscopeY, int gyroscopeZ, int accelerometerX, int accelerometerY, int accelerometerZ) {
            String time;
            if (utc != 255) {
                time = "\nUTC:" + MainActivity.this.mDateFormat.format(new Date(utc)) + "(" + utc + ")";
            } else {
                time = "";
            }
            MainActivity.this.mTv6DRawData.setText("Sensor:" + time + "\nSequence:" + sequence + "\nGyroscopeX:" + gyroscopeX + "\nGyroscopeY:" + gyroscopeY + "\nGyroscopeZ:" + gyroscopeZ + "\nAccelerometerX:" + accelerometerX + "\nAccelerometerY:" + accelerometerY + "\nAccelerometerZ:" + accelerometerZ);
        }
    }

    private void launchHistory(int type) {
        Intent history = new Intent(this, (Class<?>) HistoryActivity.class);
        history.putExtra(HistoryActivity.EXTRA_HISTORY, type);
        startActivity(history);
    }

    private void showDeviceScanningDialog() {
        if (isLocationEnabled(this)) {
            XXPermissions.with(this).permission(getPermissions()).request(new AnonymousClass6());
        } else {
            new AlertDialog.Builder(this).setTitle(getString(R.string.location_permission_title)).setMessage(getString(R.string.location_permission_info)).setPositiveButton("OK", new DialogInterface.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$aFX-l_v_kHEZfcsamg7ZACwhqoA
                @Override // android.content.DialogInterface.OnClickListener
                public final void onClick(DialogInterface dialogInterface, int i) {
                    this.f$0.lambda$showDeviceScanningDialog$48$MainActivity(dialogInterface, i);
                }
            }).setNegativeButton("Cancel", (DialogInterface.OnClickListener) null).show();
        }
    }

    /* renamed from: com.chileaf.cl831.sample.MainActivity$6, reason: invalid class name */
    class AnonymousClass6 implements OnPermissionCallback {
        AnonymousClass6() {
        }

        @Override // com.hjq.permissions.OnPermissionCallback
        public void onGranted(List<String> permissions, boolean allGranted) {
            if (allGranted) {
                MainActivity.this.runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$6$SMN58hP-pQhGp1P1aB31KNVmhoY
                    @Override // java.lang.Runnable
                    public final void run() {
                        this.f$0.lambda$onGranted$0$MainActivity$6();
                    }
                });
            } else {
                MainActivity.this.showToast("permission is denied");
            }
        }

        public /* synthetic */ void lambda$onGranted$0$MainActivity$6() {
            ScannerFragment dialog = ScannerFragment.getInstance();
            dialog.show(MainActivity.this.getSupportFragmentManager(), "scan_fragment");
        }

        @Override // com.hjq.permissions.OnPermissionCallback
        public void onDenied(List<String> permissions, boolean doNotAskAgain) {
            if (doNotAskAgain) {
                new AlertDialog.Builder(MainActivity.this).setTitle(MainActivity.this.getString(R.string.permission_required)).setMessage(MainActivity.this.getString(R.string.permission_location_info)).setPositiveButton(MainActivity.this.getString(R.string.yes), new DialogInterface.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$6$XBsMiwVoFOsjvbbwCV_lSlOK1Q0
                    @Override // android.content.DialogInterface.OnClickListener
                    public final void onClick(DialogInterface dialogInterface, int i) {
                        this.f$0.lambda$onDenied$1$MainActivity$6(dialogInterface, i);
                    }
                }).setNegativeButton(MainActivity.this.getString(R.string.f5no), (DialogInterface.OnClickListener) null).show();
            } else {
                MainActivity.this.showToast("permission is denied");
            }
        }

        public /* synthetic */ void lambda$onDenied$1$MainActivity$6(DialogInterface dialog, int which) {
            MainActivity.this.onPermissionSettings();
        }
    }

    public /* synthetic */ void lambda$showDeviceScanningDialog$48$MainActivity(DialogInterface dialog, int which) {
        onEnableLocation();
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* renamed from: defaultUI, reason: merged with bridge method [inline-methods] and merged with bridge method [inline-methods] */
    public void lambda$onLinkLossOccurred$56$MainActivity() {
        this.mTvDeviceName.setText("Device name");
        this.mTvVersion.setText("Version:--");
        this.mTvRssi.setText("Rssi:--");
        this.mTvBattery.setText("Battery:--");
        this.mTvSport.setText("Sport:--");
        this.mTvAccelerometer.setText("Accelerometer:--");
        this.mTvHeartRate.setText("Heart Rate:--");
        this.mTvHRStatus.setText("HR Status Min:--");
        this.mTvHRAlertStatus.setText("HR Alarm:--");
        this.mTvHRMax.setText("HeartRate Max:--");
        this.mTv3DFrequency.setText("3D Frequency:--");
        this.mTv3DStatus.setText("3D Status:--");
        this.mTvHealth.setText("Health:--");
        this.mTv6DFrequency.setText("6D Frequency:--");
        this.mTv6DRawData.setText("6D RawData:--");
        this.mBtnConnect.setText(getString(R.string.action_connect));
    }

    /* JADX INFO: Access modifiers changed from: private */
    public String get3DStatus(boolean enabled) {
        return enabled ? "Enabled 3D" : "Disabled 3D";
    }

    /* JADX INFO: Access modifiers changed from: private */
    public String getAlarm(boolean enabled) {
        return enabled ? "Alarm By Age" : "Alarm By High-Low";
    }

    @Override // com.chileaf.cl831.sample.ScannerFragment.OnDeviceSelectedListener
    public void onDeviceSelected(BluetoothDevice device, String name) {
        this.mManager.connectDevice(device);
        this.mTvDeviceName.setText(getString(R.string.device_name, new Object[]{name}));
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public void onError(BluetoothDevice device, String message, int errorCode) {
        Timber.e("onError: (" + errorCode + ")", new Object[0]);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public void onDeviceNotSupported(BluetoothDevice device) {
        showToast(getString(R.string.not_supported));
    }

    public /* synthetic */ void lambda$onSoftwareVersion$49$MainActivity(String software) {
        this.mTvVersion.setText("Software Version:" + software);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, com.android.chileaf.fitness.common.profile.ProfileCallback
    public void onSoftwareVersion(BluetoothDevice device, final String software) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$Pn9EMjAA7eYEWkDpgbsAEPp7OVc
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onSoftwareVersion$49$MainActivity(software);
            }
        });
    }

    public /* synthetic */ void lambda$onRssiRead$50$MainActivity(int rssi) {
        this.mTvRssi.setText("Rssi:" + rssi + "dBm");
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.callback.RssiCallback
    public void onRssiRead(BluetoothDevice device, final int rssi) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$oXZbkH6hHJxa-20mxj42_ODvPqE
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onRssiRead$50$MainActivity(rssi);
            }
        });
    }

    public /* synthetic */ void lambda$onBatteryLevelChanged$51$MainActivity(int batteryLevel) {
        this.mTvBattery.setText(getString(R.string.battery, new Object[]{Integer.valueOf(batteryLevel)}));
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, com.android.chileaf.fitness.common.battery.BatteryLevelCallback
    public void onBatteryLevelChanged(final BluetoothDevice device, final int batteryLevel) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$uYq1aARReh3yCgAJplhTUrD4mkY
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onBatteryLevelChanged$51$MainActivity(batteryLevel);
            }
        });
    }

    @Override // com.android.chileaf.fitness.callback.WearManagerCallbacks, com.android.chileaf.fitness.common.heart.HeartRateMeasurementCallback
    public void onHeartRateMeasurementReceived(BluetoothDevice device, final int heartRate, Boolean contactDetected, Integer energyExpanded, final List<Integer> rrIntervals) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$6eMLfJ4RUmAGaR--J7Pe1XvfQzQ
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onHeartRateMeasurementReceived$52$MainActivity(heartRate, rrIntervals);
            }
        });
    }

    public /* synthetic */ void lambda$onHeartRateMeasurementReceived$52$MainActivity(int heartRate, List rrIntervals) {
        this.mTvHeartRate.setText(getString(R.string.heart_rate, new Object[]{Integer.valueOf(heartRate)}));
        if (rrIntervals != null) {
            Timber.e("rrIntervals:%s", rrIntervals.toString());
        }
    }

    public /* synthetic */ void lambda$onSportReceived$53$MainActivity(int step, int distance, int calorie) {
        this.mTvSport.setText(getString(R.string.sport, new Object[]{Integer.valueOf(step), Float.valueOf(distance / 100.0f), Float.valueOf(calorie / 10.0f)}));
    }

    @Override // com.android.chileaf.fitness.callback.WearManagerCallbacks, com.android.chileaf.fitness.callback.BodySportCallback
    public void onSportReceived(BluetoothDevice device, final int step, final int distance, final int calorie) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$jkeBc9RjsCBLWBD59rzSVnwSgAI
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onSportReceived$53$MainActivity(step, distance, calorie);
            }
        });
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public void onDeviceConnected(BluetoothDevice device) {
        this.mDeviceConnected = true;
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$KYwzGmWn0Dc8FGd51Oa3QOEd5-o
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onDeviceConnected$54$MainActivity();
            }
        });
    }

    public /* synthetic */ void lambda$onDeviceConnected$54$MainActivity() {
        this.mBtnConnect.setText(R.string.action_disconnect);
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public void onDeviceDisconnected(final BluetoothDevice device) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$RRZb6DLOhArzQ4BEMitqDYTzQEs
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onDeviceDisconnected$55$MainActivity();
            }
        });
        this.mDeviceConnected = false;
        this.mManager.close();
    }

    @Override // com.android.chileaf.fitness.FitnessManagerCallbacks, no.nordicsemi.android.ble.BleManagerCallbacks
    public void onLinkLossOccurred(BluetoothDevice device) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$MainActivity$KcnwJzbTW79FsLXFRPO-VI8TInc
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onLinkLossOccurred$56$MainActivity();
            }
        });
        this.mDeviceConnected = false;
        this.mManager.close();
    }

    @Override // androidx.activity.ComponentActivity, android.app.Activity
    public void onBackPressed() {
        this.mManager.disconnectDevice();
        super.onBackPressed();
    }
}
