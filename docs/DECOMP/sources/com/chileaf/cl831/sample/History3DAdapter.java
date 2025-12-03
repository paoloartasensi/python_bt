package com.chileaf.cl831.sample;

import com.android.chileaf.model.HistoryOf3D;
import com.chad.library.adapter.base.BaseQuickAdapter;
import com.chad.library.adapter.base.viewholder.BaseViewHolder;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Locale;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class History3DAdapter extends BaseQuickAdapter<HistoryOf3D, BaseViewHolder> {
    private SimpleDateFormat mDateFormat;

    public History3DAdapter() {
        super(R.layout.item_history, new ArrayList());
        this.mDateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault());
    }

    /* JADX INFO: Access modifiers changed from: protected */
    @Override // com.chad.library.adapter.base.BaseQuickAdapter
    public void convert(BaseViewHolder helper, HistoryOf3D history) {
        helper.setText(R.id.tv_history, "X,Y,Z:[ " + history.accX + ", " + history.accY + ", " + history.accZ + " ]");
    }
}
