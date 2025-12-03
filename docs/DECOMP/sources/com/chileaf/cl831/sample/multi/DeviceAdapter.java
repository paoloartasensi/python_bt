package com.chileaf.cl831.sample.multi;

import android.bluetooth.BluetoothDevice;
import android.widget.TextView;
import com.chad.library.adapter.base.BaseQuickAdapter;
import com.chad.library.adapter.base.viewholder.BaseViewHolder;
import com.chileaf.cl831.sample.R;
import java.util.ArrayList;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes3.dex */
public class DeviceAdapter extends BaseQuickAdapter<DeviceItem, BaseViewHolder> {
    public DeviceAdapter() {
        super(R.layout.item_device, new ArrayList());
        addChildClickViewIds(R.id.btn_disconnect);
    }

    /* JADX INFO: Access modifiers changed from: protected */
    @Override // com.chad.library.adapter.base.BaseQuickAdapter
    public void convert(BaseViewHolder helper, DeviceItem item) {
        TextView tvName = (TextView) helper.getView(R.id.name);
        TextView tvAddress = (TextView) helper.getView(R.id.address);
        TextView tvHeart = (TextView) helper.getView(R.id.heart);
        TextView tvStep = (TextView) helper.getView(R.id.step);
        TextView tvDistance = (TextView) helper.getView(R.id.distance);
        TextView tvCalorie = (TextView) helper.getView(R.id.calorie);
        tvName.setText(item.device.getName());
        tvAddress.setText(item.device.getAddress());
        tvHeart.setText(item.heartRate + "BPM");
        tvStep.setText(item.step + "steps");
        tvDistance.setText((((float) item.distance) / 100.0f) + "m");
        tvCalorie.setText((((float) item.calorie) / 10.0f) + "KCal");
    }

    public void addDevice(DeviceItem item) {
        getData().add(item);
        notifyDataSetChanged();
    }

    public void removeDevice(BluetoothDevice device) {
        DeviceItem item = getItem(device);
        if (item != null) {
            getData().remove(item);
            notifyDataSetChanged();
        }
    }

    public DeviceItem getItem(BluetoothDevice device) {
        for (DeviceItem item : getData()) {
            if (item.device.getAddress() == device.getAddress()) {
                return item;
            }
        }
        return null;
    }

    public void onSoftwareVersion(BluetoothDevice device, String software) {
        DeviceItem item = getItem(device);
        if (item != null) {
            item.version = software;
            notifyItemChanged(getData().indexOf(item));
        }
    }

    public void onBatteryLevelChanged(final BluetoothDevice device, final int batteryLevel) {
        DeviceItem item = getItem(device);
        if (item != null) {
            item.battery = batteryLevel;
            notifyItemChanged(getData().indexOf(item));
        }
    }

    public void onHeartRateMeasurementReceived(BluetoothDevice device, int heartRate) {
        DeviceItem item = getItem(device);
        if (item != null) {
            item.heartRate = heartRate;
            notifyItemChanged(getData().indexOf(item));
        }
    }

    public void onSportReceived(BluetoothDevice device, int step, int distance, int calorie) {
        DeviceItem item = getItem(device);
        if (item != null) {
            item.step = step;
            item.distance = distance;
            item.calorie = calorie;
            notifyItemChanged(getData().indexOf(item));
        }
    }
}
