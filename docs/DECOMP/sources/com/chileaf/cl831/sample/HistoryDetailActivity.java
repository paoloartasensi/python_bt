package com.chileaf.cl831.sample;

import android.bluetooth.BluetoothDevice;
import android.os.Bundle;
import androidx.appcompat.widget.AppCompatTextView;
import androidx.core.internal.view.SupportMenu;
import com.android.chileaf.fitness.callback.HistoryOfHRDataCallback;
import com.android.chileaf.fitness.callback.HistoryOfRRDataCallback;
import com.android.chileaf.fitness.callback.HistoryOfStepDataCallback;
import com.android.chileaf.model.HistoryOfHeartRate;
import com.android.chileaf.model.HistoryOfRespiratoryRate;
import com.android.chileaf.model.HistoryOfStep;
import com.github.mikephil.charting.charts.LineChart;
import com.github.mikephil.charting.components.XAxis;
import com.github.mikephil.charting.data.Entry;
import com.github.mikephil.charting.data.LineData;
import com.github.mikephil.charting.data.LineDataSet;
import com.github.mikephil.charting.formatter.ValueFormatter;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import timber.log.Timber;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class HistoryDetailActivity extends BaseActivity {
    public static final String EXTRA_STAMP = "extra_stamp";
    public static final String EXTRA_TYPE = "extra_type";
    public static final int TYPE_HR = 3;
    public static final int TYPE_RR = 5;
    public static final int TYPE_STEP = 7;
    private LineChart mChart;
    private SimpleDateFormat mDateFormat;
    private AppCompatTextView mTvHistory;

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected int layoutId() {
        return R.layout.activity_record_detail;
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initView() {
        this.mTvHistory = (AppCompatTextView) findViewById(R.id.tv_history);
        this.mChart = (LineChart) findViewById(R.id.chart_history);
        initChart();
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initData(Bundle savedInstanceState) {
        showLoadingAutoDismiss(2000L);
        int type = getIntent().getIntExtra(EXTRA_TYPE, 0);
        long stamp = getIntent().getLongExtra(EXTRA_STAMP, 0L);
        this.mDateFormat = new SimpleDateFormat("MM-dd HH:mm:ss", Locale.getDefault());
        if (type == 3) {
            setTitle("HR history detail");
            this.mManager.addHistoryOfHRDataCallback(new HistoryOfHRDataCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryDetailActivity$jPoknXpNgG3uiDKfaf_OmKOHUic
                @Override // com.android.chileaf.fitness.callback.HistoryOfHRDataCallback
                public final void onHistoryOfHRDataReceived(BluetoothDevice bluetoothDevice, List list) {
                    this.f$0.lambda$initData$1$HistoryDetailActivity(bluetoothDevice, list);
                }
            });
            this.mManager.getHistoryOfHRData(stamp);
        } else if (type == 5) {
            setTitle("RR history detail");
            this.mManager.addHistoryOfRRDataCallback(new HistoryOfRRDataCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryDetailActivity$2MHn-kx1Onf2tzO6Uit7UZK2KXo
                @Override // com.android.chileaf.fitness.callback.HistoryOfRRDataCallback
                public final void onHistoryOfRRDataReceived(BluetoothDevice bluetoothDevice, List list) {
                    this.f$0.lambda$initData$3$HistoryDetailActivity(bluetoothDevice, list);
                }
            });
            this.mManager.getHistoryOfRRData(stamp);
        } else if (type == 7) {
            setTitle("Step history detail");
            this.mManager.addHistoryOfStepDataCallback(new HistoryOfStepDataCallback() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryDetailActivity$txPu055GZrPzGXxu58vHA0d53xQ
                @Override // com.android.chileaf.fitness.callback.HistoryOfStepDataCallback
                public final void onHistoryOfStepDataReceived(BluetoothDevice bluetoothDevice, List list) {
                    this.f$0.lambda$initData$5$HistoryDetailActivity(bluetoothDevice, list);
                }
            });
            this.mManager.getHistoryOfStepData(stamp);
        }
    }

    public /* synthetic */ void lambda$initData$1$HistoryDetailActivity(BluetoothDevice device, final List heartRates) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryDetailActivity$cx_CGuXefg4p0GlzhUycDY8GMLo
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$0$HistoryDetailActivity(heartRates);
            }
        });
    }

    public /* synthetic */ void lambda$initData$0$HistoryDetailActivity(List heartRates) {
        Timber.d("heartRates:%d %s", Integer.valueOf(heartRates.size()), heartRates.toString());
        updateHeartRates(heartRates);
        hideLoading();
    }

    public /* synthetic */ void lambda$initData$3$HistoryDetailActivity(BluetoothDevice device, final List respiratoryRates) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryDetailActivity$AXBc_uRKjsy0P3aXu26jAbOkBt0
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$2$HistoryDetailActivity(respiratoryRates);
            }
        });
    }

    public /* synthetic */ void lambda$initData$2$HistoryDetailActivity(List respiratoryRates) {
        Timber.d("respiratoryRates:%d %s", Integer.valueOf(respiratoryRates.size()), respiratoryRates.toString());
        updateRespiratoryRates(respiratoryRates);
        hideLoading();
    }

    public /* synthetic */ void lambda$initData$5$HistoryDetailActivity(BluetoothDevice device, final List steps) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistoryDetailActivity$1XHFO40tJI3lUv24zQZkKzaN7TY
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$initData$4$HistoryDetailActivity(steps);
            }
        });
    }

    public /* synthetic */ void lambda$initData$4$HistoryDetailActivity(List steps) {
        Timber.d("steps:%d %s", Integer.valueOf(steps.size()), steps.toString());
        updateSteps(steps);
        hideLoading();
    }

    private void initChart() {
        this.mChart.setNoDataText("");
        this.mChart.setTouchEnabled(true);
        this.mChart.setScaleEnabled(true);
        this.mChart.setPinchZoom(false);
        this.mChart.getDescription().setEnabled(false);
        this.mChart.getLegend().setEnabled(true);
        this.mChart.setScaleYEnabled(false);
        this.mChart.setScaleXEnabled(true);
        this.mChart.setDragEnabled(true);
        this.mChart.getAxisLeft().setDrawGridLines(true);
        this.mChart.getAxisLeft().setDrawAxisLine(true);
        this.mChart.getAxisLeft().setEnabled(true);
        this.mChart.getAxisLeft().setAxisMinimum(0.0f);
        this.mChart.getAxisRight().setEnabled(false);
        this.mChart.getXAxis().setTextSize(8.0f);
        this.mChart.getXAxis().setGranularity(1.0f);
        this.mChart.getXAxis().setDrawAxisLine(true);
        this.mChart.getXAxis().setDrawGridLines(false);
        this.mChart.getXAxis().setPosition(XAxis.XAxisPosition.BOTTOM);
    }

    private void updateHeartRates(List<HistoryOfHeartRate> heartRates) {
        List<Entry> values = new ArrayList<>();
        List<String> stamps = new ArrayList<>();
        for (int i = 0; i < heartRates.size(); i++) {
            HistoryOfHeartRate history = heartRates.get(i);
            values.add(new Entry(i, history.heartRate));
            stamps.add(this.mDateFormat.format(new Date(history.stamp)));
        }
        this.mChart.resetTracking();
        LineDataSet dataSet = new LineDataSet(values, "Heart rate");
        dataSet.setValueTextSize(8.0f);
        dataSet.setCircleRadius(1.5f);
        dataSet.setColor(SupportMenu.CATEGORY_MASK);
        dataSet.setFillColor(SupportMenu.CATEGORY_MASK);
        dataSet.setCircleColor(SupportMenu.CATEGORY_MASK);
        dataSet.setCircleHoleColor(SupportMenu.CATEGORY_MASK);
        dataSet.setValueTextColor(SupportMenu.CATEGORY_MASK);
        dataSet.setLineWidth(1.0f);
        dataSet.setDrawValues(true);
        dataSet.setDrawCircles(true);
        dataSet.setHighlightEnabled(false);
        dataSet.setMode(LineDataSet.Mode.LINEAR);
        dataSet.setDrawFilled(false);
        this.mChart.getXAxis().setValueFormatter(new StampValueFormatter(stamps));
        LineData data = new LineData(dataSet);
        this.mChart.setData(data);
        this.mChart.invalidate();
    }

    private void updateRespiratoryRates(List<HistoryOfRespiratoryRate> respiratoryRates) {
        List<Entry> values = new ArrayList<>();
        List<String> stamps = new ArrayList<>();
        for (int i = 0; i < respiratoryRates.size(); i++) {
            HistoryOfRespiratoryRate history = respiratoryRates.get(i);
            values.add(new Entry(i, history.respiratoryRate));
            stamps.add(this.mDateFormat.format(new Date(history.stamp)));
        }
        this.mChart.resetTracking();
        LineDataSet dataSet = new LineDataSet(values, "RR");
        dataSet.setValueTextSize(8.0f);
        dataSet.setCircleRadius(1.5f);
        dataSet.setColor(-16776961);
        dataSet.setFillColor(-16776961);
        dataSet.setCircleColor(-16776961);
        dataSet.setValueTextColor(-16776961);
        dataSet.setLineWidth(1.0f);
        dataSet.setDrawValues(true);
        dataSet.setDrawCircles(true);
        dataSet.setHighlightEnabled(false);
        dataSet.setMode(LineDataSet.Mode.LINEAR);
        dataSet.setDrawFilled(false);
        this.mChart.getXAxis().setValueFormatter(new StampValueFormatter(stamps));
        LineData data = new LineData(dataSet);
        this.mChart.setData(data);
        this.mChart.invalidate();
    }

    private void updateSteps(List<HistoryOfStep> steps) {
        List<Entry> values = new ArrayList<>();
        List<String> stamps = new ArrayList<>();
        for (int i = 0; i < steps.size(); i++) {
            HistoryOfStep history = steps.get(i);
            values.add(new Entry(i, history.steps));
            stamps.add(this.mDateFormat.format(new Date(history.stamp)));
        }
        this.mChart.resetTracking();
        LineDataSet dataSet = new LineDataSet(values, "Step");
        dataSet.setValueTextSize(8.0f);
        dataSet.setCircleRadius(1.5f);
        dataSet.setColor(-16776961);
        dataSet.setFillColor(-16776961);
        dataSet.setCircleColor(-16776961);
        dataSet.setValueTextColor(-16776961);
        dataSet.setLineWidth(1.0f);
        dataSet.setDrawValues(true);
        dataSet.setDrawCircles(true);
        dataSet.setHighlightEnabled(false);
        dataSet.setMode(LineDataSet.Mode.LINEAR);
        dataSet.setDrawFilled(false);
        this.mChart.getXAxis().setValueFormatter(new StampValueFormatter(stamps));
        LineData data = new LineData(dataSet);
        this.mChart.setData(data);
        this.mChart.invalidate();
    }

    private static class StampValueFormatter extends ValueFormatter {
        private final List<String> stamps;

        private StampValueFormatter(List<String> stamps) {
            this.stamps = stamps;
        }

        @Override // com.github.mikephil.charting.formatter.ValueFormatter
        public String getFormattedValue(float value) {
            int index = (int) value;
            if (index >= 0 && index < this.stamps.size()) {
                return this.stamps.get(index);
            }
            return "";
        }
    }
}
