package com.android.chileaf.model;

import android.os.Parcel;
import android.os.Parcelable;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public class HistorySleep implements Parcelable {
    public static final Parcelable.Creator<HistorySleep> CREATOR = new Parcelable.Creator<HistorySleep>() { // from class: com.android.chileaf.model.HistorySleep.1
        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public HistorySleep createFromParcel(Parcel in) {
            return new HistorySleep(in);
        }

        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public HistorySleep[] newArray(int size) {
            return new HistorySleep[size];
        }
    };
    public int[] actions;
    public long utc;

    public HistorySleep() {
    }

    public HistorySleep(long utc, int[] actions) {
        this.utc = utc;
        this.actions = actions;
    }

    protected HistorySleep(Parcel in) {
        this.utc = in.readLong();
        this.actions = in.createIntArray();
    }

    @Override // android.os.Parcelable
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeLong(this.utc);
        dest.writeIntArray(this.actions);
    }

    @Override // android.os.Parcelable
    public int describeContents() {
        return 0;
    }
}
