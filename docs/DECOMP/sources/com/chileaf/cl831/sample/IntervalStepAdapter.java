package com.chileaf.cl831.sample;

import com.android.chileaf.model.IntervalStep;
import com.chad.library.adapter.base.BaseQuickAdapter;
import com.chad.library.adapter.base.viewholder.BaseViewHolder;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.Locale;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class IntervalStepAdapter extends BaseQuickAdapter<IntervalStep, BaseViewHolder> {
    private SimpleDateFormat mDateFormat;

    public IntervalStepAdapter() {
        super(R.layout.item_history, new ArrayList());
        this.mDateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault());
    }

    /* JADX INFO: Access modifiers changed from: protected */
    @Override // com.chad.library.adapter.base.BaseQuickAdapter
    public void convert(BaseViewHolder helper, IntervalStep interval) {
        StringBuilder item = new StringBuilder();
        String date = this.mDateFormat.format(new Date(interval.stamp));
        item.append("Date time : ");
        item.append(date);
        item.append("\n");
        item.append("Steps : ");
        item.append(interval.steps);
        item.append("\n");
        helper.setText(R.id.tv_history, item.toString());
    }
}
