package com.chileaf.cl831.sample;

import android.bluetooth.BluetoothDevice;
import android.os.Bundle;
import androidx.appcompat.widget.AppCompatTextView;
import com.android.chileaf.fitness.callback.BodySportHealthCallback;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class SportHealthActivity extends BaseActivity implements BodySportHealthCallback {
    private AppCompatTextView mTvSportHealth;

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected int layoutId() {
        return R.layout.activity_sport_health;
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initView() {
        setTitle("Sport health");
        this.mTvSportHealth = (AppCompatTextView) findViewById(R.id.tv_sport_health);
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initData(Bundle savedInstanceState) {
        this.mManager.addBodySportHealthCallback(this);
    }

    @Override // com.android.chileaf.fitness.callback.BodySportHealthCallback
    public void onSportHealthReceived(BluetoothDevice device, final int vo2Max, final int breathRate, final int emotion, final int pressure, final int stamina) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$SportHealthActivity$v_NPfuJqN25RmIfL2Yc7TXrltzc
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onSportHealthReceived$0$SportHealthActivity(vo2Max, breathRate, emotion, pressure, stamina);
            }
        });
    }

    public /* synthetic */ void lambda$onSportHealthReceived$0$SportHealthActivity(int vo2Max, int breathRate, int emotion, int pressure, int stamina) {
        this.mTvSportHealth.setText("Sport health \nvo2Max:" + vo2Max + "\nbreathRate:" + breathRate + "\nemotion:" + getEmotion(emotion) + "\npressure:" + pressure + "%\nstamina:" + getStamina(stamina));
    }
}
