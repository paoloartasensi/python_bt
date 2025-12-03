package com.android.chileaf.fitness.common;

import java.util.List;
import no.nordicsemi.android.support.v18.scanner.ScanResult;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public interface FilterScanCallback {
    void onBatchScanResults(final List<ScanResult> results);

    void onFilterScanResults(final List<ScanResult> results);

    void onScanFailed(final int errorCode);

    void onScanResult(final int callbackType, final ScanResult result);

    /* renamed from: com.android.chileaf.fitness.common.FilterScanCallback$-CC, reason: invalid class name */
    public final /* synthetic */ class CC {
        public static void $default$onScanResult(FilterScanCallback _this, int callbackType, ScanResult result) {
        }

        public static void $default$onBatchScanResults(FilterScanCallback _this, List list) {
        }

        public static void $default$onScanFailed(FilterScanCallback _this, int errorCode) {
        }
    }
}
