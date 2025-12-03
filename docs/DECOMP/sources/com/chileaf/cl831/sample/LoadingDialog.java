package com.chileaf.cl831.sample;

import android.app.Activity;
import android.content.Context;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatDialog;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class LoadingDialog extends AppCompatDialog {
    private View mRoot;

    public LoadingDialog(Builder builder) {
        this(builder, builder.context, R.style.DialogStyle);
    }

    public LoadingDialog(Builder builder, Context context, int theme) {
        super(context, theme);
        View viewInflate = LayoutInflater.from(context).inflate(R.layout.dialog_loading, (ViewGroup) null);
        this.mRoot = viewInflate;
        TextView tvLoading = (TextView) viewInflate.findViewById(R.id.tv_loading);
        if (!TextUtils.isEmpty(builder.message)) {
            tvLoading.setVisibility(0);
            tvLoading.setText(builder.message);
        } else {
            tvLoading.setVisibility(8);
        }
        setCanceledOnTouchOutside(false);
        setCancelable(false);
    }

    @Override // androidx.appcompat.app.AppCompatDialog, androidx.activity.ComponentDialog, android.app.Dialog
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(this.mRoot);
    }

    public static Builder Builder(Activity activity) {
        return new Builder(activity);
    }

    public static final class Builder {
        private Context context;
        private String message;

        private Builder(Context context) {
            this.context = context;
        }

        public Builder setMessage(String message) {
            this.message = message;
            return this;
        }

        public LoadingDialog build() {
            return new LoadingDialog(this);
        }
    }
}
