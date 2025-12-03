package com.android.chileaf.model;

import android.os.Parcel;
import android.os.Parcelable;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public class HistoryOfHeartRate implements Parcelable {
    public static final Parcelable.Creator<HistoryOfHeartRate> CREATOR = new Parcelable.Creator<HistoryOfHeartRate>() { // from class: com.android.chileaf.model.HistoryOfHeartRate.1
        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public HistoryOfHeartRate createFromParcel(Parcel in) {
            return new HistoryOfHeartRate(in);
        }

        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public HistoryOfHeartRate[] newArray(int size) {
            return new HistoryOfHeartRate[size];
        }
    };
    public int heartRate;
    public long stamp;

    public HistoryOfHeartRate(long stamp, int heartRate) {
        this.stamp = stamp;
        this.heartRate = heartRate;
    }

    public String toString() {
        return "HistoryOfHeartRate{startTime=" + this.stamp + ", heartRate=" + this.heartRate + '}';
    }

    protected HistoryOfHeartRate(Parcel in) {
        this.stamp = in.readLong();
        this.heartRate = in.readInt();
    }

    @Override // android.os.Parcelable
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeLong(this.stamp);
        dest.writeInt(this.heartRate);
    }

    @Override // android.os.Parcelable
    public int describeContents() {
        return 0;
    }
}
