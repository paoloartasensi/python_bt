package no.nordicsemi.android.ble.utils;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface ILogger {
    int getMinLogPriority();

    void log(int i, int i2, Object... objArr);

    void log(int i, String str);
}
