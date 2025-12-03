package no.nordicsemi.android.ble.callback.profile;

import android.bluetooth.BluetoothDevice;
import no.nordicsemi.android.ble.callback.DataReceivedCallback;
import no.nordicsemi.android.ble.data.Data;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface ProfileDataCallback extends DataReceivedCallback {
    void onInvalidDataReceived(BluetoothDevice bluetoothDevice, Data data);

    /* renamed from: no.nordicsemi.android.ble.callback.profile.ProfileDataCallback$-CC, reason: invalid class name */
    public final /* synthetic */ class CC {
        public static void $default$onInvalidDataReceived(ProfileDataCallback _this, BluetoothDevice device, Data data) {
        }
    }
}
