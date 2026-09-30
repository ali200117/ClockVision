# VisionClock

VisionClock is a small attendance system I am building mainly to practice Java backend development and machine learning in the same project.

The first part of the project is a normal attendance system where employees can be registered and clock in and out.

Later, the goal is to add my own face recognition model. An employee will register their face beforehand, and a camera can then recognize the employee and use that identity to clock them in or out.

The point of the project is not to build a production-ready biometric system. It is mainly a project for learning how the different parts work, especially the ML part instead of relying on a finished face recognition service.

## Planned flow

```text
Employee stands in front of camera
        ↓
Face is detected
        ↓
ML model identifies employee
        ↓
Employee ID is sent to Java backend
        ↓
Backend checks current attendance status
        ↓
CLOCK_IN or CLOCK_OUT
        ↓
Attendance is stored in PostgreSQL
```

## Current focus

The first version does not include machine learning.

For now the goal is to build the Java backend properly first:

- Employee management
- Create, read, update and deactivate employees
- Clock employees in and out
- Store attendance history
- Find an employee's current attendance status
- PostgreSQL database
- REST API
- Business logic kept separate from controllers and database access

## Planned backend structure

```text
src/main/java/.../

├── employee/
│   ├── Employee.java
│   ├── EmployeeController.java
│   ├── EmployeeService.java
│   ├── EmployeeRepository.java
│   └── dto/
│
├── attendance/
│   ├── Attendance.java
│   ├── AttendanceType.java
│   ├── AttendanceController.java
│   ├── AttendanceService.java
│   ├── AttendanceRepository.java
│   └── dto/
│
├── recognition/
│   └── added later
│
├── common/
│   ├── exception/
│   └── config/
│
└── VisionClockApplication.java
```

## Main entities

### Employee

Stores the employees registered in the system.

```text
id
firstName
lastName
employeeNumber
active
createdAt
```

### Attendance

Each clock-in or clock-out is stored as a separate event.

```text
id
employeeId
type
timestamp
```

Attendance types:

```text
CLOCK_IN
CLOCK_OUT
```

## Attendance logic

The backend checks the employee's latest attendance event before creating a new one.

```text
No previous attendance
→ CLOCK_IN

Last event = CLOCK_OUT
→ CLOCK_IN

Last event = CLOCK_IN
→ CLOCK_OUT
```

The ML model will not decide whether someone should clock in or out.

Its job will only be to answer:

```text
Who is standing in front of the camera?
```

The Java backend will handle everything after that.

## Machine learning plan

Once the backend works, the next part is to start experimenting with face recognition.

The plan is to:

- Register multiple employees
- Collect face images for each employee
- Build the dataset myself
- Preprocess the images
- Train and evaluate my own model
- Recognize employees from a camera
- Handle unknown faces
- Connect the recognition result to the Java backend

I want to build as much of the ML part myself as reasonably possible while learning the concepts behind it.

The goal is to understand things like:

- Image preprocessing
- Training and validation data
- Neural networks
- CNNs
- Loss functions
- Backpropagation
- Overfitting
- Classification
- Face embeddings
- Similarity and distance
- Confidence thresholds

## Technologies

### Backend

- Java
- Spring Boot
- Spring Data JPA
- PostgreSQL
- REST

### Machine Learning

Planned:

- Python
- PyTorch
- NumPy
- OpenCV

Python will be used for the ML part, while Java remains responsible for the main system and business logic.

## Project status

Currently building the Java backend first.

Machine learning and camera recognition will be added after the attendance system works without ML.
