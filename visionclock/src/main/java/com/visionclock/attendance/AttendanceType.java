package com.visionclock.attendance;

public enum AttendanceType {
    CLOCK_IN,
    CLOCK_OUT;

    public AttendanceType opposite() {
        return this == CLOCK_IN ? CLOCK_OUT : CLOCK_IN;
    }
}
