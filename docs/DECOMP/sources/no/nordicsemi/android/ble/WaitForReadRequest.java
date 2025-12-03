package no.nordicsemi.android.ble;

import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattDescriptor;
import android.os.Handler;
import android.util.Log;
import no.nordicsemi.android.ble.Request;
import no.nordicsemi.android.ble.callback.AfterCallback;
import no.nordicsemi.android.ble.callback.BeforeCallback;
import no.nordicsemi.android.ble.callback.DataSentCallback;
import no.nordicsemi.android.ble.callback.FailCallback;
import no.nordicsemi.android.ble.callback.InvalidRequestCallback;
import no.nordicsemi.android.ble.callback.SuccessCallback;
import no.nordicsemi.android.ble.callback.WriteProgressCallback;
import no.nordicsemi.android.ble.data.Data;
import no.nordicsemi.android.ble.data.DataSplitter;
import no.nordicsemi.android.ble.data.DefaultMtuSplitter;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public final class WaitForReadRequest extends AwaitingRequest<DataSentCallback> implements Operation {
    private static final DataSplitter MTU_SPLITTER = new DefaultMtuSplitter();
    private boolean complete;
    private int count;
    private byte[] data;
    private DataSplitter dataSplitter;
    private byte[] nextChunk;
    private WriteProgressCallback progressCallback;

    WaitForReadRequest(Request.Type type, BluetoothGattCharacteristic characteristic) {
        super(type, characteristic);
        this.count = 0;
        this.complete = false;
        this.data = null;
        this.complete = true;
    }

    WaitForReadRequest(Request.Type type, BluetoothGattDescriptor descriptor) {
        super(type, descriptor);
        this.count = 0;
        this.complete = false;
        this.data = null;
        this.complete = true;
    }

    WaitForReadRequest(Request.Type type, BluetoothGattCharacteristic characteristic, byte[] data, int offset, int length) {
        super(type, characteristic);
        this.count = 0;
        this.complete = false;
        this.data = Bytes.copy(data, offset, length);
    }

    WaitForReadRequest(Request.Type type, BluetoothGattDescriptor descriptor, byte[] data, int offset, int length) {
        super(type, descriptor);
        this.count = 0;
        this.complete = false;
        this.data = Bytes.copy(data, offset, length);
    }

    void setDataIfNull(byte[] data) {
        if (this.data == null) {
            this.data = data;
        }
    }

    /* JADX INFO: Access modifiers changed from: package-private */
    @Override // no.nordicsemi.android.ble.TimeoutableRequest, no.nordicsemi.android.ble.Request
    public WaitForReadRequest setRequestHandler(RequestHandler requestHandler) {
        super.setRequestHandler(requestHandler);
        return this;
    }

    @Override // no.nordicsemi.android.ble.TimeoutableRequest, no.nordicsemi.android.ble.Request
    public WaitForReadRequest setHandler(Handler handler) {
        super.setHandler(handler);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public WaitForReadRequest done(SuccessCallback callback) {
        super.done(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public WaitForReadRequest fail(FailCallback callback) {
        super.fail(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public WaitForReadRequest invalid(InvalidRequestCallback callback) {
        super.invalid(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public WaitForReadRequest before(BeforeCallback callback) {
        super.before(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public WaitForReadRequest then(AfterCallback callback) {
        super.then(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.TimeoutableValueRequest
    public WaitForReadRequest with(DataSentCallback callback) {
        super.with((WaitForReadRequest) callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.AwaitingRequest
    public AwaitingRequest<DataSentCallback> trigger(Operation trigger) {
        super.trigger(trigger);
        return this;
    }

    public WaitForReadRequest split(DataSplitter splitter) {
        this.dataSplitter = splitter;
        this.progressCallback = null;
        return this;
    }

    public WaitForReadRequest split(DataSplitter splitter, WriteProgressCallback callback) {
        this.dataSplitter = splitter;
        this.progressCallback = callback;
        return this;
    }

    public WaitForReadRequest split() {
        this.dataSplitter = MTU_SPLITTER;
        this.progressCallback = null;
        return this;
    }

    public WaitForReadRequest split(WriteProgressCallback callback) {
        this.dataSplitter = MTU_SPLITTER;
        this.progressCallback = callback;
        return this;
    }

    byte[] getData(int mtu) {
        byte[] bArr;
        DataSplitter dataSplitter = this.dataSplitter;
        if (dataSplitter == null || (bArr = this.data) == null) {
            this.complete = true;
            byte[] bArr2 = this.data;
            return bArr2 != null ? bArr2 : new byte[0];
        }
        int maxLength = mtu - 1;
        byte[] chunk = this.nextChunk;
        if (chunk == null) {
            chunk = dataSplitter.chunk(bArr, this.count, maxLength);
        }
        if (chunk != null) {
            this.nextChunk = this.dataSplitter.chunk(this.data, this.count + 1, maxLength);
        }
        if (this.nextChunk == null) {
            this.complete = true;
        }
        return chunk != null ? chunk : new byte[0];
    }

    void notifyPacketRead(final BluetoothDevice device, final byte[] data) {
        this.handler.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$WaitForReadRequest$LU0o2wLIiVqcazZPEpcOoouVhFc
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$notifyPacketRead$0$WaitForReadRequest(device, data);
            }
        });
        this.count++;
    }

    public /* synthetic */ void lambda$notifyPacketRead$0$WaitForReadRequest(BluetoothDevice device, byte[] data) {
        WriteProgressCallback writeProgressCallback = this.progressCallback;
        if (writeProgressCallback != null) {
            try {
                writeProgressCallback.onPacketSent(device, data, this.count);
            } catch (Throwable t) {
                Log.e(TAG, "Exception in Progress callback", t);
            }
        }
    }

    @Override // no.nordicsemi.android.ble.TimeoutableRequest, no.nordicsemi.android.ble.Request
    boolean notifySuccess(final BluetoothDevice device) {
        this.handler.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$WaitForReadRequest$j10HPxx_Sq-L0sD3zaoW3We-2ow
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$notifySuccess$1$WaitForReadRequest(device);
            }
        });
        return super.notifySuccess(device);
    }

    public /* synthetic */ void lambda$notifySuccess$1$WaitForReadRequest(BluetoothDevice device) {
        if (this.valueCallback != 0) {
            try {
                ((DataSentCallback) this.valueCallback).onDataSent(device, new Data(this.data));
            } catch (Throwable t) {
                Log.e(TAG, "Exception in Value callback", t);
            }
        }
    }

    boolean hasMore() {
        return !this.complete;
    }
}
