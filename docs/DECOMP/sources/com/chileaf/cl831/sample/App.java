package com.chileaf.cl831.sample;

import android.app.Application;
import android.os.Build;
import no.nordicsemi.android.dfu.DfuServiceInitiator;
import timber.log.Timber;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class App extends Application {
    @Override // android.app.Application
    public void onCreate() {
        super.onCreate();
        if (BuildConfig.DEBUG) {
            Timber.plant(new Timber.DebugTree());
        }
        if (Build.VERSION.SDK_INT >= 26) {
            DfuServiceInitiator.createDfuNotificationChannel(this);
        }
    }
}
