package no.nordicsemi.android.ble;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCallback;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattDescriptor;
import android.bluetooth.BluetoothGattServer;
import android.bluetooth.BluetoothGattService;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Build;
import android.os.Handler;
import android.os.SystemClock;
import android.util.Log;
import android.util.Pair;
import java.lang.reflect.Method;
import java.security.InvalidParameterException;
import java.util.Deque;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.Map;
import java.util.concurrent.LinkedBlockingDeque;
import no.nordicsemi.android.ble.BleManagerHandler;
import no.nordicsemi.android.ble.Request;
import no.nordicsemi.android.ble.callback.ConnectionParametersUpdatedCallback;
import no.nordicsemi.android.ble.callback.DataReceivedCallback;
import no.nordicsemi.android.ble.data.Data;
import no.nordicsemi.android.ble.data.DataProvider;
import no.nordicsemi.android.ble.error.GattError;
import no.nordicsemi.android.ble.observer.BondingObserver;
import no.nordicsemi.android.ble.observer.ConnectionObserver;
import no.nordicsemi.android.ble.utils.ParserUtils;

/* JADX INFO: Access modifiers changed from: package-private */
/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public abstract class BleManagerHandler extends RequestHandler {
    private static final long CONNECTION_TIMEOUT_THRESHOLD = 20000;
    private static final String ERROR_AUTH_ERROR_WHILE_BONDED = "Phone has lost bonding information";
    private static final String ERROR_CONNECTION_PRIORITY_REQUEST = "Error on connection priority request";
    private static final String ERROR_CONNECTION_STATE_CHANGE = "Error on connection state change";
    private static final String ERROR_DISCOVERY_SERVICE = "Error on discovering services";
    private static final String ERROR_MTU_REQUEST = "Error on mtu request";
    private static final String ERROR_NOTIFY = "Error on sending notification/indication";
    private static final String ERROR_PHY_UPDATE = "Error on PHY update";
    private static final String ERROR_READ_CHARACTERISTIC = "Error on reading characteristic";
    private static final String ERROR_READ_DESCRIPTOR = "Error on reading descriptor";
    private static final String ERROR_READ_PHY = "Error on PHY read";
    private static final String ERROR_READ_RSSI = "Error on RSSI read";
    private static final String ERROR_RELIABLE_WRITE = "Error on Execute Reliable Write";
    private static final String ERROR_WRITE_CHARACTERISTIC = "Error on writing characteristic";
    private static final String ERROR_WRITE_DESCRIPTOR = "Error on writing descriptor";
    private static final String TAG = "BleManager";
    private AwaitingRequest<?> awaitingRequest;

    @Deprecated
    private ValueChangedCallback batteryLevelNotificationCallback;
    private BluetoothDevice bluetoothDevice;
    private BluetoothGatt bluetoothGatt;
    private Map<BluetoothGattCharacteristic, byte[]> characteristicValues;
    private ConnectRequest connectRequest;
    private boolean connected;
    private ConnectionParametersUpdatedCallback connectionParametersUpdatedCallback;
    private long connectionTime;
    private Map<BluetoothGattDescriptor, byte[]> descriptorValues;
    private boolean deviceNotSupported;
    private Handler handler;
    private Deque<Request> initQueue;
    private boolean initialConnection;
    private boolean initialization;
    private int interval;
    private int latency;
    private BleManager manager;
    private boolean operationInProgress;
    private int prepareError;
    private Deque<Pair<Object, byte[]>> preparedValues;
    private boolean ready;
    private boolean reliableWriteInProgress;
    private Request request;
    private RequestQueue requestQueue;
    private BleServerManager serverManager;
    private boolean serviceDiscoveryRequested;
    private boolean servicesDiscovered;
    private int timeout;
    private boolean userDisconnected;
    private final Object LOCK = new Object();
    private final Deque<Request> taskQueue = new LinkedBlockingDeque();
    private int connectionCount = 0;
    private int connectionState = 0;
    private boolean connectionPriorityOperationInProgress = false;
    private int mtu = 23;

    @Deprecated
    private int batteryValue = -1;
    private final HashMap<Object, ValueChangedCallback> valueChangedCallbacks = new HashMap<>();
    private final HashMap<Object, DataProvider> dataProviders = new HashMap<>();
    private final BroadcastReceiver bluetoothStateBroadcastReceiver = new AnonymousClass1();
    private final BroadcastReceiver mBondingBroadcastReceiver = new AnonymousClass2();
    private final BluetoothGattCallback gattCallback = new AnonymousClass3();

    /* JADX INFO: Access modifiers changed from: private */
    interface BondingObserverRunnable {
        void run(BondingObserver bondingObserver);
    }

    /* JADX INFO: Access modifiers changed from: private */
    @Deprecated
    interface CallbackRunnable {
        void run(BleManagerCallbacks bleManagerCallbacks);
    }

    /* JADX INFO: Access modifiers changed from: private */
    interface ConnectionObserverRunnable {
        void run(ConnectionObserver connectionObserver);
    }

    /* JADX INFO: Access modifiers changed from: private */
    @FunctionalInterface
    interface Loggable {
        String log();
    }

    protected abstract boolean isRequiredServiceSupported(BluetoothGatt bluetoothGatt);

    @Deprecated
    protected abstract void onServicesInvalidated();

    BleManagerHandler() {
    }

    static /* synthetic */ int access$2304(BleManagerHandler x0) {
        int i = x0.connectionCount + 1;
        x0.connectionCount = i;
        return i;
    }

    /* renamed from: no.nordicsemi.android.ble.BleManagerHandler$1, reason: invalid class name */
    class AnonymousClass1 extends BroadcastReceiver {
        AnonymousClass1() {
        }

        @Override // android.content.BroadcastReceiver
        public void onReceive(Context context, Intent intent) {
            final int state = intent.getIntExtra("android.bluetooth.adapter.extra.STATE", 10);
            int previousState = intent.getIntExtra("android.bluetooth.adapter.extra.PREVIOUS_STATE", 10);
            BleManagerHandler.this.log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$1$0mRAG6EumOb-l5QzmEqT9p7HaSo
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return this.f$0.lambda$onReceive$0$BleManagerHandler$1(state);
                }
            });
            switch (state) {
                case 10:
                case 13:
                    if (previousState != 13 && previousState != 10) {
                        BleManagerHandler.this.operationInProgress = true;
                        BleManagerHandler.this.taskQueue.clear();
                        BleManagerHandler.this.initQueue = null;
                        boolean wasConnected = BleManagerHandler.this.connected;
                        BleManagerHandler.this.connected = false;
                        BleManagerHandler.this.ready = false;
                        BleManagerHandler.this.connectionState = 0;
                        BluetoothDevice device = BleManagerHandler.this.bluetoothDevice;
                        if (device != null) {
                            if (BleManagerHandler.this.request != null && BleManagerHandler.this.request.type != Request.Type.DISCONNECT) {
                                BleManagerHandler.this.request.notifyFail(device, -100);
                                BleManagerHandler.this.request = null;
                            }
                            if (BleManagerHandler.this.awaitingRequest != null) {
                                BleManagerHandler.this.awaitingRequest.notifyFail(device, -100);
                                BleManagerHandler.this.awaitingRequest = null;
                            }
                            if (BleManagerHandler.this.connectRequest != null) {
                                BleManagerHandler.this.connectRequest.notifyFail(device, -100);
                                BleManagerHandler.this.connectRequest = null;
                            }
                        }
                        BleManagerHandler.this.userDisconnected = true;
                        BleManagerHandler.this.operationInProgress = false;
                        if (device != null) {
                            BleManagerHandler.this.connected = wasConnected;
                            BleManagerHandler.this.notifyDeviceDisconnected(device, 1);
                            break;
                        }
                    } else {
                        BleManagerHandler.this.close();
                        break;
                    }
                    break;
            }
        }

        public /* synthetic */ String lambda$onReceive$0$BleManagerHandler$1(int state) {
            return "[Broadcast] Action received: android.bluetooth.adapter.action.STATE_CHANGED, state changed to " + state2String(state);
        }

        private String state2String(int state) {
            switch (state) {
                case 10:
                    return "OFF";
                case 11:
                    return "TURNING ON";
                case 12:
                    return "ON";
                case 13:
                    return "TURNING OFF";
                default:
                    return "UNKNOWN (" + state + ")";
            }
        }
    }

    /* renamed from: no.nordicsemi.android.ble.BleManagerHandler$2, reason: invalid class name */
    class AnonymousClass2 extends BroadcastReceiver {
        AnonymousClass2() {
        }

        @Override // android.content.BroadcastReceiver
        public void onReceive(Context context, Intent intent) {
            final BluetoothDevice device = (BluetoothDevice) intent.getParcelableExtra("android.bluetooth.device.extra.DEVICE");
            final int bondState = intent.getIntExtra("android.bluetooth.device.extra.BOND_STATE", -1);
            int previousBondState = intent.getIntExtra("android.bluetooth.device.extra.PREVIOUS_BOND_STATE", -1);
            if (BleManagerHandler.this.bluetoothDevice != null && device != null && device.getAddress().equals(BleManagerHandler.this.bluetoothDevice.getAddress())) {
                BleManagerHandler.this.log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$OreoJ7M1soCWG_Mv54kK38JvpqQ
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass2.lambda$onReceive$0(bondState);
                    }
                });
                switch (bondState) {
                    case 10:
                        if (previousBondState == 11) {
                            BleManagerHandler.this.postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$LlH4iV1a2YF5VIrg4P62kk4v-Cg
                                @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                                public final void run(BleManagerCallbacks bleManagerCallbacks) {
                                    bleManagerCallbacks.onBondingFailed(device);
                                }
                            });
                            BleManagerHandler.this.postBondingStateChange(new BondingObserverRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$iJKC8pnr1CFXUoH9K4lo131YSms
                                @Override // no.nordicsemi.android.ble.BleManagerHandler.BondingObserverRunnable
                                public final void run(BondingObserver bondingObserver) {
                                    bondingObserver.onBondingFailed(device);
                                }
                            });
                            BleManagerHandler.this.log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$DcskRkQbEoL649AcE8k66ywCu1U
                                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                                public final String log() {
                                    return BleManagerHandler.AnonymousClass2.lambda$onReceive$3();
                                }
                            });
                            if (BleManagerHandler.this.request != null && BleManagerHandler.this.request.type == Request.Type.CREATE_BOND) {
                                BleManagerHandler.this.request.notifyFail(device, -4);
                                BleManagerHandler.this.request = null;
                            }
                            if (!BleManagerHandler.this.servicesDiscovered && !BleManagerHandler.this.serviceDiscoveryRequested) {
                                BleManagerHandler.this.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$5G28krA0TAH-8P4nqh8S4tVgadY
                                    @Override // java.lang.Runnable
                                    public final void run() {
                                        this.f$0.lambda$onReceive$6$BleManagerHandler$2();
                                    }
                                });
                                return;
                            }
                        } else if (previousBondState == 12) {
                            BleManagerHandler.this.userDisconnected = true;
                            if (BleManagerHandler.this.request != null && BleManagerHandler.this.request.type == Request.Type.REMOVE_BOND) {
                                BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$OIcUO003cKCWhCUwGCO-pwC7gkY
                                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                                    public final String log() {
                                        return BleManagerHandler.AnonymousClass2.lambda$onReceive$7();
                                    }
                                });
                                BleManagerHandler.this.request.notifySuccess(device);
                                BleManagerHandler.this.request = null;
                            }
                            if (!BleManagerHandler.this.isConnected()) {
                                BleManagerHandler.this.close();
                                break;
                            }
                        }
                        break;
                    case 11:
                        BleManagerHandler.this.postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$saeMFs7SQzdPV5_FfgfKWGCzPgA
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                            public final void run(BleManagerCallbacks bleManagerCallbacks) {
                                bleManagerCallbacks.onBondingRequired(device);
                            }
                        });
                        BleManagerHandler.this.postBondingStateChange(new BondingObserverRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$QucwGaCaEpxK5CwjgNR4P4tnWFk
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.BondingObserverRunnable
                            public final void run(BondingObserver bondingObserver) {
                                bondingObserver.onBondingRequired(device);
                            }
                        });
                        return;
                    case 12:
                        BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$ftbt9wWf85ClajG5pDSO4kMgR14
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                            public final String log() {
                                return BleManagerHandler.AnonymousClass2.lambda$onReceive$10();
                            }
                        });
                        BleManagerHandler.this.postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$_mtlltmFLucSAwnG-Dn3wchJQMM
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                            public final void run(BleManagerCallbacks bleManagerCallbacks) {
                                bleManagerCallbacks.onBonded(device);
                            }
                        });
                        BleManagerHandler.this.postBondingStateChange(new BondingObserverRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$6JC9_-fil6z-VBBUqj-7-TUiLC4
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.BondingObserverRunnable
                            public final void run(BondingObserver bondingObserver) {
                                bondingObserver.onBonded(device);
                            }
                        });
                        if (BleManagerHandler.this.request == null || BleManagerHandler.this.request.type != Request.Type.CREATE_BOND) {
                            if (!BleManagerHandler.this.servicesDiscovered && !BleManagerHandler.this.serviceDiscoveryRequested) {
                                BleManagerHandler.this.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$Y9klKfKMZ5oPxORwboT_cUYcpOw
                                    @Override // java.lang.Runnable
                                    public final void run() {
                                        this.f$0.lambda$onReceive$15$BleManagerHandler$2();
                                    }
                                });
                                return;
                            } else if (Build.VERSION.SDK_INT < 26 && BleManagerHandler.this.request != null) {
                                BleManagerHandler bleManagerHandler = BleManagerHandler.this;
                                bleManagerHandler.enqueueFirst(bleManagerHandler.request);
                                break;
                            } else {
                                return;
                            }
                        } else {
                            BleManagerHandler.this.request.notifySuccess(device);
                            BleManagerHandler.this.request = null;
                            break;
                        }
                        break;
                }
                BleManagerHandler.this.nextRequest(true);
            }
        }

        static /* synthetic */ String lambda$onReceive$0(int bondState) {
            return "[Broadcast] Action received: android.bluetooth.device.action.BOND_STATE_CHANGED, bond state changed to: " + ParserUtils.bondStateToString(bondState) + " (" + bondState + ")";
        }

        static /* synthetic */ String lambda$onReceive$3() {
            return "Bonding failed";
        }

        public /* synthetic */ void lambda$onReceive$6$BleManagerHandler$2() {
            BluetoothGatt bluetoothGatt = BleManagerHandler.this.bluetoothGatt;
            if (!BleManagerHandler.this.servicesDiscovered && !BleManagerHandler.this.serviceDiscoveryRequested && bluetoothGatt != null) {
                BleManagerHandler.this.serviceDiscoveryRequested = true;
                BleManagerHandler.this.log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$KCQvuvAyue70EtFsr0C0LPLlWjk
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass2.lambda$onReceive$4();
                    }
                });
                BleManagerHandler.this.log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$HYhyCzUvJu923oZX7HyuS7PZXdM
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass2.lambda$onReceive$5();
                    }
                });
                bluetoothGatt.discoverServices();
            }
        }

        static /* synthetic */ String lambda$onReceive$4() {
            return "Discovering services...";
        }

        static /* synthetic */ String lambda$onReceive$5() {
            return "gatt.discoverServices()";
        }

        static /* synthetic */ String lambda$onReceive$7() {
            return "Bond information removed";
        }

        static /* synthetic */ String lambda$onReceive$10() {
            return "Device bonded";
        }

        public /* synthetic */ void lambda$onReceive$15$BleManagerHandler$2() {
            BluetoothGatt bluetoothGatt = BleManagerHandler.this.bluetoothGatt;
            if (!BleManagerHandler.this.servicesDiscovered && !BleManagerHandler.this.serviceDiscoveryRequested && bluetoothGatt != null) {
                BleManagerHandler.this.serviceDiscoveryRequested = true;
                BleManagerHandler.this.log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$UtvbIc9iUj-t2NAekZjeXY26Rjw
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass2.lambda$onReceive$13();
                    }
                });
                BleManagerHandler.this.log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2$m0_k_jfikn903TLhG-e4RO5Cz2Y
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass2.lambda$onReceive$14();
                    }
                });
                bluetoothGatt.discoverServices();
            }
        }

        static /* synthetic */ String lambda$onReceive$13() {
            return "Discovering services...";
        }

        static /* synthetic */ String lambda$onReceive$14() {
            return "gatt.discoverServices()";
        }
    }

    void init(BleManager manager, Handler handler) {
        this.manager = manager;
        this.handler = handler;
    }

    void useServer(BleServerManager server) {
        this.serverManager = server;
    }

    void attachClientConnection(BluetoothDevice clientDevice) {
        if (this.bluetoothDevice != null) {
            log(6, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$8pLUNiZgMxS5c3TC-erK8qh9mUE
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$attachClientConnection$0();
                }
            });
            return;
        }
        this.bluetoothDevice = clientDevice;
        initializeServerAttributes();
        this.manager.initialize();
    }

    static /* synthetic */ String lambda$attachClientConnection$0() {
        return "attachClientConnection called on existing connection, call ignored";
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void initializeServerAttributes() {
        BluetoothGattServer server;
        BleServerManager bleServerManager = this.serverManager;
        if (bleServerManager != null && (server = bleServerManager.getServer()) != null) {
            for (BluetoothGattService service : server.getServices()) {
                for (BluetoothGattCharacteristic characteristic : service.getCharacteristics()) {
                    if (!this.serverManager.isShared(characteristic)) {
                        if (this.characteristicValues == null) {
                            this.characteristicValues = new HashMap();
                        }
                        this.characteristicValues.put(characteristic, characteristic.getValue());
                    }
                    for (BluetoothGattDescriptor descriptor : characteristic.getDescriptors()) {
                        if (!this.serverManager.isShared(descriptor)) {
                            if (this.descriptorValues == null) {
                                this.descriptorValues = new HashMap();
                            }
                            this.descriptorValues.put(descriptor, descriptor.getValue());
                        }
                    }
                }
            }
            this.manager.onServerReady(server);
        }
    }

    void close() {
        try {
            Context context = this.manager.getContext();
            context.unregisterReceiver(this.bluetoothStateBroadcastReceiver);
            context.unregisterReceiver(this.mBondingBroadcastReceiver);
        } catch (Exception e) {
        }
        synchronized (this.LOCK) {
            if (this.bluetoothGatt != null) {
                if (this.manager.shouldClearCacheWhenDisconnected()) {
                    if (internalRefreshDeviceCache()) {
                        log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$FlLy1rxJ36wv5CHABV0fPaZVAaY
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                            public final String log() {
                                return BleManagerHandler.lambda$close$1();
                            }
                        });
                    } else {
                        log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$fADqxa9G6MXK3aWw9odZuvG97nI
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                            public final String log() {
                                return BleManagerHandler.lambda$close$2();
                            }
                        });
                    }
                }
                log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$LCqtxGAFpv8hHwBC3QMylc_7yrQ
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.lambda$close$3();
                    }
                });
                try {
                    this.bluetoothGatt.close();
                } catch (Throwable th) {
                }
                this.bluetoothGatt = null;
            }
            this.reliableWriteInProgress = false;
            this.initialConnection = false;
            this.taskQueue.clear();
            this.initQueue = null;
            this.initialization = false;
            this.bluetoothDevice = null;
            this.connected = false;
        }
    }

    static /* synthetic */ String lambda$close$1() {
        return "Cache refreshed";
    }

    static /* synthetic */ String lambda$close$2() {
        return "Refreshing failed";
    }

    static /* synthetic */ String lambda$close$3() {
        return "gatt.close()";
    }

    public BluetoothDevice getBluetoothDevice() {
        return this.bluetoothDevice;
    }

    public final byte[] getCharacteristicValue(BluetoothGattCharacteristic serverCharacteristic) {
        Map<BluetoothGattCharacteristic, byte[]> map = this.characteristicValues;
        if (map != null && map.containsKey(serverCharacteristic)) {
            return this.characteristicValues.get(serverCharacteristic);
        }
        return serverCharacteristic.getValue();
    }

    public final byte[] getDescriptorValue(BluetoothGattDescriptor serverDescriptor) {
        Map<BluetoothGattDescriptor, byte[]> map = this.descriptorValues;
        if (map != null && map.containsKey(serverDescriptor)) {
            return this.descriptorValues.get(serverDescriptor);
        }
        return serverDescriptor.getValue();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public boolean internalConnect(final BluetoothDevice device, final ConnectRequest connectRequest) {
        int i;
        boolean bluetoothEnabled = BluetoothAdapter.getDefaultAdapter().isEnabled();
        if (this.connected || !bluetoothEnabled) {
            BluetoothDevice currentDevice = this.bluetoothDevice;
            if (bluetoothEnabled && currentDevice != null && currentDevice.equals(device)) {
                ConnectRequest connectRequest2 = this.connectRequest;
                if (connectRequest2 != null) {
                    connectRequest2.notifySuccess(device);
                }
            } else {
                ConnectRequest connectRequest3 = this.connectRequest;
                if (connectRequest3 != null) {
                    if (bluetoothEnabled) {
                        i = -4;
                    } else {
                        i = -100;
                    }
                    connectRequest3.notifyFail(device, i);
                }
            }
            this.connectRequest = null;
            nextRequest(true);
            return true;
        }
        Context context = this.manager.getContext();
        synchronized (this.LOCK) {
            if (this.bluetoothGatt != null) {
                if (!this.initialConnection) {
                    log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$K9LHAnRN_fsQ-nq_TmyZEko6-Zs
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.lambda$internalConnect$4();
                        }
                    });
                    try {
                        this.bluetoothGatt.close();
                    } catch (Throwable th) {
                    }
                    this.bluetoothGatt = null;
                    try {
                        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$hFHZSkdCG9oQgeiXWcxwgSZFFzo
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                            public final String log() {
                                return BleManagerHandler.lambda$internalConnect$5();
                            }
                        });
                        Thread.sleep(200L);
                    } catch (InterruptedException e) {
                    }
                } else {
                    this.initialConnection = false;
                    this.connectionTime = 0L;
                    this.connectionState = 1;
                    log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$J6wu-EXA8Unh79dd_73gxv816Lo
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.lambda$internalConnect$6();
                        }
                    });
                    postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$DyoOPIQam8zccda6I5n9HvuL5EI
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                        public final void run(BleManagerCallbacks bleManagerCallbacks) {
                            bleManagerCallbacks.onDeviceConnecting(device);
                        }
                    });
                    postConnectionStateChange(new ConnectionObserverRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$7Kp5y2nzlTmZ2gEsDJe9Q03MZas
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.ConnectionObserverRunnable
                        public final void run(ConnectionObserver connectionObserver) {
                            connectionObserver.onDeviceConnecting(device);
                        }
                    });
                    log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$AEadbZz9HZCCOCwovfIRNajiQxY
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.lambda$internalConnect$9();
                        }
                    });
                    this.bluetoothGatt.connect();
                    return true;
                }
            } else if (connectRequest != null) {
                context.registerReceiver(this.bluetoothStateBroadcastReceiver, new IntentFilter("android.bluetooth.adapter.action.STATE_CHANGED"));
                context.registerReceiver(this.mBondingBroadcastReceiver, new IntentFilter("android.bluetooth.device.action.BOND_STATE_CHANGED"));
            }
            if (connectRequest == null) {
                return false;
            }
            boolean shouldAutoConnect = connectRequest.shouldAutoConnect();
            this.userDisconnected = !shouldAutoConnect;
            if (shouldAutoConnect) {
                this.initialConnection = true;
            }
            this.bluetoothDevice = device;
            log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$uxufB5FIdwoX8ze5naVAwntzkRc
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalConnect$10(connectRequest);
                }
            });
            this.connectionState = 1;
            postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$9GT2BK4OZn9Z1KG4D-qMjrmlNPc
                @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                public final void run(BleManagerCallbacks bleManagerCallbacks) {
                    bleManagerCallbacks.onDeviceConnecting(device);
                }
            });
            postConnectionStateChange(new ConnectionObserverRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$CYpAP1VllIJePRzqc2zVKRwHXlM
                @Override // no.nordicsemi.android.ble.BleManagerHandler.ConnectionObserverRunnable
                public final void run(ConnectionObserver connectionObserver) {
                    connectionObserver.onDeviceConnecting(device);
                }
            });
            this.connectionTime = SystemClock.elapsedRealtime();
            if (Build.VERSION.SDK_INT > 26) {
                final int preferredPhy = connectRequest.getPreferredPhy();
                log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$rKEvK6C0dJ7QGKz7c1z1ftyO2H0
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.lambda$internalConnect$13(preferredPhy);
                    }
                });
                this.bluetoothGatt = device.connectGatt(context, false, this.gattCallback, 2, preferredPhy, this.handler);
            } else if (Build.VERSION.SDK_INT == 26) {
                final int preferredPhy2 = connectRequest.getPreferredPhy();
                log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$h0ItCyoL-yqDAHeYhJfK1afrmc8
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.lambda$internalConnect$14(preferredPhy2);
                    }
                });
                this.bluetoothGatt = device.connectGatt(context, false, this.gattCallback, 2, preferredPhy2);
            } else if (Build.VERSION.SDK_INT >= 23) {
                log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$aUp-g2zzih2WuKTjwpgeX1pFRYs
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.lambda$internalConnect$15();
                    }
                });
                this.bluetoothGatt = device.connectGatt(context, false, this.gattCallback, 2);
            } else {
                log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$GWYbd3T0gwNGkWPf9G0x8cTLssg
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.lambda$internalConnect$16();
                    }
                });
                this.bluetoothGatt = device.connectGatt(context, false, this.gattCallback);
            }
            return true;
        }
    }

    static /* synthetic */ String lambda$internalConnect$4() {
        return "gatt.close()";
    }

    static /* synthetic */ String lambda$internalConnect$5() {
        return "wait(200)";
    }

    static /* synthetic */ String lambda$internalConnect$6() {
        return "Connecting...";
    }

    static /* synthetic */ String lambda$internalConnect$9() {
        return "gatt.connect()";
    }

    static /* synthetic */ String lambda$internalConnect$10(ConnectRequest connectRequest) {
        return connectRequest.isFirstAttempt() ? "Connecting..." : "Retrying...";
    }

    static /* synthetic */ String lambda$internalConnect$13(int preferredPhy) {
        return "gatt = device.connectGatt(autoConnect = false, TRANSPORT_LE, " + ParserUtils.phyMaskToString(preferredPhy) + ")";
    }

    static /* synthetic */ String lambda$internalConnect$14(int preferredPhy) {
        return "gatt = device.connectGatt(autoConnect = false, TRANSPORT_LE, " + ParserUtils.phyMaskToString(preferredPhy) + ")";
    }

    static /* synthetic */ String lambda$internalConnect$15() {
        return "gatt = device.connectGatt(autoConnect = false, TRANSPORT_LE)";
    }

    static /* synthetic */ String lambda$internalConnect$16() {
        return "gatt = device.connectGatt(autoConnect = false)";
    }

    /* JADX INFO: Access modifiers changed from: private */
    public boolean internalDisconnect(final int reason) {
        this.userDisconnected = true;
        this.initialConnection = false;
        this.ready = false;
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt != null) {
            final boolean wasConnected = this.connected;
            this.connectionState = 3;
            log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$qe2F7inG6sJYaNFr3CK3XWFRxfs
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalDisconnect$17(wasConnected);
                }
            });
            final BluetoothDevice device = gatt.getDevice();
            if (wasConnected) {
                postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$4UT4L6WrYcKm6U4WX09yOHI5GXs
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                    public final void run(BleManagerCallbacks bleManagerCallbacks) {
                        bleManagerCallbacks.onDeviceDisconnecting(device);
                    }
                });
                postConnectionStateChange(new ConnectionObserverRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$wEi5c9JrllAdN_QFdYFDv6AM4dE
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.ConnectionObserverRunnable
                    public final void run(ConnectionObserver connectionObserver) {
                        connectionObserver.onDeviceDisconnecting(device);
                    }
                });
            }
            log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$JIt1yS6fRQx8DQ2xMAMqxnIGzPc
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalDisconnect$20();
                }
            });
            gatt.disconnect();
            if (wasConnected) {
                return true;
            }
            this.connectionState = 0;
            log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$Fb_cfAsBklz32WT_vG5JhqKGkY4
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalDisconnect$21();
                }
            });
            close();
            postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$dUPKYS2idF7L1Iexn3WeGhWFHUE
                @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                public final void run(BleManagerCallbacks bleManagerCallbacks) {
                    bleManagerCallbacks.onDeviceDisconnected(device);
                }
            });
            postConnectionStateChange(new ConnectionObserverRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$prem6yd6lKMF05941r2Fl4_ZhtU
                @Override // no.nordicsemi.android.ble.BleManagerHandler.ConnectionObserverRunnable
                public final void run(ConnectionObserver connectionObserver) {
                    connectionObserver.onDeviceDisconnected(device, reason);
                }
            });
        }
        Request r = this.request;
        if (r != null && r.type == Request.Type.DISCONNECT) {
            BluetoothDevice device2 = this.bluetoothDevice;
            if (device2 != null || gatt != null) {
                if (device2 == null) {
                    device2 = gatt.getDevice();
                }
                r.notifySuccess(device2);
            } else {
                r.notifyInvalidRequest();
            }
        }
        nextRequest(true);
        return true;
    }

    static /* synthetic */ String lambda$internalDisconnect$17(boolean wasConnected) {
        return wasConnected ? "Disconnecting..." : "Cancelling connection...";
    }

    static /* synthetic */ String lambda$internalDisconnect$20() {
        return "gatt.disconnect()";
    }

    static /* synthetic */ String lambda$internalDisconnect$21() {
        return "Disconnected";
    }

    private boolean internalCreateBond(boolean ensure) throws NoSuchMethodException, SecurityException {
        BluetoothDevice device = this.bluetoothDevice;
        if (device == null) {
            return false;
        }
        if (ensure) {
            log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$87gO0qRGy9_BoJyxfm_lBC6cAJQ
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalCreateBond$24();
                }
            });
        } else {
            log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$LcGgrvXNAnkATMGIIOjFO8tmCg8
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalCreateBond$25();
                }
            });
        }
        if (!ensure && device.getBondState() == 12) {
            log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$bSd0XubArnhY2-wX0Ph0G6pRIZM
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalCreateBond$26();
                }
            });
            this.request.notifySuccess(device);
            nextRequest(true);
            return true;
        }
        boolean result = createBond(device);
        if (ensure && !result) {
            Request bond = Request.createBond().setRequestHandler(this);
            bond.successCallback = this.request.successCallback;
            bond.invalidRequestCallback = this.request.invalidRequestCallback;
            bond.failCallback = this.request.failCallback;
            bond.internalSuccessCallback = this.request.internalSuccessCallback;
            bond.internalFailCallback = this.request.internalFailCallback;
            this.request.successCallback = null;
            this.request.invalidRequestCallback = null;
            this.request.failCallback = null;
            this.request.internalSuccessCallback = null;
            this.request.internalFailCallback = null;
            enqueueFirst(bond);
            enqueueFirst(Request.removeBond().setRequestHandler(this));
            nextRequest(true);
            return true;
        }
        return result;
    }

    static /* synthetic */ String lambda$internalCreateBond$24() {
        return "Ensuring bonding...";
    }

    static /* synthetic */ String lambda$internalCreateBond$25() {
        return "Starting bonding...";
    }

    static /* synthetic */ String lambda$internalCreateBond$26() {
        return "Bond information present on client, skipping bonding";
    }

    private boolean createBond(BluetoothDevice device) throws NoSuchMethodException, SecurityException {
        if (Build.VERSION.SDK_INT >= 19) {
            log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$saSXd3jH-ZEmgYhtvP1_-XNIX5o
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$createBond$27();
                }
            });
            return device.createBond();
        }
        try {
            Method createBond = device.getClass().getMethod("createBond", new Class[0]);
            log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$Ro5XY5Xa4gfNcH0syY5pSl9LohI
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$createBond$28();
                }
            });
            return createBond.invoke(device, new Object[0]) == Boolean.TRUE;
        } catch (Exception e) {
            Log.w(TAG, "An exception occurred while creating bond", e);
            return false;
        }
    }

    static /* synthetic */ String lambda$createBond$27() {
        return "device.createBond()";
    }

    static /* synthetic */ String lambda$createBond$28() {
        return "device.createBond() (hidden)";
    }

    private boolean internalRemoveBond() throws NoSuchMethodException, SecurityException {
        BluetoothDevice device = this.bluetoothDevice;
        if (device == null) {
            return false;
        }
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$WBUeZ6t972Pfr-WkVf_Lb9QN2tU
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalRemoveBond$29();
            }
        });
        if (device.getBondState() != 10) {
            try {
                Method removeBond = device.getClass().getMethod("removeBond", new Class[0]);
                log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$FehfgrLI_yNiebmhfS3FY5e2HsQ
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.lambda$internalRemoveBond$31();
                    }
                });
                this.userDisconnected = true;
                return removeBond.invoke(device, new Object[0]) == Boolean.TRUE;
            } catch (Exception e) {
                Log.w(TAG, "An exception occurred while removing bond", e);
                return false;
            }
        }
        log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$eZdv6pJH02fFYPmoTQMN00klUx4
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalRemoveBond$30();
            }
        });
        this.request.notifySuccess(device);
        nextRequest(true);
        return true;
    }

    static /* synthetic */ String lambda$internalRemoveBond$29() {
        return "Removing bond information...";
    }

    static /* synthetic */ String lambda$internalRemoveBond$30() {
        return "Device is not bonded";
    }

    static /* synthetic */ String lambda$internalRemoveBond$31() {
        return "device.removeBond() (hidden)";
    }

    private boolean ensureServiceChangedEnabled() {
        BluetoothGattService gaService;
        BluetoothGattCharacteristic scCharacteristic;
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || !this.connected) {
            return false;
        }
        BluetoothDevice device = gatt.getDevice();
        if (device.getBondState() != 12 || (gaService = gatt.getService(BleManager.GENERIC_ATTRIBUTE_SERVICE)) == null || (scCharacteristic = gaService.getCharacteristic(BleManager.SERVICE_CHANGED_CHARACTERISTIC)) == null) {
            return false;
        }
        log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$LJacf2xPRmucsOQKEocPZShRvBY
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$ensureServiceChangedEnabled$32();
            }
        });
        return internalEnableIndications(scCharacteristic);
    }

    static /* synthetic */ String lambda$ensureServiceChangedEnabled$32() {
        return "Service Changed characteristic found on a bonded device";
    }

    private boolean internalEnableNotifications(final BluetoothGattCharacteristic characteristic) {
        BluetoothGattDescriptor descriptor;
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || characteristic == null || !this.connected || (descriptor = getCccd(characteristic, 16)) == null) {
            return false;
        }
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$b9W0WmmEGamQveqFRSPl1UhFyLk
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalEnableNotifications$33(characteristic);
            }
        });
        gatt.setCharacteristicNotification(characteristic, true);
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$cuveZ_hBadOsXOyns-YnPqaDAq0
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalEnableNotifications$34(characteristic);
            }
        });
        if (Build.VERSION.SDK_INT >= 33) {
            log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$K9moLak0poO2WiY5S7xocoEaMV4
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalEnableNotifications$35();
                }
            });
            return gatt.writeDescriptor(descriptor, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE) == 0;
        }
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$cYUcIsouO8W4YXCknpf4fR8tQG8
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalEnableNotifications$36();
            }
        });
        descriptor.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE);
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$ZeNAwO151vroaBZAuK8R7EBpO1E
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalEnableNotifications$37();
            }
        });
        if (Build.VERSION.SDK_INT >= 24) {
            return gatt.writeDescriptor(descriptor);
        }
        return internalWriteDescriptorWorkaround(descriptor);
    }

    static /* synthetic */ String lambda$internalEnableNotifications$33(BluetoothGattCharacteristic characteristic) {
        return "gatt.setCharacteristicNotification(" + characteristic.getUuid() + ", true)";
    }

    static /* synthetic */ String lambda$internalEnableNotifications$34(BluetoothGattCharacteristic characteristic) {
        return "Enabling notifications for " + characteristic.getUuid();
    }

    static /* synthetic */ String lambda$internalEnableNotifications$35() {
        return "gatt.writeDescriptor(00002902-0000-1000-8000-00805f9b34fb, value=0x01-00)";
    }

    static /* synthetic */ String lambda$internalEnableNotifications$36() {
        return "descriptor.setValue(0x01-00)";
    }

    static /* synthetic */ String lambda$internalEnableNotifications$37() {
        return "gatt.writeDescriptor(00002902-0000-1000-8000-00805f9b34fb)";
    }

    private boolean internalDisableNotifications(final BluetoothGattCharacteristic characteristic) {
        BluetoothGattDescriptor descriptor;
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || characteristic == null || !this.connected || (descriptor = getCccd(characteristic, 48)) == null) {
            return false;
        }
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$O7GzvmmimNkBx2xnOsVzXXyVI2k
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalDisableNotifications$38(characteristic);
            }
        });
        gatt.setCharacteristicNotification(characteristic, false);
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$GnVz0XqjWby1DI2AzK23o6NVvho
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalDisableNotifications$39(characteristic);
            }
        });
        if (Build.VERSION.SDK_INT >= 33) {
            log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$Hg6q6hgFmMZ_692sGJXm-1mSAzQ
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalDisableNotifications$40();
                }
            });
            return gatt.writeDescriptor(descriptor, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE) == 0;
        }
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$m16jPEGlT3SY5WplIZ8QDtJiyXM
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalDisableNotifications$41();
            }
        });
        descriptor.setValue(BluetoothGattDescriptor.DISABLE_NOTIFICATION_VALUE);
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$kRgqg7P6_krgZ_NM_Pwh8Zbz1Yc
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalDisableNotifications$42();
            }
        });
        if (Build.VERSION.SDK_INT >= 24) {
            return gatt.writeDescriptor(descriptor);
        }
        return internalWriteDescriptorWorkaround(descriptor);
    }

    static /* synthetic */ String lambda$internalDisableNotifications$38(BluetoothGattCharacteristic characteristic) {
        return "gatt.setCharacteristicNotification(" + characteristic.getUuid() + ", false)";
    }

    static /* synthetic */ String lambda$internalDisableNotifications$39(BluetoothGattCharacteristic characteristic) {
        return "Disabling notifications and indications for " + characteristic.getUuid();
    }

    static /* synthetic */ String lambda$internalDisableNotifications$40() {
        return "gatt.writeDescriptor(00002902-0000-1000-8000-00805f9b34fb, value=0x00-00)";
    }

    static /* synthetic */ String lambda$internalDisableNotifications$41() {
        return "descriptor.setValue(0x00-00)";
    }

    static /* synthetic */ String lambda$internalDisableNotifications$42() {
        return "gatt.writeDescriptor(00002902-0000-1000-8000-00805f9b34fb)";
    }

    private boolean internalEnableIndications(final BluetoothGattCharacteristic characteristic) {
        BluetoothGattDescriptor descriptor;
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || characteristic == null || !this.connected || (descriptor = getCccd(characteristic, 32)) == null) {
            return false;
        }
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$2Wmy5Y-dqbcwj02VAJytGNfYkDk
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalEnableIndications$43(characteristic);
            }
        });
        gatt.setCharacteristicNotification(characteristic, true);
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$XlyPow1bvlqX7Gewj1M7YUWbqt0
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalEnableIndications$44(characteristic);
            }
        });
        if (Build.VERSION.SDK_INT >= 33) {
            log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$-AeRA13DC19AvjidK7ZcTl9jQ1k
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalEnableIndications$45();
                }
            });
            return gatt.writeDescriptor(descriptor, BluetoothGattDescriptor.ENABLE_INDICATION_VALUE) == 0;
        }
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$_MGZjbsj2YiMKRViycI2nq4kmx8
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalEnableIndications$46();
            }
        });
        descriptor.setValue(BluetoothGattDescriptor.ENABLE_INDICATION_VALUE);
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$GaS7S860lQVdO5DxksavjUsFAbE
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalEnableIndications$47();
            }
        });
        if (Build.VERSION.SDK_INT >= 24) {
            return gatt.writeDescriptor(descriptor);
        }
        return internalWriteDescriptorWorkaround(descriptor);
    }

    static /* synthetic */ String lambda$internalEnableIndications$43(BluetoothGattCharacteristic characteristic) {
        return "gatt.setCharacteristicNotification(" + characteristic.getUuid() + ", true)";
    }

    static /* synthetic */ String lambda$internalEnableIndications$44(BluetoothGattCharacteristic characteristic) {
        return "Enabling indications for " + characteristic.getUuid();
    }

    static /* synthetic */ String lambda$internalEnableIndications$45() {
        return "gatt.writeDescriptor(00002902-0000-1000-8000-00805f9b34fb, value=0x02-00)";
    }

    static /* synthetic */ String lambda$internalEnableIndications$46() {
        return "descriptor.setValue(0x02-00)";
    }

    static /* synthetic */ String lambda$internalEnableIndications$47() {
        return "gatt.writeDescriptor(00002902-0000-1000-8000-00805f9b34fb)";
    }

    private boolean internalDisableIndications(BluetoothGattCharacteristic characteristic) {
        return internalDisableNotifications(characteristic);
    }

    private boolean internalSendNotification(final BluetoothGattCharacteristic serverCharacteristic, final boolean confirm, final byte[] data) {
        BluetoothGattDescriptor cccd;
        BleServerManager bleServerManager = this.serverManager;
        if (bleServerManager == null || bleServerManager.getServer() == null || serverCharacteristic == null) {
            return false;
        }
        int requiredProperty = confirm ? 32 : 16;
        if ((serverCharacteristic.getProperties() & requiredProperty) == 0 || (cccd = serverCharacteristic.getDescriptor(BleManager.CLIENT_CHARACTERISTIC_CONFIG_DESCRIPTOR_UUID)) == null) {
            return false;
        }
        Map<BluetoothGattDescriptor, byte[]> map = this.descriptorValues;
        byte[] value = (map == null || !map.containsKey(cccd)) ? cccd.getValue() : this.descriptorValues.get(cccd);
        if (value != null && value.length == 2 && value[0] != 0) {
            log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$ySlXBg_3O-ANXXKben6im51FSvM
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalSendNotification$48(confirm, serverCharacteristic);
                }
            });
            if (Build.VERSION.SDK_INT >= 33) {
                log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$6Yi-qc-A_xBFwnzXGItfwTtPF4M
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.lambda$internalSendNotification$49(serverCharacteristic, confirm, data);
                    }
                });
                return this.serverManager.getServer().notifyCharacteristicChanged(this.bluetoothDevice, serverCharacteristic, confirm, data) == 0;
            }
            log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$ar2r_9DaWPzNU14QWKotizkmuuU
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalSendNotification$50(data);
                }
            });
            serverCharacteristic.setValue(data);
            log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$_k8iLoYC_j7N0UHGSpZSyAFx2kA
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalSendNotification$51(serverCharacteristic, confirm);
                }
            });
            boolean result = this.serverManager.getServer().notifyCharacteristicChanged(this.bluetoothDevice, serverCharacteristic, confirm);
            if (result && Build.VERSION.SDK_INT < 21) {
                post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$_MXKjbry8rn6TSvFJpgmHhar3hg
                    @Override // java.lang.Runnable
                    public final void run() {
                        this.f$0.lambda$internalSendNotification$52$BleManagerHandler();
                    }
                });
            }
            return result;
        }
        nextRequest(true);
        return true;
    }

    static /* synthetic */ String lambda$internalSendNotification$48(boolean confirm, BluetoothGattCharacteristic serverCharacteristic) {
        StringBuilder sb = new StringBuilder();
        sb.append("[Server] Sending ");
        sb.append(confirm ? "indication" : "notification");
        sb.append(" to ");
        sb.append(serverCharacteristic.getUuid());
        return sb.toString();
    }

    static /* synthetic */ String lambda$internalSendNotification$49(BluetoothGattCharacteristic serverCharacteristic, boolean confirm, byte[] data) {
        return "[Server] gattServer.notifyCharacteristicChanged(" + serverCharacteristic.getUuid() + ", confirm=" + confirm + ", value=" + ParserUtils.parseDebug(data) + ")";
    }

    static /* synthetic */ String lambda$internalSendNotification$50(byte[] data) {
        return "[Server] characteristic.setValue(" + ParserUtils.parseDebug(data) + ")";
    }

    static /* synthetic */ String lambda$internalSendNotification$51(BluetoothGattCharacteristic serverCharacteristic, boolean confirm) {
        return "[Server] gattServer.notifyCharacteristicChanged(" + serverCharacteristic.getUuid() + ", confirm=" + confirm + ")";
    }

    public /* synthetic */ void lambda$internalSendNotification$52$BleManagerHandler() {
        notifyNotificationSent(this.bluetoothDevice);
        nextRequest(true);
    }

    private static BluetoothGattDescriptor getCccd(BluetoothGattCharacteristic characteristic, int requiredProperty) {
        if (characteristic == null) {
            return null;
        }
        int properties = characteristic.getProperties();
        if ((properties & requiredProperty) == 0) {
            return null;
        }
        return characteristic.getDescriptor(BleManager.CLIENT_CHARACTERISTIC_CONFIG_DESCRIPTOR_UUID);
    }

    private boolean internalReadCharacteristic(final BluetoothGattCharacteristic characteristic) {
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || characteristic == null || !this.connected) {
            return false;
        }
        int properties = characteristic.getProperties();
        if ((properties & 2) == 0) {
            return false;
        }
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$9h_XTfPVYmKpBD2FunvnvQ3uHI4
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalReadCharacteristic$53(characteristic);
            }
        });
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$Bb9O1hEDN4EPE-3MLZ0h_qUZZOM
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalReadCharacteristic$54(characteristic);
            }
        });
        return gatt.readCharacteristic(characteristic);
    }

    static /* synthetic */ String lambda$internalReadCharacteristic$53(BluetoothGattCharacteristic characteristic) {
        return "Reading characteristic " + characteristic.getUuid();
    }

    static /* synthetic */ String lambda$internalReadCharacteristic$54(BluetoothGattCharacteristic characteristic) {
        return "gatt.readCharacteristic(" + characteristic.getUuid() + ")";
    }

    private boolean internalWriteCharacteristic(final BluetoothGattCharacteristic characteristic, final byte[] data, final int writeType) {
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || characteristic == null || !this.connected) {
            return false;
        }
        int properties = characteristic.getProperties();
        if ((properties & 12) == 0) {
            return false;
        }
        if (Build.VERSION.SDK_INT >= 33) {
            log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$cPIyzyyprEjEsdzi1tXm-zw0S4A
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalWriteCharacteristic$55(characteristic, writeType);
                }
            });
            log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$79ePH0CzC0A5T0TpGKmIjnOVzRM
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalWriteCharacteristic$56(characteristic, data, writeType);
                }
            });
            return gatt.writeCharacteristic(characteristic, data, writeType) == 0;
        }
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$pOyqES8ZYbwih6HMOqWc9YA4lAg
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalWriteCharacteristic$57(characteristic, writeType);
            }
        });
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$0Kcdm6gOrz8hVg4snWe2qHZ3ESM
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalWriteCharacteristic$58(data);
            }
        });
        characteristic.setValue(data);
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$IIewn1gHf6RsVqzqURFIKbKSF14
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalWriteCharacteristic$59(writeType);
            }
        });
        characteristic.setWriteType(writeType);
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$oePzJC1jLcvzSvtzOPO4wqfhFZY
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalWriteCharacteristic$60(characteristic);
            }
        });
        return gatt.writeCharacteristic(characteristic);
    }

    static /* synthetic */ String lambda$internalWriteCharacteristic$55(BluetoothGattCharacteristic characteristic, int writeType) {
        return "Writing characteristic " + characteristic.getUuid() + " (" + ParserUtils.writeTypeToString(writeType) + ")";
    }

    static /* synthetic */ String lambda$internalWriteCharacteristic$56(BluetoothGattCharacteristic characteristic, byte[] data, int writeType) {
        return "gatt.writeCharacteristic(" + characteristic.getUuid() + ", value=" + ParserUtils.parseDebug(data) + ", " + ParserUtils.writeTypeToString(writeType) + ")";
    }

    static /* synthetic */ String lambda$internalWriteCharacteristic$57(BluetoothGattCharacteristic characteristic, int writeType) {
        return "Writing characteristic " + characteristic.getUuid() + " (" + ParserUtils.writeTypeToString(writeType) + ")";
    }

    static /* synthetic */ String lambda$internalWriteCharacteristic$58(byte[] data) {
        return "characteristic.setValue(" + ParserUtils.parseDebug(data) + ")";
    }

    static /* synthetic */ String lambda$internalWriteCharacteristic$59(int writeType) {
        return "characteristic.setWriteType(" + ParserUtils.writeTypeToString(writeType) + ")";
    }

    static /* synthetic */ String lambda$internalWriteCharacteristic$60(BluetoothGattCharacteristic characteristic) {
        return "gatt.writeCharacteristic(" + characteristic.getUuid() + ")";
    }

    private boolean internalReadDescriptor(final BluetoothGattDescriptor descriptor) {
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || descriptor == null || !this.connected) {
            return false;
        }
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$TJ0fGBtOe3zcd7tOgdOxRZ7z2MM
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalReadDescriptor$61(descriptor);
            }
        });
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$_O_rWkTZro5CuRlrL5MIdOcnLVk
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalReadDescriptor$62(descriptor);
            }
        });
        return gatt.readDescriptor(descriptor);
    }

    static /* synthetic */ String lambda$internalReadDescriptor$61(BluetoothGattDescriptor descriptor) {
        return "Reading descriptor " + descriptor.getUuid();
    }

    static /* synthetic */ String lambda$internalReadDescriptor$62(BluetoothGattDescriptor descriptor) {
        return "gatt.readDescriptor(" + descriptor.getUuid() + ")";
    }

    private boolean internalWriteDescriptor(final BluetoothGattDescriptor descriptor, final byte[] data) {
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || descriptor == null || !this.connected) {
            return false;
        }
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$QsyylVeiB4PMy-41xoI4qFlNYnM
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalWriteDescriptor$63(descriptor);
            }
        });
        if (Build.VERSION.SDK_INT >= 33) {
            log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$85DKBxRTYURsQ5leX9mdGSph0qI
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalWriteDescriptor$64(descriptor, data);
                }
            });
            return gatt.writeDescriptor(descriptor, data) == 0;
        }
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$lCwZTc-1CyDuNHbx_t4sXizTzD0
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalWriteDescriptor$65(descriptor);
            }
        });
        descriptor.setValue(data);
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$J9A0QC-lmqA9zPmXwoFXXdFDg0o
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalWriteDescriptor$66(descriptor);
            }
        });
        if (Build.VERSION.SDK_INT >= 24) {
            return internalWriteDescriptorWorkaround(descriptor);
        }
        return gatt.writeDescriptor(descriptor);
    }

    static /* synthetic */ String lambda$internalWriteDescriptor$63(BluetoothGattDescriptor descriptor) {
        return "Writing descriptor " + descriptor.getUuid();
    }

    static /* synthetic */ String lambda$internalWriteDescriptor$64(BluetoothGattDescriptor descriptor, byte[] data) {
        return "gatt.writeDescriptor(" + descriptor.getUuid() + ", value=" + ParserUtils.parseDebug(data) + ")";
    }

    static /* synthetic */ String lambda$internalWriteDescriptor$65(BluetoothGattDescriptor descriptor) {
        return "descriptor.setValue(" + descriptor.getUuid() + ")";
    }

    static /* synthetic */ String lambda$internalWriteDescriptor$66(BluetoothGattDescriptor descriptor) {
        return "gatt.writeDescriptor(" + descriptor.getUuid() + ")";
    }

    private boolean internalWriteDescriptorWorkaround(BluetoothGattDescriptor descriptor) {
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || descriptor == null || !this.connected) {
            return false;
        }
        BluetoothGattCharacteristic parentCharacteristic = descriptor.getCharacteristic();
        int originalWriteType = parentCharacteristic.getWriteType();
        parentCharacteristic.setWriteType(2);
        boolean result = gatt.writeDescriptor(descriptor);
        parentCharacteristic.setWriteType(originalWriteType);
        return result;
    }

    private boolean internalBeginReliableWrite() {
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || !this.connected) {
            return false;
        }
        if (this.reliableWriteInProgress) {
            return true;
        }
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$r6reaPsgYAaaIooGSgl6Huy15U0
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalBeginReliableWrite$67();
            }
        });
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$GM3QRtr4VTP3aBXJ7tn7dkZfhAE
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalBeginReliableWrite$68();
            }
        });
        boolean zBeginReliableWrite = gatt.beginReliableWrite();
        this.reliableWriteInProgress = zBeginReliableWrite;
        return zBeginReliableWrite;
    }

    static /* synthetic */ String lambda$internalBeginReliableWrite$67() {
        return "Beginning reliable write...";
    }

    static /* synthetic */ String lambda$internalBeginReliableWrite$68() {
        return "gatt.beginReliableWrite()";
    }

    private boolean internalExecuteReliableWrite() {
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || !this.connected || !this.reliableWriteInProgress) {
            return false;
        }
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$UH3Yn8r_cBDbnpMEhAwkEsX0eRo
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalExecuteReliableWrite$69();
            }
        });
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$zPVd36lIRVzv3Wf_-g3YgyZFF28
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalExecuteReliableWrite$70();
            }
        });
        return gatt.executeReliableWrite();
    }

    static /* synthetic */ String lambda$internalExecuteReliableWrite$69() {
        return "Executing reliable write...";
    }

    static /* synthetic */ String lambda$internalExecuteReliableWrite$70() {
        return "gatt.executeReliableWrite()";
    }

    private boolean internalAbortReliableWrite() {
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || !this.connected || !this.reliableWriteInProgress) {
            return false;
        }
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$NGbg5d60p6SWjrlePECRNUyE-hg
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalAbortReliableWrite$71();
            }
        });
        if (Build.VERSION.SDK_INT >= 19) {
            log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$mibaIVhaftFs3iJQL4IZu-Eib94
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalAbortReliableWrite$72();
                }
            });
            gatt.abortReliableWrite();
            return true;
        }
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$4ZED49xHlOMqlLgqjVUVEWYrZTM
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalAbortReliableWrite$73();
            }
        });
        gatt.abortReliableWrite(gatt.getDevice());
        return true;
    }

    static /* synthetic */ String lambda$internalAbortReliableWrite$71() {
        return "Aborting reliable write...";
    }

    static /* synthetic */ String lambda$internalAbortReliableWrite$72() {
        return "gatt.abortReliableWrite()";
    }

    static /* synthetic */ String lambda$internalAbortReliableWrite$73() {
        return "gatt.abortReliableWrite(device)";
    }

    @Deprecated
    private boolean internalReadBatteryLevel() {
        BluetoothGattService batteryService;
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || !this.connected || (batteryService = gatt.getService(BleManager.BATTERY_SERVICE)) == null) {
            return false;
        }
        BluetoothGattCharacteristic batteryLevelCharacteristic = batteryService.getCharacteristic(BleManager.BATTERY_LEVEL_CHARACTERISTIC);
        return internalReadCharacteristic(batteryLevelCharacteristic);
    }

    @Deprecated
    private boolean internalSetBatteryNotifications(boolean enable) {
        BluetoothGattService batteryService;
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || !this.connected || (batteryService = gatt.getService(BleManager.BATTERY_SERVICE)) == null) {
            return false;
        }
        BluetoothGattCharacteristic batteryLevelCharacteristic = batteryService.getCharacteristic(BleManager.BATTERY_LEVEL_CHARACTERISTIC);
        if (enable) {
            return internalEnableNotifications(batteryLevelCharacteristic);
        }
        return internalDisableNotifications(batteryLevelCharacteristic);
    }

    private boolean internalRequestMtu(final int mtu) {
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || !this.connected) {
            return false;
        }
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$V3YvhOy3UwLekpuH2ybfsk6M670
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalRequestMtu$74();
            }
        });
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$t2O6lwHH2W8iZ2gDnZVmqvCKWgI
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalRequestMtu$75(mtu);
            }
        });
        return gatt.requestMtu(mtu);
    }

    static /* synthetic */ String lambda$internalRequestMtu$74() {
        return "Requesting new MTU...";
    }

    static /* synthetic */ String lambda$internalRequestMtu$75(int mtu) {
        return "gatt.requestMtu(" + mtu + ")";
    }

    private boolean internalRequestConnectionPriority(final int priority) {
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || !this.connected) {
            return false;
        }
        final int supervisionTimeout = Build.VERSION.SDK_INT >= 26 ? 5 : 20;
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$O21JaKWZ2hbqmO3E4r6iyIDgq9k
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalRequestConnectionPriority$76(priority, supervisionTimeout);
            }
        });
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$u5F_QQKtjuy7pNVxRsJxtn9pe0E
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalRequestConnectionPriority$77(priority);
            }
        });
        return gatt.requestConnectionPriority(priority);
    }

    static /* synthetic */ String lambda$internalRequestConnectionPriority$76(int priority, int supervisionTimeout) {
        String text;
        switch (priority) {
            case 1:
                if (Build.VERSION.SDK_INT >= 23) {
                    text = "HIGH (11.25–15ms, 0, " + supervisionTimeout + "s)";
                    break;
                } else {
                    text = "HIGH (7.5–10ms, 0, " + supervisionTimeout + "s)";
                    break;
                }
            case 2:
                text = "LOW POWER (100–125ms, 2, " + supervisionTimeout + "s)";
                break;
            default:
                text = "BALANCED (30–50ms, 0, " + supervisionTimeout + "s)";
                break;
        }
        return "Requesting connection priority: " + text + "...";
    }

    static /* synthetic */ String lambda$internalRequestConnectionPriority$77(int priority) {
        String text;
        switch (priority) {
            case 1:
                text = "HIGH";
                break;
            case 2:
                text = "LOW POWER";
                break;
            default:
                text = "BALANCED";
                break;
        }
        return "gatt.requestConnectionPriority(" + text + ")";
    }

    private boolean internalSetPreferredPhy(final int txPhy, final int rxPhy, final int phyOptions) {
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || !this.connected) {
            return false;
        }
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$7v048rJwk8KXDSphq--UDUdBxqU
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalSetPreferredPhy$78();
            }
        });
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$Kw-Pt4LQ6XZpbP0JDFFiAyefxY0
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalSetPreferredPhy$79(txPhy, rxPhy, phyOptions);
            }
        });
        gatt.setPreferredPhy(txPhy, rxPhy, phyOptions);
        return true;
    }

    static /* synthetic */ String lambda$internalSetPreferredPhy$78() {
        return "Requesting preferred PHYs...";
    }

    static /* synthetic */ String lambda$internalSetPreferredPhy$79(int txPhy, int rxPhy, int phyOptions) {
        return "gatt.setPreferredPhy(" + ParserUtils.phyMaskToString(txPhy) + ", " + ParserUtils.phyMaskToString(rxPhy) + ", coding option = " + ParserUtils.phyCodedOptionToString(phyOptions) + ")";
    }

    private boolean internalReadPhy() {
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || !this.connected) {
            return false;
        }
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$uhtvAEaqOiilmEi5idKMak9_GdY
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalReadPhy$80();
            }
        });
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$KBco4uHU-0kvbzddEN_TBHfXSvI
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalReadPhy$81();
            }
        });
        gatt.readPhy();
        return true;
    }

    static /* synthetic */ String lambda$internalReadPhy$80() {
        return "Reading PHY...";
    }

    static /* synthetic */ String lambda$internalReadPhy$81() {
        return "gatt.readPhy()";
    }

    private boolean internalReadRssi() {
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null || !this.connected) {
            return false;
        }
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$KQM2VVLb6V-NfAKYBHxqqWDTZNA
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalReadRssi$82();
            }
        });
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$SlcSPJVWKmyWisn1tEeYincHWMg
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalReadRssi$83();
            }
        });
        return gatt.readRemoteRssi();
    }

    static /* synthetic */ String lambda$internalReadRssi$82() {
        return "Reading remote RSSI...";
    }

    static /* synthetic */ String lambda$internalReadRssi$83() {
        return "gatt.readRemoteRssi()";
    }

    ValueChangedCallback getValueChangedCallback(Object attribute) {
        ValueChangedCallback callback = this.valueChangedCallbacks.get(attribute);
        if (callback == null) {
            callback = new ValueChangedCallback(this);
            if (attribute != null) {
                this.valueChangedCallbacks.put(attribute, callback);
            }
        } else if (this.bluetoothDevice != null) {
            callback.notifyClosed();
        }
        return callback;
    }

    void removeValueChangedCallback(Object attribute) {
        ValueChangedCallback callback = this.valueChangedCallbacks.remove(attribute);
        if (callback != null) {
            callback.notifyClosed();
        }
    }

    void setCharacteristicValue(BluetoothGattCharacteristic serverCharacteristic, DataProvider dataProvider) {
        if (serverCharacteristic == null) {
            return;
        }
        if (dataProvider == null) {
            this.dataProviders.remove(serverCharacteristic);
        } else {
            this.dataProviders.put(serverCharacteristic, dataProvider);
        }
    }

    void setDescriptorValue(BluetoothGattDescriptor serverDescriptor, DataProvider dataProvider) {
        if (serverDescriptor == null) {
            return;
        }
        if (dataProvider == null) {
            this.dataProviders.remove(serverDescriptor);
        } else {
            this.dataProviders.put(serverDescriptor, dataProvider);
        }
    }

    void setConnectionParametersListener(ConnectionParametersUpdatedCallback callback) {
        BluetoothDevice bluetoothDevice;
        int i;
        this.connectionParametersUpdatedCallback = callback;
        if (callback != null && (bluetoothDevice = this.bluetoothDevice) != null && (i = this.interval) > 0) {
            callback.onConnectionUpdated(bluetoothDevice, i, this.latency, this.timeout);
        }
    }

    @Deprecated
    DataReceivedCallback getBatteryLevelCallback() {
        return new DataReceivedCallback() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$HEkHjr858fKT4LVgKzC7guXdXAs
            @Override // no.nordicsemi.android.ble.callback.DataReceivedCallback
            public final void onDataReceived(BluetoothDevice bluetoothDevice, Data data) {
                this.f$0.lambda$getBatteryLevelCallback$86$BleManagerHandler(bluetoothDevice, data);
            }
        };
    }

    public /* synthetic */ void lambda$getBatteryLevelCallback$86$BleManagerHandler(final BluetoothDevice device, Data data) {
        if (data.size() == 1) {
            final int batteryLevel = data.getIntValue(17, 0).intValue();
            log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$ayWGZlZpZc9pytxTK35Hdh8Bs08
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$getBatteryLevelCallback$84(batteryLevel);
                }
            });
            this.batteryValue = batteryLevel;
            onBatteryValueReceived(this.bluetoothGatt, batteryLevel);
            postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$Ijx0ewSslpBoLAllyhluDR7MZ74
                @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                public final void run(BleManagerCallbacks bleManagerCallbacks) {
                    bleManagerCallbacks.onBatteryValueReceived(device, batteryLevel);
                }
            });
        }
    }

    static /* synthetic */ String lambda$getBatteryLevelCallback$84(int batteryLevel) {
        return "Battery Level received: " + batteryLevel + "%";
    }

    @Deprecated
    void setBatteryLevelNotificationCallback() {
        if (this.batteryLevelNotificationCallback == null) {
            this.batteryLevelNotificationCallback = new ValueChangedCallback(this).with(new DataReceivedCallback() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$X7FlHpsmPGBYVH3Q1ZmMxa50ypA
                @Override // no.nordicsemi.android.ble.callback.DataReceivedCallback
                public final void onDataReceived(BluetoothDevice bluetoothDevice, Data data) {
                    this.f$0.lambda$setBatteryLevelNotificationCallback$88$BleManagerHandler(bluetoothDevice, data);
                }
            });
        }
    }

    public /* synthetic */ void lambda$setBatteryLevelNotificationCallback$88$BleManagerHandler(final BluetoothDevice device, Data data) {
        if (data.size() == 1) {
            final int batteryLevel = data.getIntValue(17, 0).intValue();
            this.batteryValue = batteryLevel;
            onBatteryValueReceived(this.bluetoothGatt, batteryLevel);
            postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$4dlbMbvuoNB02RtrPWRx-e8OVn4
                @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                public final void run(BleManagerCallbacks bleManagerCallbacks) {
                    bleManagerCallbacks.onBatteryValueReceived(device, batteryLevel);
                }
            });
        }
    }

    private boolean internalRefreshDeviceCache() throws NoSuchMethodException, SecurityException {
        BluetoothGatt gatt = this.bluetoothGatt;
        if (gatt == null) {
            return false;
        }
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$LDYJS23G6nLc7rwWfyhHk_HLAt4
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalRefreshDeviceCache$89();
            }
        });
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$zn5Ppy06SJ1AA0suGz9vY_ixN_A
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$internalRefreshDeviceCache$90();
            }
        });
        try {
            Method refresh = gatt.getClass().getMethod("refresh", new Class[0]);
            return refresh.invoke(gatt, new Object[0]) == Boolean.TRUE;
        } catch (Exception e) {
            Log.w(TAG, "An exception occurred while refreshing device", e);
            log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$Ut9KCMTUMf9dtCm0OmThZQiEFsg
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$internalRefreshDeviceCache$91();
                }
            });
            return false;
        }
    }

    static /* synthetic */ String lambda$internalRefreshDeviceCache$89() {
        return "Refreshing device cache...";
    }

    static /* synthetic */ String lambda$internalRefreshDeviceCache$90() {
        return "gatt.refresh() (hidden)";
    }

    static /* synthetic */ String lambda$internalRefreshDeviceCache$91() {
        return "gatt.refresh() method not found";
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void enqueueFirst(Request request) {
        Deque<Request> queue;
        RequestQueue rq = this.requestQueue;
        if (rq == null) {
            if (!this.initialization || (queue = this.initQueue) == null) {
                queue = this.taskQueue;
            }
            queue.addFirst(request);
        } else {
            rq.addFirst(request);
        }
        request.enqueued = true;
        this.operationInProgress = false;
    }

    @Override // no.nordicsemi.android.ble.RequestHandler
    final void enqueue(Request request) {
        Deque<Request> queue;
        if (!request.enqueued) {
            if (!this.initialization || (queue = this.initQueue) == null) {
                queue = this.taskQueue;
            }
            queue.add(request);
            request.enqueued = true;
        }
        nextRequest(false);
    }

    @Override // no.nordicsemi.android.ble.RequestHandler
    final void cancelQueue() {
        this.taskQueue.clear();
        this.initQueue = null;
        this.initialization = false;
        BluetoothDevice device = this.bluetoothDevice;
        if (device == null) {
            return;
        }
        if (this.operationInProgress) {
            cancelCurrent();
        }
        ConnectRequest connectRequest = this.connectRequest;
        if (connectRequest != null) {
            connectRequest.notifyFail(device, -7);
            this.connectRequest = null;
            internalDisconnect(5);
        }
    }

    @Override // no.nordicsemi.android.ble.RequestHandler
    final void cancelCurrent() {
        BluetoothDevice device = this.bluetoothDevice;
        if (device == null) {
            return;
        }
        log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$TokRH1UM5JG0e0Emk7GRbtcRT0k
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$cancelCurrent$92();
            }
        });
        Request request = this.request;
        if (request instanceof TimeoutableRequest) {
            request.notifyFail(device, -7);
        }
        AwaitingRequest<?> awaitingRequest = this.awaitingRequest;
        if (awaitingRequest != null) {
            awaitingRequest.notifyFail(device, -7);
            this.awaitingRequest = null;
        }
        RequestQueue requestQueue = this.requestQueue;
        if (requestQueue instanceof ReliableWriteRequest) {
            requestQueue.cancelQueue();
        } else if (requestQueue != null) {
            requestQueue.notifyFail(device, -7);
            this.requestQueue = null;
        }
        Request request2 = this.request;
        nextRequest(request2 == null || request2.finished);
    }

    static /* synthetic */ String lambda$cancelCurrent$92() {
        return "Request cancelled";
    }

    @Override // no.nordicsemi.android.ble.RequestHandler
    final void onRequestTimeout(BluetoothDevice device, TimeoutableRequest tr) {
        if (tr instanceof SleepRequest) {
            tr.notifySuccess(device);
        } else {
            log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$7s50DKqfwAZ_JyE5ULbOy2UUNxY
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$onRequestTimeout$93();
                }
            });
        }
        Request request = this.request;
        if (request instanceof TimeoutableRequest) {
            request.notifyFail(device, -5);
        }
        AwaitingRequest<?> awaitingRequest = this.awaitingRequest;
        if (awaitingRequest != null) {
            awaitingRequest.notifyFail(device, -5);
            this.awaitingRequest = null;
        }
        tr.notifyFail(device, -5);
        if (tr.type == Request.Type.CONNECT) {
            this.connectRequest = null;
            internalDisconnect(10);
        } else if (tr.type == Request.Type.DISCONNECT) {
            close();
        } else {
            Request request2 = this.request;
            nextRequest(request2 == null || request2.finished);
        }
    }

    static /* synthetic */ String lambda$onRequestTimeout$93() {
        return "Request timed out";
    }

    @Override // no.nordicsemi.android.ble.CallbackHandler
    public void post(Runnable r) {
        this.handler.post(r);
    }

    @Override // no.nordicsemi.android.ble.CallbackHandler
    public void postDelayed(Runnable r, long delayMillis) {
        this.handler.postDelayed(r, delayMillis);
    }

    @Override // no.nordicsemi.android.ble.CallbackHandler
    public void removeCallbacks(Runnable r) {
        this.handler.removeCallbacks(r);
    }

    /* JADX INFO: Access modifiers changed from: private */
    @Deprecated
    public void postCallback(final CallbackRunnable r) {
        final BleManagerCallbacks callbacks = this.manager.callbacks;
        if (callbacks != null) {
            post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$zMV7b_cG3-ypaEvJ61_vbCMPoOA
                @Override // java.lang.Runnable
                public final void run() {
                    r.run(callbacks);
                }
            });
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void postBondingStateChange(final BondingObserverRunnable r) {
        final BondingObserver observer = this.manager.bondingObserver;
        if (observer != null) {
            post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$RUaqt6mvCsFlUNSgY7p0rPK5UNs
                @Override // java.lang.Runnable
                public final void run() {
                    r.run(observer);
                }
            });
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void postConnectionStateChange(final ConnectionObserverRunnable r) {
        final ConnectionObserver observer = this.manager.connectionObserver;
        if (observer != null) {
            post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$FueVNhj4THcxlGLJhamIhrTvenA
                @Override // java.lang.Runnable
                public final void run() {
                    r.run(observer);
                }
            });
        }
    }

    final int getConnectionState() {
        return this.connectionState;
    }

    final boolean isConnected() {
        return this.connected;
    }

    @Deprecated
    final int getBatteryValue() {
        return this.batteryValue;
    }

    final boolean isReady() {
        return this.ready;
    }

    final boolean isReliableWriteInProgress() {
        return this.reliableWriteInProgress;
    }

    final int getMtu() {
        return this.mtu;
    }

    final void overrideMtu(int mtu) {
        if (Build.VERSION.SDK_INT >= 21) {
            this.mtu = mtu;
        }
    }

    @Deprecated
    protected boolean isOptionalServiceSupported(BluetoothGatt gatt) {
        return false;
    }

    @Deprecated
    protected Deque<Request> initGatt(BluetoothGatt gatt) {
        return null;
    }

    @Deprecated
    protected void initialize() {
    }

    @Deprecated
    protected void onServerReady(BluetoothGattServer server) {
    }

    @Deprecated
    protected void onDeviceReady() {
    }

    @Deprecated
    protected void onManagerReady() {
    }

    @Deprecated
    protected void onDeviceDisconnected() {
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void notifyDeviceDisconnected(final BluetoothDevice device, final int status) {
        boolean wasConnected = this.connected;
        this.connected = false;
        this.ready = false;
        this.servicesDiscovered = false;
        this.serviceDiscoveryRequested = false;
        this.deviceNotSupported = false;
        this.mtu = 23;
        this.timeout = 0;
        this.latency = 0;
        this.interval = 0;
        this.connectionState = 0;
        checkCondition();
        if (!wasConnected) {
            log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$MUIrrJOGrUahwrCq_ZKSE-87YLI
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$notifyDeviceDisconnected$97();
                }
            });
            close();
            postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$0yjzBeg0UQup8IJyGssCqE3Un10
                @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                public final void run(BleManagerCallbacks bleManagerCallbacks) {
                    bleManagerCallbacks.onDeviceDisconnected(device);
                }
            });
            postConnectionStateChange(new ConnectionObserverRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$CBTzM95zfwAR7OjoKPVupIDIUys
                @Override // no.nordicsemi.android.ble.BleManagerHandler.ConnectionObserverRunnable
                public final void run(ConnectionObserver connectionObserver) {
                    connectionObserver.onDeviceFailedToConnect(device, status);
                }
            });
        } else if (this.userDisconnected) {
            log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$6qRzxhDY-F5Xq0YN-i8vQR4r0TM
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$notifyDeviceDisconnected$100();
                }
            });
            Request request = this.request;
            if (request == null || request.type != Request.Type.REMOVE_BOND) {
                close();
            }
            postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$8FQuAvyr3EI0cdEXVpHL6WxqD3M
                @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                public final void run(BleManagerCallbacks bleManagerCallbacks) {
                    bleManagerCallbacks.onDeviceDisconnected(device);
                }
            });
            postConnectionStateChange(new ConnectionObserverRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$jiECyiQosznBqyw6NpHG5xRZ1HI
                @Override // no.nordicsemi.android.ble.BleManagerHandler.ConnectionObserverRunnable
                public final void run(ConnectionObserver connectionObserver) {
                    connectionObserver.onDeviceDisconnected(device, status);
                }
            });
            if (request != null && request.type == Request.Type.DISCONNECT) {
                request.notifySuccess(device);
                this.request = null;
            }
        } else {
            log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$O5o7wM_MdtmHLAMBtdozO4fpmoc
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$notifyDeviceDisconnected$103();
                }
            });
            postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$-ku0KyfiBuFmqLff4R5e7_o1FJw
                @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                public final void run(BleManagerCallbacks bleManagerCallbacks) {
                    bleManagerCallbacks.onLinkLossOccurred(device);
                }
            });
            final int reason = status != 2 ? 3 : 2;
            postConnectionStateChange(new ConnectionObserverRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$M6YWlLdqclfccT0m1zGPFcnjC6s
                @Override // no.nordicsemi.android.ble.BleManagerHandler.ConnectionObserverRunnable
                public final void run(ConnectionObserver connectionObserver) {
                    connectionObserver.onDeviceDisconnected(device, reason);
                }
            });
        }
        for (ValueChangedCallback callback : this.valueChangedCallbacks.values()) {
            callback.notifyClosed();
        }
        this.valueChangedCallbacks.clear();
        this.dataProviders.clear();
        this.batteryLevelNotificationCallback = null;
        this.batteryValue = -1;
        this.manager.onServicesInvalidated();
        onDeviceDisconnected();
    }

    static /* synthetic */ String lambda$notifyDeviceDisconnected$97() {
        return "Connection attempt timed out";
    }

    static /* synthetic */ String lambda$notifyDeviceDisconnected$100() {
        return "Disconnected";
    }

    static /* synthetic */ String lambda$notifyDeviceDisconnected$103() {
        return "Connection lost";
    }

    @Deprecated
    protected void onCharacteristicRead(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic) {
    }

    @Deprecated
    protected void onCharacteristicWrite(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic) {
    }

    @Deprecated
    protected void onDescriptorRead(BluetoothGatt gatt, BluetoothGattDescriptor descriptor) {
    }

    @Deprecated
    protected void onDescriptorWrite(BluetoothGatt gatt, BluetoothGattDescriptor descriptor) {
    }

    @Deprecated
    protected void onBatteryValueReceived(BluetoothGatt gatt, int value) {
    }

    @Deprecated
    protected void onCharacteristicNotified(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic) {
    }

    @Deprecated
    protected void onCharacteristicIndicated(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic) {
    }

    @Deprecated
    protected void onMtuChanged(BluetoothGatt gatt, int mtu) {
    }

    @Deprecated
    protected void onConnectionUpdated(BluetoothGatt gatt, int interval, int latency, int timeout) {
    }

    static /* synthetic */ String lambda$onError$106(int errorCode) {
        return "Error (0x" + Integer.toHexString(errorCode) + "): " + GattError.parse(errorCode);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void onError(final BluetoothDevice device, final String message, final int errorCode) {
        log(6, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$naVr5XTpiSE6Ayg1Ixic8KCtMZU
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$onError$106(errorCode);
            }
        });
        postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$q_VQK_z3UQBuuq2toPOCl4eUtTM
            @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
            public final void run(BleManagerCallbacks bleManagerCallbacks) {
                bleManagerCallbacks.onError(device, message, errorCode);
            }
        });
    }

    /* renamed from: no.nordicsemi.android.ble.BleManagerHandler$3, reason: invalid class name */
    class AnonymousClass3 extends BluetoothGattCallback {
        AnonymousClass3() {
        }

        @Override // android.bluetooth.BluetoothGattCallback
        public void onConnectionStateChange(final BluetoothGatt gatt, final int status, final int newState) {
            int reason;
            BleManagerHandler.this.log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$14yjF-OdMXeVQNvcbG1feRz6prY
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.AnonymousClass3.lambda$onConnectionStateChange$0(status, newState);
                }
            });
            int iMapDisconnectStatusToReason = 4;
            if (status == 0 && newState == 2) {
                if (BleManagerHandler.this.bluetoothDevice != null) {
                    BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$utITHzJhDAFAHPYSbNI6n1q_FZ4
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.AnonymousClass3.lambda$onConnectionStateChange$2(gatt);
                        }
                    });
                    BleManagerHandler.this.connected = true;
                    BleManagerHandler.this.connectionTime = 0L;
                    BleManagerHandler.this.connectionState = 2;
                    BleManagerHandler.this.postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$ems8dJF4XnO4LG4HympIzmV7eV4
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                        public final void run(BleManagerCallbacks bleManagerCallbacks) {
                            bleManagerCallbacks.onDeviceConnected(gatt.getDevice());
                        }
                    });
                    BleManagerHandler.this.postConnectionStateChange(new ConnectionObserverRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$-ztT9CQ2NM9OWCZOrsPPbvtMYzM
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.ConnectionObserverRunnable
                        public final void run(ConnectionObserver connectionObserver) {
                            connectionObserver.onDeviceConnected(gatt.getDevice());
                        }
                    });
                    if (!BleManagerHandler.this.serviceDiscoveryRequested) {
                        boolean bonded = gatt.getDevice().getBondState() == 12;
                        final int delay = BleManagerHandler.this.manager.getServiceDiscoveryDelay(bonded);
                        if (delay > 0) {
                            BleManagerHandler.this.log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$bW7cF26d4hBYK0am9RymlExV3OI
                                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                                public final String log() {
                                    return BleManagerHandler.AnonymousClass3.lambda$onConnectionStateChange$5(delay);
                                }
                            });
                        }
                        final int connectionCount = BleManagerHandler.access$2304(BleManagerHandler.this);
                        BleManagerHandler.this.postDelayed(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$0q6uN9xUKr-oRAQXqx-ltuNcxiA
                            @Override // java.lang.Runnable
                            public final void run() {
                                this.f$0.lambda$onConnectionStateChange$8$BleManagerHandler$3(connectionCount, gatt);
                            }
                        }, delay);
                        return;
                    }
                    return;
                }
                Log.e(BleManagerHandler.TAG, "Device received notification after disconnection.");
                BleManagerHandler.this.log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$leEXQ4SQqkUIT4IFLPeDxTBIHY4
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onConnectionStateChange$1();
                    }
                });
                try {
                    gatt.close();
                    return;
                } catch (Throwable th) {
                    return;
                }
            }
            if (newState == 0) {
                long now = SystemClock.elapsedRealtime();
                boolean canTimeout = BleManagerHandler.this.connectionTime > 0;
                boolean timeout = canTimeout && now > BleManagerHandler.this.connectionTime + BleManagerHandler.CONNECTION_TIMEOUT_THRESHOLD;
                if (status != 0) {
                    BleManagerHandler.this.log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$hx-XLGkV-tyixqqG5Ihx03OA8P4
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.AnonymousClass3.lambda$onConnectionStateChange$9(status);
                        }
                    });
                }
                if (status == 0 || !canTimeout || timeout || BleManagerHandler.this.connectRequest == null || !BleManagerHandler.this.connectRequest.canRetry()) {
                    if (BleManagerHandler.this.connectRequest == null || !BleManagerHandler.this.connectRequest.shouldAutoConnect() || !BleManagerHandler.this.initialConnection || gatt.getDevice().getBondState() != 12) {
                        BleManagerHandler.this.operationInProgress = true;
                        BleManagerHandler.this.taskQueue.clear();
                        BleManagerHandler.this.initQueue = null;
                        BleManagerHandler.this.ready = false;
                        boolean wasConnected = BleManagerHandler.this.connected;
                        boolean notSupported = BleManagerHandler.this.deviceNotSupported;
                        BleManagerHandler bleManagerHandler = BleManagerHandler.this;
                        BluetoothDevice device = gatt.getDevice();
                        if (timeout) {
                            iMapDisconnectStatusToReason = 10;
                        } else if (!notSupported) {
                            iMapDisconnectStatusToReason = BleManagerHandler.this.mapDisconnectStatusToReason(status);
                        }
                        bleManagerHandler.notifyDeviceDisconnected(device, iMapDisconnectStatusToReason);
                        if (BleManagerHandler.this.request != null && BleManagerHandler.this.request.type != Request.Type.DISCONNECT && BleManagerHandler.this.request.type != Request.Type.REMOVE_BOND) {
                            BleManagerHandler.this.request.notifyFail(gatt.getDevice(), status == 0 ? -1 : status);
                            BleManagerHandler.this.request = null;
                        }
                        if (BleManagerHandler.this.awaitingRequest != null) {
                            BleManagerHandler.this.awaitingRequest.notifyFail(gatt.getDevice(), -1);
                            BleManagerHandler.this.awaitingRequest = null;
                        }
                        if (BleManagerHandler.this.connectRequest != null) {
                            if (notSupported) {
                                reason = -2;
                            } else if (status == 0) {
                                reason = -1;
                            } else if (status == 133 && timeout) {
                                reason = -5;
                            } else {
                                reason = status;
                            }
                            BleManagerHandler.this.connectRequest.notifyFail(gatt.getDevice(), reason);
                            BleManagerHandler.this.connectRequest = null;
                        }
                        BleManagerHandler.this.operationInProgress = false;
                        if (!wasConnected || !BleManagerHandler.this.initialConnection) {
                            BleManagerHandler.this.initialConnection = false;
                            BleManagerHandler.this.nextRequest(false);
                        } else {
                            BleManagerHandler.this.internalConnect(gatt.getDevice(), null);
                        }
                        if (wasConnected || status == 0) {
                            return;
                        }
                    } else {
                        BleManagerHandler.this.log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$hMc0r8uSDhijJmXtw_5hyMXgKaQ
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                            public final String log() {
                                return BleManagerHandler.AnonymousClass3.lambda$onConnectionStateChange$12();
                            }
                        });
                        BleManagerHandler.this.post(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$FXMJNUX3oxnUqSs9eFuzUn4OrZk
                            @Override // java.lang.Runnable
                            public final void run() {
                                this.f$0.lambda$onConnectionStateChange$13$BleManagerHandler$3(gatt);
                            }
                        });
                        return;
                    }
                } else {
                    final int delay2 = BleManagerHandler.this.connectRequest.getRetryDelay();
                    if (delay2 > 0) {
                        BleManagerHandler.this.log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$mxvi9xlqKwszNSbdXUYuOMJ0iFQ
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                            public final String log() {
                                return BleManagerHandler.AnonymousClass3.lambda$onConnectionStateChange$10(delay2);
                            }
                        });
                    }
                    BleManagerHandler.this.postDelayed(new Runnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$9ltLOSBq0E21CBikzqVOxPkaNrE
                        @Override // java.lang.Runnable
                        public final void run() {
                            this.f$0.lambda$onConnectionStateChange$11$BleManagerHandler$3(gatt);
                        }
                    }, delay2);
                    return;
                }
            } else if (status != 0) {
                BleManagerHandler.this.log(6, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$OC4QYoqI2dkmqnYv-mTt1S4IQoY
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onConnectionStateChange$14(status);
                    }
                });
            }
            BleManagerHandler.this.postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$rHVsUTzAhB4AZHiTLkDG1i4aGBY
                @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                public final void run(BleManagerCallbacks bleManagerCallbacks) {
                    bleManagerCallbacks.onError(gatt.getDevice(), BleManagerHandler.ERROR_CONNECTION_STATE_CHANGE, status);
                }
            });
        }

        static /* synthetic */ String lambda$onConnectionStateChange$0(int status, int newState) {
            return "[Callback] Connection state changed with status: " + status + " and new state: " + newState + " (" + ParserUtils.stateToString(newState) + ")";
        }

        static /* synthetic */ String lambda$onConnectionStateChange$1() {
            return "gatt.close()";
        }

        static /* synthetic */ String lambda$onConnectionStateChange$2(BluetoothGatt gatt) {
            return "Connected to " + gatt.getDevice().getAddress();
        }

        static /* synthetic */ String lambda$onConnectionStateChange$5(int delay) {
            return "wait(" + delay + ")";
        }

        public /* synthetic */ void lambda$onConnectionStateChange$8$BleManagerHandler$3(int connectionCount, BluetoothGatt gatt) {
            if (connectionCount == BleManagerHandler.this.connectionCount && BleManagerHandler.this.connected && !BleManagerHandler.this.servicesDiscovered && !BleManagerHandler.this.serviceDiscoveryRequested && gatt.getDevice().getBondState() != 11) {
                BleManagerHandler.this.serviceDiscoveryRequested = true;
                BleManagerHandler.this.log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$OClTyk3LGYIXJ9TSJWLXnJP-b2E
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onConnectionStateChange$6();
                    }
                });
                BleManagerHandler.this.log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$w1Mp6J6Wy6gnecnzhJ3OrhNkd1w
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onConnectionStateChange$7();
                    }
                });
                gatt.discoverServices();
            }
        }

        static /* synthetic */ String lambda$onConnectionStateChange$6() {
            return "Discovering services...";
        }

        static /* synthetic */ String lambda$onConnectionStateChange$7() {
            return "gatt.discoverServices()";
        }

        static /* synthetic */ String lambda$onConnectionStateChange$9(int status) {
            return "Error: (0x" + Integer.toHexString(status) + "): " + GattError.parseConnectionError(status);
        }

        static /* synthetic */ String lambda$onConnectionStateChange$10(int delay) {
            return "wait(" + delay + ")";
        }

        public /* synthetic */ void lambda$onConnectionStateChange$11$BleManagerHandler$3(BluetoothGatt gatt) {
            BleManagerHandler.this.internalConnect(gatt.getDevice(), BleManagerHandler.this.connectRequest);
        }

        static /* synthetic */ String lambda$onConnectionStateChange$12() {
            return "autoConnect = false called failed; retrying with autoConnect = true";
        }

        public /* synthetic */ void lambda$onConnectionStateChange$13$BleManagerHandler$3(BluetoothGatt gatt) {
            BleManagerHandler.this.internalConnect(gatt.getDevice(), BleManagerHandler.this.connectRequest);
        }

        static /* synthetic */ String lambda$onConnectionStateChange$14(int status) {
            return "Error (0x" + Integer.toHexString(status) + "): " + GattError.parseConnectionError(status);
        }

        @Override // android.bluetooth.BluetoothGattCallback
        public void onServicesDiscovered(final BluetoothGatt gatt, int status) {
            if (BleManagerHandler.this.serviceDiscoveryRequested) {
                BleManagerHandler.this.serviceDiscoveryRequested = false;
                if (status == 0) {
                    BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$NoL7HY2UHYt6hYt7JD8CE-gEJxc
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.AnonymousClass3.lambda$onServicesDiscovered$16();
                        }
                    });
                    BleManagerHandler.this.servicesDiscovered = true;
                    if (BleManagerHandler.this.manager.isRequiredServiceSupported(gatt)) {
                        BleManagerHandler.this.log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$sFWJvPX_DlKzmxkX6KbbVMWk9A4
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                            public final String log() {
                                return BleManagerHandler.AnonymousClass3.lambda$onServicesDiscovered$17();
                            }
                        });
                        BleManagerHandler.this.deviceNotSupported = false;
                        final boolean optionalServicesFound = BleManagerHandler.this.manager.isOptionalServiceSupported(gatt);
                        if (optionalServicesFound) {
                            BleManagerHandler.this.log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$ygz91eJWj4hUnzn209_YrFKOFek
                                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                                public final String log() {
                                    return BleManagerHandler.AnonymousClass3.lambda$onServicesDiscovered$18();
                                }
                            });
                        }
                        BleManagerHandler.this.postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$PYh5Q-FvZD3_-b28lgOiEoITVLw
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                            public final void run(BleManagerCallbacks bleManagerCallbacks) {
                                bleManagerCallbacks.onServicesDiscovered(gatt.getDevice(), optionalServicesFound);
                            }
                        });
                        BleManagerHandler.this.initializeServerAttributes();
                        BleManagerHandler.this.operationInProgress = true;
                        BleManagerHandler.this.initialization = true;
                        BleManagerHandler bleManagerHandler = BleManagerHandler.this;
                        bleManagerHandler.initQueue = bleManagerHandler.initGatt(gatt);
                        boolean deprecatedApiUsed = BleManagerHandler.this.initQueue != null;
                        if (deprecatedApiUsed) {
                            for (Request request : BleManagerHandler.this.initQueue) {
                                request.setRequestHandler(BleManagerHandler.this);
                                request.enqueued = true;
                            }
                        }
                        if (BleManagerHandler.this.initQueue == null) {
                            BleManagerHandler.this.initQueue = new LinkedBlockingDeque();
                        }
                        if (Build.VERSION.SDK_INT < 23 || Build.VERSION.SDK_INT == 26 || Build.VERSION.SDK_INT == 27 || Build.VERSION.SDK_INT == 28) {
                            BleManagerHandler.this.enqueueFirst(Request.newEnableServiceChangedIndicationsRequest().setRequestHandler((RequestHandler) BleManagerHandler.this));
                            BleManagerHandler.this.operationInProgress = true;
                        }
                        if (deprecatedApiUsed) {
                            BleManagerHandler.this.manager.readBatteryLevel();
                            if (BleManagerHandler.this.manager.callbacks != null && BleManagerHandler.this.manager.callbacks.shouldEnableBatteryLevelNotifications(gatt.getDevice())) {
                                BleManagerHandler.this.manager.enableBatteryLevelNotifications();
                            }
                        }
                        BleManagerHandler.this.manager.initialize();
                        BleManagerHandler.this.initialization = false;
                        BleManagerHandler.this.nextRequest(true);
                        return;
                    }
                    BleManagerHandler.this.log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$IZeMV9oZw4y6i5pzHk051odYhQU
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.AnonymousClass3.lambda$onServicesDiscovered$20();
                        }
                    });
                    BleManagerHandler.this.deviceNotSupported = true;
                    BleManagerHandler.this.postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$vh1t4ybi95ImRREYqS7g7VqBvZM
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                        public final void run(BleManagerCallbacks bleManagerCallbacks) {
                            bleManagerCallbacks.onDeviceNotSupported(gatt.getDevice());
                        }
                    });
                    BleManagerHandler.this.internalDisconnect(4);
                    return;
                }
                Log.e(BleManagerHandler.TAG, "onServicesDiscovered error " + status);
                BleManagerHandler.this.onError(gatt.getDevice(), BleManagerHandler.ERROR_DISCOVERY_SERVICE, status);
                if (BleManagerHandler.this.connectRequest != null) {
                    BleManagerHandler.this.connectRequest.notifyFail(gatt.getDevice(), -4);
                    BleManagerHandler.this.connectRequest = null;
                }
                BleManagerHandler.this.internalDisconnect(-1);
            }
        }

        static /* synthetic */ String lambda$onServicesDiscovered$16() {
            return "Services discovered";
        }

        static /* synthetic */ String lambda$onServicesDiscovered$17() {
            return "Primary service found";
        }

        static /* synthetic */ String lambda$onServicesDiscovered$18() {
            return "Secondary service found";
        }

        static /* synthetic */ String lambda$onServicesDiscovered$20() {
            return "Device is not supported";
        }

        static /* synthetic */ String lambda$onServiceChanged$22() {
            return "Service changed, invalidating services";
        }

        @Override // android.bluetooth.BluetoothGattCallback
        public void onServiceChanged(BluetoothGatt gatt) {
            BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$1sQYd5oyo2woYujW8tkOIXlF_D4
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.AnonymousClass3.lambda$onServiceChanged$22();
                }
            });
            BleManagerHandler.this.operationInProgress = true;
            BleManagerHandler.this.manager.onServicesInvalidated();
            BleManagerHandler.this.onDeviceDisconnected();
            BleManagerHandler.this.taskQueue.clear();
            BleManagerHandler.this.initQueue = null;
            BleManagerHandler.this.serviceDiscoveryRequested = true;
            BleManagerHandler.this.servicesDiscovered = false;
            BleManagerHandler.this.log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$tD46z4bCSJD1railD5WJu2W-5o4
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.AnonymousClass3.lambda$onServiceChanged$23();
                }
            });
            BleManagerHandler.this.log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$e7m2kNoYDerdaKtTpflfL5QMMYs
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.AnonymousClass3.lambda$onServiceChanged$24();
                }
            });
            gatt.discoverServices();
        }

        static /* synthetic */ String lambda$onServiceChanged$23() {
            return "Discovering Services...";
        }

        static /* synthetic */ String lambda$onServiceChanged$24() {
            return "gatt.discoverServices()";
        }

        @Override // android.bluetooth.BluetoothGattCallback
        public void onCharacteristicRead(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic, int status) {
            onCharacteristicRead(gatt, characteristic, characteristic.getValue(), status);
        }

        @Override // android.bluetooth.BluetoothGattCallback
        public void onCharacteristicRead(final BluetoothGatt gatt, final BluetoothGattCharacteristic characteristic, final byte[] data, final int status) {
            if (status == 0) {
                BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$kSHuPFWZYnQeprjsBjIRuPluWmg
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onCharacteristicRead$25(characteristic, data);
                    }
                });
                BleManagerHandler.this.onCharacteristicRead(gatt, characteristic);
                if (BleManagerHandler.this.request instanceof ReadRequest) {
                    ReadRequest rr = (ReadRequest) BleManagerHandler.this.request;
                    boolean matches = rr.matches(data);
                    if (matches) {
                        rr.notifyValueChanged(gatt.getDevice(), data);
                    }
                    if (!matches || rr.hasMore()) {
                        BleManagerHandler.this.enqueueFirst(rr);
                    } else {
                        rr.notifySuccess(gatt.getDevice());
                    }
                }
            } else {
                if (status == 5 || status == 8 || status == 137) {
                    BleManagerHandler.this.log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$SW_5XBOR57Y6O49MdPfDWJWZ3lA
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.AnonymousClass3.lambda$onCharacteristicRead$26(status);
                        }
                    });
                    if (gatt.getDevice().getBondState() != 10) {
                        Log.w(BleManagerHandler.TAG, BleManagerHandler.ERROR_AUTH_ERROR_WHILE_BONDED);
                        BleManagerHandler.this.postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$WYkSZHe-6XjJvR_UJ9kg1zgdj34
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                            public final void run(BleManagerCallbacks bleManagerCallbacks) {
                                bleManagerCallbacks.onError(gatt.getDevice(), BleManagerHandler.ERROR_AUTH_ERROR_WHILE_BONDED, status);
                            }
                        });
                        return;
                    }
                    return;
                }
                Log.e(BleManagerHandler.TAG, "onCharacteristicRead error " + status);
                if (BleManagerHandler.this.request instanceof ReadRequest) {
                    BleManagerHandler.this.request.notifyFail(gatt.getDevice(), status);
                }
                BleManagerHandler.this.awaitingRequest = null;
                BleManagerHandler.this.onError(gatt.getDevice(), BleManagerHandler.ERROR_READ_CHARACTERISTIC, status);
            }
            BleManagerHandler.this.checkCondition();
            BleManagerHandler.this.nextRequest(true);
        }

        static /* synthetic */ String lambda$onCharacteristicRead$25(BluetoothGattCharacteristic characteristic, byte[] data) {
            return "Read Response received from " + characteristic.getUuid() + ", value: " + ParserUtils.parse(data);
        }

        static /* synthetic */ String lambda$onCharacteristicRead$26(int status) {
            return "Authentication required (" + status + ")";
        }

        @Override // android.bluetooth.BluetoothGattCallback
        public void onCharacteristicWrite(final BluetoothGatt gatt, final BluetoothGattCharacteristic characteristic, final int status) {
            if (status == 0) {
                BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$h376l_RDTQPdTvzYBIVSYBRrjpI
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onCharacteristicWrite$28(characteristic);
                    }
                });
                BleManagerHandler.this.onCharacteristicWrite(gatt, characteristic);
                if (BleManagerHandler.this.request instanceof WriteRequest) {
                    WriteRequest wr = (WriteRequest) BleManagerHandler.this.request;
                    boolean valid = wr.notifyPacketSent(gatt.getDevice(), characteristic.getValue());
                    if (!valid && (BleManagerHandler.this.requestQueue instanceof ReliableWriteRequest)) {
                        wr.notifyFail(gatt.getDevice(), -6);
                        BleManagerHandler.this.requestQueue.cancelQueue();
                    } else if (wr.hasMore()) {
                        BleManagerHandler.this.enqueueFirst(wr);
                    } else {
                        wr.notifySuccess(gatt.getDevice());
                    }
                }
            } else {
                if (status == 5 || status == 8 || status == 137) {
                    BleManagerHandler.this.log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$eTKjRJ6VMRbdMuxfl5cgeWLOeiM
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.AnonymousClass3.lambda$onCharacteristicWrite$29(status);
                        }
                    });
                    if (gatt.getDevice().getBondState() != 10) {
                        Log.w(BleManagerHandler.TAG, BleManagerHandler.ERROR_AUTH_ERROR_WHILE_BONDED);
                        BleManagerHandler.this.postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$Hg1y4QHc1fnJWqEQX2ZdTzB2zk0
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                            public final void run(BleManagerCallbacks bleManagerCallbacks) {
                                bleManagerCallbacks.onError(gatt.getDevice(), BleManagerHandler.ERROR_AUTH_ERROR_WHILE_BONDED, status);
                            }
                        });
                        return;
                    }
                    return;
                }
                Log.e(BleManagerHandler.TAG, "onCharacteristicWrite error " + status);
                if (BleManagerHandler.this.request instanceof WriteRequest) {
                    BleManagerHandler.this.request.notifyFail(gatt.getDevice(), status);
                    if (BleManagerHandler.this.requestQueue instanceof ReliableWriteRequest) {
                        BleManagerHandler.this.requestQueue.cancelQueue();
                    }
                }
                BleManagerHandler.this.awaitingRequest = null;
                BleManagerHandler.this.onError(gatt.getDevice(), BleManagerHandler.ERROR_WRITE_CHARACTERISTIC, status);
            }
            BleManagerHandler.this.checkCondition();
            BleManagerHandler.this.nextRequest(true);
        }

        static /* synthetic */ String lambda$onCharacteristicWrite$28(BluetoothGattCharacteristic characteristic) {
            return "Data written to " + characteristic.getUuid();
        }

        static /* synthetic */ String lambda$onCharacteristicWrite$29(int status) {
            return "Authentication required (" + status + ")";
        }

        @Override // android.bluetooth.BluetoothGattCallback
        public void onReliableWriteCompleted(BluetoothGatt gatt, int status) {
            boolean execute = BleManagerHandler.this.request.type == Request.Type.EXECUTE_RELIABLE_WRITE;
            BleManagerHandler.this.reliableWriteInProgress = false;
            if (status == 0) {
                if (execute) {
                    BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$wDqc8fYBT6K8okLrZPu1LwFBU-Q
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.AnonymousClass3.lambda$onReliableWriteCompleted$31();
                        }
                    });
                    BleManagerHandler.this.request.notifySuccess(gatt.getDevice());
                } else {
                    BleManagerHandler.this.log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$6Mr23xPJ9Pyd7a0xJdtERs52WXg
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.AnonymousClass3.lambda$onReliableWriteCompleted$32();
                        }
                    });
                    BleManagerHandler.this.request.notifySuccess(gatt.getDevice());
                    BleManagerHandler.this.requestQueue.notifyFail(gatt.getDevice(), -4);
                }
            } else {
                Log.e(BleManagerHandler.TAG, "onReliableWriteCompleted execute " + execute + ", error " + status);
                BleManagerHandler.this.request.notifyFail(gatt.getDevice(), status);
                BleManagerHandler.this.onError(gatt.getDevice(), BleManagerHandler.ERROR_RELIABLE_WRITE, status);
            }
            BleManagerHandler.this.checkCondition();
            BleManagerHandler.this.nextRequest(true);
        }

        static /* synthetic */ String lambda$onReliableWriteCompleted$31() {
            return "Reliable Write executed";
        }

        static /* synthetic */ String lambda$onReliableWriteCompleted$32() {
            return "Reliable Write aborted";
        }

        @Override // android.bluetooth.BluetoothGattCallback
        public void onDescriptorRead(final BluetoothGatt gatt, final BluetoothGattDescriptor descriptor, final int status) {
            final byte[] data = descriptor.getValue();
            if (status == 0) {
                BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$FcYxFvDDnnrn42ARJyTd3L9V3lM
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onDescriptorRead$33(descriptor, data);
                    }
                });
                BleManagerHandler.this.onDescriptorRead(gatt, descriptor);
                if (BleManagerHandler.this.request instanceof ReadRequest) {
                    ReadRequest request = (ReadRequest) BleManagerHandler.this.request;
                    request.notifyValueChanged(gatt.getDevice(), data);
                    if (request.hasMore()) {
                        BleManagerHandler.this.enqueueFirst(request);
                    } else {
                        request.notifySuccess(gatt.getDevice());
                    }
                }
            } else {
                if (status == 5 || status == 8 || status == 137) {
                    BleManagerHandler.this.log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$Tcy9qHdP-YJi34NF2hV4NNN6XJU
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.AnonymousClass3.lambda$onDescriptorRead$34(status);
                        }
                    });
                    if (gatt.getDevice().getBondState() != 10) {
                        Log.w(BleManagerHandler.TAG, BleManagerHandler.ERROR_AUTH_ERROR_WHILE_BONDED);
                        BleManagerHandler.this.postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$_aw6pVZBa2SlTAUHjRWzNytw_o0
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                            public final void run(BleManagerCallbacks bleManagerCallbacks) {
                                bleManagerCallbacks.onError(gatt.getDevice(), BleManagerHandler.ERROR_AUTH_ERROR_WHILE_BONDED, status);
                            }
                        });
                        return;
                    }
                    return;
                }
                Log.e(BleManagerHandler.TAG, "onDescriptorRead error " + status);
                if (BleManagerHandler.this.request instanceof ReadRequest) {
                    BleManagerHandler.this.request.notifyFail(gatt.getDevice(), status);
                }
                BleManagerHandler.this.awaitingRequest = null;
                BleManagerHandler.this.onError(gatt.getDevice(), BleManagerHandler.ERROR_READ_DESCRIPTOR, status);
            }
            BleManagerHandler.this.checkCondition();
            BleManagerHandler.this.nextRequest(true);
        }

        static /* synthetic */ String lambda$onDescriptorRead$33(BluetoothGattDescriptor descriptor, byte[] data) {
            return "Read Response received from descr. " + descriptor.getUuid() + ", value: " + ParserUtils.parse(data);
        }

        static /* synthetic */ String lambda$onDescriptorRead$34(int status) {
            return "Authentication required (" + status + ")";
        }

        @Override // android.bluetooth.BluetoothGattCallback
        public void onDescriptorWrite(final BluetoothGatt gatt, final BluetoothGattDescriptor descriptor, final int status) {
            byte[] data = descriptor.getValue();
            if (status == 0) {
                BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$FfNNlBuwiUH1vTNhUduHMn7T04U
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onDescriptorWrite$36(descriptor);
                    }
                });
                if (BleManagerHandler.this.isServiceChangedCCCD(descriptor)) {
                    BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$e6xoWS3dtCiSmoOAamkk1Bo381M
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.AnonymousClass3.lambda$onDescriptorWrite$37();
                        }
                    });
                } else if (BleManagerHandler.this.isCCCD(descriptor)) {
                    if (data != null && data.length == 2 && data[1] == 0) {
                        switch (data[0]) {
                            case 0:
                                BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$F3L6iFOIon0fPbEIQEWuKKok_XM
                                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                                    public final String log() {
                                        return BleManagerHandler.AnonymousClass3.lambda$onDescriptorWrite$38();
                                    }
                                });
                                break;
                            case 1:
                                BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$lUEFOvzUzSmg66X-l92M0Zj8zWk
                                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                                    public final String log() {
                                        return BleManagerHandler.AnonymousClass3.lambda$onDescriptorWrite$39();
                                    }
                                });
                                break;
                            case 2:
                                BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$QeUAnIF6LxctwXaCXoxKTB6KHcU
                                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                                    public final String log() {
                                        return BleManagerHandler.AnonymousClass3.lambda$onDescriptorWrite$40();
                                    }
                                });
                                break;
                        }
                        BleManagerHandler.this.onDescriptorWrite(gatt, descriptor);
                    }
                } else {
                    BleManagerHandler.this.onDescriptorWrite(gatt, descriptor);
                }
                if (BleManagerHandler.this.request instanceof WriteRequest) {
                    WriteRequest wr = (WriteRequest) BleManagerHandler.this.request;
                    boolean valid = wr.notifyPacketSent(gatt.getDevice(), data);
                    if (!valid && (BleManagerHandler.this.requestQueue instanceof ReliableWriteRequest)) {
                        wr.notifyFail(gatt.getDevice(), -6);
                        BleManagerHandler.this.requestQueue.cancelQueue();
                    } else if (wr.hasMore()) {
                        BleManagerHandler.this.enqueueFirst(wr);
                    } else {
                        wr.notifySuccess(gatt.getDevice());
                    }
                }
            } else {
                if (status == 5 || status == 8 || status == 137) {
                    BleManagerHandler.this.log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$8rSJ7PKoFEB_n40DDatFmyXPgp4
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.AnonymousClass3.lambda$onDescriptorWrite$41(status);
                        }
                    });
                    if (gatt.getDevice().getBondState() != 10) {
                        Log.w(BleManagerHandler.TAG, BleManagerHandler.ERROR_AUTH_ERROR_WHILE_BONDED);
                        BleManagerHandler.this.postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$kWhU8F5ADX1uDm9yF8Xl3qF8qmo
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                            public final void run(BleManagerCallbacks bleManagerCallbacks) {
                                bleManagerCallbacks.onError(gatt.getDevice(), BleManagerHandler.ERROR_AUTH_ERROR_WHILE_BONDED, status);
                            }
                        });
                        return;
                    }
                    return;
                }
                Log.e(BleManagerHandler.TAG, "onDescriptorWrite error " + status);
                if (BleManagerHandler.this.request instanceof WriteRequest) {
                    BleManagerHandler.this.request.notifyFail(gatt.getDevice(), status);
                    if (BleManagerHandler.this.requestQueue instanceof ReliableWriteRequest) {
                        BleManagerHandler.this.requestQueue.cancelQueue();
                    }
                }
                BleManagerHandler.this.awaitingRequest = null;
                BleManagerHandler.this.onError(gatt.getDevice(), BleManagerHandler.ERROR_WRITE_DESCRIPTOR, status);
            }
            BleManagerHandler.this.checkCondition();
            BleManagerHandler.this.nextRequest(true);
        }

        static /* synthetic */ String lambda$onDescriptorWrite$36(BluetoothGattDescriptor descriptor) {
            return "Data written to descr. " + descriptor.getUuid();
        }

        static /* synthetic */ String lambda$onDescriptorWrite$37() {
            return "Service Changed notifications enabled";
        }

        static /* synthetic */ String lambda$onDescriptorWrite$38() {
            return "Notifications and indications disabled";
        }

        static /* synthetic */ String lambda$onDescriptorWrite$39() {
            return "Notifications enabled";
        }

        static /* synthetic */ String lambda$onDescriptorWrite$40() {
            return "Indications enabled";
        }

        static /* synthetic */ String lambda$onDescriptorWrite$41(int status) {
            return "Authentication required (" + status + ")";
        }

        @Override // android.bluetooth.BluetoothGattCallback
        public void onCharacteristicChanged(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic) {
            onCharacteristicChanged(gatt, characteristic, characteristic.getValue());
        }

        @Override // android.bluetooth.BluetoothGattCallback
        public void onCharacteristicChanged(BluetoothGatt gatt, final BluetoothGattCharacteristic characteristic, final byte[] data) {
            if (BleManagerHandler.this.isServiceChangedCharacteristic(characteristic)) {
                if (Build.VERSION.SDK_INT <= 30) {
                    BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$wtKQVgrsV3M_giAs-AYVyIIY-1I
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.AnonymousClass3.lambda$onCharacteristicChanged$43();
                        }
                    });
                    BleManagerHandler.this.operationInProgress = true;
                    BleManagerHandler.this.manager.onServicesInvalidated();
                    BleManagerHandler.this.onDeviceDisconnected();
                    BleManagerHandler.this.taskQueue.clear();
                    BleManagerHandler.this.initQueue = null;
                    BleManagerHandler.this.serviceDiscoveryRequested = true;
                    BleManagerHandler.this.log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$6pcLDGrZcoTyDmNHmcUB6TM9X3I
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.AnonymousClass3.lambda$onCharacteristicChanged$44();
                        }
                    });
                    BleManagerHandler.this.log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$abb3jr8aWIGQUEQxWxt2PREDyEE
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.AnonymousClass3.lambda$onCharacteristicChanged$45();
                        }
                    });
                    gatt.discoverServices();
                    return;
                }
                return;
            }
            BluetoothGattDescriptor cccd = characteristic.getDescriptor(BleManager.CLIENT_CHARACTERISTIC_CONFIG_DESCRIPTOR_UUID);
            boolean notifications = cccd == null || cccd.getValue() == null || cccd.getValue().length != 2 || cccd.getValue()[0] == 1;
            if (notifications) {
                BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$MYJxqAsXRw18IC6-ldwM5WIJ-cM
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onCharacteristicChanged$46(characteristic, data);
                    }
                });
                BleManagerHandler.this.onCharacteristicNotified(gatt, characteristic);
            } else {
                BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$ME8invUZEHw8GZ14qvaiPyIHWAg
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onCharacteristicChanged$47(characteristic, data);
                    }
                });
                BleManagerHandler.this.onCharacteristicIndicated(gatt, characteristic);
            }
            if (BleManagerHandler.this.batteryLevelNotificationCallback != null && BleManagerHandler.this.isBatteryLevelCharacteristic(characteristic)) {
                BleManagerHandler.this.batteryLevelNotificationCallback.notifyValueChanged(gatt.getDevice(), data);
            }
            ValueChangedCallback request = (ValueChangedCallback) BleManagerHandler.this.valueChangedCallbacks.get(characteristic);
            if (request != null && request.matches(data)) {
                request.notifyValueChanged(gatt.getDevice(), data);
            }
            if ((BleManagerHandler.this.awaitingRequest instanceof WaitForValueChangedRequest) && BleManagerHandler.this.awaitingRequest.characteristic == characteristic && !BleManagerHandler.this.awaitingRequest.isTriggerPending()) {
                WaitForValueChangedRequest valueChangedRequest = (WaitForValueChangedRequest) BleManagerHandler.this.awaitingRequest;
                if (valueChangedRequest.matches(data)) {
                    valueChangedRequest.notifyValueChanged(gatt.getDevice(), data);
                    if (valueChangedRequest.isComplete()) {
                        BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$AxRy9vPTNB_CAr6Q2j4o47n1Tgg
                            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                            public final String log() {
                                return BleManagerHandler.AnonymousClass3.lambda$onCharacteristicChanged$48();
                            }
                        });
                        valueChangedRequest.notifySuccess(gatt.getDevice());
                        BleManagerHandler.this.awaitingRequest = null;
                        if (valueChangedRequest.isTriggerCompleteOrNull()) {
                            BleManagerHandler.this.nextRequest(true);
                        }
                    }
                }
            }
            if (BleManagerHandler.this.checkCondition()) {
                BleManagerHandler.this.nextRequest(true);
            }
        }

        static /* synthetic */ String lambda$onCharacteristicChanged$43() {
            return "Service Changed indication received";
        }

        static /* synthetic */ String lambda$onCharacteristicChanged$44() {
            return "Discovering Services...";
        }

        static /* synthetic */ String lambda$onCharacteristicChanged$45() {
            return "gatt.discoverServices()";
        }

        static /* synthetic */ String lambda$onCharacteristicChanged$46(BluetoothGattCharacteristic characteristic, byte[] data) {
            return "Notification received from " + characteristic.getUuid() + ", value: " + ParserUtils.parse(data);
        }

        static /* synthetic */ String lambda$onCharacteristicChanged$47(BluetoothGattCharacteristic characteristic, byte[] data) {
            return "Indication received from " + characteristic.getUuid() + ", value: " + ParserUtils.parse(data);
        }

        static /* synthetic */ String lambda$onCharacteristicChanged$48() {
            return "Wait for value changed complete";
        }

        @Override // android.bluetooth.BluetoothGattCallback
        public void onMtuChanged(BluetoothGatt gatt, final int mtu, int status) {
            if (status == 0) {
                BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$zHAvjr5s7bpmEIVfD5MfrSoe3VU
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onMtuChanged$49(mtu);
                    }
                });
                BleManagerHandler.this.mtu = mtu;
                BleManagerHandler.this.onMtuChanged(gatt, mtu);
                if (BleManagerHandler.this.request instanceof MtuRequest) {
                    ((MtuRequest) BleManagerHandler.this.request).notifyMtuChanged(gatt.getDevice(), mtu);
                    BleManagerHandler.this.request.notifySuccess(gatt.getDevice());
                }
            } else {
                Log.e(BleManagerHandler.TAG, "onMtuChanged error: " + status + ", mtu: " + mtu);
                if (BleManagerHandler.this.request instanceof MtuRequest) {
                    BleManagerHandler.this.request.notifyFail(gatt.getDevice(), status);
                    BleManagerHandler.this.awaitingRequest = null;
                }
                BleManagerHandler.this.onError(gatt.getDevice(), BleManagerHandler.ERROR_MTU_REQUEST, status);
            }
            BleManagerHandler.this.checkCondition();
            if (BleManagerHandler.this.servicesDiscovered) {
                BleManagerHandler.this.nextRequest(true);
            }
        }

        static /* synthetic */ String lambda$onMtuChanged$49(int mtu) {
            return "MTU changed to: " + mtu;
        }

        public void onConnectionUpdated(final BluetoothGatt gatt, final int interval, final int latency, final int timeout, final int status) {
            if (status == 0) {
                BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$C2M399nMZdXzY4kNYE70ZYwAZPk
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onConnectionUpdated$50(interval, latency, timeout);
                    }
                });
                BleManagerHandler.this.interval = interval;
                BleManagerHandler.this.latency = latency;
                BleManagerHandler.this.timeout = timeout;
                BleManagerHandler.this.onConnectionUpdated(gatt, interval, latency, timeout);
                ConnectionParametersUpdatedCallback cpuc = BleManagerHandler.this.connectionParametersUpdatedCallback;
                if (cpuc != null) {
                    cpuc.onConnectionUpdated(gatt.getDevice(), interval, latency, timeout);
                }
                if (BleManagerHandler.this.request instanceof ConnectionPriorityRequest) {
                    ((ConnectionPriorityRequest) BleManagerHandler.this.request).notifyConnectionPriorityChanged(gatt.getDevice(), interval, latency, timeout);
                    BleManagerHandler.this.request.notifySuccess(gatt.getDevice());
                }
            } else if (status == 59) {
                Log.e(BleManagerHandler.TAG, "onConnectionUpdated received status: Unacceptable connection interval, interval: " + interval + ", latency: " + latency + ", timeout: " + timeout);
                BleManagerHandler.this.log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$jt-c5XKX4EU7GVnMiUUa9UZi2qc
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onConnectionUpdated$51(interval, latency, timeout);
                    }
                });
                if (BleManagerHandler.this.request instanceof ConnectionPriorityRequest) {
                    BleManagerHandler.this.request.notifyFail(gatt.getDevice(), status);
                    BleManagerHandler.this.awaitingRequest = null;
                }
            } else {
                Log.e(BleManagerHandler.TAG, "onConnectionUpdated received status: " + status + ", interval: " + interval + ", latency: " + latency + ", timeout: " + timeout);
                BleManagerHandler.this.log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$0PAGpbM02UKfk5OAtXXspN0nFxc
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onConnectionUpdated$52(status, interval, latency, timeout);
                    }
                });
                if (BleManagerHandler.this.request instanceof ConnectionPriorityRequest) {
                    BleManagerHandler.this.request.notifyFail(gatt.getDevice(), status);
                    BleManagerHandler.this.awaitingRequest = null;
                }
                BleManagerHandler.this.postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$-jAEgXd29MOE4ZvbId4nv24RRe4
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                    public final void run(BleManagerCallbacks bleManagerCallbacks) {
                        bleManagerCallbacks.onError(gatt.getDevice(), BleManagerHandler.ERROR_CONNECTION_PRIORITY_REQUEST, status);
                    }
                });
            }
            if (BleManagerHandler.this.connectionPriorityOperationInProgress) {
                BleManagerHandler.this.connectionPriorityOperationInProgress = false;
                BleManagerHandler.this.checkCondition();
                BleManagerHandler.this.nextRequest(true);
            }
        }

        static /* synthetic */ String lambda$onConnectionUpdated$50(int interval, int latency, int timeout) {
            return "Connection parameters updated (interval: " + (interval * 1.25d) + "ms, latency: " + latency + ", timeout: " + (timeout * 10) + "ms)";
        }

        static /* synthetic */ String lambda$onConnectionUpdated$51(int interval, int latency, int timeout) {
            return "Connection parameters update failed with status: UNACCEPT CONN INTERVAL (0x3b) (interval: " + (interval * 1.25d) + "ms, latency: " + latency + ", timeout: " + (timeout * 10) + "ms)";
        }

        static /* synthetic */ String lambda$onConnectionUpdated$52(int status, int interval, int latency, int timeout) {
            return "Connection parameters update failed with status " + status + " (interval: " + (interval * 1.25d) + "ms, latency: " + latency + ", timeout: " + (timeout * 10) + "ms)";
        }

        @Override // android.bluetooth.BluetoothGattCallback
        public void onPhyUpdate(final BluetoothGatt gatt, final int txPhy, final int rxPhy, final int status) {
            if (status == 0) {
                BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$ihcAjoVoiMcYf91rs1xO8Yew1MQ
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onPhyUpdate$54(txPhy, rxPhy);
                    }
                });
                if (BleManagerHandler.this.request instanceof PhyRequest) {
                    ((PhyRequest) BleManagerHandler.this.request).notifyPhyChanged(gatt.getDevice(), txPhy, rxPhy);
                    BleManagerHandler.this.request.notifySuccess(gatt.getDevice());
                }
            } else {
                BleManagerHandler.this.log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$54CzrUOC9trS1B1KqzET-G2ukFk
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onPhyUpdate$55(status);
                    }
                });
                if (BleManagerHandler.this.request instanceof PhyRequest) {
                    BleManagerHandler.this.request.notifyFail(gatt.getDevice(), status);
                    BleManagerHandler.this.awaitingRequest = null;
                }
                BleManagerHandler.this.postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$SzCQVGYJc6FYCTR44J2z8MWTslk
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                    public final void run(BleManagerCallbacks bleManagerCallbacks) {
                        bleManagerCallbacks.onError(gatt.getDevice(), BleManagerHandler.ERROR_PHY_UPDATE, status);
                    }
                });
            }
            if (BleManagerHandler.this.checkCondition() || (BleManagerHandler.this.request instanceof PhyRequest)) {
                BleManagerHandler.this.nextRequest(true);
            }
        }

        static /* synthetic */ String lambda$onPhyUpdate$54(int txPhy, int rxPhy) {
            return "PHY updated (TX: " + ParserUtils.phyToString(txPhy) + ", RX: " + ParserUtils.phyToString(rxPhy) + ")";
        }

        static /* synthetic */ String lambda$onPhyUpdate$55(int status) {
            return "PHY updated failed with status " + status;
        }

        @Override // android.bluetooth.BluetoothGattCallback
        public void onPhyRead(final BluetoothGatt gatt, final int txPhy, final int rxPhy, final int status) {
            if (status == 0) {
                BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$aJbDsOSELoTcrVenVbfPGiOWy5k
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onPhyRead$57(txPhy, rxPhy);
                    }
                });
                if (BleManagerHandler.this.request instanceof PhyRequest) {
                    ((PhyRequest) BleManagerHandler.this.request).notifyPhyChanged(gatt.getDevice(), txPhy, rxPhy);
                    BleManagerHandler.this.request.notifySuccess(gatt.getDevice());
                }
            } else {
                BleManagerHandler.this.log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$gCEm_UjHzSQYnTnrxra9PQVqQfY
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onPhyRead$58(status);
                    }
                });
                if (BleManagerHandler.this.request instanceof PhyRequest) {
                    BleManagerHandler.this.request.notifyFail(gatt.getDevice(), status);
                }
                BleManagerHandler.this.awaitingRequest = null;
                BleManagerHandler.this.postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$SwmpVSUPZ6u0mtnzqsbd5GSXHpU
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                    public final void run(BleManagerCallbacks bleManagerCallbacks) {
                        bleManagerCallbacks.onError(gatt.getDevice(), BleManagerHandler.ERROR_READ_PHY, status);
                    }
                });
            }
            BleManagerHandler.this.checkCondition();
            BleManagerHandler.this.nextRequest(true);
        }

        static /* synthetic */ String lambda$onPhyRead$57(int txPhy, int rxPhy) {
            return "PHY read (TX: " + ParserUtils.phyToString(txPhy) + ", RX: " + ParserUtils.phyToString(rxPhy) + ")";
        }

        static /* synthetic */ String lambda$onPhyRead$58(int status) {
            return "PHY read failed with status " + status;
        }

        @Override // android.bluetooth.BluetoothGattCallback
        public void onReadRemoteRssi(final BluetoothGatt gatt, final int rssi, final int status) {
            if (status == 0) {
                BleManagerHandler.this.log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$OVbegzYSt2a8oUKwTSjEIwS_Zp4
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onReadRemoteRssi$60(rssi);
                    }
                });
                if (BleManagerHandler.this.request instanceof ReadRssiRequest) {
                    ((ReadRssiRequest) BleManagerHandler.this.request).notifyRssiRead(gatt.getDevice(), rssi);
                    BleManagerHandler.this.request.notifySuccess(gatt.getDevice());
                }
            } else {
                BleManagerHandler.this.log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$SQDPoefdtwAvLk6AisWnyTUzV44
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.AnonymousClass3.lambda$onReadRemoteRssi$61(status);
                    }
                });
                if (BleManagerHandler.this.request instanceof ReadRssiRequest) {
                    BleManagerHandler.this.request.notifyFail(gatt.getDevice(), status);
                }
                BleManagerHandler.this.awaitingRequest = null;
                BleManagerHandler.this.postCallback(new CallbackRunnable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$3$62bYJ5eMSICWeHjGh7Kxt1VxwXQ
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.CallbackRunnable
                    public final void run(BleManagerCallbacks bleManagerCallbacks) {
                        bleManagerCallbacks.onError(gatt.getDevice(), BleManagerHandler.ERROR_READ_RSSI, status);
                    }
                });
            }
            BleManagerHandler.this.checkCondition();
            BleManagerHandler.this.nextRequest(true);
        }

        static /* synthetic */ String lambda$onReadRemoteRssi$60(int rssi) {
            return "Remote RSSI received: " + rssi + " dBm";
        }

        static /* synthetic */ String lambda$onReadRemoteRssi$61(int status) {
            return "Reading remote RSSI failed with status " + status;
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public int mapDisconnectStatusToReason(int status) {
        switch (status) {
            case 0:
                return 0;
            case 8:
                return 10;
            case 19:
                return 2;
            case 22:
                return 1;
            default:
                return -1;
        }
    }

    static /* synthetic */ String lambda$onCharacteristicReadRequest$108(BluetoothGattCharacteristic characteristic, int requestId, int offset) {
        return "[Server callback] Read request for characteristic " + characteristic.getUuid() + " (requestId=" + requestId + ", offset: " + offset + ")";
    }

    /* JADX WARN: Removed duplicated region for block: B:33:0x0085  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
        To view partially-correct code enable 'Show inconsistent code' option in preferences
    */
    final void onCharacteristicReadRequest(android.bluetooth.BluetoothGattServer r18, android.bluetooth.BluetoothDevice r19, final int r20, final int r21, final android.bluetooth.BluetoothGattCharacteristic r22) {
        /*
            r17 = this;
            r7 = r17
            r8 = r19
            r9 = r21
            r10 = r22
            no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$HWjak0nDGsrXPYr5hOPrB41oUdY r0 = new no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$HWjak0nDGsrXPYr5hOPrB41oUdY
            r11 = r20
            r0.<init>()
            r1 = 3
            r7.log(r1, r0)
            r12 = 4
            if (r9 != 0) goto L1e
            no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$dKTD6leUbnZBMbF30_JoBrbas_o r0 = new no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$dKTD6leUbnZBMbF30_JoBrbas_o
            r0.<init>()
            r7.log(r12, r0)
        L1e:
            java.util.HashMap<java.lang.Object, no.nordicsemi.android.ble.data.DataProvider> r0 = r7.dataProviders
            java.lang.Object r0 = r0.get(r10)
            r13 = r0
            no.nordicsemi.android.ble.data.DataProvider r13 = (no.nordicsemi.android.ble.data.DataProvider) r13
            if (r9 != 0) goto L30
            if (r13 == 0) goto L30
            byte[] r0 = r13.getData(r8)
            goto L31
        L30:
            r0 = 0
        L31:
            if (r0 == 0) goto L37
            r7.assign(r10, r0)
            goto L50
        L37:
            java.util.Map<android.bluetooth.BluetoothGattCharacteristic, byte[]> r1 = r7.characteristicValues
            if (r1 == 0) goto L4b
            boolean r1 = r1.containsKey(r10)
            if (r1 != 0) goto L42
            goto L4b
        L42:
            java.util.Map<android.bluetooth.BluetoothGattCharacteristic, byte[]> r1 = r7.characteristicValues
            java.lang.Object r1 = r1.get(r10)
            byte[] r1 = (byte[]) r1
            goto L4f
        L4b:
            byte[] r1 = r22.getValue()
        L4f:
            r0 = r1
        L50:
            r1 = 0
            no.nordicsemi.android.ble.AwaitingRequest<?> r2 = r7.awaitingRequest
            boolean r3 = r2 instanceof no.nordicsemi.android.ble.WaitForReadRequest
            if (r3 == 0) goto L73
            android.bluetooth.BluetoothGattCharacteristic r2 = r2.characteristic
            if (r2 != r10) goto L73
            no.nordicsemi.android.ble.AwaitingRequest<?> r2 = r7.awaitingRequest
            boolean r2 = r2.isTriggerPending()
            if (r2 != 0) goto L73
            no.nordicsemi.android.ble.AwaitingRequest<?> r2 = r7.awaitingRequest
            r1 = r2
            no.nordicsemi.android.ble.WaitForReadRequest r1 = (no.nordicsemi.android.ble.WaitForReadRequest) r1
            r1.setDataIfNull(r0)
            int r2 = r7.mtu
            byte[] r0 = r1.getData(r2)
            r15 = r1
            goto L74
        L73:
            r15 = r1
        L74:
            r6 = 1
            if (r0 == 0) goto L85
            int r1 = r0.length
            int r2 = r7.mtu
            int r3 = r2 + (-1)
            if (r1 <= r3) goto L85
            int r2 = r2 - r6
            byte[] r0 = no.nordicsemi.android.ble.Bytes.copy(r0, r9, r2)
            r5 = r0
            goto L86
        L85:
            r5 = r0
        L86:
            r3 = 0
            r0 = r17
            r1 = r18
            r2 = r19
            r4 = r20
            r16 = r5
            r5 = r21
            r14 = 1
            r6 = r16
            r0.sendResponse(r1, r2, r3, r4, r5, r6)
            if (r15 == 0) goto Lbd
            r0 = r16
            r15.notifyPacketRead(r8, r0)
            boolean r1 = r15.hasMore()
            if (r1 != 0) goto Lc8
            if (r0 == 0) goto Lae
            int r1 = r0.length
            int r2 = r7.mtu
            int r2 = r2 - r14
            if (r1 >= r2) goto Lc8
        Lae:
            no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$c1VsMaqOJg9kSpyKTWvfDh-JS6I r1 = new no.nordicsemi.android.ble.BleManagerHandler.Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$c1VsMaqOJg9kSpyKTWvfDh-JS6I
                static {
                    /*
                        no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$c1VsMaqOJg9kSpyKTWvfDh-JS6I r0 = new no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$c1VsMaqOJg9kSpyKTWvfDh-JS6I
                        r0.<init>()
                        
                        // error: 0x0005: SPUT (r0 I:no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$c1VsMaqOJg9kSpyKTWvfDh-JS6I) no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$c1VsMaqOJg9kSpyKTWvfDh-JS6I.INSTANCE no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$c1VsMaqOJg9kSpyKTWvfDh-JS6I
                        return
                    */
                    throw new UnsupportedOperationException("Method not decompiled: no.nordicsemi.android.ble.$$Lambda$BleManagerHandler$c1VsMaqOJg9kSpyKTWvfDhJS6I.<clinit>():void");
                }

                {
                    /*
                        r0 = this;
                        r0.<init>()
                        return
                    */
                    throw new UnsupportedOperationException("Method not decompiled: no.nordicsemi.android.ble.$$Lambda$BleManagerHandler$c1VsMaqOJg9kSpyKTWvfDhJS6I.<init>():void");
                }

                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final java.lang.String log() {
                    /*
                        r1 = this;
                        java.lang.String r0 = no.nordicsemi.android.ble.BleManagerHandler.lambda$onCharacteristicReadRequest$110()
                        return r0
                    */
                    throw new UnsupportedOperationException("Method not decompiled: no.nordicsemi.android.ble.$$Lambda$BleManagerHandler$c1VsMaqOJg9kSpyKTWvfDhJS6I.log():java.lang.String");
                }
            }
            r7.log(r12, r1)
            r15.notifySuccess(r8)
            r1 = 0
            r7.awaitingRequest = r1
            r7.nextRequest(r14)
            goto Lc8
        Lbd:
            r0 = r16
            boolean r1 = r17.checkCondition()
            if (r1 == 0) goto Lc8
            r7.nextRequest(r14)
        Lc8:
            return
        */
        throw new UnsupportedOperationException("Method not decompiled: no.nordicsemi.android.ble.BleManagerHandler.onCharacteristicReadRequest(android.bluetooth.BluetoothGattServer, android.bluetooth.BluetoothDevice, int, int, android.bluetooth.BluetoothGattCharacteristic):void");
    }

    static /* synthetic */ String lambda$onCharacteristicReadRequest$109(BluetoothGattCharacteristic characteristic) {
        return "[Server] READ request for characteristic " + characteristic.getUuid() + " received";
    }

    static /* synthetic */ String lambda$onCharacteristicReadRequest$110() {
        return "Wait for read complete";
    }

    final void onCharacteristicWriteRequest(BluetoothGattServer server, BluetoothDevice device, final int requestId, final BluetoothGattCharacteristic characteristic, final boolean preparedWrite, final boolean responseNeeded, final int offset, final byte[] value) {
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$FucFCvZaXOJeuXRyHpaco0MXjAc
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$onCharacteristicWriteRequest$111(responseNeeded, characteristic, requestId, preparedWrite, offset, value);
            }
        });
        if (offset == 0) {
            log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$tdYwuyVOjxAYLhuOTda0f6XH4ik
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$onCharacteristicWriteRequest$112(responseNeeded, preparedWrite, characteristic, value);
                }
            });
        }
        if (responseNeeded) {
            sendResponse(server, device, 0, requestId, offset, value);
        }
        if (preparedWrite) {
            if (this.preparedValues == null) {
                this.preparedValues = new LinkedList();
            }
            if (offset == 0) {
                this.preparedValues.offer(new Pair<>(characteristic, value));
                return;
            }
            Pair<Object, byte[]> last = this.preparedValues.peekLast();
            if (last == null || !characteristic.equals(last.first)) {
                this.prepareError = 7;
            } else {
                this.preparedValues.pollLast();
                this.preparedValues.offer(new Pair<>(characteristic, Bytes.concat((byte[]) last.second, value, offset)));
            }
            return;
        }
        if (assignAndNotify(device, characteristic, value) || checkCondition()) {
            nextRequest(true);
        }
    }

    static /* synthetic */ String lambda$onCharacteristicWriteRequest$111(boolean responseNeeded, BluetoothGattCharacteristic characteristic, int requestId, boolean preparedWrite, int offset, byte[] value) {
        StringBuilder sb = new StringBuilder();
        sb.append("[Server callback] Write ");
        sb.append(responseNeeded ? "request" : "command");
        sb.append(" to characteristic ");
        sb.append(characteristic.getUuid());
        sb.append(" (requestId=");
        sb.append(requestId);
        sb.append(", prepareWrite=");
        sb.append(preparedWrite);
        sb.append(", responseNeeded=");
        sb.append(responseNeeded);
        sb.append(", offset: ");
        sb.append(offset);
        sb.append(", value=");
        sb.append(ParserUtils.parseDebug(value));
        sb.append(")");
        return sb.toString();
    }

    static /* synthetic */ String lambda$onCharacteristicWriteRequest$112(boolean responseNeeded, boolean preparedWrite, BluetoothGattCharacteristic characteristic, byte[] value) {
        String type = responseNeeded ? "WRITE REQUEST" : "WRITE COMMAND";
        String option = preparedWrite ? "Prepare " : "";
        return "[Server] " + option + type + " for characteristic " + characteristic.getUuid() + " received, value: " + ParserUtils.parse(value);
    }

    /* JADX WARN: Removed duplicated region for block: B:33:0x0086  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
        To view partially-correct code enable 'Show inconsistent code' option in preferences
    */
    final void onDescriptorReadRequest(android.bluetooth.BluetoothGattServer r18, android.bluetooth.BluetoothDevice r19, final int r20, final int r21, final android.bluetooth.BluetoothGattDescriptor r22) {
        /*
            r17 = this;
            r7 = r17
            r8 = r19
            r9 = r21
            r10 = r22
            no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$Ll4AY0nuyjRDZeD3rn4Yk1SaXiM r0 = new no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$Ll4AY0nuyjRDZeD3rn4Yk1SaXiM
            r11 = r20
            r0.<init>()
            r1 = 3
            r7.log(r1, r0)
            if (r9 != 0) goto L1e
            r0 = 4
            no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$aBf48ULG_K5lAI3dp8b8QEENyZY r1 = new no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$aBf48ULG_K5lAI3dp8b8QEENyZY
            r1.<init>()
            r7.log(r0, r1)
        L1e:
            java.util.HashMap<java.lang.Object, no.nordicsemi.android.ble.data.DataProvider> r0 = r7.dataProviders
            java.lang.Object r0 = r0.get(r10)
            r12 = r0
            no.nordicsemi.android.ble.data.DataProvider r12 = (no.nordicsemi.android.ble.data.DataProvider) r12
            r13 = 0
            if (r9 != 0) goto L31
            if (r12 == 0) goto L31
            byte[] r0 = r12.getData(r8)
            goto L32
        L31:
            r0 = r13
        L32:
            if (r0 == 0) goto L38
            r7.assign(r10, r0)
            goto L51
        L38:
            java.util.Map<android.bluetooth.BluetoothGattDescriptor, byte[]> r1 = r7.descriptorValues
            if (r1 == 0) goto L4c
            boolean r1 = r1.containsKey(r10)
            if (r1 != 0) goto L43
            goto L4c
        L43:
            java.util.Map<android.bluetooth.BluetoothGattDescriptor, byte[]> r1 = r7.descriptorValues
            java.lang.Object r1 = r1.get(r10)
            byte[] r1 = (byte[]) r1
            goto L50
        L4c:
            byte[] r1 = r22.getValue()
        L50:
            r0 = r1
        L51:
            r1 = 0
            no.nordicsemi.android.ble.AwaitingRequest<?> r2 = r7.awaitingRequest
            boolean r3 = r2 instanceof no.nordicsemi.android.ble.WaitForReadRequest
            if (r3 == 0) goto L74
            android.bluetooth.BluetoothGattDescriptor r2 = r2.descriptor
            if (r2 != r10) goto L74
            no.nordicsemi.android.ble.AwaitingRequest<?> r2 = r7.awaitingRequest
            boolean r2 = r2.isTriggerPending()
            if (r2 != 0) goto L74
            no.nordicsemi.android.ble.AwaitingRequest<?> r2 = r7.awaitingRequest
            r1 = r2
            no.nordicsemi.android.ble.WaitForReadRequest r1 = (no.nordicsemi.android.ble.WaitForReadRequest) r1
            r1.setDataIfNull(r0)
            int r2 = r7.mtu
            byte[] r0 = r1.getData(r2)
            r14 = r1
            goto L75
        L74:
            r14 = r1
        L75:
            r15 = 1
            if (r0 == 0) goto L86
            int r1 = r0.length
            int r2 = r7.mtu
            int r3 = r2 + (-1)
            if (r1 <= r3) goto L86
            int r2 = r2 - r15
            byte[] r0 = no.nordicsemi.android.ble.Bytes.copy(r0, r9, r2)
            r6 = r0
            goto L87
        L86:
            r6 = r0
        L87:
            r3 = 0
            r0 = r17
            r1 = r18
            r2 = r19
            r4 = r20
            r5 = r21
            r16 = r6
            r0.sendResponse(r1, r2, r3, r4, r5, r6)
            if (r14 == 0) goto Lb5
            r0 = r16
            r14.notifyPacketRead(r8, r0)
            boolean r1 = r14.hasMore()
            if (r1 != 0) goto Lc0
            if (r0 == 0) goto Lac
            int r1 = r0.length
            int r2 = r7.mtu
            int r2 = r2 - r15
            if (r1 >= r2) goto Lc0
        Lac:
            r14.notifySuccess(r8)
            r7.awaitingRequest = r13
            r7.nextRequest(r15)
            goto Lc0
        Lb5:
            r0 = r16
            boolean r1 = r17.checkCondition()
            if (r1 == 0) goto Lc0
            r7.nextRequest(r15)
        Lc0:
            return
        */
        throw new UnsupportedOperationException("Method not decompiled: no.nordicsemi.android.ble.BleManagerHandler.onDescriptorReadRequest(android.bluetooth.BluetoothGattServer, android.bluetooth.BluetoothDevice, int, int, android.bluetooth.BluetoothGattDescriptor):void");
    }

    static /* synthetic */ String lambda$onDescriptorReadRequest$113(BluetoothGattDescriptor descriptor, int requestId, int offset) {
        return "[Server callback] Read request for descriptor " + descriptor.getUuid() + " (requestId=" + requestId + ", offset: " + offset + ")";
    }

    static /* synthetic */ String lambda$onDescriptorReadRequest$114(BluetoothGattDescriptor descriptor) {
        return "[Server] READ request for descriptor " + descriptor.getUuid() + " received";
    }

    final void onDescriptorWriteRequest(BluetoothGattServer server, BluetoothDevice device, final int requestId, final BluetoothGattDescriptor descriptor, final boolean preparedWrite, final boolean responseNeeded, final int offset, final byte[] value) {
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$T-hNQ_m3LCmIyoynlfWVFZ1MEfs
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$onDescriptorWriteRequest$115(responseNeeded, descriptor, requestId, preparedWrite, offset, value);
            }
        });
        if (offset == 0) {
            log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$Xu2CBsSj6B-B_Dyo6sfwjMjl-v0
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$onDescriptorWriteRequest$116(responseNeeded, preparedWrite, descriptor, value);
                }
            });
        }
        if (responseNeeded) {
            sendResponse(server, device, 0, requestId, offset, value);
        }
        if (preparedWrite) {
            if (this.preparedValues == null) {
                this.preparedValues = new LinkedList();
            }
            if (offset == 0) {
                this.preparedValues.offer(new Pair<>(descriptor, value));
                return;
            }
            Pair<Object, byte[]> last = this.preparedValues.peekLast();
            if (last == null || !descriptor.equals(last.first)) {
                this.prepareError = 7;
            } else {
                this.preparedValues.pollLast();
                this.preparedValues.offer(new Pair<>(descriptor, Bytes.concat((byte[]) last.second, value, offset)));
            }
            return;
        }
        if (assignAndNotify(device, descriptor, value) || checkCondition()) {
            nextRequest(true);
        }
    }

    static /* synthetic */ String lambda$onDescriptorWriteRequest$115(boolean responseNeeded, BluetoothGattDescriptor descriptor, int requestId, boolean preparedWrite, int offset, byte[] value) {
        StringBuilder sb = new StringBuilder();
        sb.append("[Server callback] Write ");
        sb.append(responseNeeded ? "request" : "command");
        sb.append(" to descriptor ");
        sb.append(descriptor.getUuid());
        sb.append(" (requestId=");
        sb.append(requestId);
        sb.append(", prepareWrite=");
        sb.append(preparedWrite);
        sb.append(", responseNeeded=");
        sb.append(responseNeeded);
        sb.append(", offset: ");
        sb.append(offset);
        sb.append(", value=");
        sb.append(ParserUtils.parseDebug(value));
        sb.append(")");
        return sb.toString();
    }

    static /* synthetic */ String lambda$onDescriptorWriteRequest$116(boolean responseNeeded, boolean preparedWrite, BluetoothGattDescriptor descriptor, byte[] value) {
        String type = responseNeeded ? "WRITE REQUEST" : "WRITE COMMAND";
        String option = preparedWrite ? "Prepare " : "";
        return "[Server] " + option + type + " request for descriptor " + descriptor.getUuid() + " received, value: " + ParserUtils.parse(value);
    }

    final void onExecuteWrite(BluetoothGattServer server, BluetoothDevice device, final int requestId, final boolean execute) {
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$mLIk7V5uw4TmFS2ZgYdVUCmoVbg
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$onExecuteWrite$117(requestId, execute);
            }
        });
        if (execute) {
            Deque<Pair<Object, byte[]>> values = this.preparedValues;
            log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$o5Z9k9WlyQsL-0F-QYS-UI-lXnM
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$onExecuteWrite$118();
                }
            });
            this.preparedValues = null;
            int i = this.prepareError;
            if (i != 0) {
                sendResponse(server, device, i, requestId, 0, null);
                this.prepareError = 0;
                return;
            }
            sendResponse(server, device, 0, requestId, 0, null);
            if (values == null || values.isEmpty()) {
                return;
            }
            boolean startNextRequest = false;
            Iterator<Pair<Object, byte[]>> it = values.iterator();
            while (true) {
                boolean z = true;
                if (!it.hasNext()) {
                    break;
                }
                Pair<Object, byte[]> value = it.next();
                if (value.first instanceof BluetoothGattCharacteristic) {
                    BluetoothGattCharacteristic characteristic = (BluetoothGattCharacteristic) value.first;
                    if (!assignAndNotify(device, characteristic, (byte[]) value.second) && !startNextRequest) {
                        z = false;
                    }
                    startNextRequest = z;
                } else if (value.first instanceof BluetoothGattDescriptor) {
                    BluetoothGattDescriptor descriptor = (BluetoothGattDescriptor) value.first;
                    if (!assignAndNotify(device, descriptor, (byte[]) value.second) && !startNextRequest) {
                        z = false;
                    }
                    startNextRequest = z;
                }
            }
            if (checkCondition() || startNextRequest) {
                nextRequest(true);
                return;
            }
            return;
        }
        log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$4BtRVo-WBRZlq1VNxdHIKvY_LRU
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$onExecuteWrite$119();
            }
        });
        this.preparedValues = null;
        sendResponse(server, device, 0, requestId, 0, null);
    }

    static /* synthetic */ String lambda$onExecuteWrite$117(int requestId, boolean execute) {
        return "[Server callback] Execute write request (requestId=" + requestId + ", execute=" + execute + ")";
    }

    static /* synthetic */ String lambda$onExecuteWrite$118() {
        return "[Server] Execute write request received";
    }

    static /* synthetic */ String lambda$onExecuteWrite$119() {
        return "[Server] Cancel write request received";
    }

    static /* synthetic */ String lambda$onNotificationSent$120(int status) {
        return "[Server callback] Notification sent (status=" + status + ")";
    }

    final void onNotificationSent(BluetoothGattServer server, BluetoothDevice device, final int status) {
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$kHKcQ1MkCLtytYenAs0iENQCP-4
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$onNotificationSent$120(status);
            }
        });
        if (status == 0) {
            notifyNotificationSent(device);
        } else {
            Log.e(TAG, "onNotificationSent error " + status);
            Request request = this.request;
            if (request instanceof WriteRequest) {
                request.notifyFail(device, status);
            }
            this.awaitingRequest = null;
            onError(device, ERROR_NOTIFY, status);
        }
        checkCondition();
        nextRequest(true);
    }

    static /* synthetic */ String lambda$onMtuChanged$121(int mtu) {
        return "[Server] MTU changed to: " + mtu;
    }

    final void onMtuChanged(BluetoothGattServer server, BluetoothDevice device, final int mtu) {
        log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$USrKNJ0bUwY80Ynzqt9g0COUhkk
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$onMtuChanged$121(mtu);
            }
        });
        this.mtu = mtu;
        checkCondition();
        nextRequest(false);
    }

    private void notifyNotificationSent(BluetoothDevice device) {
        Request request = this.request;
        if (request instanceof WriteRequest) {
            WriteRequest wr = (WriteRequest) request;
            switch (AnonymousClass4.$SwitchMap$no$nordicsemi$android$ble$Request$Type[wr.type.ordinal()]) {
                case 1:
                    log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$Ry8b4-CVxoVc74rT0IzNgi9qmK0
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.lambda$notifyNotificationSent$122();
                        }
                    });
                    break;
                case 2:
                    log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$pvqRJD3EkhSPXWcTj9qjyxx10RM
                        @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                        public final String log() {
                            return BleManagerHandler.lambda$notifyNotificationSent$123();
                        }
                    });
                    break;
            }
            wr.notifyPacketSent(device, wr.characteristic.getValue());
            if (wr.hasMore()) {
                enqueueFirst(wr);
            } else {
                wr.notifySuccess(device);
            }
        }
    }

    static /* synthetic */ String lambda$notifyNotificationSent$122() {
        return "[Server] Notification sent";
    }

    static /* synthetic */ String lambda$notifyNotificationSent$123() {
        return "[Server] Indication sent";
    }

    private void assign(BluetoothGattCharacteristic characteristic, byte[] value) {
        Map<BluetoothGattCharacteristic, byte[]> map = this.characteristicValues;
        boolean isShared = map == null || !map.containsKey(characteristic);
        if (isShared) {
            characteristic.setValue(value);
        } else {
            this.characteristicValues.put(characteristic, value);
        }
    }

    private boolean assignAndNotify(BluetoothDevice device, BluetoothGattCharacteristic characteristic, byte[] value) {
        assign(characteristic, value);
        ValueChangedCallback callback = this.valueChangedCallbacks.get(characteristic);
        if (callback != null) {
            callback.notifyValueChanged(device, value);
        }
        AwaitingRequest<?> awaitingRequest = this.awaitingRequest;
        if ((awaitingRequest instanceof WaitForValueChangedRequest) && awaitingRequest.characteristic == characteristic && !this.awaitingRequest.isTriggerPending()) {
            WaitForValueChangedRequest waitForWrite = (WaitForValueChangedRequest) this.awaitingRequest;
            if (waitForWrite.matches(value)) {
                waitForWrite.notifyValueChanged(device, value);
                if (waitForWrite.isComplete()) {
                    waitForWrite.notifySuccess(device);
                    this.awaitingRequest = null;
                    return waitForWrite.isTriggerCompleteOrNull();
                }
                return false;
            }
            return false;
        }
        return false;
    }

    private void assign(BluetoothGattDescriptor descriptor, byte[] value) {
        Map<BluetoothGattDescriptor, byte[]> map = this.descriptorValues;
        boolean isShared = map == null || !map.containsKey(descriptor);
        if (isShared) {
            descriptor.setValue(value);
        } else {
            this.descriptorValues.put(descriptor, value);
        }
    }

    private boolean assignAndNotify(BluetoothDevice device, BluetoothGattDescriptor descriptor, byte[] value) {
        assign(descriptor, value);
        ValueChangedCallback callback = this.valueChangedCallbacks.get(descriptor);
        if (callback != null) {
            callback.notifyValueChanged(device, value);
        }
        AwaitingRequest<?> awaitingRequest = this.awaitingRequest;
        if ((awaitingRequest instanceof WaitForValueChangedRequest) && awaitingRequest.descriptor == descriptor && !this.awaitingRequest.isTriggerPending()) {
            WaitForValueChangedRequest waitForWrite = (WaitForValueChangedRequest) this.awaitingRequest;
            if (waitForWrite.matches(value)) {
                waitForWrite.notifyValueChanged(device, value);
                if (waitForWrite.isComplete()) {
                    waitForWrite.notifySuccess(device);
                    this.awaitingRequest = null;
                    return waitForWrite.isTriggerCompleteOrNull();
                }
                return false;
            }
            return false;
        }
        return false;
    }

    private void sendResponse(BluetoothGattServer server, BluetoothDevice device, int status, int requestId, final int offset, final byte[] response) {
        final String msg;
        switch (status) {
            case 0:
                msg = "GATT_SUCCESS";
                break;
            case 6:
                msg = "GATT_REQUEST_NOT_SUPPORTED";
                break;
            case 7:
                msg = "GATT_INVALID_OFFSET";
                break;
            default:
                throw new InvalidParameterException();
        }
        log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$tKPyii6nju4W0LgPgNSrQwI4oo0
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$sendResponse$124(msg, offset, response);
            }
        });
        server.sendResponse(device, requestId, status, offset, response);
        log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$PoNwkda4F0O3uHRGBqvJGvqVMSs
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$sendResponse$125();
            }
        });
    }

    static /* synthetic */ String lambda$sendResponse$124(String msg, int offset, byte[] response) {
        return "server.sendResponse(" + msg + ", offset=" + offset + ", value=" + ParserUtils.parseDebug(response) + ")";
    }

    static /* synthetic */ String lambda$sendResponse$125() {
        return "[Server] Response sent";
    }

    /* JADX INFO: Access modifiers changed from: private */
    public boolean checkCondition() {
        AwaitingRequest<?> awaitingRequest = this.awaitingRequest;
        if (awaitingRequest instanceof ConditionalWaitRequest) {
            ConditionalWaitRequest<?> cwr = (ConditionalWaitRequest) awaitingRequest;
            if (cwr.isFulfilled()) {
                log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$8F1fJG-DWo4G1R4ASSjdQILedsU
                    @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                    public final String log() {
                        return BleManagerHandler.lambda$checkCondition$126();
                    }
                });
                cwr.notifySuccess(this.bluetoothDevice);
                this.awaitingRequest = null;
                return true;
            }
            return false;
        }
        return false;
    }

    static /* synthetic */ String lambda$checkCondition$126() {
        return "Condition fulfilled";
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* JADX WARN: Removed duplicated region for block: B:14:0x0016 A[DONT_GENERATE] */
    /* JADX WARN: Removed duplicated region for block: B:16:0x0018 A[Catch: all -> 0x03de, TRY_ENTER, TRY_LEAVE, TryCatch #2 {, blocks: (B:5:0x0005, B:7:0x0009, B:11:0x0010, B:12:0x0012, B:16:0x0018, B:18:0x001c, B:20:0x0020, B:22:0x0026, B:23:0x0032, B:25:0x0038, B:27:0x0040, B:28:0x0046, B:30:0x004f, B:32:0x0053, B:40:0x0061, B:42:0x0065, B:44:0x0072, B:45:0x0082, B:47:0x0086, B:48:0x008f, B:51:0x009a, B:54:0x00a5, B:56:0x00a9, B:60:0x00af, B:62:0x00b7, B:63:0x00c5, B:69:0x00d4, B:72:0x00da, B:74:0x00de, B:80:0x00ed, B:82:0x00f2, B:84:0x0100, B:87:0x0111, B:89:0x0115, B:90:0x011a, B:92:0x011e, B:93:0x0123, B:95:0x012b, B:96:0x0135, B:98:0x013b, B:101:0x014b, B:102:0x015d, B:208:0x03b4, B:215:0x03c8, B:211:0x03ba, B:104:0x0162, B:105:0x0171, B:107:0x0179, B:108:0x0183, B:110:0x018b, B:111:0x0195, B:113:0x019c, B:114:0x01a3, B:116:0x01a8, B:119:0x01b3, B:121:0x01bb, B:123:0x01d2, B:124:0x01de, B:126:0x01e3, B:129:0x01ee, B:133:0x01f8, B:135:0x01fe, B:137:0x0209, B:138:0x0213, B:139:0x0217, B:141:0x0222, B:143:0x0226, B:144:0x0231, B:146:0x0236, B:149:0x0243, B:150:0x024a, B:151:0x0251, B:152:0x0258, B:153:0x025f, B:154:0x0268, B:155:0x0271, B:156:0x027a, B:157:0x0283, B:158:0x028a, B:159:0x0291, B:161:0x0298, B:164:0x02a2, B:166:0x02a9, B:168:0x02ad, B:170:0x02b5, B:172:0x02ce, B:171:0x02c3, B:173:0x02d7, B:175:0x02de, B:177:0x02e2, B:179:0x02ea, B:181:0x0303, B:180:0x02f8, B:182:0x030c, B:183:0x031e, B:184:0x0327, B:185:0x033d, B:186:0x0346, B:189:0x0350, B:190:0x0356, B:191:0x035c, B:192:0x0362, B:193:0x0368, B:194:0x0379, B:196:0x0386, B:198:0x038f, B:200:0x0397, B:201:0x039e, B:205:0x03a9, B:100:0x0148, B:218:0x03d4), top: B:228:0x0005, inners: #1 }] */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
        To view partially-correct code enable 'Show inconsistent code' option in preferences
    */
    public synchronized void nextRequest(boolean r14) {
        /*
            Method dump skipped, instructions count: 1082
            To view this dump change 'Code comments level' option to 'DEBUG'
        */
        throw new UnsupportedOperationException("Method not decompiled: no.nordicsemi.android.ble.BleManagerHandler.nextRequest(boolean):void");
    }

    static /* synthetic */ String lambda$nextRequest$129() {
        return "Waiting for fulfillment of condition...";
    }

    static /* synthetic */ String lambda$nextRequest$130() {
        return "Condition fulfilled";
    }

    static /* synthetic */ String lambda$nextRequest$131() {
        return "Waiting for read request...";
    }

    static /* synthetic */ String lambda$nextRequest$132() {
        return "Waiting for value change...";
    }

    public /* synthetic */ void lambda$nextRequest$133$BleManagerHandler(ConnectionPriorityRequest cpr, BluetoothDevice bluetoothDevice) {
        if (cpr.notifySuccess(bluetoothDevice)) {
            this.connectionPriorityOperationInProgress = false;
            nextRequest(true);
        }
    }

    public /* synthetic */ void lambda$nextRequest$135$BleManagerHandler(PhyRequest pr) {
        if (!pr.finished) {
            log(5, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$fICAdsqVtTdsklg_d3tHWva5Glw
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$nextRequest$134();
                }
            });
            internalReadPhy();
        }
    }

    static /* synthetic */ String lambda$nextRequest$134() {
        return "Callback not received in 1000 ms";
    }

    public /* synthetic */ void lambda$nextRequest$136$BleManagerHandler(Request r, BluetoothDevice bluetoothDevice) {
        if (this.request == r) {
            r.notifyFail(bluetoothDevice, -5);
            nextRequest(true);
        }
    }

    static /* synthetic */ String lambda$nextRequest$137() {
        return "Cache refreshed";
    }

    public /* synthetic */ void lambda$nextRequest$140$BleManagerHandler(Request r, BluetoothDevice bluetoothDevice) {
        log(4, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$_ntpHN_MHEys-vnP1j82b_CfwFY
            @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
            public final String log() {
                return BleManagerHandler.lambda$nextRequest$137();
            }
        });
        r.notifySuccess(bluetoothDevice);
        this.request = null;
        AwaitingRequest<?> awaitingRequest = this.awaitingRequest;
        if (awaitingRequest != null) {
            awaitingRequest.notifyFail(bluetoothDevice, -3);
            this.awaitingRequest = null;
        }
        this.taskQueue.clear();
        this.initQueue = null;
        BluetoothGatt bluetoothGatt = this.bluetoothGatt;
        if (this.connected && bluetoothGatt != null) {
            this.manager.onServicesInvalidated();
            onDeviceDisconnected();
            this.serviceDiscoveryRequested = true;
            this.servicesDiscovered = false;
            log(2, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$05m4A96b4ZpV69RUts4hmGLWypE
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$nextRequest$138();
                }
            });
            log(3, new Loggable() { // from class: no.nordicsemi.android.ble.-$$Lambda$BleManagerHandler$kT9RWuEK4I5wv1SAWZ61zQniLX4
                @Override // no.nordicsemi.android.ble.BleManagerHandler.Loggable
                public final String log() {
                    return BleManagerHandler.lambda$nextRequest$139();
                }
            });
            bluetoothGatt.discoverServices();
        }
    }

    static /* synthetic */ String lambda$nextRequest$138() {
        return "Discovering Services...";
    }

    static /* synthetic */ String lambda$nextRequest$139() {
        return "gatt.discoverServices()";
    }

    static /* synthetic */ String lambda$nextRequest$141(SleepRequest sr) {
        return "sleep(" + sr.timeout + ")";
    }

    /* JADX INFO: Access modifiers changed from: private */
    public boolean isServiceChangedCCCD(BluetoothGattDescriptor descriptor) {
        return descriptor != null && BleManager.SERVICE_CHANGED_CHARACTERISTIC.equals(descriptor.getCharacteristic().getUuid());
    }

    /* JADX INFO: Access modifiers changed from: private */
    public boolean isServiceChangedCharacteristic(BluetoothGattCharacteristic characteristic) {
        return characteristic != null && BleManager.SERVICE_CHANGED_CHARACTERISTIC.equals(characteristic.getUuid());
    }

    /* JADX INFO: Access modifiers changed from: private */
    @Deprecated
    public boolean isBatteryLevelCharacteristic(BluetoothGattCharacteristic characteristic) {
        return characteristic != null && BleManager.BATTERY_LEVEL_CHARACTERISTIC.equals(characteristic.getUuid());
    }

    /* JADX INFO: Access modifiers changed from: private */
    public boolean isCCCD(BluetoothGattDescriptor descriptor) {
        return descriptor != null && BleManager.CLIENT_CHARACTERISTIC_CONFIG_DESCRIPTOR_UUID.equals(descriptor.getUuid());
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void log(int priority, Loggable message) {
        if (priority >= this.manager.getMinLogPriority()) {
            this.manager.log(priority, message.log());
        }
    }
}
