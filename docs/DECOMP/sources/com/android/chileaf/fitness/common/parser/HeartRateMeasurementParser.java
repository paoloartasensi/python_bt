package com.android.chileaf.fitness.common.parser;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import no.nordicsemi.android.ble.data.Data;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public class HeartRateMeasurementParser {
    private static final byte ENERGY_EXPANDED_STATUS = 8;
    private static final byte HEART_RATE_VALUE_FORMAT = 1;
    private static final byte RR_INTERVAL = 16;
    private static final byte SENSOR_CONTACT_STATUS = 6;

    public static String parse(final Data data) {
        int offset = 0 + 1;
        int flags = data.getIntValue(17, 0).intValue();
        char c = 0;
        boolean value16bit = (flags & 1) > 0;
        int sensorContactStatus = (flags & 6) >> 1;
        boolean energyExpandedStatus = (flags & 8) > 0;
        boolean rrIntervalStatus = (flags & 16) > 0;
        int offset2 = offset + 1;
        int heartRateValue = data.getIntValue(value16bit ? 18 : 17, offset).intValue();
        if (value16bit) {
            offset2++;
        }
        int energyExpanded = -1;
        if (energyExpandedStatus) {
            energyExpanded = data.getIntValue(18, offset2).intValue();
        }
        int offset3 = offset2 + 2;
        List<Float> rrIntervals = new ArrayList<>();
        if (rrIntervalStatus) {
            for (int o = offset3; o < data.getValue().length; o += 2) {
                int units = data.getIntValue(18, o).intValue();
                rrIntervals.add(Float.valueOf((units * 1000.0f) / 1024.0f));
            }
        }
        StringBuilder builder = new StringBuilder();
        builder.append("Heart Rate Measurement: ");
        builder.append(heartRateValue);
        builder.append(" bpm");
        switch (sensorContactStatus) {
            case 0:
            case 1:
                builder.append(",Sensor Contact Not Supported");
                break;
            case 2:
                builder.append(",Contact is NOT Detected");
                break;
            case 3:
                builder.append(",Contact is Detected");
                break;
        }
        if (energyExpandedStatus) {
            builder.append(",Energy Expanded: ");
            builder.append(energyExpanded);
            builder.append(" kJ");
        }
        if (rrIntervalStatus) {
            builder.append(",RR Interval: ");
            for (Float interval : rrIntervals) {
                Locale locale = Locale.US;
                Object[] objArr = new Object[1];
                objArr[c] = interval;
                builder.append(String.format(locale, "%.02f ms, ", objArr));
                c = 0;
            }
            builder.setLength(builder.length() - 2);
        }
        return builder.toString();
    }
}
