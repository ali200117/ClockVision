package com.visionclock.attendance;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

public interface AttendanceRepository extends JpaRepository<Attendance, Long> {

    Optional<Attendance> findFirstByEmployeeIdOrderByRecordedAtDesc(Long employeeId);

    List<Attendance> findByEmployeeIdOrderByRecordedAtDesc(Long employeeId);

    List<Attendance> findByEmployeeIdAndRecordedAtBetweenOrderByRecordedAtDesc(
            Long employeeId, Instant from, Instant to);
}
