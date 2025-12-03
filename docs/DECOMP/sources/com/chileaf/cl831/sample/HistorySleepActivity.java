package com.chileaf.cl831.sample;

import android.bluetooth.BluetoothDevice;
import android.os.Bundle;
import android.util.Log;
import android.widget.ArrayAdapter;
import android.widget.ListAdapter;
import android.widget.ListView;
import android.widget.TextView;
import com.android.chileaf.fitness.callback.HistoryOfSleepCallback;
import com.android.chileaf.model.HistorySleep;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class HistorySleepActivity extends BaseActivity implements HistoryOfSleepCallback {
    private static final SimpleDateFormat mFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault());
    private ArrayAdapter mArrayAdapter;
    private ListView mListView;
    private List<String> strings = new ArrayList();

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected int layoutId() {
        return R.layout.activity_sleepdata;
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initView() {
        TextView mTvToolbarTitle = (TextView) findViewById(R.id.tv_toolbar_title);
        mTvToolbarTitle.setText("Get Sleep Data");
        this.mListView = (ListView) findViewById(R.id.listView);
        ArrayAdapter arrayAdapter = new ArrayAdapter(this, android.R.layout.simple_list_item_1, this.strings);
        this.mArrayAdapter = arrayAdapter;
        this.mListView.setAdapter((ListAdapter) arrayAdapter);
        showLoadingAutoDismiss(2000L);
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initData(Bundle savedInstanceState) {
        this.mManager.addHistoryOfSleepCallback(this);
        this.mManager.getHistoryOfSleep();
    }

    @Override // com.android.chileaf.fitness.callback.HistoryOfSleepCallback
    public void onHistoryOfSleepReceived(BluetoothDevice device, final List<HistorySleep> sleeps) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$HistorySleepActivity$uUHSkZwx_WE3Mw607aSJo5kppfE
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onHistoryOfSleepReceived$0$HistorySleepActivity(sleeps);
            }
        });
    }

    public /* synthetic */ void lambda$onHistoryOfSleepReceived$0$HistorySleepActivity(List sleeps) {
        long utc;
        int i1;
        for (int i = 0; i < sleeps.size(); i++) {
            HistorySleep sleep = (HistorySleep) sleeps.get(i);
            int[] actions = sleep.actions;
            int len = actions.length;
            long utc2 = sleep.utc;
            int index = 0;
            long utc22 = 0;
            String text = "";
            int i12 = 0;
            while (i12 < len) {
                int action = actions[i12];
                HistorySleep sleep2 = sleep;
                StringBuilder sb = new StringBuilder();
                int[] actions2 = actions;
                sb.append("action: ");
                sb.append(action);
                Log.d("", sb.toString());
                long utc1 = (i12 * 300000) + utc2;
                int len2 = len;
                if (action > 20) {
                    if (index >= 3) {
                        utc = utc2;
                        long utc3 = utc22 - (index * 300000);
                        int i2 = 0;
                        while (i2 < index) {
                            text = text + "\nutc:" + millsToDate(Long.valueOf((i2 * 300000) + utc3)) + "\naction Index: deep Sleep";
                            i2++;
                            i12 = i12;
                        }
                        i1 = i12;
                    } else {
                        utc = utc2;
                        i1 = i12;
                        if (index > 0) {
                            long utc32 = utc22 - (index * 300000);
                            int i22 = 0;
                            while (i22 < index) {
                                StringBuilder sb2 = new StringBuilder();
                                sb2.append(text);
                                sb2.append("\nutc:");
                                long utc23 = utc22;
                                long utc24 = i22 * 300000;
                                sb2.append(millsToDate(Long.valueOf(utc24 + utc32)));
                                sb2.append("\naction Index: light sleep");
                                text = sb2.toString();
                                i22++;
                                utc22 = utc23;
                            }
                        }
                    }
                    utc22 = 0;
                    text = text + "\nutc:" + millsToDate(Long.valueOf(utc1)) + "\naction Index: not Sleep";
                    index = 0;
                } else {
                    utc = utc2;
                    long utc25 = utc22;
                    i1 = i12;
                    if (action <= 20 && action > 0) {
                        if (index >= 3) {
                            long utc33 = utc25 - (index * 300000);
                            for (int i23 = 0; i23 < index; i23++) {
                                text = text + "\nutc:" + millsToDate(Long.valueOf((i23 * 300000) + utc33)) + "\naction Index: deep Sleep";
                            }
                        } else if (index > 0) {
                            long utc34 = utc25 - (index * 300000);
                            for (int i24 = 0; i24 < index; i24++) {
                                text = text + "\nutc:" + millsToDate(Long.valueOf((i24 * 300000) + utc34)) + "\naction Index: light sleep";
                            }
                        }
                        utc22 = 0;
                        text = text + "\nutc:" + millsToDate(Long.valueOf(utc1)) + "\naction Index: light sleep";
                        index = 0;
                    } else {
                        index++;
                        utc22 = utc1;
                    }
                }
                i12 = i1 + 1;
                sleep = sleep2;
                actions = actions2;
                len = len2;
                utc2 = utc;
            }
            long utc26 = utc22;
            if (index >= 3) {
                long utc35 = utc26 - (index * 300000);
                for (int i25 = 0; i25 < index; i25++) {
                    text = text + "\nutc:" + millsToDate(Long.valueOf((i25 * 300000) + utc35)) + "\naction Index: deep Sleep";
                }
            } else if (index > 0) {
                long utc36 = utc26 - (index * 300000);
                for (int i26 = 0; i26 < index; i26++) {
                    text = text + "\nutc:" + millsToDate(Long.valueOf((i26 * 300000) + utc36)) + "\naction Index: light sleep";
                }
            }
            this.strings.add(text);
        }
        this.mArrayAdapter.notifyDataSetChanged();
    }

    private String millsToDate(Long time) {
        Date dt = new Date(time.longValue());
        return mFormat.format(dt);
    }
}
