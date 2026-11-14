# KIT College API – Technical Reference Specification

Source of Truth: `https://ht.knowvally.com/docs` (OpenAPI 3.1.0)
Base URL: `https://ht.knowvally.com`
Sandbox ID: `QH-85D794`

---

## 1. Authentication & Security Architecture

### 1.1 Headers Required on Every Request
All HTTP requests sent to the KIT API must include the participant access key:
```http
X-Participant-Key: kit_live_d32872467c3ab0eef357287c822da643165b5ef4
Content-Type: application/json
Accept: application/json
```

### 1.2 User Authentication (`POST /v1/auth/login`)
Public endpoint used to exchange student or faculty credentials for a scoped JWT bearer token.

- **Endpoint:** `POST /v1/auth/login`
- **Headers:** `X-Participant-Key`
- **Request Schema:**
  ```json
  {
    "login_id": "arjun",
    "password": "Kit@2026"
  }
  ```
- **Response Schema (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "user": {
      "id": 76,
      "login_id": "arjun",
      "full_name": "Arjun K",
      "role": "student",
      "department": "CSE",
      "class_id": 31,
      "class_code": "CSE-2A",
      "programme": "UG",
      "year_of_study": 2,
      "notes": null
    }
  }
  ```
- **Token Validity:** 8 hours (480 minutes). Token expiry is validated by the server and client.
- **Test Accounts (Password for all: `Kit@2026`):**
  - **Students:** `arjun`, `priya`, `kavya`, `rahul`, `karthik`, `meena`, `divya`, `sneha`
  - **Teachers:** `lakshmi`, `senthil`

### 1.3 Protected Endpoints Authorization
All student and teacher operations require the bearer token in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```

### 1.4 Idempotency Protection
State-changing operations (`POST /v1/me/requests`, `POST /v1/teacher/requests/{id}/approve`, `POST /v1/teacher/requests/{id}/reject`) accept an optional but recommended header:
```http
Idempotency-Key: <unique-uuid>
```
When provided, if a network error occurs and the request is retried with the identical key, the college system returns the existing created resource without performing a duplicate write.

### 1.5 Error Response Structure
All client and server errors return structured JSON:
```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Detailed error explanation",
    "field": "optional_field_name"
  }
}
```
HTTP status codes used:
- `400 Bad Request`: Validation failure or policy rejection.
- `401 Unauthorized`: Missing or invalid `X-Participant-Key`, or expired bearer token.
- `403 Forbidden`: Role mismatch (e.g., student attempting teacher action).
- `404 Not Found`: Target resource ID not found.
- `422 Unprocessable Entity`: Request body schema validation error.
- `500 Internal Server Error`: Backend execution failure.

---

## 2. Public / Visitor Endpoints (No Bearer Token Required)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/college` | Returns official institute profile, tagline, accreditation, and contact details. |
| `GET` | `/v1/courses` | Returns degree programs, intake seats, tuition fees, and durations. |
| `GET` | `/v1/today` | Current academic day overview, active events, and day order. |
| `GET` | `/v1/calendar` | Academic calendar dates, official holidays, and scheduled exams. |
| `GET` | `/v1/documents` | List of published documents, handbooks, lesson notes, and circulars. |
| `GET` | `/v1/documents/{id}/file` | Binary download of the specified document PDF. |
| `GET` | `/v1/placements/drives` | Upcoming campus placement drives, visiting companies, and eligibility criteria. |
| `POST` | `/v1/admissions/applications` | Submit application for admission into an academic course. |
| `GET` | `/v1/health` | Upstream service health status. |

---

## 3. Student Operations (Require Student Bearer Token)

### 3.1 Attendance (`GET /v1/me/attendance`)
- **Response:**
  ```json
  {
    "as_of_date": "2026-11-21",
    "overall_percentage": 76.0,
    "total_classes_held": 50,
    "total_classes_attended": 38,
    "subjects": [
      {
        "subject_id": 25,
        "subject_code": "CS304",
        "subject_name": "Database Management Systems",
        "classes_held": 25,
        "classes_attended": 19,
        "percentage": 76.0
      }
    ]
  }
  ```

### 3.2 Timetable (`GET /v1/me/timetable`)
- **Response:** Array of scheduled periods:
  ```json
  [
    {
      "id": 85,
      "weekday": 1,
      "period": 1,
      "start_time": "09:00",
      "end_time": "09:50",
      "subject_code": "CS301",
      "subject_name": "Data Structures and Algorithms",
      "room": "Hall A",
      "teacher_name": "Dr. Lakshmi"
    }
  ]
  ```

### 3.3 Enrolled Subjects (`GET /v1/me/subjects`)
Returns subjects registered for the student's current semester.

### 3.4 Student Requests (`GET /v1/me/requests`)
Lists student's submitted leave and On-Duty requests with status (`pending`, `approved`, `rejected`, `cancelled`).

### 3.5 Submit Request (`POST /v1/me/requests`)
- **Request Payload:**
  ```json
  {
    "type": "personal_leave",
    "from_date": "2026-11-25",
    "to_date": "2026-11-25",
    "half_day": false,
    "reason": "Family function in hometown",
    "event_name": null
  }
  ```
  *(For `type: "on_duty"`, `event_name` is required)*
- **Response (`200 OK` or `201 Created`):**
  ```json
  {
    "id": 119,
    "student_id": 76,
    "type": "personal_leave",
    "from_date": "2026-11-25",
    "to_date": "2026-11-25",
    "reason": "Family function in hometown",
    "status": "pending",
    "created_at": "2026-11-14T07:44:00Z"
  }
  ```

### 3.6 Cancel Request (`POST /v1/me/requests/{id}/cancel`)
Cancels a previously submitted request before teacher review.

### 3.7 Placement Drives Registration (`POST /v1/placements/drives/{id}/register`)
Registers the student for an eligible placement recruitment drive.

---

## 4. Teacher / Faculty Operations (Require Teacher Bearer Token)

### 4.1 Assigned Classes (`GET /v1/teacher/classes`)
Returns classes assigned to the instructor and advisor roles.
```json
[
  {
    "class_id": 31,
    "class_code": "CSE-2A",
    "department": "CSE",
    "programme": "UG",
    "year": 2,
    "role_type": "advisor"
  }
]
```

### 4.2 Review Pending Requests (`GET /v1/teacher/requests`)
Returns pending student requests requiring instructor/advisor review.

### 4.3 Approve Request (`POST /v1/teacher/requests/{id}/approve`)
- **Payload:** `{"comment": "Approved by advisor."}`
- **Response:** `{"success": true, "status": "approved"}`

### 4.4 Reject Request (`POST /v1/teacher/requests/{id}/reject`)
- **Payload:** `{"reason": "Event proof missing."}` *(Reason is mandatory)*
- **Response:** `{"success": true, "status": "rejected"}`

