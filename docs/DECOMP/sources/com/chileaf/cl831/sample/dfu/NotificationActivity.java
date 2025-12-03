package com.chileaf.cl831.sample.dfu;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import com.chileaf.cl831.sample.MainActivity;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes4.dex */
public class NotificationActivity extends Activity {
    @Override // android.app.Activity
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (isTaskRoot()) {
            Intent parentIntent = new Intent(this, (Class<?>) MainActivity.class);
            parentIntent.addFlags(268435456);
            Intent startAppIntent = new Intent(this, (Class<?>) DfuActivity.class);
            startAppIntent.putExtras(getIntent().getExtras());
            startActivities(new Intent[]{parentIntent, startAppIntent});
        }
        finish();
    }
}
