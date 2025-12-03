package no.nordicsemi.android.ble;

import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattDescriptor;
import android.os.Handler;
import android.util.Log;
import no.nordicsemi.android.ble.Request;
import no.nordicsemi.android.ble.callback.AfterCallback;
import no.nordicsemi.android.ble.callback.BeforeCallback;
import no.nordicsemi.android.ble.callback.DataReceivedCallback;
import no.nordicsemi.android.ble.callback.FailCallback;
import no.nordicsemi.android.ble.callback.InvalidRequestCallback;
import no.nordicsemi.android.ble.callback.ReadProgressCallback;
import no.nordicsemi.android.ble.callback.SuccessCallback;
import no.nordicsemi.android.ble.callback.profile.ProfileReadResponse;
import no.nordicsemi.android.ble.data.Data;
import no.nordicsemi.android.ble.data.DataFilter;
import no.nordicsemi.android.ble.data.DataMerger;
import no.nordicsemi.android.ble.data.DataStream;
import no.nordicsemi.android.ble.data.PacketFilter;
import no.nordicsemi.android.ble.exception.BluetoothDisabledException;
import no.nordicsemi.android.ble.exception.DeviceDisconnectedException;
import no.nordicsemi.android.ble.exception.InvalidDataException;
import no.nordicsemi.android.ble.exception.InvalidRequestException;
import no.nordicsemi.android.ble.exception.RequestFailedException;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public final class ReadRequest extends SimpleValueRequest<DataReceivedCallback> implements Operation {
    private DataStream buffer;
    private boolean complete;
    private int count;
    private DataMerger dataMerger;
    private DataFilter filter;
    private PacketFilter packetFilter;
    private ReadProgressCallback progressCallback;

    ReadRequest(Request.Type type) {
        super(type);
        this.count = 0;
        this.complete = false;
    }

    ReadRequest(Request.Type type, BluetoothGattCharacteristic characteristic) {
        super(type, characteristic);
        this.count = 0;
        this.complete = false;
    }

    ReadRequest(Request.Type type, BluetoothGattDescriptor descriptor) {
        super(type, descriptor);
        this.count = 0;
        this.complete = false;
    }

    /* JADX INFO: Access modifiers changed from: package-private */
    @Override // no.nordicsemi.android.ble.Request
    public ReadRequest setRequestHandler(RequestHandler requestHandler) {
        super.setRequestHandler(requestHandler);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public ReadRequest setHandler(Handler handler) {
        super.setHandler(handler);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public ReadRequest done(SuccessCallback callback) {
        super.done(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public ReadRequest fail(FailCallback callback) {
        super.fail(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public ReadRequest invalid(InvalidRequestCallback callback) {
        super.invalid(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public ReadRequest before(BeforeCallback callback) {
        super.before(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public ReadRequest then(AfterCallback callback) {
        super.then(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.SimpleValueRequest
    public ReadRequest with(DataReceivedCallback callback) {
        super.with((ReadRequest) callback);
        return this;
    }

    public ReadRequest filter(DataFilter filter) {
        this.filter = filter;
        return this;
    }

    public ReadRequest filterPacket(PacketFilter filter) {
        this.packetFilter = filter;
        return this;
    }

    public ReadRequest merge(DataMerger merger) {
        this.dataMerger = merger;
        this.progressCallback = null;
        return this;
    }

    public ReadRequest merge(DataMerger merger, ReadProgressCallback callback) {
        this.dataMerger = merger;
        this.progressCallback = callback;
        return this;
    }

    public <E extends ProfileReadResponse> E awaitValid(Class<E> responseClass) throws InvalidDataException, DeviceDisconnectedException, RequestFailedException, InvalidRequestException, BluetoothDisabledException {
        E e = (E) await((Class) responseClass);
        if (!e.isValid()) {
            throw new InvalidDataException(e);
        }
        return e;
    }

    public <E extends ProfileReadResponse> E awaitValid(E response) throws InvalidDataException, DeviceDisconnectedException, RequestFailedException, InvalidRequestException, BluetoothDisabledException {
        await((ReadRequest) response);
        if (!response.isValid()) {
            throw new InvalidDataException(response);
        }
        return response;
    }

    boolean matches(byte[] packet) {
        DataFilter dataFilter = this.filter;
        return dataFilter == null || dataFilter.filter(packet);
    }

    void notifyValueChanged(final BluetoothDevice device, final byte[] value) {
        final DataReceivedCallback valueCallback = (DataReceivedCallback) this.valueCallback;
        if (valueCallback == null) {
            PacketFilter packetFilter = this.packetFilter;
            if (packetFilter == null || packetFilter.filter(value)) {
                this.complete = true;
                return;
            }
            return;
        }
        if (this.dataMerger == null) {
            this.complete = true;
            final Data data = new Data(value);
            this.handler.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$ReadRequest$tp_fv3X0rfRpaIc9tbgr8Xu0thQ
                @Override // java.lang.Runnable
                public final void run() {
                    ReadRequest.lambda$notifyValueChanged$0(valueCallback, device, data);
                }
            });
            return;
        }
        this.handler.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$ReadRequest$SBcgraCgp82hhvLITIwaUCVYYbg
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$notifyValueChanged$1$ReadRequest(device, value);
            }
        });
        if (this.buffer == null) {
            this.buffer = new DataStream();
        }
        DataMerger dataMerger = this.dataMerger;
        DataStream dataStream = this.buffer;
        int i = this.count;
        this.count = i + 1;
        if (dataMerger.merge(dataStream, value, i)) {
            byte[] merged = this.buffer.toByteArray();
            PacketFilter packetFilter2 = this.packetFilter;
            if (packetFilter2 == null || packetFilter2.filter(merged)) {
                this.complete = true;
                final Data data2 = new Data(merged);
                this.handler.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$ReadRequest$ZwTEYoiNZx-QShL6xvX20Doayl4
                    @Override // java.lang.Runnable
                    public final void run() {
                        ReadRequest.lambda$notifyValueChanged$2(valueCallback, device, data2);
                    }
                });
            }
            this.buffer = null;
            this.count = 0;
        }
    }

    static /* synthetic */ void lambda$notifyValueChanged$0(DataReceivedCallback valueCallback, BluetoothDevice device, Data data) {
        try {
            valueCallback.onDataReceived(device, data);
        } catch (Throwable t) {
            Log.e(TAG, "Exception in Value callback", t);
        }
    }

    public /* synthetic */ void lambda$notifyValueChanged$1$ReadRequest(BluetoothDevice device, byte[] value) {
        ReadProgressCallback readProgressCallback = this.progressCallback;
        if (readProgressCallback != null) {
            try {
                readProgressCallback.onPacketReceived(device, value, this.count);
            } catch (Throwable t) {
                Log.e(TAG, "Exception in Progress callback", t);
            }
        }
    }

    static /* synthetic */ void lambda$notifyValueChanged$2(DataReceivedCallback valueCallback, BluetoothDevice device, Data data) {
        try {
            valueCallback.onDataReceived(device, data);
        } catch (Throwable t) {
            Log.e(TAG, "Exception in Value callback", t);
        }
    }

    boolean hasMore() {
        return !this.complete;
    }
}
