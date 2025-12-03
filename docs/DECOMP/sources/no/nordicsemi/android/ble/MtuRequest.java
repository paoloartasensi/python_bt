package no.nordicsemi.android.ble;

import android.bluetooth.BluetoothDevice;
import android.os.Handler;
import android.util.Log;
import no.nordicsemi.android.ble.Request;
import no.nordicsemi.android.ble.callback.AfterCallback;
import no.nordicsemi.android.ble.callback.BeforeCallback;
import no.nordicsemi.android.ble.callback.FailCallback;
import no.nordicsemi.android.ble.callback.InvalidRequestCallback;
import no.nordicsemi.android.ble.callback.MtuCallback;
import no.nordicsemi.android.ble.callback.SuccessCallback;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public final class MtuRequest extends SimpleValueRequest<MtuCallback> implements Operation {
    private final int value;

    MtuRequest(Request.Type type, int mtu) {
        super(type);
        mtu = mtu < 23 ? 23 : mtu;
        this.value = mtu > 517 ? 517 : mtu;
    }

    /* JADX INFO: Access modifiers changed from: package-private */
    @Override // no.nordicsemi.android.ble.Request
    public MtuRequest setRequestHandler(RequestHandler requestHandler) {
        super.setRequestHandler(requestHandler);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public MtuRequest setHandler(Handler handler) {
        super.setHandler(handler);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public MtuRequest done(SuccessCallback callback) {
        super.done(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public MtuRequest fail(FailCallback callback) {
        super.fail(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public MtuRequest invalid(InvalidRequestCallback callback) {
        super.invalid(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public MtuRequest before(BeforeCallback callback) {
        super.before(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.Request
    public MtuRequest then(AfterCallback callback) {
        super.then(callback);
        return this;
    }

    @Override // no.nordicsemi.android.ble.SimpleValueRequest
    public MtuRequest with(MtuCallback callback) {
        super.with((MtuRequest) callback);
        return this;
    }

    void notifyMtuChanged(final BluetoothDevice device, final int mtu) {
        this.handler.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$MtuRequest$_-gzlu2HxBciFf-2oJ60BeE7wWw
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$notifyMtuChanged$0$MtuRequest(device, mtu);
            }
        });
    }

    public /* synthetic */ void lambda$notifyMtuChanged$0$MtuRequest(BluetoothDevice device, int mtu) {
        if (this.valueCallback != 0) {
            try {
                ((MtuCallback) this.valueCallback).onMtuChanged(device, mtu);
            } catch (Throwable t) {
                Log.e(TAG, "Exception in Value callback", t);
            }
        }
    }

    int getRequiredMtu() {
        return this.value;
    }
}
