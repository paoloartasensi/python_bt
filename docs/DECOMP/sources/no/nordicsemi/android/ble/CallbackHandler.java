package no.nordicsemi.android.ble;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
interface CallbackHandler {
    void post(Runnable runnable);

    void postDelayed(Runnable runnable, long j);

    void removeCallbacks(Runnable runnable);
}
