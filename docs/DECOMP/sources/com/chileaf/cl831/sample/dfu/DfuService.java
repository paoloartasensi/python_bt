package com.chileaf.cl831.sample.dfu;

import android.app.Activity;
import no.nordicsemi.android.dfu.DfuBaseService;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes4.dex */
public class DfuService extends DfuBaseService {
    @Override // no.nordicsemi.android.dfu.DfuBaseService
    protected Class<? extends Activity> getNotificationTarget() {
        return NotificationActivity.class;
    }

    @Override // no.nordicsemi.android.dfu.DfuBaseService
    protected boolean isDebug() {
        return true;
    }
}
