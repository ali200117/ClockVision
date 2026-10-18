package com.visionclock.employee;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;
import org.springframework.boot.jdbc.test.autoconfigure.AutoConfigureTestDatabase;

@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class EmployeeRepositoryTest {

    @Autowired
    private EmployeeRepository employeeRepository;

    @Test
    void savesAndFindsEmployeeById() {
        // Arrange: lag en ansatt
        Employee employee = new Employee("Ola", "Nordmann", "T-1001");

        // Act: lagre den og hent den tilbake på id
        Employee saved = employeeRepository.save(employee);
        Employee found = employeeRepository.findById(saved.getId()).orElseThrow();

        // Assert: det vi fikk tilbake stemmer med det vi lagret
        assertThat(found.getFirstName()).isEqualTo("Ola");
        assertThat(found.getEmployeeNumber()).isEqualTo("T-1001");
        assertThat(found.isActive()).isTrue();
    }

    @Test
    void existsByEmployeeNumberReturnsTrueOnlyForSavedNumber() {
        // Arrange: lagre en ansatt med nummer T-1001
        employeeRepository.save(new Employee("Ola", "Nordmann", "T-1001"));

        // Act: spør om et nummer som er lagret og et som ikke er det
        boolean savedNumberExists = employeeRepository.existsByEmployeeNumber("T-1001");
        boolean unknownNumberExists = employeeRepository.existsByEmployeeNumber("T-9999");

        // Assert: bare det lagrede nummeret finnes
        assertThat(savedNumberExists).isTrue();
        assertThat(unknownNumberExists).isFalse();
    }
}
