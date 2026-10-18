package com.visionclock.employee;

import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.visionclock.common.exception.DuplicateEmployeeNumberException;
import com.visionclock.common.exception.EmployeeNotFoundException;
import com.visionclock.employee.dto.CreateEmployeeRequest;
import com.visionclock.employee.dto.EmployeeResponse;
import com.visionclock.employee.dto.UpdateEmployeeRequest;

@Service
public class EmployeeService {

    private final EmployeeRepository employeeRepository;

    public EmployeeService(EmployeeRepository employeeRepository) {
        this.employeeRepository = employeeRepository;
    }

    @Transactional
    public EmployeeResponse create(CreateEmployeeRequest request) {
        if (employeeRepository.existsByEmployeeNumber(request.employeeNumber())) {
            throw new DuplicateEmployeeNumberException(request.employeeNumber());
        }
        Employee employee = new Employee(
                request.firstName(), request.lastName(), request.employeeNumber());
        return EmployeeResponse.from(employeeRepository.save(employee));
    }

    @Transactional(readOnly = true)
    public EmployeeResponse get(Long id) {
        return EmployeeResponse.from(findOrThrow(id));
    }

    @Transactional(readOnly = true)
    public List<EmployeeResponse> list(boolean activeOnly) {
        List<Employee> employees = activeOnly
                ? employeeRepository.findByActiveTrue()
                : employeeRepository.findAll();
        return employees.stream().map(EmployeeResponse::from).toList();
    }

    @Transactional
    public EmployeeResponse update(Long id, UpdateEmployeeRequest request) {
        Employee employee = findOrThrow(id);
        employee.updateName(request.firstName(), request.lastName());
        return EmployeeResponse.from(employee);
    }

    @Transactional
    public EmployeeResponse deactivate(Long id) {
        Employee employee = findOrThrow(id);
        employee.deactivate();
        return EmployeeResponse.from(employee);
    }

    private Employee findOrThrow(Long id) {
        return employeeRepository.findById(id)
                .orElseThrow(() -> new EmployeeNotFoundException(id));
    }
}
