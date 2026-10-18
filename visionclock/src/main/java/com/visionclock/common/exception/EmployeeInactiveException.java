package com.visionclock.common.exception;

public class EmployeeInactiveException extends RuntimeException {

    public EmployeeInactiveException(Long id) {
        super("Employee with id " + id + " is deactivated");
    }
}
