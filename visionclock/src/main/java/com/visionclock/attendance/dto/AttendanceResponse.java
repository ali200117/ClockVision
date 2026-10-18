package com.visionclock.attendance.dto;

import java.time.Instant;

import com.visionclock.attendance.Attendance;
import com.visionclock.attendance.AttendanceType;

public record AttendanceResponse(
        Long id,
        Long employeeId,
        AttendanceType type,
        Instant recordedAt) {

    public static AttendanceResponse from(Attendance attendance) {
        return new AttendanceResponse(
                attendance.getId(),
                attendance.getEmployee().getId(),
                attendance.getType(),
                attendance.getRecordedAt());
    }
}
