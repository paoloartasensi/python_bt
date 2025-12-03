package com.chileaf.cl831.sample;

import android.bluetooth.BluetoothDevice;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.view.View;
import android.widget.EditText;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import com.android.chileaf.fitness.callback.UserInfoCallback;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class UserInfoActivity extends BaseActivity implements UserInfoCallback {
    private int mAge;
    private EditText mEtAge;
    private EditText mEtHeight;
    private EditText mEtUserId;
    private EditText mEtWeight;
    private int mHeight;
    private RadioButton mRbFemale;
    private RadioButton mRbMale;
    private RadioGroup mRgSex;
    private int mSex;
    private long mUserId;
    private int mWeight;

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected int layoutId() {
        return R.layout.activity_user_info;
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initView() {
        this.mEtAge = (EditText) findViewById(R.id.et_age);
        this.mEtHeight = (EditText) findViewById(R.id.et_height);
        this.mEtWeight = (EditText) findViewById(R.id.et_weight);
        this.mEtUserId = (EditText) findViewById(R.id.et_user_id);
        this.mRgSex = (RadioGroup) findViewById(R.id.rg_sex);
        this.mRbMale = (RadioButton) findViewById(R.id.rb_male);
        this.mRbFemale = (RadioButton) findViewById(R.id.rb_female);
        this.mEtAge.addTextChangedListener(new SimpleTextWatcher() { // from class: com.chileaf.cl831.sample.UserInfoActivity.1
            @Override // android.text.TextWatcher
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                if (!TextUtils.isEmpty(s)) {
                    UserInfoActivity.this.mAge = Integer.parseInt(s.toString());
                }
            }
        });
        this.mRgSex.setOnCheckedChangeListener(new RadioGroup.OnCheckedChangeListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$UserInfoActivity$pzNtObYZhO67yGBFOMSG7KjQz7Q
            @Override // android.widget.RadioGroup.OnCheckedChangeListener
            public final void onCheckedChanged(RadioGroup radioGroup, int i) {
                this.f$0.lambda$initView$0$UserInfoActivity(radioGroup, i);
            }
        });
        this.mEtHeight.addTextChangedListener(new SimpleTextWatcher() { // from class: com.chileaf.cl831.sample.UserInfoActivity.2
            @Override // android.text.TextWatcher
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                if (!TextUtils.isEmpty(s)) {
                    UserInfoActivity.this.mHeight = Integer.parseInt(s.toString());
                }
            }
        });
        this.mEtWeight.addTextChangedListener(new SimpleTextWatcher() { // from class: com.chileaf.cl831.sample.UserInfoActivity.3
            @Override // android.text.TextWatcher
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                if (!TextUtils.isEmpty(s)) {
                    UserInfoActivity.this.mWeight = Integer.parseInt(s.toString());
                }
            }
        });
        this.mEtUserId.addTextChangedListener(new SimpleTextWatcher() { // from class: com.chileaf.cl831.sample.UserInfoActivity.4
            @Override // android.text.TextWatcher
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                if (!TextUtils.isEmpty(s)) {
                    UserInfoActivity.this.mUserId = Long.parseLong(s.toString());
                }
            }
        });
        findViewById(R.id.btn_get_user).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$UserInfoActivity$UhuIkNjDk89cYIpFLRq7ORRh07w
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$1$UserInfoActivity(view);
            }
        });
        findViewById(R.id.btn_set_user).setOnClickListener(new View.OnClickListener() { // from class: com.chileaf.cl831.sample.-$$Lambda$UserInfoActivity$HDFH9PJme8DyYaa73yTwPRdg1e8
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.lambda$initView$2$UserInfoActivity(view);
            }
        });
    }

    public /* synthetic */ void lambda$initView$0$UserInfoActivity(RadioGroup group, int checkedId) {
        this.mSex = checkedId == 2131231121 ? 1 : 0;
    }

    public /* synthetic */ void lambda$initView$1$UserInfoActivity(View view) {
        this.mManager.getUserInfo();
    }

    public /* synthetic */ void lambda$initView$2$UserInfoActivity(View view) {
        if (isEmpty(this.mEtAge, this.mAge)) {
            showToast("Please input the correct age");
            return;
        }
        if (isEmpty(this.mEtHeight, this.mHeight)) {
            showToast("Please input the correct height");
            return;
        }
        if (isEmpty(this.mEtWeight, this.mWeight)) {
            showToast("Please input the correct weigh");
        } else if (isEmpty(this.mEtUserId, this.mUserId)) {
            showToast("Please input the correct user id");
        } else {
            this.mManager.setUserInfo(this.mAge, this.mSex, this.mWeight, this.mHeight, this.mUserId);
            showToast("Set success");
        }
    }

    @Override // com.chileaf.cl831.sample.BaseActivity
    protected void initData(Bundle savedInstanceState) {
        setTitle("User information");
        this.mManager.addUserInfoCallback(this);
    }

    private boolean isEmpty(EditText view, long value) {
        return view.getText().toString().isEmpty() || value == 0;
    }

    @Override // com.android.chileaf.fitness.callback.UserInfoCallback
    public void onUserInfoReceived(BluetoothDevice device, final int age, final int sex, final int weight, final int height, final long userId) {
        runOnUiThread(new Runnable() { // from class: com.chileaf.cl831.sample.-$$Lambda$UserInfoActivity$CRKQWGqwCI2uUz5ErF3xFqcbEGY
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.lambda$onUserInfoReceived$3$UserInfoActivity(age, height, weight, userId, sex);
            }
        });
    }

    public /* synthetic */ void lambda$onUserInfoReceived$3$UserInfoActivity(int age, int height, int weight, long userId, int sex) {
        this.mEtAge.setText(String.valueOf(age));
        this.mEtHeight.setText(String.valueOf(height));
        this.mEtWeight.setText(String.valueOf(weight));
        this.mEtUserId.setText(String.valueOf(userId));
        this.mRbMale.setChecked(sex == 1);
        this.mRbFemale.setChecked(sex == 0);
    }

    private static abstract class SimpleTextWatcher implements TextWatcher {
        private SimpleTextWatcher() {
        }

        @Override // android.text.TextWatcher
        public void beforeTextChanged(CharSequence s, int start, int count, int after) {
        }

        @Override // android.text.TextWatcher
        public void afterTextChanged(Editable s) {
        }
    }
}
