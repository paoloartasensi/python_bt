package com.chileaf.cl831.sample;

import android.app.Dialog;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.content.Context;
import android.content.DialogInterface;
import android.os.Bundle;
import android.os.Handler;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.ListAdapter;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AlertDialog;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.DialogFragment;
import com.android.chileaf.WearManager;
import com.android.chileaf.fitness.common.FilterScanCallback;
import com.hjq.permissions.Permission;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import no.nordicsemi.android.support.v18.scanner.ScanResult;
import timber.log.Timber;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class ScannerFragment extends DialogFragment {
    private static final int REQUEST_PERMISSION_REQ_CODE = 34;
    private static final long SCAN_DURATION = 15000;
    private DeviceListAdapter mAdapter;
    private BluetoothAdapter mBluetoothAdapter;
    private OnDeviceSelectedListener mListener;
    private WearManager mManager;
    private View mPermissionRationale;
    private Button mScanButton;
    private final Handler mHandler = new Handler();
    private boolean mIsScanning = false;
    private FilterScanCallback mScanCallback = new FilterScanCallback() { // from class: com.chileaf.cl831.sample.ScannerFragment.1
        @Override // com.android.chileaf.fitness.common.FilterScanCallback
        public /* synthetic */ void onBatchScanResults(List list) {
            FilterScanCallback.CC.$default$onBatchScanResults(this, list);
        }

        @Override // com.android.chileaf.fitness.common.FilterScanCallback
        public /* synthetic */ void onScanFailed(int i) {
            FilterScanCallback.CC.$default$onScanFailed(this, i);
        }

        @Override // com.android.chileaf.fitness.common.FilterScanCallback
        public /* synthetic */ void onScanResult(int i, ScanResult scanResult) {
            FilterScanCallback.CC.$default$onScanResult(this, i, scanResult);
        }

        @Override // com.android.chileaf.fitness.common.FilterScanCallback
        public void onFilterScanResults(List<ScanResult> results) {
            ScannerFragment.this.mAdapter.update(results);
        }
    };

    public static ScannerFragment getInstance() {
        ScannerFragment fragment = new ScannerFragment();
        Bundle args = new Bundle();
        fragment.setArguments(args);
        return fragment;
    }

    public interface OnDeviceSelectedListener {
        void onDeviceSelected(final BluetoothDevice device, final String name);

        void onDialogCanceled();

        /* renamed from: com.chileaf.cl831.sample.ScannerFragment$OnDeviceSelectedListener$-CC, reason: invalid class name */
        public final /* synthetic */ class CC {
            public static void $default$onDialogCanceled(OnDeviceSelectedListener _this) {
            }
        }
    }

    /* JADX WARN: Multi-variable type inference failed */
    @Override // androidx.fragment.app.DialogFragment, androidx.fragment.app.Fragment
    public void onAttach(final Context context) {
        super.onAttach(context);
        try {
            this.mListener = (OnDeviceSelectedListener) context;
        } catch (ClassCastException e) {
            throw new ClassCastException(context.toString() + " must implement OnDeviceSelectedListener");
        }
    }

    @Override // androidx.fragment.app.DialogFragment, androidx.fragment.app.Fragment
    public void onCreate(final Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BluetoothManager manager = (BluetoothManager) requireContext().getSystemService("bluetooth");
        if (manager != null) {
            this.mBluetoothAdapter = manager.getAdapter();
        }
    }

    @Override // androidx.fragment.app.DialogFragment, androidx.fragment.app.Fragment
    public void onDestroyView() {
        stopScan();
        super.onDestroyView();
    }

    @Override // androidx.fragment.app.DialogFragment
    public Dialog onCreateDialog(final Bundle savedInstanceState) {
        this.mManager = WearManager.getInstance(requireContext());
        AlertDialog.Builder builder = new AlertDialog.Builder(requireContext());
        View dialogView = LayoutInflater.from(getActivity()).inflate(R.layout.fragment_device_scan, (ViewGroup) null);
        ListView listview = (ListView) dialogView.findViewById(android.R.id.list);
        listview.setEmptyView(dialogView.findViewById(android.R.id.empty));
        DeviceListAdapter deviceListAdapter = new DeviceListAdapter(getActivity());
        this.mAdapter = deviceListAdapter;
        listview.setAdapter((ListAdapter) deviceListAdapter);
        builder.setTitle(R.string.scanner_title);
        final AlertDialog dialog = builder.setView(dialogView).create();
        listview.setOnItemClickListener(new AdapterView.OnItemClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$ScannerFragment$AX5H2BrwKUJM-f9CW-8-w0Wif5Q
            @Override // android.widget.AdapterView.OnItemClickListener
            public final void onItemClick(AdapterView adapterView, View view, int i, long j) {
                this.f$0.lambda$onCreateDialog$0$ScannerFragment(dialog, adapterView, view, i, j);
            }
        });
        this.mPermissionRationale = dialogView.findViewById(R.id.permission_rationale);
        Button button = (Button) dialogView.findViewById(R.id.action_cancel);
        this.mScanButton = button;
        button.setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$ScannerFragment$CUBmSYhdRMMf18_hf5ctdygc-do
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$onCreateDialog$1$ScannerFragment(dialog, view);
            }
        });
        addBoundDevices();
        if (savedInstanceState == null) {
            startScan();
        }
        return dialog;
    }

    public /* synthetic */ void lambda$onCreateDialog$0$ScannerFragment(AlertDialog dialog, AdapterView parent, View view, int position, long id) {
        stopScan();
        dialog.dismiss();
        ExtendedBluetoothDevice d = (ExtendedBluetoothDevice) this.mAdapter.getItem(position);
        this.mListener.onDeviceSelected(d.device, d.name);
    }

    public /* synthetic */ void lambda$onCreateDialog$1$ScannerFragment(AlertDialog dialog, View v) {
        if (v.getId() == 2131230779) {
            if (this.mIsScanning) {
                dialog.cancel();
            } else {
                startScan();
            }
        }
    }

    @Override // androidx.fragment.app.DialogFragment, android.content.DialogInterface.OnCancelListener
    public void onCancel(DialogInterface dialog) {
        super.onCancel(dialog);
        this.mListener.onDialogCanceled();
    }

    @Override // androidx.fragment.app.Fragment
    public void onRequestPermissionsResult(final int requestCode, final String[] permissions, final int[] grantResults) {
        switch (requestCode) {
            case 34:
                if (grantResults[0] != 0) {
                    this.mPermissionRationale.setVisibility(0);
                    Toast.makeText(getActivity(), R.string.no_required_permission, 0).show();
                    break;
                } else {
                    startScan();
                    break;
                }
        }
    }

    private void startScan() {
        if (ContextCompat.checkSelfPermission(requireContext(), Permission.ACCESS_COARSE_LOCATION) != 0) {
            if (ActivityCompat.shouldShowRequestPermissionRationale(requireActivity(), Permission.ACCESS_COARSE_LOCATION) && this.mPermissionRationale.getVisibility() == 8) {
                this.mPermissionRationale.setVisibility(0);
                return;
            } else {
                requestPermissions(new String[]{Permission.ACCESS_COARSE_LOCATION}, 34);
                return;
            }
        }
        View view = this.mPermissionRationale;
        if (view != null) {
            view.setVisibility(8);
        }
        this.mAdapter.clearDevices();
        this.mScanButton.setText(R.string.scanner_action_cancel);
        this.mManager.startScan(this.mScanCallback);
        this.mIsScanning = true;
        this.mHandler.postDelayed(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$ScannerFragment$EOJfNwlRva5LwaNNlGpN6a29rmE
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$startScan$2$ScannerFragment();
            }
        }, SCAN_DURATION);
    }

    public /* synthetic */ void lambda$startScan$2$ScannerFragment() {
        if (this.mIsScanning) {
            stopScan();
        }
    }

    private void stopScan() {
        if (this.mIsScanning) {
            this.mScanButton.setText(R.string.scanner_action_scan);
            WearManager.getInstance(getActivity()).stopScan();
            this.mIsScanning = false;
        }
    }

    private void addBoundDevices() {
        Set<BluetoothDevice> devices = this.mBluetoothAdapter.getBondedDevices();
        this.mAdapter.addBondedDevices(devices);
    }

    private static class DeviceListAdapter extends BaseAdapter {
        private static final int TYPE_EMPTY = 2;
        private static final int TYPE_ITEM = 1;
        private static final int TYPE_TITLE = 0;
        private final Context mContext;
        private final ArrayList<ExtendedBluetoothDevice> mListBondedValues = new ArrayList<>();
        private final ArrayList<ExtendedBluetoothDevice> mListValues = new ArrayList<>();

        public DeviceListAdapter(final Context context) {
            this.mContext = context;
        }

        /* JADX INFO: Access modifiers changed from: private */
        public void addBondedDevices(final Set<BluetoothDevice> devices) {
            List<ExtendedBluetoothDevice> bondedDevices = this.mListBondedValues;
            for (BluetoothDevice device : devices) {
                bondedDevices.add(new ExtendedBluetoothDevice(device));
            }
            notifyDataSetChanged();
        }

        /* JADX INFO: Access modifiers changed from: private */
        public void update(final List<ScanResult> results) {
            for (ScanResult result : results) {
                Timber.e(result.toString(), new Object[0]);
                ExtendedBluetoothDevice device = findDevice(result);
                if (device == null) {
                    this.mListValues.add(new ExtendedBluetoothDevice(result));
                } else if (result.getScanRecord() != null) {
                    device.name = result.getScanRecord().getDeviceName();
                    device.rssi = result.getRssi();
                }
            }
            notifyDataSetChanged();
        }

        private ExtendedBluetoothDevice findDevice(final ScanResult result) {
            Iterator<ExtendedBluetoothDevice> it = this.mListBondedValues.iterator();
            while (it.hasNext()) {
                ExtendedBluetoothDevice device = it.next();
                if (device.matches(result)) {
                    return device;
                }
            }
            Iterator<ExtendedBluetoothDevice> it2 = this.mListValues.iterator();
            while (it2.hasNext()) {
                ExtendedBluetoothDevice device2 = it2.next();
                if (device2.matches(result)) {
                    return device2;
                }
            }
            return null;
        }

        /* JADX INFO: Access modifiers changed from: private */
        public void clearDevices() {
            this.mListValues.clear();
            notifyDataSetChanged();
        }

        @Override // android.widget.Adapter
        public int getCount() {
            int bondedCount = this.mListBondedValues.size() + 1;
            int availableCount = this.mListValues.isEmpty() ? 2 : this.mListValues.size() + 1;
            if (bondedCount == 1) {
                return availableCount;
            }
            return bondedCount + availableCount;
        }

        @Override // android.widget.Adapter
        public Object getItem(int position) {
            int bondedCount = this.mListBondedValues.size() + 1;
            boolean zIsEmpty = this.mListBondedValues.isEmpty();
            Integer numValueOf = Integer.valueOf(R.string.scanner_subtitle_not_bonded);
            if (zIsEmpty) {
                if (position == 0) {
                    return numValueOf;
                }
                return this.mListValues.get(position - 1);
            }
            if (position == 0) {
                return Integer.valueOf(R.string.scanner_subtitle_bonded);
            }
            if (position < bondedCount) {
                return this.mListBondedValues.get(position - 1);
            }
            if (position == bondedCount) {
                return numValueOf;
            }
            return this.mListValues.get((position - bondedCount) - 1);
        }

        @Override // android.widget.BaseAdapter, android.widget.Adapter
        public int getViewTypeCount() {
            return 3;
        }

        @Override // android.widget.BaseAdapter, android.widget.ListAdapter
        public boolean areAllItemsEnabled() {
            return false;
        }

        @Override // android.widget.BaseAdapter, android.widget.ListAdapter
        public boolean isEnabled(int position) {
            return getItemViewType(position) == 1;
        }

        @Override // android.widget.BaseAdapter, android.widget.Adapter
        public int getItemViewType(int position) {
            if (position == 0) {
                return 0;
            }
            if (this.mListBondedValues.isEmpty() || position != this.mListBondedValues.size() + 1) {
                return (position == getCount() - 1 && this.mListValues.isEmpty()) ? 2 : 1;
            }
            return 0;
        }

        @Override // android.widget.Adapter
        public long getItemId(int position) {
            return position;
        }

        @Override // android.widget.Adapter
        public View getView(int position, View oldView, ViewGroup parent) {
            LayoutInflater inflater = LayoutInflater.from(this.mContext);
            int type = getItemViewType(position);
            View view = oldView;
            switch (type) {
                case 0:
                    if (view == null) {
                        view = new TextView(this.mContext);
                    }
                    TextView title = (TextView) view;
                    title.setGravity(1);
                    title.setText(((Integer) getItem(position)).intValue());
                    break;
                case 1:
                default:
                    if (view == null) {
                        view = inflater.inflate(R.layout.item_device_list, parent, false);
                        ViewHolder holder = new ViewHolder();
                        holder.name = (TextView) view.findViewById(R.id.name);
                        holder.address = (TextView) view.findViewById(R.id.address);
                        holder.signal = (TextView) view.findViewById(R.id.rssi);
                        view.setTag(holder);
                    }
                    ExtendedBluetoothDevice device = (ExtendedBluetoothDevice) getItem(position);
                    ViewHolder holder2 = (ViewHolder) view.getTag();
                    String name = device.name;
                    holder2.name.setText(name != null ? name : this.mContext.getString(R.string.not_available));
                    holder2.address.setText(device.device.getAddress());
                    if (!device.isBonded || device.rssi != -1000) {
                        holder2.signal.setText(device.rssi + "dBm");
                        holder2.signal.setVisibility(0);
                        break;
                    } else {
                        holder2.signal.setVisibility(8);
                        break;
                    }
                    break;
                case 2:
                    if (view == null) {
                        View view2 = new TextView(this.mContext);
                        TextView empty = (TextView) view2;
                        empty.setGravity(1);
                        empty.setText(this.mContext.getString(R.string.scanner_empty));
                        break;
                    }
                    break;
            }
            return view;
        }

        private class ViewHolder {
            private TextView address;
            private TextView name;
            private TextView signal;

            private ViewHolder() {
            }
        }
    }

    private static class ExtendedBluetoothDevice {
        private static final int NO_RSSI = -1000;
        private final BluetoothDevice device;
        private boolean isBonded;
        private String name;
        private int rssi;

        private ExtendedBluetoothDevice(final ScanResult scanResult) {
            this.device = scanResult.getDevice();
            this.name = scanResult.getScanRecord() != null ? scanResult.getScanRecord().getDeviceName() : null;
            this.rssi = scanResult.getRssi();
            this.isBonded = false;
        }

        private ExtendedBluetoothDevice(final BluetoothDevice device) {
            this.device = device;
            this.name = device.getName();
            this.rssi = -1000;
            this.isBonded = true;
        }

        /* JADX INFO: Access modifiers changed from: private */
        public boolean matches(final ScanResult scanResult) {
            return this.device.getAddress().equals(scanResult.getDevice().getAddress());
        }
    }
}
