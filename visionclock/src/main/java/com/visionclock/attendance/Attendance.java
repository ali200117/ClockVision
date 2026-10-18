package com.visionclock.attendance;

import java.time.Instant;

import com.visionclock.employee.Employee;

import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;

@Entity
public class Attendance {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "employee_id")
    private Employee employee;

    @Enumerated(EnumType.STRING)
    private AttendanceType type;

    private Instant recordedAt;

    protected Attendance() {
        // kreves av JPA
    }

    public Attendance(Employee employee, AttendanceType type, Instant recordedAt) {
        this.employee = employee;
        this.type = type;
        this.recordedAt = recordedAt;
    }

    public Long getId() {
        return id;
    }

    public Employee getEmployee() {
        return employee;
    }

    public AttendanceType getType() {
        return type;
    }

    public Instant getRecordedAt() {
        return recordedAt;
    }
}
