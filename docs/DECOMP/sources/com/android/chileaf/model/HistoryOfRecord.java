package com.android.chileaf.model;

import android.os.Parcel;
import android.os.Parcelable;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public class HistoryOfRecord implements Parcelable {
    public static final Parcelable.Creator<HistoryOfRecord> CREATOR = new Parcelable.Creator<HistoryOfRecord>() { // from class: com.android.chileaf.model.HistoryOfRecord.1
        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public HistoryOfRecord createFromParcel(Parcel in) {
            return new HistoryOfRecord(in);
        }

        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public HistoryOfRecord[] newArray(int size) {
            return new HistoryOfRecord[size];
        }
    };
    public long record;
    public long stamp;

    public HistoryOfRecord(long stamp, long record) {
        this.stamp = stamp;
        this.record = record;
    }

    public String toString() {
        return "HistoryOfSport{startTime=" + this.stamp + ", record=" + this.record + '}';
    }

    protected HistoryOfRecord(Parcel in) {
        this.stamp = in.readLong();
        this.record = in.readLong();
    }

    @Override // android.os.Parcelable
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeLong(this.stamp);
        dest.writeLong(this.record);
    }

    @Override // android.os.Parcelable
    public int describeContents() {
        return 0;
    }
}
