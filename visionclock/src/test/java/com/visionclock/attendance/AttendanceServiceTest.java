package com.visionclock.attendance;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Optional;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.visionclock.attendance.dto.AttendanceResponse;
import com.visionclock.attendance.dto.AttendanceStatusResponse;
import com.visionclock.common.exception.EmployeeInactiveException;
import com.visionclock.common.exception.EmployeeNotFoundException;
import com.visionclock.employee.Employee;
import com.visionclock.employee.EmployeeRepository;

@ExtendWith(MockitoExtension.class)
class AttendanceServiceTest {

    private static final Instant NOW = Instant.parse("2026-01-05T08:00:00Z");

    @Mock
    private AttendanceRepository attendanceRepository;

    @Mock
    private EmployeeRepository employeeRepository;

    private AttendanceService attendanceService;
    private Employee employee;

    @BeforeEach
    void setUp() {
        Clock fixedClock = Clock.fixed(NOW, ZoneOffset.UTC);
        attendanceService = new AttendanceService(attendanceRepository, employeeRepository, fixedClock);
        employee = new Employee("Ola", "Nordmann", "T-1001");
    }

    @Test
    void firstClockIsClockIn() {
        when(employeeRepository.findByIdForUpdate(1L)).thenReturn(Optional.of(employee));
        when(attendanceRepository.findFirstByEmployeeIdOrderByRecordedAtDesc(1L))
                .thenReturn(Optional.empty());
        when(attendanceRepository.save(any(Attendance.class))).thenAnswer(inv -> inv.getArgument(0));

        AttendanceResponse response = attendanceService.clock(1L);

        assertThat(response.type()).isEqualTo(AttendanceType.CLOCK_IN);
        assertThat(response.recordedAt()).isEqualTo(NOW);
    }

    @Test
    void clockAfterClockInIsClockOut() {
        when(employeeRepository.findByIdForUpdate(1L)).thenReturn(Optional.of(employee));
        when(attendanceRepository.findFirstByEmployeeIdOrderByRecordedAtDesc(1L))
                .thenReturn(Optional.of(new Attendance(employee, AttendanceType.CLOCK_IN, NOW.minusSeconds(3600))));
        when(attendanceRepository.save(any(Attendance.class))).thenAnswer(inv -> inv.getArgument(0));

        AttendanceResponse response = attendanceService.clock(1L);

        assertThat(response.type()).isEqualTo(AttendanceType.CLOCK_OUT);
    }

    @Test
    void clockAfterClockOutIsClockIn() {
        when(employeeRepository.findByIdForUpdate(1L)).thenReturn(Optional.of(employee));
        when(attendanceRepository.findFirstByEmployeeIdOrderByRecordedAtDesc(1L))
                .thenReturn(Optional.of(new Attendance(employee, AttendanceType.CLOCK_OUT, NOW.minusSeconds(3600))));
        when(attendanceRepository.save(any(Attendance.class))).thenAnswer(inv -> inv.getArgument(0));

        AttendanceResponse response = attendanceService.clock(1L);

        assertThat(response.type()).isEqualTo(AttendanceType.CLOCK_IN);
    }

    @Test
    void inactiveEmployeeCannotClock() {
        employee.deactivate();
        when(employeeRepository.findByIdForUpdate(1L)).thenReturn(Optional.of(employee));

        assertThatThrownBy(() -> attendanceService.clock(1L))
                .isInstanceOf(EmployeeInactiveException.class);
        verify(attendanceRepository, never()).save(any());
    }

    @Test
    void unknownEmployeeCannotClock() {
        when(employeeRepository.findByIdForUpdate(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> attendanceService.clock(99L))
                .isInstanceOf(EmployeeNotFoundException.class);
    }

    @Test
    void statusIsClockedInAfterClockIn() {
        when(employeeRepository.existsById(1L)).thenReturn(true);
        when(attendanceRepository.findFirstByEmployeeIdOrderByRecordedAtDesc(1L))
                .thenReturn(Optional.of(new Attendance(employee, AttendanceType.CLOCK_IN, NOW)));

        AttendanceStatusResponse status = attendanceService.status(1L);

        assertThat(status.status()).isEqualTo(AttendanceStatus.CLOCKED_IN);
        assertThat(status.since()).isEqualTo(NOW);
    }

    @Test
    void statusIsClockedOutWithoutHistory() {
        when(employeeRepository.existsById(1L)).thenReturn(true);
        when(attendanceRepository.findFirstByEmployeeIdOrderByRecordedAtDesc(1L))
                .thenReturn(Optional.empty());

        AttendanceStatusResponse status = attendanceService.status(1L);

        assertThat(status.status()).isEqualTo(AttendanceStatus.CLOCKED_OUT);
        assertThat(status.since()).isNull();
    }
}
