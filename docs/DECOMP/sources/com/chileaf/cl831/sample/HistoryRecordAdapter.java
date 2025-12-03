package com.chileaf.cl831.sample;

import android.widget.TextView;
import com.android.chileaf.model.HistoryOfRecord;
import com.chad.library.adapter.base.BaseQuickAdapter;
import com.chad.library.adapter.base.viewholder.BaseViewHolder;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.Locale;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class HistoryRecordAdapter extends BaseQuickAdapter<HistoryOfRecord, BaseViewHolder> {
    private SimpleDateFormat mDateFormat;

    public HistoryRecordAdapter() {
        super(R.layout.item_history, new ArrayList());
        this.mDateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault());
    }

    /* JADX INFO: Access modifiers changed from: protected */
    @Override // com.chad.library.adapter.base.BaseQuickAdapter
    public void convert(BaseViewHolder helper, HistoryOfRecord history) {
        String date = this.mDateFormat.format(new Date(history.record));
        TextView tvHistory = (TextView) helper.getView(R.id.tv_history);
        tvHistory.setTextSize(20.0f);
        tvHistory.setText(date);
    }
}
