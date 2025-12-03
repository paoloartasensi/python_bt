package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface UserInfoCallback {
    void onUserInfoReceived(final BluetoothDevice device, final int age, final int sex, final int weight, final int height, final long userId);
}
