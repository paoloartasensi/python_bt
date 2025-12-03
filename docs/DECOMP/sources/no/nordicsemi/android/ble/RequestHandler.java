package no.nordicsemi.android.ble;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
abstract class RequestHandler implements CallbackHandler {
    abstract void cancelCurrent();

    abstract void cancelQueue();

    abstract void enqueue(Request request);

    abstract void onRequestTimeout(BluetoothDevice bluetoothDevice, TimeoutableRequest timeoutableRequest);

    RequestHandler() {
    }
}
