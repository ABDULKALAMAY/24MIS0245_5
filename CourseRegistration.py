"""
University Course Registration and Timetable Conflict System
Manages student course registration with prerequisites, credit limits, and timetable conflict detection
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Set
from datetime import datetime, time
from enum import Enum
import json


class Semester(Enum):
    """Semester enumeration"""
    FALL = "Fall"
    SPRING = "Spring"
    SUMMER = "Summer"


class DayOfWeek(Enum):
    """Day of week enumeration"""
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"


@dataclass
class TimeSlot:
    """Represents a time slot for a course"""
    day: DayOfWeek
    start_time: str  # Format: "HH:MM"
    end_time: str    # Format: "HH:MM"

    def overlaps_with(self, other: 'TimeSlot') -> bool:
        """
        Check if this time slot overlaps with another
        
        Args:
            other: Another TimeSlot to check against
            
        Returns:
            True if time slots overlap, False otherwise
        """
        if self.day != other.day:
            return False
        
        # Convert time strings to comparable format
        self_start = self._time_to_minutes(self.start_time)
        self_end = self._time_to_minutes(self.end_time)
        other_start = self._time_to_minutes(other.start_time)
        other_end = self._time_to_minutes(other.end_time)
        
        # Check for overlap
        return not (self_end <= other_start or self_start >= other_end)

    @staticmethod
    def _time_to_minutes(time_str: str) -> int:
        """Convert HH:MM format to minutes since midnight"""
        parts = time_str.split(':')
        if len(parts) != 2:
            raise ValueError(f"Invalid time format: {time_str}")
        hours, minutes = int(parts[0]), int(parts[1])
        return hours * 60 + minutes


@dataclass
class Course:
    """Represents a course offered by the university"""
    course_code: str
    course_name: str
    credits: int
    capacity: int
    prerequisite: Optional[str] = None
    semester_offered: Semester = Semester.FALL
    time_slots: List[TimeSlot] = field(default_factory=list)
    current_enrollment: int = 0

    def is_full(self) -> bool:
        """Check if course is at capacity"""
        return self.current_enrollment >= self.capacity

    def has_capacity(self) -> bool:
        """Check if course has available seats"""
        return self.current_enrollment < self.capacity


@dataclass
class Student:
    """Represents a student"""
    student_id: str
    name: str
    program: str
    completed_courses: Set[str] = field(default_factory=set)
    registered_courses: Dict[str, Course] = field(default_factory=dict)
    current_semester: Semester = Semester.FALL
    max_credits: int = 18
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class CourseRegistrationSystem:
    """System to manage course registration with conflict detection"""

    def __init__(self):
        """Initialize the course registration system"""
        self.courses: Dict[str, Course] = {}
        self.students: Dict[str, Student] = {}
        self.processed_student_courses: Set[Tuple[str, str]] = set()

    def add_course(self, course: Course) -> dict:
        """
        Add a course to the system
        
        Args:
            course: Course object to add
            
        Returns:
            Dictionary with result
        """
        if course.course_code in self.courses:
            return {
                "status": "REJECTED",
                "course_code": course.course_code,
                "reason": f"Course {course.course_code} already exists"
            }

        self.courses[course.course_code] = course
        return {
            "status": "ADDED",
            "course_code": course.course_code,
            "course_name": course.course_name,
            "credits": course.credits,
            "capacity": course.capacity
        }

    def add_student(self, student: Student) -> dict:
        """
        Add a student to the system
        
        Args:
            student: Student object to add
            
        Returns:
            Dictionary with result
        """
        if student.student_id in self.students:
            return {
                "status": "REJECTED",
                "student_id": student.student_id,
                "reason": f"Student {student.student_id} already exists"
            }

        self.students[student.student_id] = student
        return {
            "status": "ADDED",
            "student_id": student.student_id,
            "name": student.name,
            "program": student.program
        }

    def validate_registration(self, student_id: str, course_code: str) -> Tuple[bool, str]:
        """
        Validate if a student can register for a course
        
        Args:
            student_id: Student ID
            course_code: Course code
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if student exists
        if student_id not in self.students:
            return False, f"STUDENT_NOT_FOUND: Student {student_id} not found"

        # Check if course exists
        if course_code not in self.courses:
            return False, f"COURSE_NOT_FOUND: Course {course_code} does not exist"

        student = self.students[student_id]
        course = self.courses[course_code]

        # Check for duplicate registration
        if course_code in student.registered_courses:
            return False, f"DUPLICATE: Student {student_id} already registered for {course_code}"

        # Check if registration pair has been processed
        if (student_id, course_code) in self.processed_student_courses:
            return False, f"ALREADY_PROCESSED: Registration for {student_id}-{course_code} already processed"

        # Check course capacity
        if course.is_full():
            return False, f"FULL_COURSE: Course {course_code} is at full capacity ({course.capacity})"

        # Check prerequisite
        if course.prerequisite and course.prerequisite not in student.completed_courses:
            return False, f"MISSING_PREREQUISITE: Course {course_code} requires {course.prerequisite}"

        # Check semester offering
        if course.semester_offered != student.current_semester:
            return False, f"SEMESTER_MISMATCH: Course {course_code} not offered in {student.current_semester.value}"

        return True, "VALID"

    def check_timetable_conflict(self, student_id: str, course_code: str) -> Tuple[bool, Optional[str]]:
        """
        Check for timetable conflicts between new course and registered courses
        
        Args:
            student_id: Student ID
            course_code: Course code
            
        Returns:
            Tuple of (has_conflict, conflicting_course_code)
        """
        if student_id not in self.students or course_code not in self.courses:
            return False, None

        student = self.students[student_id]
        new_course = self.courses[course_code]

        # Check against all registered courses
        for registered_code, registered_course in student.registered_courses.items():
            # Check each time slot combination
            for new_slot in new_course.time_slots:
                for registered_slot in registered_course.time_slots:
                    if new_slot.overlaps_with(registered_slot):
                        return True, registered_code

        return False, None

    def check_credit_limit(self, student_id: str, course_code: str) -> Tuple[bool, str]:
        """
        Check if adding course exceeds credit limit
        
        Args:
            student_id: Student ID
            course_code: Course code
            
        Returns:
            Tuple of (within_limit, message)
        """
        if student_id not in self.students or course_code not in self.courses:
            return False, "Invalid student or course"

        student = self.students[student_id]
        course = self.courses[course_code]

        # Calculate current credits
        current_credits = sum(c.credits for c in student.registered_courses.values())
        total_credits = current_credits + course.credits

        if total_credits > student.max_credits:
            return False, f"CREDIT_LIMIT_EXCEEDED: Total credits {total_credits} exceeds limit {student.max_credits}"

        return True, f"WITHIN_LIMIT: Current {current_credits} + {course.credits} = {total_credits} <= {student.max_credits}"

    def register_student(self, student_id: str, course_code: str) -> dict:
        """
        Register a student for a course
        
        Args:
            student_id: Student ID
            course_code: Course code
            
        Returns:
            Dictionary with registration result
        """
        # Validate basic registration
        is_valid, message = self.validate_registration(student_id, course_code)
        if not is_valid:
            return {
                "status": "REJECTED",
                "student_id": student_id,
                "course_code": course_code,
                "reason": message
            }

        student = self.students[student_id]
        course = self.courses[course_code]

        # Check timetable conflicts
        has_conflict, conflicting_course = self.check_timetable_conflict(student_id, course_code)
        if has_conflict:
            return {
                "status": "CONFLICT",
                "student_id": student_id,
                "course_code": course_code,
                "reason": f"TIMETABLE_CONFLICT: Conflicts with {conflicting_course}",
                "conflicting_course": conflicting_course
            }

        # Check credit limits
        within_limit, credit_message = self.check_credit_limit(student_id, course_code)
        if not within_limit:
            return {
                "status": "REJECTED",
                "student_id": student_id,
                "course_code": course_code,
                "reason": credit_message
            }

        # Register the student
        student.registered_courses[course_code] = course
        course.current_enrollment += 1
        self.processed_student_courses.add((student_id, course_code))

        # Calculate total credits
        total_credits = sum(c.credits for c in student.registered_courses.values())

        return {
            "status": "REGISTERED",
            "student_id": student_id,
            "course_code": course_code,
            "course_name": course.course_name,
            "credits": course.credits,
            "total_registered_credits": total_credits,
            "max_credits": student.max_credits,
            "timestamp": datetime.now().isoformat()
        }

    def deregister_student(self, student_id: str, course_code: str) -> dict:
        """
        Deregister a student from a course
        
        Args:
            student_id: Student ID
            course_code: Course code
            
        Returns:
            Dictionary with result
        """
        if student_id not in self.students:
            return {
                "status": "NOT_FOUND",
                "student_id": student_id,
                "error": "Student not found"
            }

        student = self.students[student_id]

        if course_code not in student.registered_courses:
            return {
                "status": "NOT_FOUND",
                "student_id": student_id,
                "course_code": course_code,
                "error": "Student not registered for this course"
            }

        # Remove from registered courses
        course = student.registered_courses.pop(course_code)
        course.current_enrollment -= 1
        self.processed_student_courses.discard((student_id, course_code))

        total_credits = sum(c.credits for c in student.registered_courses.values())

        return {
            "status": "DEREGISTERED",
            "student_id": student_id,
            "course_code": course_code,
            "course_name": course.course_name,
            "credits": course.credits,
            "total_remaining_credits": total_credits
        }

    def get_student_schedule(self, student_id: str) -> dict:
        """
        Get student's registered courses and schedule
        
        Args:
            student_id: Student ID
            
        Returns:
            Dictionary with schedule information
        """
        if student_id not in self.students:
            return {
                "status": "NOT_FOUND",
                "student_id": student_id
            }

        student = self.students[student_id]
        total_credits = sum(c.credits for c in student.registered_courses.values())

        registered = []
        for course_code, course in student.registered_courses.items():
            time_slots = [
                {
                    "day": slot.day.value,
                    "start_time": slot.start_time,
                    "end_time": slot.end_time
                }
                for slot in course.time_slots
            ]
            registered.append({
                "course_code": course_code,
                "course_name": course.course_name,
                "credits": course.credits,
                "time_slots": time_slots
            })

        return {
            "status": "SUCCESS",
            "student_id": student_id,
            "name": student.name,
            "program": student.program,
            "semester": student.current_semester.value,
            "registered_courses": registered,
            "total_credits": total_credits,
            "max_credits": student.max_credits,
            "remaining_credit_slots": student.max_credits - total_credits
        }

    def get_course_details(self, course_code: str) -> dict:
        """
        Get details of a course
        
        Args:
            course_code: Course code
            
        Returns:
            Dictionary with course details
        """
        if course_code not in self.courses:
            return {
                "status": "NOT_FOUND",
                "course_code": course_code
            }

        course = self.courses[course_code]
        time_slots = [
            {
                "day": slot.day.value,
                "start_time": slot.start_time,
                "end_time": slot.end_time
            }
            for slot in course.time_slots
        ]

        return {
            "status": "SUCCESS",
            "course_code": course.course_code,
            "course_name": course.course_name,
            "credits": course.credits,
            "capacity": course.capacity,
            "current_enrollment": course.current_enrollment,
            "available_seats": course.capacity - course.current_enrollment,
            "prerequisite": course.prerequisite,
            "semester_offered": course.semester_offered.value,
            "time_slots": time_slots
        }

    def get_registration_report(self) -> str:
        """
        Generate a registration report
        
        Returns:
            Formatted string report
        """
        report = "\n" + "="*70 + "\n"
        report += "COURSE REGISTRATION REPORT\n"
        report += "="*70 + "\n"
        report += f"Total Students: {len(self.students)}\n"
        report += f"Total Courses: {len(self.courses)}\n"
        report += f"Total Registrations: {len(self.processed_student_courses)}\n"
        report += "-"*70 + "\n"

        # Course enrollment summary
        if self.courses:
            report += "COURSE ENROLLMENT STATUS:\n"
            for course_code in sorted(self.courses.keys()):
                course = self.courses[course_code]
                report += f"  {course_code} ({course.course_name}): "
                report += f"{course.current_enrollment}/{course.capacity} enrolled, "
                report += f"{course.credits} credits\n"

        report += "-"*70 + "\n"

        # Student registration summary
        if self.students:
            report += "STUDENT REGISTRATION STATUS:\n"
            for student_id in sorted(self.students.keys()):
                student = self.students[student_id]
                total_credits = sum(c.credits for c in student.registered_courses.values())
                report += f"  {student_id} ({student.name}): {len(student.registered_courses)} courses, "
                report += f"{total_credits}/{student.max_credits} credits\n"

        report += "="*70 + "\n"
        return report
