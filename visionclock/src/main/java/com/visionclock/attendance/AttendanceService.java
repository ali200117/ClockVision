package com.visionclock.attendance;

import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Optional;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.visionclock.attendance.dto.AttendanceResponse;
import com.visionclock.attendance.dto.AttendanceStatusResponse;
import com.visionclock.common.exception.EmployeeInactiveException;
import com.visionclock.common.exception.EmployeeNotFoundException;
import com.visionclock.employee.Employee;
import com.visionclock.employee.EmployeeRepository;

@Service
public class AttendanceService {

    private final AttendanceRepository attendanceRepository;
    private final EmployeeRepository employeeRepository;
    private final Clock clock;

    public AttendanceService(AttendanceRepository attendanceRepository,
            EmployeeRepository employeeRepository, Clock clock) {
        this.attendanceRepository = attendanceRepository;
        this.employeeRepository = employeeRepository;
        this.clock = clock;
    }

    @Transactional
    public AttendanceResponse clock(Long employeeId) {
        // Låser ansatt-raden så to samtidige stemplinger ikke begge ser samme siste hendelse.
        Employee employee = employeeRepository.findByIdForUpdate(employeeId)
                .orElseThrow(() -> new EmployeeNotFoundException(employeeId));
        if (!employee.isActive()) {
            throw new EmployeeInactiveException(employeeId);
        }

        AttendanceType next = attendanceRepository
                .findFirstByEmployeeIdOrderByRecordedAtDesc(employeeId)
                .map(last -> last.getType().opposite())
                .orElse(AttendanceType.CLOCK_IN);

        Attendance saved = attendanceRepository.save(
                new Attendance(employee, next, Instant.now(clock)));
        return AttendanceResponse.from(saved);
    }

    @Transactional(readOnly = true)
    public AttendanceStatusResponse status(Long employeeId) {
        requireEmployee(employeeId);
        Optional<Attendance> last = attendanceRepository
                .findFirstByEmployeeIdOrderByRecordedAtDesc(employeeId);

        AttendanceStatus status = last
                .filter(a -> a.getType() == AttendanceType.CLOCK_IN)
                .map(a -> AttendanceStatus.CLOCKED_IN)
                .orElse(AttendanceStatus.CLOCKED_OUT);
        Instant since = last.map(Attendance::getRecordedAt).orElse(null);
        return new AttendanceStatusResponse(employeeId, status, since);
    }

    @Transactional(readOnly = true)
    public List<AttendanceResponse> history(Long employeeId, Instant from, Instant to) {
        requireEmployee(employeeId);
        List<Attendance> events = (from == null && to == null)
                ? attendanceRepository.findByEmployeeIdOrderByRecordedAtDesc(employeeId)
                : attendanceRepository.findByEmployeeIdAndRecordedAtBetweenOrderByRecordedAtDesc(
                        employeeId,
                        from != null ? from : Instant.EPOCH,
                        to != null ? to : Instant.now(clock));
        return events.stream().map(AttendanceResponse::from).toList();
    }

    private void requireEmployee(Long employeeId) {
        if (!employeeRepository.existsById(employeeId)) {
            throw new EmployeeNotFoundException(employeeId);
        }
    }
}
