import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.config import settings

# In-memory mock database for fallback and offline tests
MOCK_KIT_DB = {
    "placement_drives": [
        {"id": 21, "company": "Freshworks", "category": "dream", "min_cgpa": 8.0, "allowed_departments": ["CSE"], "eligible_years": [4], "deadline": "2026-11-28", "seats_total": 20, "seats_left": 12},
        {"id": 20, "company": "TCS", "category": "non_dream", "min_cgpa": 6.0, "allowed_departments": ["CSE", "ECE", "MECH"], "eligible_years": [4], "deadline": "2026-12-01", "seats_total": 50, "seats_left": 31}
    ],
    "today": {"date": "2026-11-21", "weekday": 6, "weekday_name": "Saturday", "timezone": "Asia/Kolkata"},
    "students": {
        "76": {
            "account_id": "76",
            "login_id": "arjun",
            "student_id": "KIT2024CS042",
            "name": "Arjun K",
            "department": "Computer Science & Engineering",
            "year": 2,
            "overall_attendance_pct": 76.0,
            "attendance_breakdown": [
                {"subject": "Data Structures and Algorithms", "code": "CS301", "attended": 18, "total": 20, "pct": 90.0},
                {"subject": "Computer Networks", "code": "CS302", "attended": 10, "total": 15, "pct": 66.7},
                {"subject": "Operating Systems", "code": "CS303", "attended": 10, "total": 15, "pct": 66.7}
            ],
            "timetable": [
                {"day": "Monday", "schedule": "09:00 CS301 (Hall A), 11:00 CS302 (Lab 2), 14:00 CS303"},
                {"day": "Tuesday", "schedule": "10:00 CS304, 11:30 CS301, 14:30 AI Elective"},
                {"day": "Wednesday", "schedule": "09:00 CS302, 11:00 OS Lab, 15:00 Library"},
                {"day": "Thursday", "schedule": "10:00 CS303, 11:30 CS304, 14:00 Seminar"},
                {"day": "Friday", "schedule": "09:00 CS301, 10:30 Sports / Club, 14:00 Mentoring"}
            ],
            "requests": [
                {
                    "id": "32",
                    "type": "ON_DUTY",
                    "date": "2026-11-30",
                    "reason": "Technical Symposium",
                    "status": "APPROVED",
                    "reviewed_by": "Dr. Lakshmi"
                }
            ]
        },
        "kit_stu_101": {
            "account_id": "kit_stu_101",
            "login_id": "aarav",
            "student_id": "KIT2024CS042",
            "name": "Aarav Sharma",
            "department": "Computer Science & Engineering",
            "year": 3,
            "overall_attendance_pct": 84.5,
            "attendance_breakdown": [
                {"subject": "Design & Analysis of Algorithms", "code": "CS301", "attended": 38, "total": 42, "pct": 90.5},
                {"subject": "Computer Networks", "code": "CS302", "attended": 32, "total": 40, "pct": 80.0}
            ],
            "timetable": [
                {"day": "Monday", "schedule": "09:00 CS301 (Hall A), 11:00 CS302 (Lab 2), 14:00 CS303"},
                {"day": "Tuesday", "schedule": "10:00 CS304, 11:30 CS301, 14:30 AI Elective"}
            ],
            "requests": []
        }
    },
    "teachers": {
        "73": {
            "account_id": "73",
            "login_id": "lakshmi",
            "teacher_id": "FAC882",
            "name": "Dr. Lakshmi",
            "department": "Computer Science & Engineering",
            "classes": ["CS301 - Algorithms", "CS302 - Networks"]
        },
        "kit_tea_501": {
            "account_id": "kit_tea_501",
            "login_id": "lakshmi",
            "teacher_id": "FAC882",
            "name": "Dr. Lakshmi",
            "department": "Computer Science & Engineering",
            "classes": ["CS301 - Algorithms", "CS302 - Networks"]
        }
    },
    "pending_requests": [
        {
            "id": "35",
            "student_id": "77",
            "student_name": "Priya M",
            "type": "LEAVE",
            "date": "2026-11-25",
            "reason": "Family function in hometown",
            "status": "PENDING"
        },
        {
            "id": "REQ-9012",
            "student_id": "76",
            "student_name": "Arjun K",
            "type": "ON_DUTY",
            "date": "2026-11-18",
            "reason": "National Hackathon 2026",
            "status": "PENDING"
        }
    ],
    "calendar": {
        "holidays": [
            {"date": "2026-12-25", "name": "Christmas Day"},
            {"date": "2027-01-01", "name": "New Year's Day"},
            {"date": "2027-01-14", "name": "Pongal Festival"}
        ],
        "exams": [
            {"date": "2026-11-20", "subject": "CS304 Database Systems Midterm", "time": "10:00 AM"},
            {"date": "2026-11-23", "subject": "CS302 Computer Networks Midterm", "time": "10:00 AM"},
            {"date": "2026-11-25", "subject": "CS301 Algorithms Midterm", "time": "02:00 PM"}
        ]
    },
    "college_info": {
        "name": "Knotopian Institute of Technology (KIT)",
        "motto": "Excellence in Engineering and Applied Technology",
        "location": "Knotopian Knowledge City, Coimbatore, Tamil Nadu 641042",
        "accreditation": "Autonomous Premier Institution",
        "helpline": "+91 422 2619000",
        "email": "admissions@kit.ac.in"
    },
    "courses": [
        {
            "code": "BTECH-CSE",
            "title": "B.Tech in Computer Science and Engineering",
            "duration": "4 Years",
            "annual_fee": "Rs. 1,80,000",
            "seats": 180,
            "eligibility": "10+2 with 60% aggregate in Physics, Chemistry & Math. Valid State CET/JEE score."
        },
        {
            "code": "BTECH-AIDS",
            "title": "B.Tech in Artificial Intelligence & Data Science",
            "duration": "4 Years",
            "annual_fee": "Rs. 1,90,000",
            "seats": 120,
            "eligibility": "10+2 with 60% aggregate in PCM."
        },
        {
            "code": "BTECH-ECE",
            "title": "B.Tech in Electronics & Communication Engineering",
            "duration": "4 Years",
            "annual_fee": "Rs. 1,60,000",
            "seats": 120,
            "eligibility": "10+2 with 55% aggregate in PCM."
        }
    ]
}

class KitApiClient:
    def __init__(self, base_url: Optional[str] = None, participant_key: Optional[str] = None):
        self.base_url = (base_url or settings.kit_api_base_url).rstrip("/")
        self.participant_key = participant_key if participant_key is not None else settings.kit_participant_key

    def _should_use_real_api(self) -> bool:
        return not settings.kit_use_mock and bool(self.participant_key)

    def _http_request(
        self,
        method: str,
        path: str,
        token: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        timeout: float = 8.0
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            "X-Participant-Key": self.participant_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_bytes = resp.read()
                if not resp_bytes:
                    return {"success": True}
                return json.loads(resp_bytes.decode("utf-8"))
        except urllib.error.HTTPError as he:
            detail = ""
            try:
                err_data = json.loads(he.read().decode("utf-8"))
                detail = err_data.get("detail", str(err_data))
            except Exception:
                detail = str(he)
            return {"error": detail or str(he), "status_code": he.code}
        except Exception as e:
            return {"error": str(e), "network_failure": True}

    def login(self, login_id: str, password: str) -> Dict[str, Any]:
        """Real KIT API login (/v1/auth/login) with fallback to mock."""
        if self._should_use_real_api():
            res = self._http_request("POST", "/v1/auth/login", data={"login_id": login_id, "password": password})
            if "access_token" in res:
                return {
                    "success": True,
                    "access_token": res["access_token"],
                    "user": res.get("user", {})
                }
            if not res.get("network_failure"):
                return {"success": False, "error": res.get("error", "Authentication failed")}

        # Fallback to local accounts
        clean_id = login_id.strip().lower()
        if clean_id in ["arjun", "priya", "kavya", "rahul", "kit_stu_101"]:
            return {
                "success": True,
                "access_token": f"mock_token_stu_{clean_id}",
                "user": {
                    "id": 76,
                    "login_id": clean_id,
                    "full_name": "Arjun K",
                    "role": "student",
                    "department": "CSE"
                }
            }
        elif clean_id in ["lakshmi", "senthil", "kit_tea_501"]:
            return {
                "success": True,
                "access_token": f"mock_token_tea_{clean_id}",
                "user": {
                    "id": 73,
                    "login_id": clean_id,
                    "full_name": "Dr. Lakshmi",
                    "role": "teacher",
                    "department": "CSE"
                }
            }
        return {"success": False, "error": "Invalid login credentials"}

    def get_attendance(self, account_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Returns student attendance records."""
        if self._should_use_real_api() and token:
            res = self._http_request("GET", "/v1/me/attendance", token=token)
            if "overall_percentage" in res:
                return {
                    "success": True,
                    "overall_pct": res.get("overall_percentage", 0.0),
                    "name": "Student",
                    "breakdown": [
                        {
                            "subject": s.get("subject_name", s.get("subject_code")),
                            "pct": s.get("percentage", 0.0)
                        } for s in res.get("subjects", [])
                    ]
                }
            if not res.get("network_failure"):
                return {"success": False, "error": res.get("error", "Failed to retrieve attendance")}

        # Fallback
        student = MOCK_KIT_DB["students"].get(str(account_id)) or MOCK_KIT_DB["students"]["76"]
        return {
            "success": True,
            "overall_pct": student["overall_attendance_pct"],
            "name": student["name"],
            "breakdown": student["attendance_breakdown"]
        }

    def get_timetable(self, account_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Returns student timetable."""
        if self._should_use_real_api() and token:
            res = self._http_request("GET", "/v1/me/timetable", token=token)
            if isinstance(res, list):
                # group by weekday
                day_names = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday"}
                items = []
                for row in res:
                    day = day_names.get(row.get("weekday", 1), f"Day {row.get('weekday')}")
                    items.append({
                        "day": day,
                        "schedule": f"{row.get('start_time')} {row.get('subject_name')} ({row.get('subject_code')})"
                    })
                return {"success": True, "timetable": items}
            if not res.get("network_failure"):
                return {"success": False, "error": res.get("error", "Failed to retrieve timetable")}

        student = MOCK_KIT_DB["students"].get(str(account_id)) or MOCK_KIT_DB["students"]["76"]
        return {"success": True, "timetable": student["timetable"]}

    def get_calendar_exams(self, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns scheduled examination dates."""
        if self._should_use_real_api():
            res = self._http_request("GET", "/v1/calendar", token=token)
            if isinstance(res, list):
                exams = [
                    {"date": r["date"], "subject": r.get("title", "Exam"), "time": "10:00 AM"}
                    for r in res if r.get("type") == "exam"
                ]
                if exams:
                    return exams
        return MOCK_KIT_DB["calendar"]["exams"]

    def get_calendar_holidays(self, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns college holidays."""
        if self._should_use_real_api():
            res = self._http_request("GET", "/v1/calendar", token=token)
            if isinstance(res, list):
                holidays = [
                    {"date": r["date"], "name": r.get("title", "Holiday")}
                    for r in res if r.get("type") == "holiday"
                ]
                if holidays:
                    return holidays
        return MOCK_KIT_DB["calendar"]["holidays"]

    def get_student_requests(self, account_id: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns requests submitted by the student."""
        if self._should_use_real_api() and token:
            res = self._http_request("GET", "/v1/me/requests", token=token)
            if isinstance(res, list):
                return [
                    {
                        "id": str(r.get("id")),
                        "type": r.get("type", "").upper(),
                        "date": r.get("from_date"),
                        "reason": r.get("reason", ""),
                        "status": r.get("status", "PENDING").upper()
                    } for r in res
                ]
        student = MOCK_KIT_DB["students"].get(str(account_id)) or MOCK_KIT_DB["students"]["76"]
        return student.get("requests", [])

    def submit_leave_request(
        self,
        account_id: str,
        leave_date: str,
        reason: str,
        idempotency_key: str,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submits leave request to KIT backend."""
        if self._should_use_real_api() and token:
            payload = {
                "type": "personal_leave",
                "from_date": leave_date,
                "to_date": leave_date,
                "half_day": False,
                "reason": reason
            }
            res = self._http_request("POST", "/v1/me/requests", token=token, data=payload, idempotency_key=idempotency_key)
            if "id" in res:
                return {
                    "success": True,
                    "request_id": str(res["id"]),
                    "status": res.get("status", "pending").upper(),
                    "message": f"Leave request for {leave_date} submitted successfully (ID: {res['id']})."
                }
            if not res.get("network_failure"):
                return {"success": False, "error": res.get("error", "Submission failed")}

        # Fallback
        req_id = f"REQ-{abs(hash(idempotency_key)) % 10000:04d}"
        new_req = {
            "id": req_id,
            "student_id": account_id,
            "student_name": "Arjun K",
            "type": "LEAVE",
            "date": leave_date,
            "reason": reason,
            "status": "PENDING"
        }
        MOCK_KIT_DB["pending_requests"].append(new_req)
        return {
            "success": True,
            "request_id": req_id,
            "status": "PENDING",
            "message": f"Leave request for {leave_date} submitted successfully."
        }

    def submit_od_request(
        self,
        account_id: str,
        od_date: str,
        event_name: str,
        idempotency_key: str,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submits On-Duty request to KIT backend."""
        if self._should_use_real_api() and token:
            payload = {
                "type": "on_duty",
                "from_date": od_date,
                "to_date": od_date,
                "half_day": False,
                "reason": event_name,
                "event_name": event_name
            }
            res = self._http_request("POST", "/v1/me/requests", token=token, data=payload, idempotency_key=idempotency_key)
            if "id" in res:
                return {
                    "success": True,
                    "request_id": str(res["id"]),
                    "status": res.get("status", "pending").upper(),
                    "message": f"On-Duty request for {od_date} ({event_name}) submitted successfully (ID: {res['id']})."
                }
            if not res.get("network_failure"):
                return {"success": False, "error": res.get("error", "Submission failed")}

        req_id = f"REQ-{abs(hash(idempotency_key)) % 10000:04d}"
        new_req = {
            "id": req_id,
            "student_id": account_id,
            "student_name": "Arjun K",
            "type": "ON_DUTY",
            "date": od_date,
            "reason": event_name,
            "status": "PENDING"
        }
        MOCK_KIT_DB["pending_requests"].append(new_req)
        return {
            "success": True,
            "request_id": req_id,
            "status": "PENDING",
            "message": f"On-Duty request for {od_date} ({event_name}) submitted successfully."
        }

    def list_pending_teacher_requests(self, account_id: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns pending requests awaiting teacher review."""
        if self._should_use_real_api() and token:
            res = self._http_request("GET", "/v1/teacher/requests", token=token)
            if isinstance(res, list):
                return [
                    {
                        "id": str(r.get("id")),
                        "student_name": r.get("student_name", "Student"),
                        "type": r.get("type", "").upper(),
                        "date": r.get("from_date"),
                        "reason": r.get("reason", ""),
                        "status": r.get("status", "PENDING").upper()
                    } for r in res if str(r.get("status", "")).lower() in ["pending", "submitted"]
                ]
        return [r for r in MOCK_KIT_DB["pending_requests"] if r["status"] == "PENDING"]

    def review_request(
        self,
        account_id: str,
        request_id: str,
        action: str,
        token: Optional[str] = None,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Approves or rejects a student request."""
        clean_id = request_id.replace("REQ-", "").strip()
        if self._should_use_real_api() and token:
            if action == "APPROVE":
                res = self._http_request(
                    "POST",
                    f"/v1/teacher/requests/{clean_id}/approve",
                    token=token,
                    data={"comment": "Approved by advisor"},
                    idempotency_key=idempotency_key
                )
                if not res.get("error"):
                    return {"success": True, "request_id": request_id, "status": "APPROVED", "message": f"Request {request_id} approved."}
            elif action == "REJECT":
                res = self._http_request(
                    "POST",
                    f"/v1/teacher/requests/{clean_id}/reject",
                    token=token,
                    data={"reason": reason or "Rejected by teacher"},
                    idempotency_key=idempotency_key
                )
                if not res.get("error"):
                    return {"success": True, "request_id": request_id, "status": "REJECTED", "message": f"Request {request_id} rejected."}

        # Fallback
        target = None
        for r in MOCK_KIT_DB["pending_requests"]:
            if r["id"].upper() == request_id.upper() or r["id"].upper() == clean_id.upper():
                target = r
                break
        if not target:
            return {"success": False, "error": f"request_{request_id}_not_found"}

        if action == "APPROVE":
            target["status"] = "APPROVED"
            return {"success": True, "request_id": target["id"], "status": "APPROVED", "message": f"Request {request_id} approved."}
        else:
            target["status"] = "REJECTED"
            return {"success": True, "request_id": target["id"], "status": "REJECTED", "message": f"Request {request_id} rejected."}

    def get_college_info(self) -> Dict[str, Any]:
        """Returns official college info."""
        if self._should_use_real_api():
            res = self._http_request("GET", "/v1/college")
            if "name" in res:
                contact = res.get("contact", {})
                return {
                    "name": res.get("name"),
                    "motto": res.get("tagline", "Excellence in Engineering"),
                    "location": contact.get("address", "Coimbatore, Tamil Nadu"),
                    "accreditation": res.get("description", "Autonomous Premier Institution"),
                    "helpline": contact.get("phone", "+91 422 2619000"),
                    "email": contact.get("email", "admissions@kit.ac.in")
                }
        return MOCK_KIT_DB["college_info"]

    def get_courses(self) -> List[Dict[str, Any]]:
        """Returns programs and courses list."""
        if self._should_use_real_api():
            res = self._http_request("GET", "/v1/courses")
            if isinstance(res, list) and res:
                return [
                    {
                        "code": c.get("code", c.get("name", "COURSE")),
                        "title": c.get("name", "Degree Course"),
                        "duration": f"{c.get('duration_years', 4)} Years",
                        # No "/year" suffix here: agents/admissions.py appends it,
                        # and a suffix here produced spoken text like "Rs. 180000/year/year".
                        "annual_fee": f"Rs. {c.get('fee_per_year', 180000)}",
                        "seats": c.get("intake", 120),
                        "eligibility": "10+2 with PCM aggregate"
                    } for c in res
                ]
        return MOCK_KIT_DB["courses"]

    def get_placement_drives(self) -> List[Dict[str, Any]]:
        """Returns upcoming placement drives (public endpoint, key-only auth)."""
        if self._should_use_real_api():
            res = self._http_request("GET", "/v1/placements/drives")
            if isinstance(res, list) and res:
                return [
                    {
                        "company": d.get("company"),
                        "category": d.get("category"),
                        "min_cgpa": d.get("min_cgpa"),
                        "departments": d.get("allowed_departments", []),
                        "eligible_years": d.get("eligible_years", []),
                        "deadline": d.get("deadline"),
                        "seats_total": d.get("seats_total"),
                        "seats_left": d.get("seats_left")
                    } for d in res
                ]
        return MOCK_KIT_DB["placement_drives"]

    def get_today(self) -> Dict[str, Any]:
        """Returns the campus current date/weekday info."""
        if self._should_use_real_api():
            res = self._http_request("GET", "/v1/today")
            if isinstance(res, dict) and "date" in res:
                return res
        return MOCK_KIT_DB["today"]

kit_client = KitApiClient()
