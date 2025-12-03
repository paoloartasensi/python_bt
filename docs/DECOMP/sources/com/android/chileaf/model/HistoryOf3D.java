package com.android.chileaf.model;

import android.os.Parcel;
import android.os.Parcelable;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes.dex */
public class HistoryOf3D implements Parcelable {
    public static final Parcelable.Creator<HistoryOf3D> CREATOR = new Parcelable.Creator<HistoryOf3D>() { // from class: com.android.chileaf.model.HistoryOf3D.1
        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public HistoryOf3D createFromParcel(Parcel in) {
            return new HistoryOf3D(in);
        }

        /* JADX WARN: Can't rename method to resolve collision */
        @Override // android.os.Parcelable.Creator
        public HistoryOf3D[] newArray(int size) {
            return new HistoryOf3D[size];
        }
    };
    public int accX;
    public int accY;
    public int accZ;

    public HistoryOf3D(int accX, int accY, int accZ) {
        this.accX = accX;
        this.accY = accY;
        this.accZ = accZ;
    }

    protected HistoryOf3D(Parcel in) {
        this.accX = in.readInt();
        this.accY = in.readInt();
        this.accZ = in.readInt();
    }

    public String toString() {
        return "HistoryOf3D{  accX=" + this.accX + ", accY=" + this.accY + ", accZ=" + this.accZ + '}';
    }

    @Override // android.os.Parcelable
    public int describeContents() {
        return 0;
    }

    @Override // android.os.Parcelable
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeInt(this.accX);
        dest.writeInt(this.accY);
        dest.writeInt(this.accZ);
    }
}
