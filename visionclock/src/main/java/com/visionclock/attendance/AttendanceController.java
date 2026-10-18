package com.visionclock.attendance;

import java.time.Instant;
import java.util.List;

import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.visionclock.attendance.dto.AttendanceResponse;
import com.visionclock.attendance.dto.AttendanceStatusResponse;

@RestController
@RequestMapping("/api/employees/{employeeId}")
public class AttendanceController {

    private final AttendanceService attendanceService;

    public AttendanceController(AttendanceService attendanceService) {
        this.attendanceService = attendanceService;
    }

    @PostMapping("/clock")
    @ResponseStatus(HttpStatus.CREATED)
    public AttendanceResponse clock(@PathVariable Long employeeId) {
        return attendanceService.clock(employeeId);
    }

    @GetMapping("/status")
    public AttendanceStatusResponse status(@PathVariable Long employeeId) {
        return attendanceService.status(employeeId);
    }

    @GetMapping("/attendance")
    public List<AttendanceResponse> history(@PathVariable Long employeeId,
            @RequestParam(required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant from,
            @RequestParam(required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant to) {
        return attendanceService.history(employeeId, from, to);
    }
}
