package com.chileaf.cl831.sample;

import android.bluetooth.BluetoothDevice;
import android.os.Bundle;
import androidx.appcompat.widget.AppCompatTextView;
import com.android.chileaf.fitness.callback.TemperatureCallback;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class TemperatureActivity extends BaseActivity implements TemperatureCallback {
    private AppCompatTextView text1;
    private AppCompatTextView text2;
    private AppCompatTextView text3;

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected int layoutId() {
        return R.layout.activity_temperature;
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initView() {
        this.text1 = (AppCompatTextView) findViewById(R.id.tv_environment);
        this.text2 = (AppCompatTextView) findViewById(R.id.tv_wrist_temperature);
        this.text3 = (AppCompatTextView) findViewById(R.id.tv_temperature);
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initData(Bundle savedInstanceState) {
        this.mManager.addTemperatureCallback(this);
    }

    @Override // com.android.chileaf.fitness.callback.TemperatureCallback
    public void onTemperatureReceived(BluetoothDevice device, final float environment, final float wrist, final float body) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$TemperatureActivity$auWrc3wOe9z4UBVXtXCcJK5pIxg
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onTemperatureReceived$0$TemperatureActivity(environment, wrist, body);
            }
        });
    }

    public /* synthetic */ void lambda$onTemperatureReceived$0$TemperatureActivity(float environment, float wrist, float body) {
        this.text1.setText(environment + "");
        this.text2.setText(wrist + "");
        this.text3.setText(body + "");
    }
}
