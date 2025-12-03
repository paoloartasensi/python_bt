package no.nordicsemi.android.ble;

import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattDescriptor;
import android.os.Handler;
import android.util.Log;
import java.util.Arrays;
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
public final class WriteRequest extends SimpleValueRequest<DataSentCallback> implements Operation {
    private static final DataSplitter MTU_SPLITTER = new DefaultMtuSplitter();
    private boolean complete;
    private int count;
    private byte[] currentChunk;
    private final byte[] data;
    private DataSplitter dataSplitter;
    private byte[] nextChunk;
    private WriteProgressCallback progressCallback;
    private final int writeType;

    WriteRequest(Request.Type type) {
        this(type, null);
    }

    WriteRequest(Request.Type type, BluetoothGattCharacteristic characteristic) {
        super(type, characteristic);
        this.count = 0;
        this.complete = false;
        this.data = null;
        this.writeType = 0;
        this.complete = true;
    }

    WriteRequest(Request.Type type, BluetoothGattCharacteristic characteristic, byte[] data, int offset, int length, int writeType) {
        super(type, characteristic);
        this.count = 0;
        this.complete = false;
        this.data = Bytes.copy(data, offset, length);
        this.writeType = writeType;
    }

    WriteRequest(Request.Type type, BluetoothGattCharacteristic characteristic, byte[] data, int offset, int length) {
        super(type, characteristic);
        this.count = 0;
        this.complete = false;
        this.data = Bytes.copy(data, offset, length);
        this.writeType = 0;
    }

    WriteRequest(Request.Type type, BluetoothGattDescriptor descriptor, byte[] data, int offset, int length) {
        super(type, descriptor);
        this.count = 0;
        this.complete = false;
        this.data = Bytes.copy(data, offset, length);
        this.writeType = 2;
    }

    /* JADX INFO: Access modifiers changed from: package-private */
    @Override // no.nordicsemi.android.ble.Request
    public WriteRequest setRequestHandler(RequestHandler requestHandler) {
        super.setRequestHandler(requestHandler);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public WriteRequest setHandler(Handler handler) {
        super.setHandler(handler);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public WriteRequest done(SuccessCallback callback) {
        super.done(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public WriteRequest fail(FailCallback callback) {
        super.fail(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public WriteRequest invalid(InvalidRequestCallback callback) {
        super.invalid(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public WriteRequest before(BeforeCallback callback) {
        super.before(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public WriteRequest then(AfterCallback callback) {
        super.then(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.SimpleValueRequest
    public WriteRequest with(DataSentCallback callback) {
        super.with((WriteRequest) callback);
        return this;
    }

    public WriteRequest split(DataSplitter splitter) {
        this.dataSplitter = splitter;
        this.progressCallback = null;
        return this;
    }

    public WriteRequest split(DataSplitter splitter, WriteProgressCallback callback) {
        this.dataSplitter = splitter;
        this.progressCallback = callback;
        return this;
    }

    public WriteRequest split() {
        this.dataSplitter = MTU_SPLITTER;
        this.progressCallback = null;
        return this;
    }

    public WriteRequest split(WriteProgressCallback callback) {
        this.dataSplitter = MTU_SPLITTER;
        this.progressCallback = callback;
        return this;
    }

    void forceSplit() {
        if (this.dataSplitter == null) {
            split();
        }
    }

    byte[] getData(int mtu) {
        byte[] bArr;
        DataSplitter dataSplitter = this.dataSplitter;
        if (dataSplitter == null || (bArr = this.data) == null) {
            this.complete = true;
            byte[] bArr2 = this.data;
            this.currentChunk = bArr2;
            return bArr2 != null ? bArr2 : new byte[0];
        }
        int maxLength = this.writeType != 4 ? mtu - 3 : mtu - 12;
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
        this.currentChunk = chunk;
        return chunk != null ? chunk : new byte[0];
    }

    boolean notifyPacketSent(final BluetoothDevice device, byte[] data) {
        this.handler.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$WriteRequest$wTNVoeGSalD21XMZfd3vlLVfbk0
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$notifyPacketSent$0$WriteRequest(device);
            }
        });
        this.count++;
        if (this.complete) {
            this.handler.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$WriteRequest$HiYkfKVczVHyPYnK2C5dyXzExP4
                @Override // java.lang.Runnable
                public final void run() {
                    this.f$0.lambda$notifyPacketSent$1$WriteRequest(device);
                }
            });
        }
        if (this.writeType == 2) {
            return Arrays.equals(data, this.currentChunk);
        }
        return true;
    }

    public /* synthetic */ void lambda$notifyPacketSent$0$WriteRequest(BluetoothDevice device) {
        WriteProgressCallback writeProgressCallback = this.progressCallback;
        if (writeProgressCallback != null) {
            try {
                writeProgressCallback.onPacketSent(device, this.currentChunk, this.count);
            } catch (Throwable t) {
                Log.e(TAG, "Exception in Progress callback", t);
            }
        }
    }

    public /* synthetic */ void lambda$notifyPacketSent$1$WriteRequest(BluetoothDevice device) {
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

    int getWriteType() {
        return this.writeType;
    }
}
