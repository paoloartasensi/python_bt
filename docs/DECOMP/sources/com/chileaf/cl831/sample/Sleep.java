package com.chileaf.cl831.sample;

/* loaded from: C:\Users\UserDemo\Downloads\New folder\CHILEAF\classes5.dex */
public class Sleep {
    private String date;
    private int deepSleepTime;
    private int index;
    private int lightSleepTime;
    private int notSleepingTime;
    private long totalTime;

    public Sleep(String date, int notSleepingTime, int lightSleepTime, int deepSleepTime, long totalTime, int index) {
        this.date = date;
        this.notSleepingTime = notSleepingTime;
        this.lightSleepTime = lightSleepTime;
        this.deepSleepTime = deepSleepTime;
        this.totalTime = totalTime;
        this.index = index;
    }

    public Sleep() {
    }

    public String getDate() {
        return this.date;
    }

    public void setDate(String date) {
        this.date = date;
    }

    public int getNotSleepingTime() {
        return this.notSleepingTime;
    }

    public void setNotSleepingTime(int notSleepingTime) {
        this.notSleepingTime = notSleepingTime;
    }

    public int getLightSleepTime() {
        return this.lightSleepTime;
    }

    public void setLightSleepTime(int lightSleepTime) {
        this.lightSleepTime = lightSleepTime;
    }

    public int getDeepSleepTime() {
        return this.deepSleepTime;
    }

    public void setDeepSleepTime(int deepSleepTime) {
        this.deepSleepTime = deepSleepTime;
    }

    public long getTotalTime() {
        return this.totalTime;
    }

    public void setTotalTime(long totalTime) {
        this.totalTime = totalTime;
    }

    public int getIndex() {
        return this.index;
    }

    public void setIndex(int index) {
        this.index = index;
    }

    public String toString() {
        return "[" + this.date + "]{\nnot Sleeping Time = " + this.notSleepingTime + "(minute)\nlight Sleep Time = " + this.lightSleepTime + "(minute)\ndeep Sleep Time = " + this.deepSleepTime + "(minute)\ntotal Time = " + this.totalTime + "(minute)}";
    }
}
