package com.chileaf.cl831.sample;

import android.bluetooth.BluetoothDevice;
import android.os.Bundle;
import android.widget.CompoundButton;
import android.widget.Switch;
import androidx.appcompat.widget.AppCompatTextView;
import com.android.chileaf.fitness.callback.BloodOxygenCallback;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class BloodOxygenActivity extends BaseActivity implements BloodOxygenCallback {
    private Switch aSwitch;
    private AppCompatTextView text1;
    private AppCompatTextView text2;
    private AppCompatTextView text3;
    private AppCompatTextView text4;

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected int layoutId() {
        return R.layout.activity_blood_oxygen;
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initView() {
        Switch r0 = (Switch) findViewById(R.id.sh_blood);
        this.aSwitch = r0;
        r0.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$BloodOxygenActivity$ZSvkh0X22hpy4k4qTM67OxxI2X0
            @Override // android.widget.CompoundButton.OnCheckedChangeListener
            public final void onCheckedChanged(CompoundButton compoundButton, boolean z) {
                this.f$0.lambda$initView$0$BloodOxygenActivity(compoundButton, z);
            }
        });
        this.text1 = (AppCompatTextView) findViewById(R.id.tv_blood);
        this.text2 = (AppCompatTextView) findViewById(R.id.tv_wrist);
        this.text3 = (AppCompatTextView) findViewById(R.id.tv_pi);
        this.text4 = (AppCompatTextView) findViewById(R.id.tv_onwrist);
        showToast("Please wear tightly and relax your body.");
    }

    public /* synthetic */ void lambda$initView$0$BloodOxygenActivity(CompoundButton compoundButton, boolean b) {
        if (b) {
            this.mManager.setBloodOxygen(1);
        } else {
            this.mManager.setBloodOxygen(0);
        }
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initData(Bundle savedInstanceState) {
        this.mManager.addBloodOxygenCallback(this);
    }

    @Override // com.android.chileaf.fitness.callback.BloodOxygenCallback
    public void onBloodOxygenReceived(BluetoothDevice device, final int bSwitch, final String value, final int gesture, final int piValue, final int onwrist) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$BloodOxygenActivity$uftJq8kBjQEB4Nz3PX5nLbMTcos
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onBloodOxygenReceived$1$BloodOxygenActivity(bSwitch, value, gesture, piValue, onwrist);
            }
        });
    }

    public /* synthetic */ void lambda$onBloodOxygenReceived$1$BloodOxygenActivity(int bSwitch, String value, int gesture, int piValue, int onwrist) {
        this.aSwitch.setChecked(bSwitch == 1);
        if (value == "" || value == null) {
            return;
        }
        this.text1.setText(value + "");
        if (gesture == 0) {
            this.text2.setText("Wrong wrist posture");
        } else if (gesture == 1) {
            this.text2.setText("Wear the correct posture");
        }
        if (piValue == 0) {
            this.text3.setText("No pulse detected");
        } else if (piValue < 8) {
            this.text3.setText("Weak signal");
        } else if (piValue < 15) {
            this.text3.setText("Good signal");
        } else if (piValue >= 15) {
            this.text3.setText("Excellent signal");
        }
        if (onwrist == 0) {
            this.text4.setText("Off the wrist");
        } else if (onwrist == 1) {
            this.text4.setText("Worn");
        }
    }
}
