package com.chileaf.cl831.sample.dfu;

import android.app.ActivityManager;
import android.app.NotificationManager;
import android.bluetooth.BluetoothDevice;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.preference.PreferenceManager;
import android.text.TextUtils;
import android.view.View;
import android.webkit.MimeTypeMap;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;
import androidx.activity.result.ActivityResultCallback;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContract;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;
import com.chileaf.cl831.sample.BaseActivity;
import com.chileaf.cl831.sample.R;
import com.chileaf.cl831.sample.dfu.UploadCancelFragment;
import com.hjq.permissions.OnPermissionCallback;
import com.hjq.permissions.Permission;
import com.hjq.permissions.XXPermissions;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import no.nordicsemi.android.dfu.DfuBaseService;
import no.nordicsemi.android.dfu.DfuProgressListener;
import no.nordicsemi.android.dfu.DfuProgressListenerAdapter;
import no.nordicsemi.android.dfu.DfuServiceInitiator;
import no.nordicsemi.android.dfu.DfuServiceListenerHelper;
import no.nordicsemi.android.support.v18.scanner.BluetoothLeScannerCompat;
import no.nordicsemi.android.support.v18.scanner.ScanCallback;
import no.nordicsemi.android.support.v18.scanner.ScanFilter;
import no.nordicsemi.android.support.v18.scanner.ScanResult;
import no.nordicsemi.android.support.v18.scanner.ScanSettings;
import timber.log.Timber;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes4.dex */
public class DfuActivity extends BaseActivity implements UploadCancelFragment.CancelFragmentListener {
    private static final String DATA_DFU_COMPLETED = "dfu_completed";
    private static final String DATA_DFU_ERROR = "dfu_error";
    private static final String DATA_STATUS = "status";
    private static final String PREFS_FILE_NAME = "com.chileaf.dfu.PREFS_FILE_NAME";
    private static final String PREFS_FILE_SIZE = "com.chileaf.dfu.PREFS_FILE_SIZE";
    private static final String PREFS_FILE_TYPE = "com.chileaf.dfu.PREFS_FILE_TYPE";
    private static final String PREFS_PREFIX = "com.chileaf.dfu";
    private static final String TAG = "DfuActivity";
    private boolean mDfuCompleted;
    private String mDfuError;
    private TextView mFileNameView;
    private TextView mFileSizeView;
    private TextView mFileStatusView;
    private Uri mFileUri;
    private boolean mResumed;
    private Button mSelectFileButton;
    private boolean mStatusOk;
    private TextView mTextPercentage;
    private TextView mTextUploading;
    private Button mUploadButton;
    private final ScanCallback mScanCallback = new ScanCallback() { // from class: com.chileaf.cl831.sample.dfu.DfuActivity.1
        @Override // no.nordicsemi.android.support.v18.scanner.ScanCallback
        public void onBatchScanResults(final List<ScanResult> results) throws NumberFormatException {
            for (ScanResult result : results) {
                BluetoothDevice device = result.getDevice();
                if (DfuActivity.this.isDfuDevice(device.getName())) {
                    DfuActivity.this.showToast("Start Update...");
                    DfuActivity.this.dfuUpdated(device);
                    return;
                }
            }
        }
    };
    private final ActivityResultLauncher<String> zipLauncher = registerForActivityResult(new ContentResultContract(), new ActivityResultCallback<Uri>() { // from class: com.chileaf.cl831.sample.dfu.DfuActivity.2
        @Override // androidx.activity.result.ActivityResultCallback
        public void onActivityResult(Uri uri) {
            String filePath;
            if (uri == null) {
                DfuActivity.this.showToast("Uri is null");
                return;
            }
            if ("content".equalsIgnoreCase(uri.getScheme())) {
                Cursor query = DfuActivity.this.getContentResolver().query(uri, null, null, null, null);
                if (query != null && query.moveToNext()) {
                    int displayNameIndex = query.getColumnIndex("_display_name");
                    int fileSizeIndex = query.getColumnIndex("_size");
                    String fileName = query.getString(displayNameIndex);
                    int fileSize = query.getInt(fileSizeIndex);
                    DfuActivity.this.updateFileInfo(uri, fileName, fileSize, 0);
                    query.close();
                } else if ("file".equalsIgnoreCase(uri.getScheme()) && (filePath = uri.getPath()) != null) {
                    File file = new File(filePath);
                    DfuActivity.this.updateFileInfo(uri, file.getName(), file.length(), 0);
                }
                Timber.i("zipLauncher  uri:%s", uri);
            }
        }
    });
    private final DfuProgressListener mDfuProgressListener = new AnonymousClass3();

    private static class ContentResultContract extends ActivityResultContract<String, Uri> {
        private ContentResultContract() {
        }

        @Override // androidx.activity.result.contract.ActivityResultContract
        public Intent createIntent(Context context, String type) {
            return new Intent("android.intent.action.GET_CONTENT").addCategory("android.intent.category.OPENABLE").setType(type);
        }

        /* JADX WARN: Can't rename method to resolve collision */
        @Override // androidx.activity.result.contract.ActivityResultContract
        public Uri parseResult(int resultCode, Intent intent) {
            if (resultCode == -1 && intent != null) {
                return intent.getData();
            }
            return null;
        }
    }

    /* renamed from: com.chileaf.cl831.sample.dfu.DfuActivity$3, reason: invalid class name */
    class AnonymousClass3 extends DfuProgressListenerAdapter {
        AnonymousClass3() {
        }

        @Override // no.nordicsemi.android.dfu.DfuProgressListenerAdapter, no.nordicsemi.android.dfu.DfuProgressListener
        public void onDeviceConnecting(final String deviceAddress) {
            DfuActivity.this.mTextPercentage.setText("Device Connecting...");
        }

        @Override // no.nordicsemi.android.dfu.DfuProgressListenerAdapter, no.nordicsemi.android.dfu.DfuProgressListener
        public void onDfuProcessStarting(final String deviceAddress) {
            DfuActivity.this.mTextPercentage.setText("Process Starting...");
        }

        @Override // no.nordicsemi.android.dfu.DfuProgressListenerAdapter, no.nordicsemi.android.dfu.DfuProgressListener
        public void onEnablingDfuMode(final String deviceAddress) {
            DfuActivity.this.mTextPercentage.setText("Updating...");
        }

        @Override // no.nordicsemi.android.dfu.DfuProgressListenerAdapter, no.nordicsemi.android.dfu.DfuProgressListener
        public void onFirmwareValidating(final String deviceAddress) {
            DfuActivity.this.mTextPercentage.setText("FirmwareValidating...");
        }

        @Override // no.nordicsemi.android.dfu.DfuProgressListenerAdapter, no.nordicsemi.android.dfu.DfuProgressListener
        public void onDeviceDisconnecting(final String deviceAddress) {
            DfuActivity.this.mTextPercentage.setText("Device Disconnecting...");
        }

        @Override // no.nordicsemi.android.dfu.DfuProgressListenerAdapter, no.nordicsemi.android.dfu.DfuProgressListener
        public void onDfuCompleted(final String deviceAddress) {
            DfuActivity.this.mTextPercentage.setText("Update Completed");
            if (!DfuActivity.this.mResumed) {
                DfuActivity.this.mDfuCompleted = true;
            } else {
                new Handler().postDelayed(new Runnable() { // from class: com.chileaf.cl831.sample.dfu.-$$Lambda$DfuActivity$3$361mcoeZXTUSlD3YUOJazFXXnKc
                    @Override // java.lang.Runnable
                    public final void run() {
                        this.f$0.lambda$onDfuCompleted$0$DfuActivity$3();
                    }
                }, 200L);
            }
        }

        public /* synthetic */ void lambda$onDfuCompleted$0$DfuActivity$3() {
            DfuActivity.this.onTransferCompleted();
            NotificationManager manager = (NotificationManager) DfuActivity.this.getSystemService("notification");
            if (manager != null) {
                manager.cancel(DfuBaseService.NOTIFICATION_ID);
            }
        }

        @Override // no.nordicsemi.android.dfu.DfuProgressListenerAdapter, no.nordicsemi.android.dfu.DfuProgressListener
        public void onDfuAborted(final String deviceAddress) {
            DfuActivity.this.mTextPercentage.setText("Update Aborted");
            new Handler().postDelayed(new Runnable() { // from class: com.chileaf.cl831.sample.dfu.-$$Lambda$DfuActivity$3$AURdAmge4viyV2HcE9yCtSNsbWo
                @Override // java.lang.Runnable
                public final void run() {
                    this.f$0.lambda$onDfuAborted$1$DfuActivity$3();
                }
            }, 200L);
        }

        public /* synthetic */ void lambda$onDfuAborted$1$DfuActivity$3() {
            DfuActivity.this.onUploadCanceled();
            NotificationManager manager = (NotificationManager) DfuActivity.this.getSystemService("notification");
            if (manager != null) {
                manager.cancel(DfuBaseService.NOTIFICATION_ID);
            }
        }

        @Override // no.nordicsemi.android.dfu.DfuProgressListenerAdapter, no.nordicsemi.android.dfu.DfuProgressListener
        public void onProgressChanged(final String deviceAddress, final int percent, final float speed, final float avgSpeed, final int currentPart, final int partsTotal) {
            DfuActivity.this.mTextPercentage.setText(DfuActivity.this.getString(R.string.dfu_uploading_percentage, new Object[]{Integer.valueOf(percent)}));
            if (partsTotal > 1) {
                DfuActivity.this.mTextUploading.setText(String.format(Locale.getDefault(), "Uploading Progress:%d/%d", Integer.valueOf(currentPart), Integer.valueOf(partsTotal)));
            } else {
                DfuActivity.this.mTextUploading.setText("Updating...");
            }
        }

        @Override // no.nordicsemi.android.dfu.DfuProgressListenerAdapter, no.nordicsemi.android.dfu.DfuProgressListener
        public void onError(final String deviceAddress, final int error, final int errorType, final String message) {
            if (DfuActivity.this.mResumed) {
                DfuActivity.this.showErrorMessage(message);
                new Handler().postDelayed(new Runnable() { // from class: com.chileaf.cl831.sample.dfu.-$$Lambda$DfuActivity$3$aYPxzTqtmoWnilxuMXNHAWzfFVU
                    @Override // java.lang.Runnable
                    public final void run() {
                        this.f$0.lambda$onError$2$DfuActivity$3();
                    }
                }, 200L);
            } else {
                DfuActivity.this.mDfuError = message;
            }
        }

        public /* synthetic */ void lambda$onError$2$DfuActivity$3() {
            NotificationManager manager = (NotificationManager) DfuActivity.this.getSystemService("notification");
            if (manager != null) {
                manager.cancel(DfuBaseService.NOTIFICATION_ID);
            }
        }
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected int layoutId() {
        return R.layout.activity_dfu;
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    public void initView() {
        if (Build.VERSION.SDK_INT >= 26) {
            DfuServiceInitiator.createDfuNotificationChannel(this);
        }
        if (!isBLEEnabled()) {
            showBLEDialog();
        }
        defaultUI();
        XXPermissions.with(this).permission(Permission.MANAGE_EXTERNAL_STORAGE).request(new OnPermissionCallback() { // from class: com.chileaf.cl831.sample.dfu.DfuActivity.4
            @Override // com.hjq.permissions.OnPermissionCallback
            public /* synthetic */ void onDenied(List list, boolean z) {
                OnPermissionCallback.CC.$default$onDenied(this, list, z);
            }

            @Override // com.hjq.permissions.OnPermissionCallback
            public void onGranted(List<String> permissions, boolean allGranted) {
                DfuActivity dfuActivity = DfuActivity.this;
                StringBuilder sb = new StringBuilder();
                sb.append("permission is ");
                sb.append(allGranted ? "granted" : "denied");
                dfuActivity.showToast(sb.toString());
            }
        });
        DfuServiceListenerHelper.registerProgressListener(this, this.mDfuProgressListener);
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    public void initData(Bundle savedInstanceState) {
        if (savedInstanceState != null) {
            boolean z = this.mStatusOk || savedInstanceState.getBoolean("status");
            this.mStatusOk = z;
            this.mUploadButton.setEnabled(z);
            this.mDfuError = savedInstanceState.getString(DATA_DFU_ERROR);
            this.mDfuCompleted = savedInstanceState.getBoolean(DATA_DFU_COMPLETED);
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public boolean isDfuDevice(String name) {
        return (name == null || TextUtils.isEmpty(name) || !name.toUpperCase().endsWith("U")) ? false : true;
    }

    @Override // androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, android.app.Activity
    protected void onDestroy() {
        super.onDestroy();
        DfuServiceListenerHelper.unregisterProgressListener(this, this.mDfuProgressListener);
    }

    @Override // androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected void onSaveInstanceState(final Bundle outState) {
        super.onSaveInstanceState(outState);
        outState.putBoolean("status", this.mStatusOk);
        outState.putString(DATA_DFU_ERROR, this.mDfuError);
        outState.putBoolean(DATA_DFU_COMPLETED, this.mDfuCompleted);
    }

    private void defaultUI() {
        this.mFileNameView = (TextView) findViewById(R.id.file_name);
        this.mFileSizeView = (TextView) findViewById(R.id.file_size);
        this.mFileStatusView = (TextView) findViewById(R.id.file_status);
        this.mSelectFileButton = (Button) findViewById(R.id.action_select_file);
        this.mUploadButton = (Button) findViewById(R.id.action_upload);
        this.mTextPercentage = (TextView) findViewById(R.id.action_progress);
        this.mTextUploading = (TextView) findViewById(R.id.action_uploading);
        SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(this);
        if (isDfuServiceRunning()) {
            this.mFileNameView.setText(preferences.getString(PREFS_FILE_NAME, ""));
            this.mFileSizeView.setText(preferences.getString(PREFS_FILE_SIZE, ""));
            this.mFileStatusView.setText(R.string.dfu_file_status_ok);
            this.mStatusOk = true;
            showProgressBar();
        }
    }

    @Override // androidx.fragment.app.FragmentActivity, android.app.Activity
    protected void onResume() {
        super.onResume();
        this.mResumed = true;
        if (this.mDfuCompleted) {
            onTransferCompleted();
        }
        String str = this.mDfuError;
        if (str != null) {
            showErrorMessage(str);
        }
        if (this.mDfuCompleted || this.mDfuError != null) {
            NotificationManager manager = (NotificationManager) getSystemService("notification");
            if (manager != null) {
                manager.cancel(DfuBaseService.NOTIFICATION_ID);
            }
            this.mDfuCompleted = false;
            this.mDfuError = null;
        }
    }

    @Override // androidx.fragment.app.FragmentActivity, android.app.Activity
    protected void onPause() {
        super.onPause();
        this.mResumed = false;
    }

    public void startScan(String address) {
        BluetoothLeScannerCompat scanner = BluetoothLeScannerCompat.getScanner();
        ScanSettings settings = new ScanSettings.Builder().setScanMode(2).setUseHardwareBatchingIfSupported(false).setReportDelay(1000L).setLegacy(false).build();
        List<ScanFilter> filters = new ArrayList<>();
        filters.add(new ScanFilter.Builder().setDeviceAddress(address).build());
        scanner.startScan(filters, settings, this.mScanCallback);
    }

    public void stopScan() {
        if (this.mScanCallback != null) {
            BluetoothLeScannerCompat scanner = BluetoothLeScannerCompat.getScanner();
            scanner.stopScan(this.mScanCallback);
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void updateFileInfo(Uri uri, final String fileName, final long fileSize, final int fileType) {
        this.mFileUri = uri;
        this.mFileNameView.setText(fileName);
        this.mFileSizeView.setText(getString(R.string.dfu_file_size_text, new Object[]{Long.valueOf(fileSize)}));
        String extension = fileType == 0 ? "(?i)ZIP" : "(?i)HEX|BIN";
        boolean statusOk = MimeTypeMap.getFileExtensionFromUrl(fileName).matches(extension);
        this.mStatusOk = statusOk;
        this.mFileStatusView.setText(statusOk ? R.string.dfu_file_status_ok : R.string.dfu_file_status_invalid);
        this.mUploadButton.setEnabled(statusOk);
        if (statusOk) {
            onUploadClicked(null);
        }
    }

    public void onSelectFileClicked(final View view) {
        this.zipLauncher.launch(DfuBaseService.MIME_TYPE_ZIP);
    }

    public void onUploadClicked(final View view) {
        if (isDfuServiceRunning()) {
            showUploadCancelDialog();
        } else {
            if (!this.mStatusOk) {
                Toast.makeText(this, R.string.dfu_file_status_invalid_message, 1).show();
                return;
            }
            String address = this.mManager.dfuMode();
            startScan(address);
            showLoadingAutoDismiss(30000L);
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void dfuUpdated(BluetoothDevice device) throws NumberFormatException {
        int numberOfPackets;
        stopScan();
        hideLoading();
        SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(this);
        SharedPreferences.Editor editor = preferences.edit();
        editor.putString(PREFS_FILE_NAME, this.mFileNameView.getText().toString());
        editor.putString(PREFS_FILE_SIZE, this.mFileSizeView.getText().toString());
        editor.apply();
        showProgressBar();
        boolean enablePRNs = Build.VERSION.SDK_INT < 23;
        String value = String.valueOf(12);
        try {
            numberOfPackets = Integer.parseInt(value);
        } catch (NumberFormatException e) {
            numberOfPackets = 12;
        }
        DfuServiceInitiator starter = new DfuServiceInitiator(device.getAddress()).setUnsafeExperimentalButtonlessServiceInSecureDfuEnabled(true).setPacketsReceiptNotificationsValue(numberOfPackets).setPacketsReceiptNotificationsEnabled(enablePRNs).setDeviceName(device.getName()).setKeepBond(false).setForceDfu(false);
        starter.setZip(this.mFileUri);
        Timber.v("dfuUpdated: %s - %s file uri:%s", device.getName(), device.getAddress(), this.mFileUri);
        starter.start(this, DfuService.class);
    }

    private void showUploadCancelDialog() {
        LocalBroadcastManager manager = LocalBroadcastManager.getInstance(this);
        Intent pauseAction = new Intent(DfuBaseService.BROADCAST_ACTION);
        pauseAction.putExtra(DfuBaseService.EXTRA_ACTION, 0);
        manager.sendBroadcast(pauseAction);
        UploadCancelFragment fragment = UploadCancelFragment.getInstance();
        fragment.show(getSupportFragmentManager(), TAG);
    }

    private void showProgressBar() {
        this.mTextPercentage.setVisibility(0);
        this.mTextPercentage.setText((CharSequence) null);
        this.mTextUploading.setVisibility(0);
        this.mTextUploading.setText("Updating...");
        this.mSelectFileButton.setEnabled(false);
        this.mUploadButton.setEnabled(true);
        this.mUploadButton.setText(R.string.dfu_action_upload_cancel);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void onTransferCompleted() {
        clearUI(true);
        showToast(getString(R.string.dfu_success));
    }

    public void onUploadCanceled() {
        clearUI(false);
        showToast(getString(R.string.dfu_status_aborted));
    }

    @Override // com.chileaf.cl831.sample.dfu.UploadCancelFragment.CancelFragmentListener
    public void onCancelUpload() {
        this.mTextUploading.setText("Cancel Upload...");
        this.mTextPercentage.setText((CharSequence) null);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void showErrorMessage(final String message) {
        clearUI(false);
        showToast("Update Failed: " + message);
    }

    private void clearUI(final boolean clearDevice) {
        this.mTextPercentage.setVisibility(4);
        this.mTextUploading.setVisibility(4);
        this.mSelectFileButton.setEnabled(true);
        this.mUploadButton.setEnabled(false);
        this.mUploadButton.setText(R.string.dfu_action_upload);
        this.mFileStatusView.setText((CharSequence) null);
        this.mFileNameView.setText((CharSequence) null);
        this.mFileSizeView.setText((CharSequence) null);
        this.mStatusOk = false;
    }

    private boolean isDfuServiceRunning() {
        ActivityManager manager = (ActivityManager) getSystemService("activity");
        if (manager != null) {
            for (ActivityManager.RunningServiceInfo service : manager.getRunningServices(Integer.MAX_VALUE)) {
                if (DfuService.class.getName().equals(service.service.getClassName())) {
                    return true;
                }
            }
            return false;
        }
        return false;
    }
}
