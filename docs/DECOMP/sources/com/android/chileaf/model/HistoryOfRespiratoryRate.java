package com.android.chileaf.model;

import android.os.Parcel;
import android.os.Parcelable;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public class HistoryOfRespiratoryRate implements Parcelable {
    public static final Parcelable.Creator<HistoryOfRespiratoryRate> CREATOR = new Parcelable.Creator<HistoryOfRespiratoryRate>() { // from class: com.android.chileaf.model.HistoryOfRespiratoryRate.1
        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public HistoryOfRespiratoryRate createFromParcel(Parcel in) {
            return new HistoryOfRespiratoryRate(in);
        }

        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public HistoryOfRespiratoryRate[] newArray(int size) {
            return new HistoryOfRespiratoryRate[size];
        }
    };
    public int respiratoryRate;
    public long stamp;

    public HistoryOfRespiratoryRate(long stamp, int respiratoryRate) {
        this.stamp = stamp;
        this.respiratoryRate = respiratoryRate;
    }

    public String toString() {
        return "HistoryOfHeartRate{stamp=" + this.stamp + ", respiratoryRate=" + this.respiratoryRate + '}';
    }

    protected HistoryOfRespiratoryRate(Parcel in) {
        this.stamp = in.readLong();
        this.respiratoryRate = in.readInt();
    }

    @Override // android.os.Parcelable
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeLong(this.stamp);
        dest.writeInt(this.respiratoryRate);
    }

    @Override // android.os.Parcelable
    public int describeContents() {
        return 0;
    }
}
