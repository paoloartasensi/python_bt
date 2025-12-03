package com.android.chileaf.model;

import android.os.Parcel;
import android.os.Parcelable;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public class HistoryOfSport implements Parcelable {
    public static final Parcelable.Creator<HistoryOfSport> CREATOR = new Parcelable.Creator<HistoryOfSport>() { // from class: com.android.chileaf.model.HistoryOfSport.1
        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public HistoryOfSport createFromParcel(Parcel in) {
            return new HistoryOfSport(in);
        }

        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public HistoryOfSport[] newArray(int size) {
            return new HistoryOfSport[size];
        }
    };
    public long calorie;
    public long endTime;
    public long startTime;
    public long step;

    public HistoryOfSport(long startTime, long step, long calorie) {
        this.startTime = startTime;
        this.step = step;
        this.calorie = calorie;
    }

    public HistoryOfSport(long startTime, long endTime, long step, long calorie) {
        this.startTime = startTime;
        this.endTime = endTime;
        this.step = step;
        this.calorie = calorie;
    }

    public String toString() {
        return "HistoryOfSport{startTime=" + this.startTime + ", endTime=" + this.endTime + ", step=" + this.step + ", calorie=" + this.calorie + '}';
    }

    protected HistoryOfSport(Parcel in) {
        this.startTime = in.readLong();
        this.step = in.readLong();
        this.calorie = in.readLong();
        this.endTime = in.readLong();
    }

    @Override // android.os.Parcelable
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeLong(this.startTime);
        dest.writeLong(this.step);
        dest.writeLong(this.calorie);
        dest.writeLong(this.endTime);
    }

    @Override // android.os.Parcelable
    public int describeContents() {
        return 0;
    }
}
