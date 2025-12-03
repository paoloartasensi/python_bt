package com.android.chileaf.util;

import java.util.Calendar;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public class DateUtil {
    public static long getZoneUTC() {
        Calendar calendar = Calendar.getInstance();
        int zoneOffset = calendar.get(15);
        int dstOffset = calendar.get(16);
        calendar.add(14, zoneOffset + dstOffset);
        return calendar.getTimeInMillis() / 1000;
    }

    public static long restoreZoneUTC(final long stamp) {
        Calendar calendar = Calendar.getInstance();
        calendar.setTimeInMillis(1000 * stamp);
        int zoneOffset = calendar.get(15);
        int dstOffset = calendar.get(16);
        calendar.add(14, -(zoneOffset + dstOffset));
        return calendar.getTimeInMillis();
    }

    public static long restoreZoneUTCTimeInMillis(final long stamp) {
        Calendar calendar = Calendar.getInstance();
        calendar.setTimeInMillis(stamp);
        int zoneOffset = calendar.get(15);
        int dstOffset = calendar.get(16);
        calendar.add(14, -(zoneOffset + dstOffset));
        return calendar.getTimeInMillis();
    }
}
