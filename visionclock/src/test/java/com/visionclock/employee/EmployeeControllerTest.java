package com.visionclock.employee;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.Instant;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import com.visionclock.common.exception.DuplicateEmployeeNumberException;
import com.visionclock.common.exception.EmployeeNotFoundException;
import com.visionclock.employee.dto.CreateEmployeeRequest;
import com.visionclock.employee.dto.EmployeeResponse;

@WebMvcTest(EmployeeController.class)
class EmployeeControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private EmployeeService employeeService;

    @Test
    void createReturns201WithLocation() throws Exception {
        when(employeeService.create(any(CreateEmployeeRequest.class))).thenReturn(
                new EmployeeResponse(5L, "Ola", "Nordmann", "T-1001", true, Instant.parse("2026-01-05T08:00:00Z")));

        mockMvc.perform(post("/api/employees")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"firstName":"Ola","lastName":"Nordmann","employeeNumber":"T-1001"}
                        """))
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", org.hamcrest.Matchers.endsWith("/api/employees/5")))
                .andExpect(jsonPath("$.id").value(5))
                .andExpect(jsonPath("$.active").value(true));
    }

    @Test
    void createWithBlankNameReturns400() throws Exception {
        mockMvc.perform(post("/api/employees")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"firstName":"","lastName":"Nordmann","employeeNumber":"T-1001"}
                        """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.errors.firstName").exists());
    }

    @Test
    void createWithDuplicateNumberReturns409() throws Exception {
        when(employeeService.create(any(CreateEmployeeRequest.class)))
                .thenThrow(new DuplicateEmployeeNumberException("T-1001"));

        mockMvc.perform(post("/api/employees")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"firstName":"Ola","lastName":"Nordmann","employeeNumber":"T-1001"}
                        """))
                .andExpect(status().isConflict());
    }

    @Test
    void getUnknownEmployeeReturns404() throws Exception {
        when(employeeService.get(99L)).thenThrow(new EmployeeNotFoundException(99L));

        mockMvc.perform(get("/api/employees/99"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.title").value("Employee not found"));
    }
}
