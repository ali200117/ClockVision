package com.visionclock.employee.dto;

import java.time.Instant;

import com.visionclock.employee.Employee;

public record EmployeeResponse(
        Long id,
        String firstName,
        String lastName,
        String employeeNumber,
        boolean active,
        Instant createdAt) {

    public static EmployeeResponse from(Employee employee) {
        return new EmployeeResponse(
                employee.getId(),
                employee.getFirstName(),
                employee.getLastName(),
                employee.getEmployeeNumber(),
                employee.isActive(),
                employee.getCreatedAt());
    }
}
