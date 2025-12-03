package com.android.chileaf.fitness.common.parser;

import no.nordicsemi.android.ble.data.Data;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public class CSCMeasurementParser {
    private static final byte CRANK_REV_DATA_PRESENT = 2;
    private static final byte WHEEL_REV_DATA_PRESENT = 1;

    public static String parse(final Data data) {
        int flags = data.getByte(0).byteValue();
        int offset = 0 + 1;
        boolean wheelRevPresent = (flags & 1) > 0;
        boolean crankRevPreset = (flags & 2) > 0;
        int wheelRevolutions = 0;
        int lastWheelEventTime = 0;
        if (wheelRevPresent) {
            wheelRevolutions = data.getIntValue(20, offset).intValue();
            int offset2 = offset + 4;
            lastWheelEventTime = data.getIntValue(18, offset2).intValue();
            offset = offset2 + 2;
        }
        int crankRevolutions = 0;
        int lastCrankEventTime = 0;
        if (crankRevPreset) {
            crankRevolutions = data.getIntValue(18, offset).intValue();
            lastCrankEventTime = data.getIntValue(18, offset + 2).intValue();
        }
        StringBuilder builder = new StringBuilder();
        if (wheelRevPresent) {
            builder.append("Wheel rev: ");
            builder.append(wheelRevolutions);
            builder.append(",");
            builder.append("Last wheel event time: ");
            builder.append(lastWheelEventTime);
            builder.append(",");
        }
        if (crankRevPreset) {
            builder.append("Crank rev: ");
            builder.append(crankRevolutions);
            builder.append(",");
            builder.append("Last crank event time: ");
            builder.append(lastCrankEventTime);
            builder.append(",");
        }
        if (!wheelRevPresent && !crankRevPreset) {
            builder.append("No wheel or crank data");
        }
        builder.setLength(builder.length() - 2);
        return builder.toString();
    }
}
