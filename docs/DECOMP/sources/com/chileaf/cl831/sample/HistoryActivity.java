package com.chileaf.cl831.sample;

import android.bluetooth.BluetoothDevice;
import android.os.Bundle;
import android.view.View;
import androidx.recyclerview.widget.DefaultItemAnimator;
import androidx.recyclerview.widget.DividerItemDecoration;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.android.chileaf.fitness.callback.HistoryOf3DDataCallback;
import com.android.chileaf.fitness.callback.HistoryOfHRRecordCallback;
import com.android.chileaf.fitness.callback.HistoryOfRRRecordCallback;
import com.android.chileaf.fitness.callback.HistoryOfSportCallback;
import com.android.chileaf.fitness.callback.HistoryOfStepRecordCallback;
import com.android.chileaf.fitness.callback.IntervalStepCallback;
import com.android.chileaf.fitness.callback.SingleTapRecordCallback;
import com.android.chileaf.model.HistoryOf3D;
import com.android.chileaf.model.HistoryOfRecord;
import com.chad.library.adapter.base.BaseQuickAdapter;
import com.chad.library.adapter.base.listener.OnItemClickListener;
import java.util.List;
import no.nordicsemi.android.dfu.DfuServiceInitiator;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class HistoryActivity extends BaseActivity {
    public static final String EXTRA_HISTORY = "extra_history";
    public static final int TYPE_3D = 18;
    public static final int TYPE_HEART = 4;
    public static final int TYPE_HEART_RR = 6;
    public static final int TYPE_INTERVAL = 8;
    public static final int TYPE_SINGLE = 16;
    public static final int TYPE_SPORT = 2;
    public static final int TYPE_STEP = 20;
    private RecyclerView mRvHistory;

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected int layoutId() {
        return R.layout.activity_history;
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initView() {
        RecyclerView recyclerView = (RecyclerView) findViewById(R.id.rv_history);
        this.mRvHistory = recyclerView;
        recyclerView.setLayoutManager(new LinearLayoutManager(this));
        this.mRvHistory.setItemAnimator(new DefaultItemAnimator());
        this.mRvHistory.addItemDecoration(new DividerItemDecoration(this, 1));
        this.mRvHistory.setHasFixedSize(true);
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initData(Bundle savedInstanceState) {
        int type = getIntent().getIntExtra(EXTRA_HISTORY, 0);
        if (type == 2) {
            setTitle("7 days sport history");
            showLoadingAutoDismiss(2000L);
            final HistorySportAdapter adapter = new HistorySportAdapter();
            this.mRvHistory.setAdapter(adapter);
            this.mManager.addHistoryOfSportCallback(new HistoryOfSportCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$zTeSPTg31xPAQ59TVn2i_Nh-vLo
                @Override // com.android.chileaf.fitness.callback.HistoryOfSportCallback
                public final void onHistoryOfSportReceived(BluetoothDevice bluetoothDevice, List list) {
                    this.f$0.lambda$initData$1$HistoryActivity(adapter, bluetoothDevice, list);
                }
            });
            this.mManager.getHistoryOfSport();
            return;
        }
        if (type == 4) {
            setTitle("Heart rate history record");
            showLoadingAutoDismiss(2000L);
            final HistoryRecordAdapter adapter2 = new HistoryRecordAdapter();
            adapter2.setOnItemClickListener(new OnItemClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$XL4ajuyhk8zwKKEEWKWr0b4OXU4
                @Override // com.chad.library.adapter.base.listener.OnItemClickListener
                public final void onItemClick(BaseQuickAdapter baseQuickAdapter, View view, int i) {
                    this.f$0.lambda$initData$2$HistoryActivity(baseQuickAdapter, view, i);
                }
            });
            this.mRvHistory.setAdapter(adapter2);
            this.mManager.addHistoryOfHRRecordCallback(new HistoryOfHRRecordCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$k5bhFnDhtrceDLuh9ogh7UNO_q0
                @Override // com.android.chileaf.fitness.callback.HistoryOfHRRecordCallback
                public final void onHistoryOfHRRecordReceived(BluetoothDevice bluetoothDevice, List list) {
                    this.f$0.lambda$initData$4$HistoryActivity(adapter2, bluetoothDevice, list);
                }
            });
            this.mManager.getHistoryOfHRRecord();
            return;
        }
        if (type == 6) {
            setTitle("RR history record");
            showLoadingAutoDismiss(2000L);
            final HistoryRecordAdapter adapter3 = new HistoryRecordAdapter();
            adapter3.setOnItemClickListener(new OnItemClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$Qg7JPQmZ8rGVL-zvC4oiQ-ZQAp0
                @Override // com.chad.library.adapter.base.listener.OnItemClickListener
                public final void onItemClick(BaseQuickAdapter baseQuickAdapter, View view, int i) {
                    this.f$0.lambda$initData$5$HistoryActivity(baseQuickAdapter, view, i);
                }
            });
            this.mRvHistory.setAdapter(adapter3);
            this.mManager.addHistoryOfRRRecordCallback(new HistoryOfRRRecordCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$LKNIE_-srmTjUvKOkDdYMJWkGfM
                @Override // com.android.chileaf.fitness.callback.HistoryOfRRRecordCallback
                public final void onHistoryOfRRRecordReceived(BluetoothDevice bluetoothDevice, List list) {
                    this.f$0.lambda$initData$7$HistoryActivity(adapter3, bluetoothDevice, list);
                }
            });
            this.mManager.getHistoryOfRRRecord();
            return;
        }
        if (type == 20) {
            setTitle("Step history record");
            showLoadingAutoDismiss(2000L);
            final HistoryRecordAdapter adapter4 = new HistoryRecordAdapter();
            adapter4.setOnItemClickListener(new OnItemClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$IZEb85iq8G7oHCCbHXGTkLBUig4
                @Override // com.chad.library.adapter.base.listener.OnItemClickListener
                public final void onItemClick(BaseQuickAdapter baseQuickAdapter, View view, int i) {
                    this.f$0.lambda$initData$8$HistoryActivity(baseQuickAdapter, view, i);
                }
            });
            this.mRvHistory.setAdapter(adapter4);
            this.mManager.addHistoryOfStepRecordCallback(new HistoryOfStepRecordCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$P-bYmYvZZHHJbBH22SB59lDrWfU
                @Override // com.android.chileaf.fitness.callback.HistoryOfStepRecordCallback
                public final void onHistoryOfStepRecordReceived(BluetoothDevice bluetoothDevice, List list) {
                    this.f$0.lambda$initData$10$HistoryActivity(adapter4, bluetoothDevice, list);
                }
            });
            this.mManager.getHistoryOfStepRecord();
            return;
        }
        if (type == 8) {
            setTitle("Interval steps record");
            showLoadingAutoDismiss(DfuServiceInitiator.DEFAULT_SCAN_TIMEOUT);
            final IntervalStepAdapter adapter5 = new IntervalStepAdapter();
            this.mRvHistory.setAdapter(adapter5);
            this.mManager.addIntervalStepCallback(new IntervalStepCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$x5ClzrJXN0GyPxT3QthgcesyzQk
                @Override // com.android.chileaf.fitness.callback.IntervalStepCallback
                public final void onIntervalStepReceived(BluetoothDevice bluetoothDevice, List list) {
                    this.f$0.lambda$initData$12$HistoryActivity(adapter5, bluetoothDevice, list);
                }
            });
            this.mManager.getIntervalSteps();
            return;
        }
        if (type == 16) {
            setTitle("Single pressed record");
            showLoadingAutoDismiss(DfuServiceInitiator.DEFAULT_SCAN_TIMEOUT);
            final HistoryRecordAdapter adapter6 = new HistoryRecordAdapter();
            this.mRvHistory.setAdapter(adapter6);
            this.mManager.addSingleTapRecordCallback(new SingleTapRecordCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$ZWwy-Gxi_mwtDROFLZUPVySulMk
                @Override // com.android.chileaf.fitness.callback.SingleTapRecordCallback
                public final void onSingleTapRecordReceived(BluetoothDevice bluetoothDevice, List list) {
                    this.f$0.lambda$initData$14$HistoryActivity(adapter6, bluetoothDevice, list);
                }
            });
            this.mManager.getSingleTapRecords();
            return;
        }
        if (type == 18) {
            setTitle("3D History");
            showLoadingAutoDismiss(2000L);
            final History3DAdapter adapter7 = new History3DAdapter();
            this.mRvHistory.setAdapter(adapter7);
            this.mManager.addHistoryOf3DDataCallback(new HistoryOf3DDataCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$jExuAYrIMjZ977_x_LuMKLNsGNc
                @Override // com.android.chileaf.fitness.callback.HistoryOf3DDataCallback
                public final void onHistoryOf3DDataReceived(BluetoothDevice bluetoothDevice, HistoryOf3D historyOf3D, boolean z) {
                    this.f$0.lambda$initData$16$HistoryActivity(adapter7, bluetoothDevice, historyOf3D, z);
                }
            });
            this.mManager.getHistoryOf3D();
        }
    }

    public /* synthetic */ void lambda$initData$1$HistoryActivity(final HistorySportAdapter adapter, BluetoothDevice device, final List sports) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$VD7ymOdE_2VPDsV_630W_DfCrL8
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$0$HistoryActivity(adapter, sports);
            }
        });
    }

    public /* synthetic */ void lambda$initData$0$HistoryActivity(HistorySportAdapter adapter, List sports) {
        adapter.replaceData(sports);
        hideLoading();
    }

    public /* synthetic */ void lambda$initData$2$HistoryActivity(BaseQuickAdapter adapter1, View view, int position) {
        HistoryOfRecord history = (HistoryOfRecord) adapter1.getData().get(position);
        launchDetail(3, history.stamp);
    }

    public /* synthetic */ void lambda$initData$4$HistoryActivity(final HistoryRecordAdapter adapter, BluetoothDevice device, final List records) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$KqdsEiq5x_YGtsGKtocSYkIXnmU
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$3$HistoryActivity(adapter, records);
            }
        });
    }

    public /* synthetic */ void lambda$initData$3$HistoryActivity(HistoryRecordAdapter adapter, List records) {
        adapter.replaceData(records);
        hideLoading();
    }

    public /* synthetic */ void lambda$initData$5$HistoryActivity(BaseQuickAdapter adapter1, View view, int position) {
        HistoryOfRecord history = (HistoryOfRecord) adapter1.getData().get(position);
        launchDetail(5, history.stamp);
    }

    public /* synthetic */ void lambda$initData$7$HistoryActivity(final HistoryRecordAdapter adapter, BluetoothDevice device, final List records) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$cLht7fOA7owtPaFNlWeRBHDLLCY
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$6$HistoryActivity(adapter, records);
            }
        });
    }

    public /* synthetic */ void lambda$initData$6$HistoryActivity(HistoryRecordAdapter adapter, List records) {
        adapter.replaceData(records);
        hideLoading();
    }

    public /* synthetic */ void lambda$initData$8$HistoryActivity(BaseQuickAdapter adapter1, View view, int position) {
        HistoryOfRecord history = (HistoryOfRecord) adapter1.getData().get(position);
        launchDetail(7, history.stamp);
    }

    public /* synthetic */ void lambda$initData$10$HistoryActivity(final HistoryRecordAdapter adapter, BluetoothDevice device, final List records) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$loIttzuiGYBqmzbpuOFOyRy3BE8
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$9$HistoryActivity(adapter, records);
            }
        });
    }

    public /* synthetic */ void lambda$initData$9$HistoryActivity(HistoryRecordAdapter adapter, List records) {
        adapter.replaceData(records);
        hideLoading();
    }

    public /* synthetic */ void lambda$initData$12$HistoryActivity(final IntervalStepAdapter adapter, BluetoothDevice device, final List steps) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$1KzlYLOttfBpA3TF2-3dMRT8oHs
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$11$HistoryActivity(adapter, steps);
            }
        });
    }

    public /* synthetic */ void lambda$initData$11$HistoryActivity(IntervalStepAdapter adapter, List steps) {
        adapter.replaceData(steps);
        hideLoading();
    }

    public /* synthetic */ void lambda$initData$14$HistoryActivity(final HistoryRecordAdapter adapter, BluetoothDevice device, final List records) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$tBVQzd3B9J59VzQdWgc9nvZuWbs
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$13$HistoryActivity(adapter, records);
            }
        });
    }

    public /* synthetic */ void lambda$initData$13$HistoryActivity(HistoryRecordAdapter adapter, List records) {
        adapter.replaceData(records);
        hideLoading();
    }

    public /* synthetic */ void lambda$initData$16$HistoryActivity(final History3DAdapter adapter, BluetoothDevice device, final HistoryOf3D history, final boolean finish) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryActivity$BLfUDKR7uzpKGaT_eyOV7Ssq6us
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$15$HistoryActivity(adapter, history, finish);
            }
        });
    }

    public /* synthetic */ void lambda$initData$15$HistoryActivity(History3DAdapter adapter, HistoryOf3D history, boolean finish) {
        adapter.addData((History3DAdapter) history);
        hideLoading();
        if (finish) {
            showToast("Complete!");
        }
    }
}
