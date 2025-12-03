package com.chileaf.cl831.sample;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothManager;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.afollestad.materialdialogs.DialogAction;
import com.afollestad.materialdialogs.MaterialDialog;
import com.android.chileaf.WearManager;
import com.hjq.permissions.OnPermissionCallback;
import com.hjq.permissions.Permission;
import com.hjq.permissions.XXPermissions;
import java.util.List;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public abstract class BaseActivity extends AppCompatActivity {
    protected Handler mHandler = new Handler(Looper.getMainLooper());
    protected LoadingDialog mLoading;
    protected WearManager mManager;

    protected abstract void initData(Bundle savedInstanceState);

    protected abstract void initView();

    protected abstract int layoutId();

    @Override // androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(layoutId());
        initialize();
        initView();
        initData(savedInstanceState);
    }

    private void initialize() {
        ImageView ivBack = (ImageView) findViewById(R.id.iv_toolbar_back);
        if (ivBack != null) {
            ivBack.setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$BaseActivity$q49ZkHyvxKogcSJfJqadtwq8dn8
                @Override // android.view.View.OnClickListener
                public final void onClick(View view) {
                    this.f$0.lambda$initialize$0$BaseActivity(view);
                }
            });
        }
        WearManager wearManager = WearManager.getInstance(this);
        this.mManager = wearManager;
        wearManager.setDebug(BuildConfig.DEBUG);
    }

    public /* synthetic */ void lambda$initialize$0$BaseActivity(View v) {
        onBackPressed();
    }

    protected void setTitle(String title) {
        TextView tvTitle = (TextView) findViewById(R.id.tv_toolbar_title);
        if (tvTitle != null) {
            tvTitle.setText(title);
        }
    }

    protected void launchDetail(int type, long stamp) {
        Intent history = new Intent(this, (Class<?>) HistoryDetailActivity.class);
        history.putExtra(HistoryDetailActivity.EXTRA_TYPE, type);
        history.putExtra(HistoryDetailActivity.EXTRA_STAMP, stamp);
        startActivity(history);
    }

    protected void showLoading() {
        showLoading(getString(R.string.loading));
    }

    protected void showLoading(String message) {
        LoadingDialog loadingDialogBuild = LoadingDialog.Builder(this).setMessage(message).build();
        this.mLoading = loadingDialogBuild;
        loadingDialogBuild.show();
    }

    protected void showLoadingAutoDismiss(final long delay) {
        showLoading();
        this.mHandler.postDelayed(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$HlcB8wm_x6lKstripHV-jdOsXMM
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.hideLoading();
            }
        }, delay);
    }

    protected void hideLoading() {
        LoadingDialog loadingDialog = this.mLoading;
        if (loadingDialog != null && loadingDialog.isShowing()) {
            this.mLoading.dismiss();
        }
    }

    protected void showToast(final int messageResId) {
        Toast.makeText(this, messageResId, 0).show();
    }

    public /* synthetic */ void lambda$showToast$1$BaseActivity(String message) {
        Toast.makeText(this, message, 0).show();
    }

    /* JADX INFO: Access modifiers changed from: protected */
    public void showToast(final String message) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$BaseActivity$NN63dUiIWHMsg77ZgfbHprA5sRg
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$showToast$1$BaseActivity(message);
            }
        });
    }

    protected void isBLESupported() {
        if (!getPackageManager().hasSystemFeature("android.hardware.bluetooth_le")) {
            new MaterialDialog.Builder(this).title(R.string.no_ble).positiveText(R.string.scanner_action_cancel).positiveColorRes(R.color.colorPrimary).onPositive(new MaterialDialog.SingleButtonCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$BaseActivity$Z0hnuHDQHzTJ8Xgrty5js1v3Xco
                @Override // com.afollestad.materialdialogs.MaterialDialog.SingleButtonCallback
                public final void onClick(MaterialDialog materialDialog, DialogAction dialogAction) {
                    this.f$0.lambda$isBLESupported$2$BaseActivity(materialDialog, dialogAction);
                }
            }).show();
        }
    }

    public /* synthetic */ void lambda$isBLESupported$2$BaseActivity(MaterialDialog dialog, DialogAction which) {
        finish();
    }

    protected boolean isBLEEnabled() {
        BluetoothManager bluetoothManager = (BluetoothManager) getSystemService("bluetooth");
        BluetoothAdapter adapter = bluetoothManager.getAdapter();
        return adapter != null && adapter.isEnabled();
    }

    protected String[] getPermissions() {
        int targetSdkVersion = getApplicationInfo().targetSdkVersion;
        if (Build.VERSION.SDK_INT >= 31 && targetSdkVersion >= 31) {
            return new String[]{Permission.BLUETOOTH_SCAN, Permission.BLUETOOTH_CONNECT, Permission.ACCESS_FINE_LOCATION};
        }
        if (Build.VERSION.SDK_INT >= 29 && targetSdkVersion >= 29) {
            return new String[]{Permission.ACCESS_FINE_LOCATION};
        }
        return new String[]{Permission.ACCESS_COARSE_LOCATION};
    }

    protected void showBLEDialog() {
        XXPermissions.with(this).permission(getPermissions()).request(new OnPermissionCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$BaseActivity$2yGmVVJ5CFale2N_klm1UtlXJ8w
            @Override // com.hjq.permissions.OnPermissionCallback
            public /* synthetic */ void onDenied(List list, boolean z) {
                OnPermissionCallback.CC.$default$onDenied(this, list, z);
            }

            @Override // com.hjq.permissions.OnPermissionCallback
            public final void onGranted(List list, boolean z) {
                this.f$0.lambda$showBLEDialog$3$BaseActivity(list, z);
            }
        });
    }

    public /* synthetic */ void lambda$showBLEDialog$3$BaseActivity(List permissions, boolean allGranted) {
        if (allGranted) {
            startActivity(new Intent("android.bluetooth.adapter.action.REQUEST_ENABLE"));
        } else {
            showToast(getString(R.string.no_required_permission));
        }
    }

    protected boolean isLocationEnabled(final Context context) throws Settings.SettingNotFoundException {
        if (Build.VERSION.SDK_INT < 23) {
            return true;
        }
        int locationMode = 0;
        try {
            locationMode = Settings.Secure.getInt(context.getContentResolver(), "location_mode");
        } catch (Settings.SettingNotFoundException e) {
        }
        return locationMode != 0;
    }

    protected void onEnableLocation() {
        Intent intent = new Intent("android.settings.LOCATION_SOURCE_SETTINGS");
        startActivity(intent);
    }

    protected void onPermissionSettings() {
        Intent intent = new Intent("android.settings.APPLICATION_DETAILS_SETTINGS");
        intent.setData(Uri.fromParts("package", getPackageName(), null));
        startActivity(intent);
    }

    protected String getEmotion(int level) {
        if (level == 0) {
            return "Not ready";
        }
        if (level == 1) {
            return "Calm";
        }
        if (level == 2) {
            return "Stressed";
        }
        if (level == 3) {
            return "Happy";
        }
        if (level == 4) {
            return "Tense";
        }
        if (level == 5) {
            return "Angry";
        }
        return "Unknown";
    }

    protected String getStamina(int stamina) {
        if (stamina == 0) {
            return "Not ready";
        }
        if (stamina == 1) {
            return "Normal";
        }
        if (stamina == 2) {
            return "Moderate fatigue";
        }
        if (stamina == 3) {
            return "Severe fatigue";
        }
        return "Unknown";
    }

    protected String getMode(int mode) {
        if (mode == 0) {
            return "Indoor running";
        }
        if (mode == 1) {
            return "Outdoor running";
        }
        if (mode == 2) {
            return "Outdoor cycling";
        }
        if (mode == 3) {
            return "Spinning bike";
        }
        if (mode == 4) {
            return "Free training";
        }
        if (mode == 5) {
            return "Skipping rope";
        }
        return "None";
    }
}
