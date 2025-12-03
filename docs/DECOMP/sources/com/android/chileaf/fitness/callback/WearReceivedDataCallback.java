package com.android.chileaf.fitness.callback;

import android.bluetooth.BluetoothDevice;
import android.os.Parcel;
import com.android.chileaf.model.HistoryOf3D;
import com.android.chileaf.model.HistoryOfHeartRate;
import com.android.chileaf.model.HistoryOfRecord;
import com.android.chileaf.model.HistoryOfRespiratoryRate;
import com.android.chileaf.model.HistoryOfSport;
import com.android.chileaf.model.HistoryOfStep;
import com.android.chileaf.model.HistorySleep;
import com.android.chileaf.model.IntervalStep;
import com.android.chileaf.util.DateUtil;
import com.android.chileaf.util.HexUtil;
import com.android.chileaf.util.LogUtil;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import kotlin.UByte;
import no.nordicsemi.android.ble.callback.profile.ProfileReadResponse;
import no.nordicsemi.android.ble.data.Data;
import no.nordicsemi.android.ble.utils.ParserUtils;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public abstract class WearReceivedDataCallback extends ProfileReadResponse implements UserInfoCallback, BodySportCallback, BluetoothStatusCallback, HistoryOfSportCallback, HistoryOfHRRecordCallback, HistoryOfHRDataCallback, HistoryOfRRRecordCallback, HistoryOfRRDataCallback, IntervalStepCallback, SingleTapRecordCallback, HeartRateStatusCallback, BloodOxygenCallback, TemperatureCallback, HistoryOfSingleRecordCallback, HeartRateAlarmCallback, AccelerometerCallback, HeartRateMaxCallback, HistoryOfSleepCallback, Sensor3DFrequencyCallback, Sensor3DStatusCallback, HistoryOf3DDataCallback, BodyHealthCallback, Sensor6DFrequencyCallback, Sensor6DRawDataCallback, BodySportHealthCallback, HistoryOfStepRecordCallback, HistoryOfStepDataCallback {
    private static final long END_TAG = 4294967295L;
    public static final int TYPE_HEART = 4;
    public static final int TYPE_HEARTS = 6;
    public static final int TYPE_HEART_RR = 8;
    public static final int TYPE_HEART_RRS = 16;
    public static final int TYPE_HISTORY_3D = 24;
    public static final int TYPE_INTERVAL = 18;
    public static final int TYPE_SINGLE_TAP = 20;
    public static final int TYPE_SLEEP = 22;
    public static final int TYPE_SPORT = 2;
    public static final int TYPE_STEP = 32;
    public static final int TYPE_STEPS = 34;
    private boolean isCL833;
    private boolean isStamp;
    private List<HistoryOfHeartRate> mHistoryOfHeartRates;
    private List<HistoryOfRecord> mHistoryOfRecords;
    private List<HistoryOfRespiratoryRate> mHistoryOfRespiratoryRates;
    private List<HistorySleep> mHistoryOfSleeps;
    private List<HistoryOfSport> mHistoryOfSports;
    private List<HistoryOfStep> mHistoryOfSteps;
    private List<IntervalStep> mIntervalSteps;
    private final List<Data> mPackages;
    private List<HistoryOfRecord> mRespiratoryRatesRecords;
    private List<HistoryOfRecord> mSingleTapRecords;
    private long mStamp;
    private List<HistoryOfRecord> mStepsRecords;

    @Retention(RetentionPolicy.SOURCE)
    public @interface DataType {
    }

    public WearReceivedDataCallback() {
        this.mStamp = 0L;
        this.isCL833 = false;
        this.isStamp = false;
        this.mPackages = new ArrayList();
    }

    protected WearReceivedDataCallback(final Parcel in) {
        super(in);
        this.mStamp = 0L;
        this.isCL833 = false;
        this.isStamp = false;
        this.mPackages = new ArrayList();
    }

    @Override // no.nordicsemi.android.ble.response.ReadResponse, no.nordicsemi.android.ble.callback.DataReceivedCallback
    public void onDataReceived(BluetoothDevice bluetoothDevice, Data data) {
        int i;
        super.onDataReceived(bluetoothDevice, data);
        byte b = 1;
        boolean z = true;
        char c = 0;
        if (!(data.getIntValue(17, 1).intValue() == data.size())) {
            onInvalidDataReceived(bluetoothDevice, data);
            LogUtil.w("onDataReceived:length:%s", Integer.valueOf(data.size()));
        }
        byte[] value = data.getValue();
        int i2 = 2;
        int iIntValue = data.getIntValue(17, 2).intValue();
        int i3 = 3;
        try {
        } catch (Exception e) {
            e = e;
        }
        if (iIntValue == 3) {
            onUserInfoReceived(bluetoothDevice, getIntParse(value, 5, 1), getIntParse(value, 6, 1), getIntParse(value, 7, 1), getIntParse(value, 8, 1), getLongParse(value, 9, 5));
            return;
        }
        int i4 = 4;
        if (iIntValue == 5) {
            if (getIntParse(value, 3, 1) == 3) {
                if (this.mHistoryOfSleeps == null) {
                    this.mHistoryOfSleeps = new ArrayList();
                }
                int i5 = 4;
                while (i5 < value.length) {
                    int i6 = value[i5];
                    if (i6 >= 1) {
                        int i7 = i5 + 1;
                        long longParse = getLongParse(value, i7, i4);
                        int i8 = i7 + 4;
                        long j = (longParse * 1000) - 28800000;
                        int[] iArr = new int[i6];
                        for (int i9 = 0; i9 < i6; i9++) {
                            iArr[i9] = getIntParse(value, i9 + i8, 1);
                        }
                        i5 = i8 + (i6 - 1);
                        this.mHistoryOfSleeps.add(new HistorySleep(j, iArr));
                        if (i5 == value.length - 2) {
                            break;
                        }
                    }
                    i5++;
                    i4 = 4;
                }
                onHistoryOfSleepReceived(bluetoothDevice, this.mHistoryOfSleeps);
                this.mHistoryOfSleeps.clear();
            }
            return;
        }
        if (iIntValue == 12) {
            byte[] bArrSubSlice = subSlice(3, value);
            for (int i10 = 0; i10 < bArrSubSlice.length / 6; i10++) {
                int i11 = i10 * 6;
                onAccelerometerReceived(bluetoothDevice, data.getIntValue(34, i11 + 3).intValue(), data.getIntValue(34, i11 + 5).intValue(), data.getIntValue(34, i11 + 7).intValue());
            }
        } else if (iIntValue != 18) {
            if (iIntValue == 19) {
                onSportHealthReceived(bluetoothDevice, getIntParse(value, 3, 1), getIntParse(value, 4, 1), getIntParse(value, 5, 1), getIntParse(value, 6, 1), getIntParse(value, 7, 1));
                return;
            }
            int i12 = 4;
            if (iIntValue == 21) {
                onSportReceived(bluetoothDevice, getIntParse(value, 3, 3), getIntParse(value, 6, 3), getIntParse(value, 9, 3));
                return;
            }
            if (iIntValue == 63) {
                if (getIntParse(value, 3, 1) != 1) {
                    z = false;
                }
                onBluetoothStatusReceived(bluetoothDevice, z);
                return;
            }
            if (iIntValue == 22) {
                if (this.mHistoryOfSports == null) {
                    this.mHistoryOfSports = new ArrayList();
                }
                long longParse2 = getLongParse(value, 3, 4);
                if (this.isCL833) {
                    parseSportHistory(subSlice(3, value));
                    Collections.reverse(this.mHistoryOfSports);
                    onHistoryOfSportReceived(bluetoothDevice, this.mHistoryOfSports);
                    this.mHistoryOfSports.clear();
                } else if (longParse2 != END_TAG) {
                    this.mPackages.add(data);
                } else {
                    for (int i13 = 0; i13 < this.mPackages.size(); i13++) {
                        byte[] bArrSubSlice2 = subSlice(3, this.mPackages.get(i13).getValue());
                        parseSportHistory(bArrSubSlice2);
                        LogUtil.d("HistoryOfSport index:%d values:%s", Integer.valueOf(i13), ParserUtils.parse(bArrSubSlice2));
                    }
                    onHistoryOfSportReceived(bluetoothDevice, this.mHistoryOfSports);
                    this.mHistoryOfSports.clear();
                    this.mPackages.clear();
                }
                return;
            }
            if (iIntValue == 33) {
                if (this.mHistoryOfRecords == null) {
                    this.mHistoryOfRecords = new ArrayList();
                }
                if (getLongParse(value, 3, 4) != END_TAG) {
                    this.mPackages.add(data);
                } else {
                    int i14 = 0;
                    while (i14 < this.mPackages.size()) {
                        byte[] bArrSubSlice3 = subSlice(i3, this.mPackages.get(i14).getValue());
                        Object[] objArr = new Object[i2];
                        objArr[c] = Integer.valueOf(i14);
                        objArr[b] = ParserUtils.parse(bArrSubSlice3);
                        LogUtil.d("mHistoryOfRecords index:%d values:%s", objArr);
                        int i15 = 0;
                        while (i15 < bArrSubSlice3.length / i12) {
                            long longParse3 = getLongParse(bArrSubSlice3, i15 * 4, i12);
                            long jRestoreZoneUTC = DateUtil.restoreZoneUTC(longParse3);
                            int i16 = i15;
                            this.mHistoryOfRecords.add(new HistoryOfRecord(longParse3, jRestoreZoneUTC));
                            LogUtil.d("mHistoryOfRecords index:%d record:%s", Integer.valueOf(i16), Long.valueOf(longParse3));
                            i15 = i16 + 1;
                            i12 = 4;
                        }
                        i14++;
                        b = 1;
                        i2 = 2;
                        i12 = 4;
                        c = 0;
                        i3 = 3;
                    }
                    onHistoryOfHRRecordReceived(bluetoothDevice, this.mHistoryOfRecords);
                    this.mHistoryOfRecords.clear();
                    this.mPackages.clear();
                }
                return;
            }
            try {
            } catch (Exception e2) {
                e = e2;
            }
            if (iIntValue == 34 || iIntValue == 35) {
                int i17 = 3;
                int i18 = iIntValue;
                if (this.mHistoryOfHeartRates == null) {
                    this.mHistoryOfHeartRates = new ArrayList();
                }
                if (i18 == 34) {
                    if (!this.isStamp) {
                        this.mStamp = getLongParse(value, i17, 4);
                        this.isStamp = true;
                    }
                    this.mPackages.add(data);
                }
                if (i18 == 35) {
                    for (int i19 = 0; i19 < this.mPackages.size(); i19++) {
                        byte[] bArrSubSlice4 = subSlice(i17, this.mPackages.get(i19).getValue());
                        LogUtil.d("mHistoryOfHeartRates index:%d values:%s", Integer.valueOf(i19), ParserUtils.parse(bArrSubSlice4));
                        for (int i20 = 4; i20 < bArrSubSlice4.length; i20++) {
                            this.mHistoryOfHeartRates.add(new HistoryOfHeartRate(DateUtil.restoreZoneUTC(this.mStamp), getIntParse(bArrSubSlice4, i20, 1)));
                            this.mStamp++;
                        }
                    }
                    onHistoryOfHRDataReceived(bluetoothDevice, this.mHistoryOfHeartRates);
                    this.mHistoryOfHeartRates.clear();
                    this.mPackages.clear();
                    this.isStamp = false;
                    this.mStamp = 0L;
                    return;
                }
                return;
            }
            if (iIntValue == 36) {
                try {
                    if (this.mRespiratoryRatesRecords == null) {
                        this.mRespiratoryRatesRecords = new ArrayList();
                    }
                    long longParse4 = getLongParse(value, 3, 4);
                    if (longParse4 != END_TAG) {
                        this.mPackages.add(data);
                        i = iIntValue;
                    } else {
                        for (int i21 = 0; i21 < this.mPackages.size(); i21++) {
                            byte[] bArrSubSlice5 = subSlice(3, this.mPackages.get(i21).getValue());
                            LogUtil.d("mRespiratoryRatesRecords index:%d values:%s", Integer.valueOf(i21), ParserUtils.parse(bArrSubSlice5));
                            int i22 = 0;
                            while (i22 < bArrSubSlice5.length / 4) {
                                long longParse5 = getLongParse(bArrSubSlice5, i22 * 4, 4);
                                long jRestoreZoneUTC2 = DateUtil.restoreZoneUTC(longParse5);
                                long j2 = longParse4;
                                i = iIntValue;
                                try {
                                    this.mRespiratoryRatesRecords.add(new HistoryOfRecord(longParse5, jRestoreZoneUTC2));
                                    i22++;
                                    longParse4 = j2;
                                    iIntValue = i;
                                } catch (Exception e3) {
                                    e = e3;
                                }
                            }
                        }
                        i = iIntValue;
                        onHistoryOfRRRecordReceived(bluetoothDevice, this.mRespiratoryRatesRecords);
                        LogUtil.d("onHistoryOfRRRecordReceived size:%d", Integer.valueOf(this.mRespiratoryRatesRecords.size()));
                        this.mRespiratoryRatesRecords.clear();
                        this.mPackages.clear();
                    }
                    return;
                } catch (Exception e4) {
                    e = e4;
                }
            } else {
                if (iIntValue == 37 || iIntValue == 38) {
                    int i23 = 3;
                    int i24 = iIntValue;
                    if (this.mHistoryOfRespiratoryRates == null) {
                        this.mHistoryOfRespiratoryRates = new ArrayList();
                    }
                    if (i24 == 37) {
                        if (!this.isStamp) {
                            this.mStamp = getLongParse(value, i23, 4);
                            this.isStamp = true;
                        }
                        this.mPackages.add(data);
                    }
                    if (i24 == 38) {
                        for (int i25 = 0; i25 < this.mPackages.size(); i25++) {
                            byte[] bArrSubSlice6 = subSlice(7, this.mPackages.get(i25).getValue());
                            LogUtil.d("index:%d HistoryOfRespiratoryRates mValues:%s", Integer.valueOf(i25), ParserUtils.parse(bArrSubSlice6));
                            for (int i26 = 0; i26 < bArrSubSlice6.length / 2; i26++) {
                                this.mHistoryOfRespiratoryRates.add(new HistoryOfRespiratoryRate(DateUtil.restoreZoneUTC(this.mStamp), getIntParse(bArrSubSlice6, i26 * 2, 2)));
                                this.mStamp++;
                            }
                        }
                        LogUtil.d("onHistoryOfRRDataReceived :%s", this.mHistoryOfRespiratoryRates.toString());
                        onHistoryOfRRDataReceived(bluetoothDevice, this.mHistoryOfRespiratoryRates);
                        this.mHistoryOfRespiratoryRates.clear();
                        this.mPackages.clear();
                        this.isStamp = false;
                        this.mStamp = 0L;
                        return;
                    }
                    return;
                }
                if (iIntValue == 55) {
                    if (value[1] <= 6) {
                        return;
                    }
                    int intParse = getIntParse(value, 3, 1);
                    if (value[1] <= 8) {
                        return;
                    }
                    onBloodOxygenReceived(bluetoothDevice, intParse, String.valueOf(getIntParse(value, 4, 1)), getIntParse(value, 5, 1), getIntParse(value, 6, 1), getIntParse(value, 7, 1));
                    return;
                }
                int i27 = 4;
                if (iIntValue == 56) {
                    onTemperatureReceived(bluetoothDevice, getIntParse(value, 3, 2) / 10.0f, getIntParse(value, 5, 2) / 10.0f, getIntParse(value, 7, 2) / 10.0f);
                    return;
                }
                if (iIntValue == 64 || iIntValue == 65) {
                    int i28 = iIntValue;
                    if (this.mIntervalSteps == null) {
                        this.mIntervalSteps = new ArrayList();
                    }
                    if (i28 == 64) {
                        this.mPackages.add(data);
                    }
                    if (i28 == 65) {
                        for (int i29 = 0; i29 < this.mPackages.size(); i29++) {
                            byte[] bArrSubSlice7 = subSlice(3, this.mPackages.get(i29).getValue());
                            LogUtil.d("mIntervalSteps index:%d values:%s", Integer.valueOf(i29), ParserUtils.parse(bArrSubSlice7));
                            for (int i30 = 0; i30 < bArrSubSlice7.length / 8; i30++) {
                                int i31 = i30 * 8;
                                this.mIntervalSteps.add(new IntervalStep(DateUtil.restoreZoneUTC(getLongParse(bArrSubSlice7, i31, 4)), getIntParse(bArrSubSlice7, i31 + 4, 4)));
                            }
                        }
                        onIntervalStepReceived(bluetoothDevice, this.mIntervalSteps);
                        this.mIntervalSteps.clear();
                        this.mPackages.clear();
                        return;
                    }
                    return;
                }
                if (iIntValue == 66 || iIntValue == 67) {
                    int i32 = iIntValue;
                    if (this.mSingleTapRecords == null) {
                        this.mSingleTapRecords = new ArrayList();
                    }
                    if (i32 == 66) {
                        this.mPackages.add(data);
                    }
                    if (i32 == 67) {
                        for (int i33 = 0; i33 < this.mPackages.size(); i33++) {
                            byte[] bArrSubSlice8 = subSlice(3, this.mPackages.get(i33).getValue());
                            LogUtil.d("mSingleTapRecords index:%d values:%s", Integer.valueOf(i33), ParserUtils.parse(bArrSubSlice8));
                            for (int i34 = 0; i34 < bArrSubSlice8.length / 4; i34++) {
                                long longParse6 = getLongParse(bArrSubSlice8, i34 * 4, 4);
                                this.mSingleTapRecords.add(new HistoryOfRecord(longParse6, DateUtil.restoreZoneUTC(longParse6)));
                            }
                        }
                        onSingleTapRecordReceived(bluetoothDevice, this.mSingleTapRecords);
                        this.mSingleTapRecords.clear();
                        this.mPackages.clear();
                        return;
                    }
                    return;
                }
                if (iIntValue == 70) {
                    onHeartRateStatusReceived(bluetoothDevice, getIntParse(value, 4, 1), getIntParse(value, 5, 1), getIntParse(value, 6, 1));
                    return;
                }
                if (iIntValue != 73) {
                    int i35 = 3;
                    if (iIntValue == 91) {
                        onHeartRateAlarmReceived(bluetoothDevice, DateUtil.restoreZoneUTC(getLongParse(value, 3, 4)), getIntParse(value, 7, 1) == 1);
                        return;
                    }
                    if (iIntValue == 96) {
                        parseSensorRawList(bluetoothDevice, getIntParse(value, 3, 1), new Data(subSlice(4, value)));
                        return;
                    }
                    if (iIntValue == 97) {
                        onSensor6DFrequencyReceived(bluetoothDevice, getIntParse(value, 3, 1));
                        return;
                    }
                    if (iIntValue == 100) {
                        parseSensorRawList(bluetoothDevice, DateUtil.restoreZoneUTCTimeInMillis((1000 * getLongParse(value, 3, 4)) + getIntParse(value, 7, 2)), getIntParse(value, 9, 1), data);
                        return;
                    }
                    if (iIntValue == 117) {
                        int intParse2 = getIntParse(value, 4, 1);
                        if (intParse2 == 6) {
                            onHeartRateMaxReceived(bluetoothDevice, getIntParse(value, 5, 1));
                        } else if (intParse2 == 11) {
                            onSensor3DFrequencyReceived(bluetoothDevice, getIntParse(value, 5, 1));
                        } else if (intParse2 == 12) {
                            onSensor3DStatusReceived(bluetoothDevice, getIntParse(value, 5, 1) == 1);
                        } else if (intParse2 == 15) {
                            onHealthReceived(bluetoothDevice, getIntParse(value, 5, 1), getIntParse(value, 6, 1), getIntParse(value, 7, 1), getIntParse(value, 8, 1), getIntParse(value, 9, 1), getLongParse(value, 10, 4) / 1000.0f, getLongParse(value, 14, 4) / 1000.0f, getLongParse(value, 18, 4) / 1000.0f);
                        }
                        return;
                    }
                    if (iIntValue != 119 && iIntValue != 120) {
                        if (iIntValue != 144) {
                            if (iIntValue != 145) {
                                if (iIntValue == 146) {
                                }
                            }
                            if (this.mHistoryOfSteps == null) {
                                this.mHistoryOfSteps = new ArrayList();
                            }
                            if (iIntValue == 145) {
                                if (!this.isStamp) {
                                    this.mStamp = getLongParse(value, 3, 4);
                                    this.isStamp = true;
                                }
                                this.mPackages.add(data);
                            }
                            if (iIntValue == 146) {
                                for (int i36 = 0; i36 < this.mPackages.size(); i36++) {
                                    byte[] bArrSubSlice9 = subSlice(7, this.mPackages.get(i36).getValue());
                                    LogUtil.d("mHistoryOfSteps index:%d values:%s", Integer.valueOf(i36), ParserUtils.parse(bArrSubSlice9));
                                    for (int i37 = 0; i37 < bArrSubSlice9.length / 2; i37++) {
                                        this.mHistoryOfSteps.add(new HistoryOfStep(DateUtil.restoreZoneUTC(this.mStamp), getIntParse(bArrSubSlice9, i37 * 2, 2)));
                                        this.mStamp++;
                                    }
                                }
                                onHistoryOfStepDataReceived(bluetoothDevice, this.mHistoryOfSteps);
                                this.mHistoryOfSteps.clear();
                                this.mPackages.clear();
                                this.isStamp = false;
                                this.mStamp = 0L;
                                return;
                            }
                            return;
                        }
                        if (this.mStepsRecords == null) {
                            this.mStepsRecords = new ArrayList();
                        }
                        long longParse7 = getLongParse(value, 3, 4);
                        if (longParse7 != END_TAG) {
                            this.mPackages.add(data);
                        } else {
                            int i38 = 0;
                            while (i38 < this.mPackages.size()) {
                                byte[] bArrSubSlice10 = subSlice(i35, this.mPackages.get(i38).getValue());
                                LogUtil.d("mStepsRecords index:%d values:%s", Integer.valueOf(i38), ParserUtils.parse(bArrSubSlice10));
                                int i39 = 0;
                                while (i39 < bArrSubSlice10.length / i27) {
                                    long longParse8 = getLongParse(bArrSubSlice10, i39 * 4, i27);
                                    this.mStepsRecords.add(new HistoryOfRecord(longParse8, DateUtil.restoreZoneUTC(longParse8)));
                                    LogUtil.d("mStepsRecords index:%d record:%s", Integer.valueOf(i39), Long.valueOf(longParse8));
                                    i39++;
                                    longParse7 = longParse7;
                                    i27 = 4;
                                }
                                i38++;
                                i35 = 3;
                                i27 = 4;
                            }
                            onHistoryOfStepRecordReceived(bluetoothDevice, this.mStepsRecords);
                            this.mStepsRecords.clear();
                            this.mPackages.clear();
                        }
                        return;
                    }
                    if (iIntValue == 119 || iIntValue == 120) {
                        byte[] bArrSubSlice11 = subSlice(3, data.getValue());
                        for (int i40 = 0; i40 < bArrSubSlice11.length / 6; i40++) {
                            int i41 = i40 * 6;
                            onHistoryOf3DDataReceived(bluetoothDevice, new HistoryOf3D(getSInt16(bArrSubSlice11, i41), getSInt16(bArrSubSlice11, i41 + 2), getSInt16(bArrSubSlice11, i41 + 4)), iIntValue == 120);
                        }
                        return;
                    }
                    return;
                }
                try {
                    onHistorySingleRecordReceived(bluetoothDevice, DateUtil.restoreZoneUTC(getLongParse(value, 3, 4)), getLongParse(value, 7, 3), getLongParse(value, 10, 3), getLongParse(value, 13, 3));
                    return;
                } catch (Exception e5) {
                    e = e5;
                }
            }
            e.printStackTrace();
        }
    }

    public void setCL833(boolean isCL833) {
        this.isCL833 = isCL833;
    }

    private int getSInt16(byte[] data, int offset) {
        return unsignedToSigned(unsignedBytesToInt(data[offset], data[offset + 1]), 16);
    }

    private int unsignedByteToInt(final byte b) {
        return b & UByte.MAX_VALUE;
    }

    private int unsignedBytesToInt(final byte b0, final byte b1) {
        return unsignedByteToInt(b0) + (unsignedByteToInt(b1) << 8);
    }

    private int unsignedToSigned(int unsigned, final int size) {
        if (((1 << (size - 1)) & unsigned) != 0) {
            return ((1 << (size - 1)) - (unsigned & ((1 << (size - 1)) - 1))) * (-1);
        }
        return unsigned;
    }

    public void clearType(int type) {
        switch (type) {
            case 2:
                List<HistoryOfSport> list = this.mHistoryOfSports;
                if (list != null) {
                    list.clear();
                    break;
                }
                break;
            case 4:
                List<HistoryOfRecord> list2 = this.mHistoryOfRecords;
                if (list2 != null) {
                    list2.clear();
                    break;
                }
                break;
            case 6:
                List<HistoryOfHeartRate> list3 = this.mHistoryOfHeartRates;
                if (list3 != null) {
                    list3.clear();
                    break;
                }
                break;
            case 8:
                List<HistoryOfRecord> list4 = this.mRespiratoryRatesRecords;
                if (list4 != null) {
                    list4.clear();
                    break;
                }
                break;
            case 16:
                List<HistoryOfRespiratoryRate> list5 = this.mHistoryOfRespiratoryRates;
                if (list5 != null) {
                    list5.clear();
                    break;
                }
                break;
            case 18:
                List<IntervalStep> list6 = this.mIntervalSteps;
                if (list6 != null) {
                    list6.clear();
                    break;
                }
                break;
            case 20:
                List<HistoryOfRecord> list7 = this.mSingleTapRecords;
                if (list7 != null) {
                    list7.clear();
                    break;
                }
                break;
            case 22:
                List<HistorySleep> list8 = this.mHistoryOfSleeps;
                if (list8 != null) {
                    list8.clear();
                    break;
                }
                break;
            case 32:
                List<HistoryOfRecord> list9 = this.mStepsRecords;
                if (list9 != null) {
                    list9.clear();
                    break;
                }
                break;
            case 34:
                List<HistoryOfStep> list10 = this.mHistoryOfSteps;
                if (list10 != null) {
                    list10.clear();
                    break;
                }
                break;
        }
        this.mPackages.clear();
        this.isStamp = false;
        this.mStamp = 0L;
    }

    private void parseSportHistory(final byte[] value) {
        WearReceivedDataCallback wearReceivedDataCallback = this;
        byte[] bArr = value;
        LogUtil.d("HistoryOfSport length:%d values:%s", Integer.valueOf(bArr.length), ParserUtils.parse(value));
        int i = 0;
        while (i < bArr.length / 10) {
            int offset = i * 10;
            long stamp = wearReceivedDataCallback.getLongParse(bArr, offset, 4);
            long step = wearReceivedDataCallback.getLongParse(bArr, offset + 4, 3);
            long calorie = wearReceivedDataCallback.getLongParse(bArr, offset + 7, 3);
            wearReceivedDataCallback.mHistoryOfSports.add(new HistoryOfSport(DateUtil.restoreZoneUTC(stamp), step, calorie));
            i++;
            wearReceivedDataCallback = this;
            bArr = value;
        }
    }

    private synchronized void parseSensorRawList(BluetoothDevice device, final int sequence, final Data data) {
        LogUtil.d("parseSensorRawList values:%s", ParserUtils.parse(data.getValue()));
        for (int i = 0; i < data.size() / 12; i++) {
            int offset = i * 12;
            int gyroscopeX = data.getIntValue(34, offset).intValue();
            int gyroscopeY = data.getIntValue(34, offset + 2).intValue();
            int gyroscopeZ = data.getIntValue(34, offset + 4).intValue();
            int accelerometerX = data.getIntValue(34, offset + 6).intValue();
            int accelerometerY = data.getIntValue(34, offset + 8).intValue();
            int accelerometerZ = data.getIntValue(34, offset + 10).intValue();
            onSensor6DRawDataReceived(device, 255L, sequence, gyroscopeX, gyroscopeY, gyroscopeZ, accelerometerX, accelerometerY, accelerometerZ);
        }
    }

    private synchronized void parseSensorRawList(BluetoothDevice device, final long utc, final int sequence, final Data data) {
        for (int i = 0; i < data.size() / 12; i++) {
            int offset = i * 12;
            int gyroscopeX = data.getIntValue(34, offset + 10).intValue();
            int gyroscopeY = data.getIntValue(34, offset + 12).intValue();
            int gyroscopeZ = data.getIntValue(34, offset + 14).intValue();
            int accelerometerX = data.getIntValue(34, offset + 16).intValue();
            int accelerometerY = data.getIntValue(34, offset + 18).intValue();
            int accelerometerZ = data.getIntValue(34, offset + 20).intValue();
            onSensor6DRawDataReceived(device, utc, sequence, gyroscopeX, gyroscopeY, gyroscopeZ, accelerometerX, accelerometerY, accelerometerZ);
        }
    }

    private synchronized byte[] subSlice(final int start, final byte[] value) {
        return HexUtil.subByte(value, start, value.length - 1);
    }

    private long getLongParse(byte[] bytes, int pos, int len) {
        long val = 0;
        for (int i = pos; i < len + pos; i++) {
            val = (val << 8) | (bytes[i] & 255);
        }
        return val;
    }

    private int getIntParse(byte[] bytes, int pos, int len) {
        int val = 0;
        int len2 = len + pos;
        for (int i = pos; i < len2; i++) {
            val = (val << 8) | (bytes[i] & UByte.MAX_VALUE);
        }
        return val;
    }
}
