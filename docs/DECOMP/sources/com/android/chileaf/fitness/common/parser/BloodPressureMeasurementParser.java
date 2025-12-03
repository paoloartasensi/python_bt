package com.android.chileaf.fitness.common.parser;

import no.nordicsemi.android.ble.data.Data;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public class BloodPressureMeasurementParser {
    public static String parse(final Data data) {
        StringBuilder builder = new StringBuilder();
        int offset = 0 + 1;
        int flags = data.getIntValue(17, 0).intValue();
        int unitType = flags & 1;
        boolean timestampPresent = (flags & 2) > 0;
        boolean pulseRatePresent = (flags & 4) > 0;
        boolean userIdPresent = (flags & 8) > 0;
        boolean statusPresent = (flags & 16) > 0;
        float systolic = data.getFloatValue(50, offset).floatValue();
        float diastolic = data.getFloatValue(50, offset + 2).floatValue();
        float meanArterialPressure = data.getFloatValue(50, offset + 4).floatValue();
        String unit = unitType == 0 ? " mmHg" : " kPa";
        int offset2 = offset + 6;
        builder.append("Systolic: ");
        builder.append(systolic);
        builder.append(unit);
        builder.append(" Diastolic: ");
        builder.append(diastolic);
        builder.append(unit);
        builder.append(" Mean AP: ");
        builder.append(meanArterialPressure);
        builder.append(unit);
        if (timestampPresent) {
            builder.append(" Timestamp: ");
            builder.append(DateTimeParser.parse(data, offset2));
            offset2 += 7;
        }
        if (pulseRatePresent) {
            float pulseRate = data.getFloatValue(50, offset2).floatValue();
            offset2 += 2;
            builder.append(" Pulse: ");
            builder.append(pulseRate);
            builder.append(" bpm");
        }
        if (userIdPresent) {
            int userId = data.getIntValue(17, offset2).intValue();
            offset2++;
            builder.append(" User ID: ");
            builder.append(userId);
        }
        if (statusPresent) {
            int status = data.getIntValue(18, offset2).intValue();
            if ((status & 1) > 0) {
                builder.append(" Body movement detected");
            }
            if ((status & 2) > 0) {
                builder.append(" Cuff too lose");
            }
            if ((status & 4) > 0) {
                builder.append(" Irregular pulse detected");
            }
            if ((status & 24) == 8) {
                builder.append(" Pulse rate exceeds upper limit");
            }
            if ((status & 24) == 16) {
                builder.append(" Pulse rate is less than lower limit");
            }
            if ((status & 24) == 24) {
                builder.append(" Pulse rate range: Reserved for future use ");
            }
            if ((status & 32) > 0) {
                builder.append(" Improper measurement position");
            }
        }
        return builder.toString();
    }
}
