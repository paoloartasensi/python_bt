package com.chileaf.cl831.sample;

import com.android.chileaf.model.HistoryOfSport;
import com.chad.library.adapter.base.BaseQuickAdapter;
import com.chad.library.adapter.base.viewholder.BaseViewHolder;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.Locale;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class HistorySportAdapter extends BaseQuickAdapter<HistoryOfSport, BaseViewHolder> {
    private SimpleDateFormat mDateFormat;

    public HistorySportAdapter() {
        super(R.layout.item_history, new ArrayList());
        this.mDateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault());
    }

    /* JADX INFO: Access modifiers changed from: protected */
    @Override // com.chad.library.adapter.base.BaseQuickAdapter
    public void convert(BaseViewHolder helper, HistoryOfSport history) {
        StringBuilder item = new StringBuilder();
        String date = this.mDateFormat.format(new Date(history.startTime));
        item.append("Date time:");
        item.append(date);
        item.append("\n");
        item.append("Step:");
        item.append(history.step);
        item.append("步\n");
        item.append("Calorie:");
        item.append(String.format("%.1f", Float.valueOf(history.calorie / 10.0f)));
        item.append("CAL");
        helper.setText(R.id.tv_history, item.toString());
    }
}
