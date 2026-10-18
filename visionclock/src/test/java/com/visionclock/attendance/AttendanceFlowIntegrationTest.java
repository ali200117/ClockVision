package com.visionclock.attendance;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import com.jayway.jsonpath.JsonPath;

@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class AttendanceFlowIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void clockInThenClockOutThenStatusAndHistory() throws Exception {
        String body = mockMvc.perform(post("/api/employees")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"firstName":"Test","lastName":"Bruker","employeeNumber":"IT-FLOW-1"}
                        """))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();
        Number id = JsonPath.read(body, "$.id");

        mockMvc.perform(post("/api/employees/{id}/clock", id))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.type").value("CLOCK_IN"));

        mockMvc.perform(get("/api/employees/{id}/status", id))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("CLOCKED_IN"));

        mockMvc.perform(post("/api/employees/{id}/clock", id))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.type").value("CLOCK_OUT"));

        mockMvc.perform(get("/api/employees/{id}/status", id))
                .andExpect(jsonPath("$.status").value("CLOCKED_OUT"));

        mockMvc.perform(get("/api/employees/{id}/attendance", id))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(2))
                .andExpect(jsonPath("$[0].type").value("CLOCK_OUT"));
    }

    @Test
    void deactivatedEmployeeCannotClock() throws Exception {
        String body = mockMvc.perform(post("/api/employees")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"firstName":"Test","lastName":"Inaktiv","employeeNumber":"IT-FLOW-2"}
                        """))
                .andReturn().getResponse().getContentAsString();
        Number id = JsonPath.read(body, "$.id");

        mockMvc.perform(post("/api/employees/{id}/deactivate", id))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.active").value(false));

        mockMvc.perform(post("/api/employees/{id}/clock", id))
                .andExpect(status().isConflict());
    }
}
