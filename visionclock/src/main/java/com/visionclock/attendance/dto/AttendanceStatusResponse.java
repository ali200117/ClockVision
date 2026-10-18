package com.visionclock.attendance.dto;

import java.time.Instant;

import com.visionclock.attendance.AttendanceStatus;

public record AttendanceStatusResponse(
        Long employeeId,
        AttendanceStatus status,
        Instant since) {
}
