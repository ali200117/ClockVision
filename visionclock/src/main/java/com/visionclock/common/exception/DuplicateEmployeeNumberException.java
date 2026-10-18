package com.visionclock.common.exception;

public class DuplicateEmployeeNumberException extends RuntimeException {

    public DuplicateEmployeeNumberException(String employeeNumber) {
        super("Employee number " + employeeNumber + " is already in use");
    }
}
