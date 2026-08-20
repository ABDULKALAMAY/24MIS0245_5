"""
Hospital ICU Resource Allocation System
Allocates ICU beds based on patient severity and priority scoring
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import json


@dataclass
class Patient:
    """Represents a patient for ICU allocation"""
    patient_id: str
    age: int
    oxygen_level: float
    heart_rate: int
    blood_pressure: str  # Format: "systolic/diastolic"
    temperature: float
    medical_conditions: List[str]
    is_emergency: bool = False
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ICUAllocationSystem:
    """System to manage ICU bed allocation based on patient priority"""

    def __init__(self, total_beds: int = 10):
        """
        Initialize the ICU allocation system
        
        Args:
            total_beds: Total number of ICU beds available
        """
        self.total_beds = total_beds
        self.allocated_patients: List[Patient] = []
        self.waiting_list: List[Patient] = []
        self.processed_ids: set = set()

    def validate_patient_data(self, patient: Patient) -> tuple[bool, str]:
        """
        Validate patient data for correctness
        
        Args:
            patient: Patient object to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for duplicate patient ID
        if patient.patient_id in self.processed_ids:
            return False, f"DUPLICATE: Patient ID {patient.patient_id} already exists"

        # Validate oxygen level (should be 0-100%)
        if not (0 <= patient.oxygen_level <= 100):
            return False, f"INVALID_OXYGEN: Oxygen level {patient.oxygen_level}% must be between 0-100%"

        # Validate heart rate (0-250 bpm is reasonable range)
        if not (0 <= patient.heart_rate <= 250):
            return False, f"INVALID_HR: Heart rate {patient.heart_rate} bpm must be between 0-250"

        # Validate age (0-150 years)
        if not (0 <= patient.age <= 150):
            return False, f"INVALID_AGE: Age {patient.age} must be between 0-150"

        # Validate blood pressure format
        try:
            bp_parts = patient.blood_pressure.split('/')
            if len(bp_parts) != 2:
                return False, f"INVALID_BP: Blood pressure must be in format 'systolic/diastolic'"
            systolic, diastolic = int(bp_parts[0]), int(bp_parts[1])
            if not (0 <= systolic <= 300 and 0 <= diastolic <= 200):
                return False, f"INVALID_BP: Blood pressure values out of reasonable range"
        except (ValueError, IndexError):
            return False, f"INVALID_BP: Blood pressure format must be 'systolic/diastolic' (e.g., '120/80')"

        # Validate temperature (18-45 Celsius is reasonable range)
        if not (18 <= patient.temperature <= 45):
            return False, f"INVALID_TEMP: Temperature {patient.temperature}°C must be between 18-45°C"

        return True, "VALID"

    def calculate_priority_score(self, patient: Patient) -> float:
        """
        Calculate patient priority score based on medical parameters
        Higher score = higher priority for ICU bed
        
        Args:
            patient: Patient object
            
        Returns:
            Priority score (float)
        """
        score = 0.0

        # Emergency override: Highest priority
        if patient.is_emergency:
            score += 1000

        # Oxygen level scoring (most critical)
        if patient.oxygen_level < 90:
            score += 50  # Critical
        elif patient.oxygen_level < 94:
            score += 35  # High
        elif patient.oxygen_level < 98:
            score += 15  # Medium

        # Heart rate scoring
        if patient.heart_rate < 40 or patient.heart_rate > 140:
            score += 40  # Critical HR
        elif patient.heart_rate < 50 or patient.heart_rate > 120:
            score += 25  # High HR
        elif patient.heart_rate < 60 or patient.heart_rate > 100:
            score += 10  # Slightly abnormal

        # Blood pressure scoring
        try:
            systolic, diastolic = map(int, patient.blood_pressure.split('/'))
            
            # Critically high or low BP
            if systolic > 180 or systolic < 90 or diastolic > 120 or diastolic < 60:
                score += 30
            # Moderately abnormal BP
            elif systolic > 160 or systolic < 100 or diastolic > 100 or diastolic < 70:
                score += 15
        except (ValueError, IndexError):
            score += 5

        # Temperature scoring
        if patient.temperature < 35 or patient.temperature > 39:
            score += 20  # Critical temperature
        elif patient.temperature < 36.5 or patient.temperature > 38.5:
            score += 10  # Abnormal temperature

        # Age factor (elderly patients)
        if patient.age > 75:
            score += 15
        elif patient.age > 65:
            score += 8

        # Medical conditions scoring
        critical_conditions = ['sepsis', 'acute respiratory distress', 'myocardial infarction', 
                              'stroke', 'severe pneumonia', 'pulmonary embolism']
        serious_conditions = ['heart failure', 'pneumonia', 'asthma', 'diabetes', 'hypertension']

        for condition in patient.medical_conditions:
            condition_lower = condition.lower()
            if any(critical in condition_lower for critical in critical_conditions):
                score += 40
            elif any(serious in condition_lower for serious in serious_conditions):
                score += 15
            else:
                score += 5

        return score

    def classify_patient(self, priority_score: float) -> str:
        """
        Classify patient based on priority score
        
        Args:
            priority_score: Priority score calculated for the patient
            
        Returns:
            Classification: CRITICAL, HIGH, MEDIUM, or LOW
        """
        if priority_score >= 100:
            return "CRITICAL"
        elif priority_score >= 50:
            return "HIGH"
        elif priority_score >= 20:
            return "MEDIUM"
        else:
            return "LOW"

    def add_patient(self, patient: Patient) -> dict:
        """
        Add a patient to the ICU allocation system
        
        Args:
            patient: Patient object to add
            
        Returns:
            Dictionary with allocation result
        """
        # Validate patient data
        is_valid, message = self.validate_patient_data(patient)
        if not is_valid:
            return {
                "status": "REJECTED",
                "patient_id": patient.patient_id,
                "reason": message,
                "allocated_bed": None,
                "priority_score": 0,
                "classification": None
            }

        # Calculate priority and classify
        priority_score = self.calculate_priority_score(patient)
        classification = self.classify_patient(priority_score)

        self.processed_ids.add(patient.patient_id)

        # Check bed availability
        if len(self.allocated_patients) < self.total_beds:
            # Allocate bed
            allocated_bed = len(self.allocated_patients) + 1
            self.allocated_patients.append(patient)
            self.allocated_patients.sort(
                key=lambda p: self.calculate_priority_score(p),
                reverse=True
            )

            return {
                "status": "ALLOCATED",
                "patient_id": patient.patient_id,
                "allocated_bed": allocated_bed,
                "priority_score": priority_score,
                "classification": classification,
                "timestamp": patient.timestamp.isoformat()
            }
        else:
            # No beds available - add to waiting list
            self.waiting_list.append(patient)
            self.waiting_list.sort(
                key=lambda p: self.calculate_priority_score(p),
                reverse=True
            )

            return {
                "status": "WAITING",
                "patient_id": patient.patient_id,
                "waiting_position": len(self.waiting_list),
                "priority_score": priority_score,
                "classification": classification,
                "reason": "No ICU beds available",
                "timestamp": patient.timestamp.isoformat()
            }

    def deallocate_bed(self, patient_id: str) -> dict:
        """
        Deallocate a bed when patient leaves ICU
        
        Args:
            patient_id: ID of patient to discharge
            
        Returns:
            Result dictionary
        """
        # Remove from allocated patients
        for i, patient in enumerate(self.allocated_patients):
            if patient.patient_id == patient_id:
                self.allocated_patients.pop(i)
                
                # If there are patients waiting, allocate next priority patient
                if self.waiting_list:
                    next_patient = self.waiting_list.pop(0)
                    self.allocated_patients.append(next_patient)
                    self.allocated_patients.sort(
                        key=lambda p: self.calculate_priority_score(p),
                        reverse=True
                    )
                    return {
                        "status": "DEALLOCATED",
                        "discharged_patient_id": patient_id,
                        "new_allocation": next_patient.patient_id,
                        "new_patient_priority": self.classify_patient(
                            self.calculate_priority_score(next_patient)
                        )
                    }
                
                return {
                    "status": "DEALLOCATED",
                    "discharged_patient_id": patient_id,
                    "new_allocation": None
                }

        return {
            "status": "NOT_FOUND",
            "patient_id": patient_id,
            "error": "Patient not found in allocated beds"
        }

    def get_current_status(self) -> dict:
        """
        Get current ICU status
        
        Returns:
            Dictionary with current bed allocation status
        """
        return {
            "total_beds": self.total_beds,
            "allocated_beds": len(self.allocated_patients),
            "available_beds": self.total_beds - len(self.allocated_patients),
            "waiting_patients": len(self.waiting_list),
            "allocated_patients": [
                {
                    "patient_id": p.patient_id,
                    "age": p.age,
                    "classification": self.classify_patient(self.calculate_priority_score(p)),
                    "priority_score": self.calculate_priority_score(p)
                }
                for p in self.allocated_patients
            ],
            "waiting_list": [
                {
                    "patient_id": p.patient_id,
                    "age": p.age,
                    "classification": self.classify_patient(self.calculate_priority_score(p)),
                    "priority_score": self.calculate_priority_score(p),
                    "position": i + 1
                }
                for i, p in enumerate(self.waiting_list)
            ]
        }

    def get_allocation_report(self) -> str:
        """
        Generate a formatted allocation report
        
        Returns:
            Formatted string report
        """
        status = self.get_current_status()
        report = "\n" + "="*60 + "\n"
        report += "ICU ALLOCATION STATUS REPORT\n"
        report += "="*60 + "\n"
        report += f"Total Beds: {status['total_beds']}\n"
        report += f"Allocated: {status['allocated_beds']}\n"
        report += f"Available: {status['available_beds']}\n"
        report += f"Waiting: {status['waiting_patients']}\n"
        report += "-"*60 + "\n"

        if status['allocated_patients']:
            report += "ALLOCATED PATIENTS:\n"
            for patient in status['allocated_patients']:
                report += f"  ID: {patient['patient_id']}, Age: {patient['age']}, "
                report += f"Classification: {patient['classification']}, "
                report += f"Score: {patient['priority_score']:.1f}\n"
        
        if status['waiting_list']:
            report += "-"*60 + "\n"
            report += "WAITING LIST:\n"
            for patient in status['waiting_list']:
                report += f"  #{patient['position']}: ID: {patient['patient_id']}, Age: {patient['age']}, "
                report += f"Classification: {patient['classification']}, "
                report += f"Score: {patient['priority_score']:.1f}\n"

        report += "="*60 + "\n"
        return report
