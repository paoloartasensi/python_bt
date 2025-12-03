package com.android.chileaf.model;

import android.os.Parcel;
import android.os.Parcelable;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public class HistoryOfStep implements Parcelable {
    public static final Parcelable.Creator<HistoryOfStep> CREATOR = new Parcelable.Creator<HistoryOfStep>() { // from class: com.android.chileaf.model.HistoryOfStep.1
        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public HistoryOfStep createFromParcel(Parcel in) {
            return new HistoryOfStep(in);
        }

        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public HistoryOfStep[] newArray(int size) {
            return new HistoryOfStep[size];
        }
    };
    public long stamp;
    public int steps;

    public HistoryOfStep(long stamp, int steps) {
        this.stamp = stamp;
        this.steps = steps;
    }

    public String toString() {
        return "HistoryOfStep{stamp=" + this.stamp + ", steps=" + this.steps + '}';
    }

    protected HistoryOfStep(Parcel in) {
        this.stamp = in.readLong();
        this.steps = in.readInt();
    }

    @Override // android.os.Parcelable
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeLong(this.stamp);
        dest.writeInt(this.steps);
    }

    @Override // android.os.Parcelable
    public int describeContents() {
        return 0;
    }
}
