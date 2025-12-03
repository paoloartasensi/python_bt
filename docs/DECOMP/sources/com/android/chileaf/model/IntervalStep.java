package com.android.chileaf.model;

import android.os.Parcel;
import android.os.Parcelable;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public class IntervalStep implements Parcelable {
    public static final Parcelable.Creator<IntervalStep> CREATOR = new Parcelable.Creator<IntervalStep>() { // from class: com.android.chileaf.model.IntervalStep.1
        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public IntervalStep createFromParcel(Parcel in) {
            return new IntervalStep(in);
        }

        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public IntervalStep[] newArray(int size) {
            return new IntervalStep[size];
        }
    };
    public long stamp;
    public int steps;

    public IntervalStep(long stamp, int steps) {
        this.stamp = stamp;
        this.steps = steps;
    }

    public String toString() {
        return "IntervalStep{startTime=" + this.stamp + ", steps=" + this.steps + '}';
    }

    protected IntervalStep(Parcel in) {
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
