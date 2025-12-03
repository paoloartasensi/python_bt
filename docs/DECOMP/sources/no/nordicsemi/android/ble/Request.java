package no.nordicsemi.android.ble;

import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattDescriptor;
import android.os.ConditionVariable;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import no.nordicsemi.android.ble.ConditionalWaitRequest;
import no.nordicsemi.android.ble.callback.AfterCallback;
import no.nordicsemi.android.ble.callback.BeforeCallback;
import no.nordicsemi.android.ble.callback.FailCallback;
import no.nordicsemi.android.ble.callback.InvalidRequestCallback;
import no.nordicsemi.android.ble.callback.SuccessCallback;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public abstract class Request {
    protected static final String TAG = Request.class.getSimpleName();
    AfterCallback afterCallback;
    BeforeCallback beforeCallback;
    final BluetoothGattCharacteristic characteristic;
    final BluetoothGattDescriptor descriptor;
    boolean enqueued;
    FailCallback failCallback;
    boolean finished;
    protected CallbackHandler handler;
    BeforeCallback internalBeforeCallback;
    FailCallback internalFailCallback;
    SuccessCallback internalSuccessCallback;
    InvalidRequestCallback invalidRequestCallback;
    protected RequestHandler requestHandler;
    boolean started;
    SuccessCallback successCallback;
    final ConditionVariable syncLock;
    final Type type;

    enum Type {
        SET,
        CONNECT,
        DISCONNECT,
        CREATE_BOND,
        ENSURE_BOND,
        REMOVE_BOND,
        WRITE,
        NOTIFY,
        INDICATE,
        READ,
        WRITE_DESCRIPTOR,
        READ_DESCRIPTOR,
        BEGIN_RELIABLE_WRITE,
        EXECUTE_RELIABLE_WRITE,
        ABORT_RELIABLE_WRITE,
        ENABLE_NOTIFICATIONS,
        ENABLE_INDICATIONS,
        DISABLE_NOTIFICATIONS,
        DISABLE_INDICATIONS,
        WAIT_FOR_NOTIFICATION,
        WAIT_FOR_INDICATION,
        WAIT_FOR_READ,
        WAIT_FOR_WRITE,
        WAIT_FOR_CONDITION,
        SET_VALUE,
        SET_DESCRIPTOR_VALUE,
        READ_BATTERY_LEVEL,
        ENABLE_BATTERY_LEVEL_NOTIFICATIONS,
        DISABLE_BATTERY_LEVEL_NOTIFICATIONS,
        ENABLE_SERVICE_CHANGED_INDICATIONS,
        REQUEST_MTU,
        REQUEST_CONNECTION_PRIORITY,
        SET_PREFERRED_PHY,
        READ_PHY,
        READ_RSSI,
        REFRESH_CACHE,
        SLEEP
    }

    Request(Type type) {
        this.type = type;
        this.characteristic = null;
        this.descriptor = null;
        this.syncLock = new ConditionVariable(true);
    }

    Request(Type type, BluetoothGattCharacteristic characteristic) {
        this.type = type;
        this.characteristic = characteristic;
        this.descriptor = null;
        this.syncLock = new ConditionVariable(true);
    }

    Request(Type type, BluetoothGattDescriptor descriptor) {
        this.type = type;
        this.characteristic = null;
        this.descriptor = descriptor;
        this.syncLock = new ConditionVariable(true);
    }

    Request setRequestHandler(RequestHandler requestHandler) {
        this.requestHandler = requestHandler;
        if (this.handler == null) {
            this.handler = requestHandler;
        }
        return this;
    }

    public Request setHandler(final Handler handler) {
        this.handler = new CallbackHandler() { // from class: no.nordicsemi.android.ble.Request.1
            @Override // no.nordicsemi.android.ble.CallbackHandler
            public void post(Runnable r) {
                Handler handler2 = handler;
                if (handler2 == null) {
                    r.run();
                } else {
                    handler2.post(r);
                }
            }

            @Override // no.nordicsemi.android.ble.CallbackHandler
            public void postDelayed(Runnable r, long delayMillis) {
                Handler handler2 = handler;
                if (handler2 == null) {
                    Request.this.requestHandler.postDelayed(r, delayMillis);
                } else {
                    handler2.postDelayed(r, delayMillis);
                }
            }

            @Override // no.nordicsemi.android.ble.CallbackHandler
            public void removeCallbacks(Runnable r) {
                Handler handler2 = handler;
                if (handler2 == null) {
                    Request.this.requestHandler.removeCallbacks(r);
                } else {
                    handler2.removeCallbacks(r);
                }
            }
        };
        return this;
    }

    static ConnectRequest connect(BluetoothDevice device) {
        return new ConnectRequest(Type.CONNECT, device);
    }

    static DisconnectRequest disconnect() {
        return new DisconnectRequest(Type.DISCONNECT);
    }

    @Deprecated
    public static SimpleRequest createBond() {
        return new SimpleRequest(Type.CREATE_BOND);
    }

    static SimpleRequest ensureBond() {
        return new SimpleRequest(Type.ENSURE_BOND);
    }

    @Deprecated
    public static SimpleRequest removeBond() {
        return new SimpleRequest(Type.REMOVE_BOND);
    }

    @Deprecated
    public static ReadRequest newReadRequest(BluetoothGattCharacteristic characteristic) {
        return new ReadRequest(Type.READ, characteristic);
    }

    @Deprecated
    public static WriteRequest newWriteRequest(BluetoothGattCharacteristic characteristic, byte[] value) {
        return new WriteRequest(Type.WRITE, characteristic, value, 0, value != null ? value.length : 0, characteristic != null ? characteristic.getWriteType() : 2);
    }

    @Deprecated
    public static WriteRequest newWriteRequest(BluetoothGattCharacteristic characteristic, byte[] value, int writeType) {
        return new WriteRequest(Type.WRITE, characteristic, value, 0, value != null ? value.length : 0, writeType);
    }

    @Deprecated
    public static WriteRequest newWriteRequest(BluetoothGattCharacteristic characteristic, byte[] value, int offset, int length) {
        return new WriteRequest(Type.WRITE, characteristic, value, offset, length, characteristic != null ? characteristic.getWriteType() : 2);
    }

    @Deprecated
    public static WriteRequest newWriteRequest(BluetoothGattCharacteristic characteristic, byte[] value, int offset, int length, int writeType) {
        return new WriteRequest(Type.WRITE, characteristic, value, offset, length, writeType);
    }

    @Deprecated
    public static ReadRequest newReadRequest(BluetoothGattDescriptor descriptor) {
        return new ReadRequest(Type.READ_DESCRIPTOR, descriptor);
    }

    @Deprecated
    public static WriteRequest newWriteRequest(BluetoothGattDescriptor descriptor, byte[] value) {
        return new WriteRequest(Type.WRITE_DESCRIPTOR, descriptor, value, 0, value != null ? value.length : 0);
    }

    @Deprecated
    public static WriteRequest newWriteRequest(BluetoothGattDescriptor descriptor, byte[] value, int offset, int length) {
        return new WriteRequest(Type.WRITE_DESCRIPTOR, descriptor, value, offset, length);
    }

    static ReliableWriteRequest newReliableWriteRequest() {
        return new ReliableWriteRequest();
    }

    static SimpleRequest newBeginReliableWriteRequest() {
        return new SimpleRequest(Type.BEGIN_RELIABLE_WRITE);
    }

    static SimpleRequest newExecuteReliableWriteRequest() {
        return new SimpleRequest(Type.EXECUTE_RELIABLE_WRITE);
    }

    static SimpleRequest newAbortReliableWriteRequest() {
        return new SimpleRequest(Type.ABORT_RELIABLE_WRITE);
    }

    static WriteRequest newNotificationRequest(BluetoothGattCharacteristic characteristic, byte[] value) {
        return new WriteRequest(Type.NOTIFY, characteristic, value, 0, value != null ? value.length : 0);
    }

    static WriteRequest newNotificationRequest(BluetoothGattCharacteristic characteristic, byte[] value, int offset, int length) {
        return new WriteRequest(Type.NOTIFY, characteristic, value, offset, length);
    }

    static WriteRequest newIndicationRequest(BluetoothGattCharacteristic characteristic, byte[] value) {
        return new WriteRequest(Type.INDICATE, characteristic, value, 0, value != null ? value.length : 0);
    }

    static WriteRequest newIndicationRequest(BluetoothGattCharacteristic characteristic, byte[] value, int offset, int length) {
        return new WriteRequest(Type.INDICATE, characteristic, value, offset, length);
    }

    @Deprecated
    public static WriteRequest newEnableNotificationsRequest(BluetoothGattCharacteristic characteristic) {
        return new WriteRequest(Type.ENABLE_NOTIFICATIONS, characteristic);
    }

    @Deprecated
    public static WriteRequest newDisableNotificationsRequest(BluetoothGattCharacteristic characteristic) {
        return new WriteRequest(Type.DISABLE_NOTIFICATIONS, characteristic);
    }

    @Deprecated
    public static WriteRequest newEnableIndicationsRequest(BluetoothGattCharacteristic characteristic) {
        return new WriteRequest(Type.ENABLE_INDICATIONS, characteristic);
    }

    @Deprecated
    public static WriteRequest newDisableIndicationsRequest(BluetoothGattCharacteristic characteristic) {
        return new WriteRequest(Type.DISABLE_INDICATIONS, characteristic);
    }

    @Deprecated
    public static WaitForValueChangedRequest newWaitForNotificationRequest(BluetoothGattCharacteristic characteristic) {
        return new WaitForValueChangedRequest(Type.WAIT_FOR_NOTIFICATION, characteristic);
    }

    @Deprecated
    public static WaitForValueChangedRequest newWaitForIndicationRequest(BluetoothGattCharacteristic characteristic) {
        return new WaitForValueChangedRequest(Type.WAIT_FOR_INDICATION, characteristic);
    }

    static WaitForValueChangedRequest newWaitForWriteRequest(BluetoothGattCharacteristic characteristic) {
        return new WaitForValueChangedRequest(Type.WAIT_FOR_WRITE, characteristic);
    }

    static WaitForValueChangedRequest newWaitForWriteRequest(BluetoothGattDescriptor descriptor) {
        return new WaitForValueChangedRequest(Type.WAIT_FOR_WRITE, descriptor);
    }

    static WaitForReadRequest newWaitForReadRequest(BluetoothGattCharacteristic characteristic) {
        return new WaitForReadRequest(Type.WAIT_FOR_READ, characteristic);
    }

    static WaitForReadRequest newWaitForReadRequest(BluetoothGattCharacteristic characteristic, byte[] value) {
        return new WaitForReadRequest(Type.WAIT_FOR_READ, characteristic, value, 0, value != null ? value.length : 0);
    }

    static WaitForReadRequest newWaitForReadRequest(BluetoothGattCharacteristic characteristic, byte[] value, int offset, int length) {
        return new WaitForReadRequest(Type.WAIT_FOR_READ, characteristic, value, offset, length);
    }

    static WaitForReadRequest newWaitForReadRequest(BluetoothGattDescriptor descriptor) {
        return new WaitForReadRequest(Type.WAIT_FOR_READ, descriptor);
    }

    static WaitForReadRequest newWaitForReadRequest(BluetoothGattDescriptor descriptor, byte[] value) {
        return new WaitForReadRequest(Type.WAIT_FOR_READ, descriptor, value, 0, value != null ? value.length : 0);
    }

    static WaitForReadRequest newWaitForReadRequest(BluetoothGattDescriptor descriptor, byte[] value, int offset, int length) {
        return new WaitForReadRequest(Type.WAIT_FOR_READ, descriptor, value, offset, length);
    }

    static <T> ConditionalWaitRequest<T> newConditionalWaitRequest(ConditionalWaitRequest.Condition<T> condition, T parameter) {
        return new ConditionalWaitRequest<>(Type.WAIT_FOR_CONDITION, condition, parameter);
    }

    static SetValueRequest newSetValueRequest(BluetoothGattCharacteristic characteristic, byte[] value) {
        return new SetValueRequest(Type.SET_VALUE, characteristic, value, 0, value != null ? value.length : 0);
    }

    static SetValueRequest newSetValueRequest(BluetoothGattCharacteristic characteristic, byte[] value, int offset, int length) {
        return new SetValueRequest(Type.SET_VALUE, characteristic, value, offset, length);
    }

    static SetValueRequest newSetValueRequest(BluetoothGattDescriptor descriptor, byte[] value) {
        return new SetValueRequest(Type.SET_DESCRIPTOR_VALUE, descriptor, value, 0, value != null ? value.length : 0);
    }

    static SetValueRequest newSetValueRequest(BluetoothGattDescriptor descriptor, byte[] value, int offset, int length) {
        return new SetValueRequest(Type.SET_DESCRIPTOR_VALUE, descriptor, value, offset, length);
    }

    @Deprecated
    public static ReadRequest newReadBatteryLevelRequest() {
        return new ReadRequest(Type.READ_BATTERY_LEVEL);
    }

    @Deprecated
    public static WriteRequest newEnableBatteryLevelNotificationsRequest() {
        return new WriteRequest(Type.ENABLE_BATTERY_LEVEL_NOTIFICATIONS);
    }

    @Deprecated
    public static WriteRequest newDisableBatteryLevelNotificationsRequest() {
        return new WriteRequest(Type.DISABLE_BATTERY_LEVEL_NOTIFICATIONS);
    }

    static WriteRequest newEnableServiceChangedIndicationsRequest() {
        return new WriteRequest(Type.ENABLE_SERVICE_CHANGED_INDICATIONS);
    }

    @Deprecated
    public static MtuRequest newMtuRequest(int mtu) {
        return new MtuRequest(Type.REQUEST_MTU, mtu);
    }

    @Deprecated
    public static ConnectionPriorityRequest newConnectionPriorityRequest(int priority) {
        return new ConnectionPriorityRequest(Type.REQUEST_CONNECTION_PRIORITY, priority);
    }

    @Deprecated
    public static PhyRequest newSetPreferredPhyRequest(int txPhy, int rxPhy, int phyOptions) {
        return new PhyRequest(Type.SET_PREFERRED_PHY, txPhy, rxPhy, phyOptions);
    }

    @Deprecated
    public static PhyRequest newReadPhyRequest() {
        return new PhyRequest(Type.READ_PHY);
    }

    @Deprecated
    public static ReadRssiRequest newReadRssiRequest() {
        return new ReadRssiRequest(Type.READ_RSSI);
    }

    @Deprecated
    public static SimpleRequest newRefreshCacheRequest() {
        return new SimpleRequest(Type.REFRESH_CACHE);
    }

    @Deprecated
    public static SleepRequest newSleepRequest(long delay) {
        return new SleepRequest(Type.SLEEP, delay);
    }

    public Request done(SuccessCallback callback) {
        this.successCallback = callback;
        return this;
    }

    public Request fail(FailCallback callback) {
        this.failCallback = callback;
        return this;
    }

    void internalBefore(BeforeCallback callback) {
        this.internalBeforeCallback = callback;
    }

    void internalSuccess(SuccessCallback callback) {
        this.internalSuccessCallback = callback;
    }

    void internalFail(FailCallback callback) {
        this.internalFailCallback = callback;
    }

    public Request invalid(InvalidRequestCallback callback) {
        this.invalidRequestCallback = callback;
        return this;
    }

    public Request before(BeforeCallback callback) {
        this.beforeCallback = callback;
        return this;
    }

    public Request then(AfterCallback callback) {
        this.afterCallback = callback;
        return this;
    }

    public void enqueue() {
        this.requestHandler.enqueue(this);
    }

    void notifyStarted(final BluetoothDevice device) {
        if (!this.started) {
            this.started = true;
            BeforeCallback beforeCallback = this.internalBeforeCallback;
            if (beforeCallback != null) {
                beforeCallback.onRequestStarted(device);
            }
            this.handler.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$Request$BaeihHrlpTD6bHuKIX5Gi2d8WXI
                @Override // java.lang.Runnable
                public final void run() {
                    this.f$0.lambda$notifyStarted$0$Request(device);
                }
            });
        }
    }

    public /* synthetic */ void lambda$notifyStarted$0$Request(BluetoothDevice device) {
        BeforeCallback beforeCallback = this.beforeCallback;
        if (beforeCallback != null) {
            try {
                beforeCallback.onRequestStarted(device);
            } catch (Throwable t) {
                Log.e(TAG, "Exception in Before callback", t);
            }
        }
    }

    boolean notifySuccess(final BluetoothDevice device) {
        if (!this.finished) {
            this.finished = true;
            SuccessCallback successCallback = this.internalSuccessCallback;
            if (successCallback != null) {
                successCallback.onRequestCompleted(device);
            }
            this.handler.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$Request$ep6TD_94xCe5LaEafH2PrarR3yc
                @Override // java.lang.Runnable
                public final void run() {
                    this.f$0.lambda$notifySuccess$1$Request(device);
                }
            });
            return true;
        }
        return false;
    }

    public /* synthetic */ void lambda$notifySuccess$1$Request(BluetoothDevice device) {
        SuccessCallback successCallback = this.successCallback;
        if (successCallback != null) {
            try {
                successCallback.onRequestCompleted(device);
            } catch (Throwable t) {
                Log.e(TAG, "Exception in Success callback", t);
            }
        }
        AfterCallback afterCallback = this.afterCallback;
        if (afterCallback != null) {
            try {
                afterCallback.onRequestFinished(device);
            } catch (Throwable t2) {
                Log.e(TAG, "Exception in After callback", t2);
            }
        }
    }

    void notifyFail(final BluetoothDevice device, final int status) {
        if (!this.finished) {
            this.finished = true;
            FailCallback failCallback = this.internalFailCallback;
            if (failCallback != null) {
                failCallback.onRequestFailed(device, status);
            }
            this.handler.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$Request$MU5LE_ePYPVe9rzIdkv_E9MTNdc
                @Override // java.lang.Runnable
                public final void run() {
                    this.f$0.lambda$notifyFail$2$Request(device, status);
                }
            });
        }
    }

    public /* synthetic */ void lambda$notifyFail$2$Request(BluetoothDevice device, int status) {
        FailCallback failCallback = this.failCallback;
        if (failCallback != null) {
            try {
                failCallback.onRequestFailed(device, status);
            } catch (Throwable t) {
                Log.e(TAG, "Exception in Fail callback", t);
            }
        }
        AfterCallback afterCallback = this.afterCallback;
        if (afterCallback != null) {
            try {
                afterCallback.onRequestFinished(device);
            } catch (Throwable t2) {
                Log.e(TAG, "Exception in After callback", t2);
            }
        }
    }

    void notifyInvalidRequest() {
        if (!this.finished) {
            this.finished = true;
            this.handler.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$Request$Jza5Hl-Pwe3UwHl1fRaxV-0S_Bs
                @Override // java.lang.Runnable
                public final void run() {
                    this.f$0.lambda$notifyInvalidRequest$3$Request();
                }
            });
        }
    }

    public /* synthetic */ void lambda$notifyInvalidRequest$3$Request() {
        InvalidRequestCallback invalidRequestCallback = this.invalidRequestCallback;
        if (invalidRequestCallback != null) {
            try {
                invalidRequestCallback.onInvalidRequest();
            } catch (Throwable t) {
                Log.e(TAG, "Exception in Invalid Request callback", t);
            }
        }
    }

    static void assertNotMainThread() throws IllegalStateException {
        if (Looper.myLooper() == Looper.getMainLooper()) {
            throw new IllegalStateException("Cannot execute synchronous operation from the UI thread.");
        }
    }

    final class RequestCallback implements SuccessCallback, FailCallback, InvalidRequestCallback {
        static final int REASON_REQUEST_INVALID = -1000000;
        int status = 0;

        RequestCallback() {
        }

        @Override // no.nordicsemi.android.ble.callback.SuccessCallback
        public void onRequestCompleted(BluetoothDevice device) {
            Request.this.syncLock.open();
        }

        @Override // no.nordicsemi.android.ble.callback.FailCallback
        public void onRequestFailed(BluetoothDevice device, int status) {
            this.status = status;
            Request.this.syncLock.open();
        }

        @Override // no.nordicsemi.android.ble.callback.InvalidRequestCallback
        public void onInvalidRequest() {
            this.status = REASON_REQUEST_INVALID;
            Request.this.syncLock.open();
        }

        boolean isSuccess() {
            return this.status == 0;
        }
    }
}
