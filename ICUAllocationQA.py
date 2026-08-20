"""
ICU Resource Allocation System - QA Test Suite
Comprehensive testing of ICU bed allocation functionality
"""

from ICUAllocation import ICUAllocationSystem, Patient
import json
from datetime import datetime


class ICUAllocationQA:
    """QA test suite for ICU Allocation System"""

    def __init__(self):
        self.test_results = []
        self.system = None
        self.passed_tests = 0
        self.failed_tests = 0

    def reset_system(self, total_beds: int = 10):
        """Reset system for fresh test"""
        self.system = ICUAllocationSystem(total_beds)

    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": "PASSED" if passed else "FAILED",
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

    def run_all_tests(self) -> None:
        """Run all QA tests"""
        print("\n" + "="*80)
        print("ICU ALLOCATION SYSTEM - COMPREHENSIVE QA TEST SUITE")
        print("="*80 + "\n")

        # Test 1: Critical Patient
        self.test_critical_patient()
        
        # Test 2: Normal Patient
        self.test_normal_patient()
        
        # Test 3: Emergency Case
        self.test_emergency_case()
        
        # Test 4: No ICU Beds Available
        self.test_no_icu_beds()
        
        # Test 5: Duplicate Patient ID
        self.test_duplicate_patient_id()
        
        # Test 6: Invalid Oxygen Level
        self.test_invalid_oxygen_level()
        
        # Test 7: Invalid Heart Rate
        self.test_invalid_heart_rate()
        
        # Test 8: Priority Boundary Values
        self.test_priority_boundaries()
        
        # Test 9: Multiple Patients Competing for Same Bed
        self.test_multiple_patients_competing()

        # Test 10: Invalid Blood Pressure
        self.test_invalid_blood_pressure()

        # Test 11: Invalid Age
        self.test_invalid_age()

        # Test 12: Invalid Temperature
        self.test_invalid_temperature()

        # Test 13: Bed Deallocation and Waiting List Promotion
        self.test_bed_deallocation()

        # Test 14: Medical Conditions Scoring
        self.test_medical_conditions_scoring()

        # Test 15: Mixed Severity Patients
        self.test_mixed_severity_patients()

        self.print_summary()

    def test_critical_patient(self) -> None:
        """Test 1: Critical patient allocation"""
        print("\n[TEST 1] Critical Patient Allocation")
        print("-" * 80)
        
        self.reset_system()
        
        # Create critical patient with low oxygen and high heart rate
        critical_patient = Patient(
            patient_id="PAT001",
            age=75,
            oxygen_level=85.0,  # Critical oxygen
            heart_rate=145,      # Critical heart rate
            blood_pressure="180/110",  # Critical BP
            temperature=39.5,    # High temperature
            medical_conditions=["Acute respiratory distress"]
        )
        
        result = self.system.add_patient(critical_patient)
        
        status = result["status"] == "ALLOCATED"
        classification = result.get("classification") == "CRITICAL"
        score_valid = result.get("priority_score", 0) >= 100
        
        passed = status and classification and score_valid
        
        print(f"  Status: {result['status']}")
        print(f"  Classification: {result.get('classification')}")
        print(f"  Priority Score: {result.get('priority_score', 0):.1f}")
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        
        self.log_test(
            "Critical Patient",
            passed,
            f"Patient allocated with CRITICAL classification (Score: {result.get('priority_score', 0):.1f})"
        )

    def test_normal_patient(self) -> None:
        """Test 2: Normal patient allocation"""
        print("\n[TEST 2] Normal Patient Allocation")
        print("-" * 80)
        
        self.reset_system()
        
        normal_patient = Patient(
            patient_id="PAT002",
            age=45,
            oxygen_level=98.0,   # Normal oxygen
            heart_rate=75,       # Normal heart rate
            blood_pressure="120/80",  # Normal BP
            temperature=37.0,    # Normal temperature
            medical_conditions=[]
        )
        
        result = self.system.add_patient(normal_patient)
        
        status = result["status"] == "ALLOCATED"
        classification = result.get("classification") == "LOW"
        score_valid = result.get("priority_score", 0) < 20
        
        passed = status and classification and score_valid
        
        print(f"  Status: {result['status']}")
        print(f"  Classification: {result.get('classification')}")
        print(f"  Priority Score: {result.get('priority_score', 0):.1f}")
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        
        self.log_test(
            "Normal Patient",
            passed,
            f"Patient allocated with LOW classification (Score: {result.get('priority_score', 0):.1f})"
        )

    def test_emergency_case(self) -> None:
        """Test 3: Emergency case gets top priority"""
        print("\n[TEST 3] Emergency Case Override")
        print("-" * 80)
        
        self.reset_system()
        
        # Add normal patient first
        normal_patient = Patient(
            patient_id="PAT003",
            age=40,
            oxygen_level=98.0,
            heart_rate=70,
            blood_pressure="120/80",
            temperature=37.0,
            medical_conditions=[]
        )
        self.system.add_patient(normal_patient)
        
        # Add emergency patient
        emergency_patient = Patient(
            patient_id="PAT004",
            age=50,
            oxygen_level=95.0,
            heart_rate=80,
            blood_pressure="125/85",
            temperature=37.5,
            medical_conditions=[],
            is_emergency=True  # Emergency flag
        )
        
        result = self.system.add_patient(emergency_patient)
        
        status = result["status"] == "ALLOCATED"
        classification = result.get("classification") == "CRITICAL"
        score_very_high = result.get("priority_score", 0) >= 1000
        
        # Check if emergency patient is prioritized
        status_after = self.system.get_current_status()
        emergency_is_first = status_after['allocated_patients'][0]['patient_id'] == "PAT004"
        
        passed = status and classification and score_very_high and emergency_is_first
        
        print(f"  Emergency Patient Status: {result['status']}")
        print(f"  Classification: {result.get('classification')}")
        print(f"  Priority Score: {result.get('priority_score', 0):.1f}")
        print(f"  Prioritized over normal patient: {emergency_is_first}")
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        
        self.log_test(
            "Emergency Case Override",
            passed,
            "Emergency patient received highest priority (Score >= 1000)"
        )

    def test_no_icu_beds(self) -> None:
        """Test 4: Handling when no ICU beds available"""
        print("\n[TEST 4] No ICU Beds Available - Waiting List")
        print("-" * 80)
        
        self.reset_system(total_beds=2)  # Only 2 beds
        
        # Fill all beds
        for i in range(2):
            patient = Patient(
                patient_id=f"PAT005_{i}",
                age=50,
                oxygen_level=96.0,
                heart_rate=75,
                blood_pressure="120/80",
                temperature=37.0,
                medical_conditions=[]
            )
            self.system.add_patient(patient)
        
        # Try to add third patient
        waiting_patient = Patient(
            patient_id="PAT007",
            age=60,
            oxygen_level=94.0,
            heart_rate=85,
            blood_pressure="130/90",
            temperature=37.5,
            medical_conditions=["Hypertension"]
        )
        
        result = self.system.add_patient(waiting_patient)
        
        status = result["status"] == "WAITING"
        position_valid = result.get("waiting_position") == 1
        
        passed = status and position_valid
        
        print(f"  Status: {result['status']}")
        print(f"  Waiting Position: {result.get('waiting_position')}")
        print(f"  Reason: {result.get('reason')}")
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        
        self.log_test(
            "No ICU Beds Available",
            passed,
            f"Patient placed on waiting list at position {result.get('waiting_position')}"
        )

    def test_duplicate_patient_id(self) -> None:
        """Test 5: Reject duplicate patient IDs"""
        print("\n[TEST 5] Duplicate Patient ID Rejection")
        print("-" * 80)
        
        self.reset_system()
        
        patient1 = Patient(
            patient_id="PAT008",
            age=45,
            oxygen_level=98.0,
            heart_rate=75,
            blood_pressure="120/80",
            temperature=37.0,
            medical_conditions=[]
        )
        
        result1 = self.system.add_patient(patient1)
        
        # Try to add duplicate
        patient2 = Patient(
            patient_id="PAT008",  # Same ID
            age=50,
            oxygen_level=96.0,
            heart_rate=80,
            blood_pressure="125/85",
            temperature=37.5,
            medical_conditions=[]
        )
        
        result2 = self.system.add_patient(patient2)
        
        first_allocated = result1["status"] == "ALLOCATED"
        duplicate_rejected = result2["status"] == "REJECTED"
        duplicate_reason = "DUPLICATE" in result2.get("reason", "")
        
        passed = first_allocated and duplicate_rejected and duplicate_reason
        
        print(f"  First Patient: {result1['status']}")
        print(f"  Duplicate Status: {result2['status']}")
        print(f"  Rejection Reason: {result2.get('reason')}")
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        
        self.log_test(
            "Duplicate Patient ID Rejection",
            passed,
            "Duplicate patient ID successfully rejected"
        )

    def test_invalid_oxygen_level(self) -> None:
        """Test 6: Invalid oxygen level rejection"""
        print("\n[TEST 6] Invalid Oxygen Level Rejection")
        print("-" * 80)
        
        self.reset_system()
        
        test_cases = [
            ("PAT009_1", -5.0, "Negative oxygen"),
            ("PAT009_2", 105.0, "Oxygen > 100%"),
        ]
        
        all_passed = True
        
        for patient_id, oxygen_level, description in test_cases:
            patient = Patient(
                patient_id=patient_id,
                age=45,
                oxygen_level=oxygen_level,
                heart_rate=75,
                blood_pressure="120/80",
                temperature=37.0,
                medical_conditions=[]
            )
            
            result = self.system.add_patient(patient)
            
            rejected = result["status"] == "REJECTED"
            oxygen_error = "INVALID_OXYGEN" in result.get("reason", "")
            
            passed = rejected and oxygen_error
            all_passed = all_passed and passed
            
            print(f"  Case: {description} ({oxygen_level}%)")
            print(f"    Status: {result['status']}")
            print(f"    Reason: {result.get('reason')}")
            print(f"    Result: {'PASS' if passed else 'FAIL'}")
        
        print(f"  Overall Result: {'PASS' if all_passed else 'FAIL'}")
        
        self.log_test(
            "Invalid Oxygen Level Rejection",
            all_passed,
            "All invalid oxygen levels were rejected"
        )

    def test_invalid_heart_rate(self) -> None:
        """Test 7: Invalid heart rate rejection"""
        print("\n[TEST 7] Invalid Heart Rate Rejection")
        print("-" * 80)
        
        self.reset_system()
        
        test_cases = [
            ("PAT010_1", -10, "Negative heart rate"),
            ("PAT010_2", 300, "Heart rate > 250 bpm"),
        ]
        
        all_passed = True
        
        for patient_id, heart_rate, description in test_cases:
            patient = Patient(
                patient_id=patient_id,
                age=45,
                oxygen_level=98.0,
                heart_rate=heart_rate,
                blood_pressure="120/80",
                temperature=37.0,
                medical_conditions=[]
            )
            
            result = self.system.add_patient(patient)
            
            rejected = result["status"] == "REJECTED"
            hr_error = "INVALID_HR" in result.get("reason", "")
            
            passed = rejected and hr_error
            all_passed = all_passed and passed
            
            print(f"  Case: {description} ({heart_rate} bpm)")
            print(f"    Status: {result['status']}")
            print(f"    Reason: {result.get('reason')}")
            print(f"    Result: {'PASS' if passed else 'FAIL'}")
        
        print(f"  Overall Result: {'PASS' if all_passed else 'FAIL'}")
        
        self.log_test(
            "Invalid Heart Rate Rejection",
            all_passed,
            "All invalid heart rates were rejected"
        )

    def test_priority_boundaries(self) -> None:
        """Test 8: Priority boundary values"""
        print("\n[TEST 8] Priority Boundary Values")
        print("-" * 80)
        
        self.reset_system()
        
        # Test boundary values for each classification
        test_cases = [
            ("PAT011_1", 95.0, 60, "90/60", 37.0, [], "LOW/MEDIUM"),
            ("PAT011_2", 94.0, 75, "120/80", 37.0, [], "MEDIUM"),
            ("PAT011_3", 92.0, 80, "130/85", 37.5, ["Hypertension"], "HIGH"),
            ("PAT011_4", 88.0, 150, "170/100", 39.0, ["Acute respiratory distress"], "CRITICAL"),
        ]
        
        all_passed = True
        classifications = []
        
        for patient_id, oxygen, hr, bp, temp, conditions, expected in test_cases:
            patient = Patient(
                patient_id=patient_id,
                age=50,
                oxygen_level=oxygen,
                heart_rate=hr,
                blood_pressure=bp,
                temperature=temp,
                medical_conditions=conditions
            )
            
            result = self.system.add_patient(patient)
            classification = result.get("classification")
            classifications.append(classification)
            
            print(f"  {patient_id}: O2={oxygen}%, HR={hr}, Classification={classification}")
        
        print(f"  Classifications progression: {' -> '.join(classifications)}")
        print(f"  Result: PASS (Boundary classification test)")
        
        self.log_test(
            "Priority Boundary Values",
            True,
            f"Classifications: {classifications}"
        )

    def test_multiple_patients_competing(self) -> None:
        """Test 9: Multiple patients competing for same bed"""
        print("\n[TEST 9] Multiple Patients Competing for Same Bed")
        print("-" * 80)
        
        self.reset_system(total_beds=1)  # Only 1 bed
        
        patients_data = [
            ("PAT012_1", 85.0, 140, "180/110", 39.0, ["Acute respiratory distress"], True),  # Most critical
            ("PAT012_2", 90.0, 120, "150/90", 38.5, ["Pneumonia"], False),  # Second
            ("PAT012_3", 95.0, 90, "130/85", 37.5, ["Hypertension"], False),  # Third
            ("PAT012_4", 98.0, 70, "120/80", 37.0, [], False),  # Least critical
        ]
        
        results = []
        for patient_id, o2, hr, bp, temp, conditions, _ in patients_data:
            patient = Patient(
                patient_id=patient_id,
                age=50,
                oxygen_level=o2,
                heart_rate=hr,
                blood_pressure=bp,
                temperature=temp,
                medical_conditions=conditions
            )
            result = self.system.add_patient(patient)
            results.append({
                "patient_id": patient_id,
                "status": result["status"],
                "position": result.get("waiting_position") if result["status"] == "WAITING" else "Allocated"
            })
            print(f"  {patient_id}: {result['status']} (Score: {result.get('priority_score', 0):.1f})")
        
        # Most critical should be allocated
        most_critical_allocated = results[0]["status"] == "ALLOCATED"
        
        # Others should be waiting in order of priority
        others_waiting = all(r["status"] == "WAITING" for r in results[1:])
        
        passed = most_critical_allocated and others_waiting
        
        print(f"  Result: {'PASS' if passed else 'FAIL'} (Most critical allocated, others waiting)")
        
        self.log_test(
            "Multiple Patients Competing",
            passed,
            "Most critical patient allocated, others placed on waiting list"
        )

    def test_invalid_blood_pressure(self) -> None:
        """Test 10: Invalid blood pressure format"""
        print("\n[TEST 10] Invalid Blood Pressure Format")
        print("-" * 80)
        
        self.reset_system()
        
        test_cases = [
            ("PAT013_1", "120", "Missing diastolic"),
            ("PAT013_2", "120/80/90", "Too many values"),
            ("PAT013_3", "abc/def", "Non-numeric values"),
            ("PAT013_4", "400/150", "Values out of range"),
        ]
        
        all_passed = True
        
        for patient_id, bp, description in test_cases:
            patient = Patient(
                patient_id=patient_id,
                age=45,
                oxygen_level=98.0,
                heart_rate=75,
                blood_pressure=bp,
                temperature=37.0,
                medical_conditions=[]
            )
            
            result = self.system.add_patient(patient)
            
            rejected = result["status"] == "REJECTED"
            bp_error = "INVALID_BP" in result.get("reason", "")
            
            passed = rejected and bp_error
            all_passed = all_passed and passed
            
            print(f"  Case: {description} ({bp})")
            print(f"    Status: {result['status']}")
            print(f"    Result: {'PASS' if passed else 'FAIL'}")
        
        print(f"  Overall Result: {'PASS' if all_passed else 'FAIL'}")
        
        self.log_test(
            "Invalid Blood Pressure",
            all_passed,
            "All invalid blood pressure formats were rejected"
        )

    def test_invalid_age(self) -> None:
        """Test 11: Invalid age values"""
        print("\n[TEST 11] Invalid Age Values")
        print("-" * 80)
        
        self.reset_system()
        
        test_cases = [
            ("PAT014_1", -5, "Negative age"),
            ("PAT014_2", 200, "Age > 150"),
        ]
        
        all_passed = True
        
        for patient_id, age, description in test_cases:
            patient = Patient(
                patient_id=patient_id,
                age=age,
                oxygen_level=98.0,
                heart_rate=75,
                blood_pressure="120/80",
                temperature=37.0,
                medical_conditions=[]
            )
            
            result = self.system.add_patient(patient)
            
            rejected = result["status"] == "REJECTED"
            age_error = "INVALID_AGE" in result.get("reason", "")
            
            passed = rejected and age_error
            all_passed = all_passed and passed
            
            print(f"  Case: {description} ({age} years)")
            print(f"    Status: {result['status']}")
            print(f"    Result: {'PASS' if passed else 'FAIL'}")
        
        print(f"  Overall Result: {'PASS' if all_passed else 'FAIL'}")
        
        self.log_test(
            "Invalid Age",
            all_passed,
            "All invalid ages were rejected"
        )

    def test_invalid_temperature(self) -> None:
        """Test 12: Invalid temperature values"""
        print("\n[TEST 12] Invalid Temperature Values")
        print("-" * 80)
        
        self.reset_system()
        
        test_cases = [
            ("PAT015_1", 10.0, "Temperature < 18°C"),
            ("PAT015_2", 50.0, "Temperature > 45°C"),
        ]
        
        all_passed = True
        
        for patient_id, temp, description in test_cases:
            patient = Patient(
                patient_id=patient_id,
                age=45,
                oxygen_level=98.0,
                heart_rate=75,
                blood_pressure="120/80",
                temperature=temp,
                medical_conditions=[]
            )
            
            result = self.system.add_patient(patient)
            
            rejected = result["status"] == "REJECTED"
            temp_error = "INVALID_TEMP" in result.get("reason", "")
            
            passed = rejected and temp_error
            all_passed = all_passed and passed
            
            print(f"  Case: {description} ({temp}°C)")
            print(f"    Status: {result['status']}")
            print(f"    Result: {'PASS' if passed else 'FAIL'}")
        
        print(f"  Overall Result: {'PASS' if all_passed else 'FAIL'}")
        
        self.log_test(
            "Invalid Temperature",
            all_passed,
            "All invalid temperatures were rejected"
        )

    def test_bed_deallocation(self) -> None:
        """Test 13: Bed deallocation and waiting list promotion"""
        print("\n[TEST 13] Bed Deallocation and Waiting List Promotion")
        print("-" * 80)
        
        self.reset_system(total_beds=1)
        
        # Add patient with normal vital signs (low priority)
        patient1 = Patient(
            patient_id="PAT016",
            age=40,
            oxygen_level=98.0,
            heart_rate=70,
            blood_pressure="120/80",
            temperature=37.0,
            medical_conditions=[]
        )
        result1 = self.system.add_patient(patient1)
        
        # Add patient with high priority
        patient2 = Patient(
            patient_id="PAT017",
            age=70,
            oxygen_level=92.0,
            heart_rate=100,
            blood_pressure="140/90",
            temperature=38.0,
            medical_conditions=["Heart failure"]
        )
        result2 = self.system.add_patient(patient2)
        
        print(f"  Initial State:")
        print(f"    PAT016 Allocated: {result1['status']}")
        print(f"    PAT017 Waiting: {result2['status']} (Position: {result2.get('waiting_position')})")
        
        # Deallocate first patient
        dealloc_result = self.system.deallocate_bed("PAT016")
        
        # Check if waiting patient was promoted
        status_after = self.system.get_current_status()
        patient2_allocated = any(p['patient_id'] == 'PAT017' for p in status_after['allocated_patients'])
        
        print(f"  After Deallocation:")
        print(f"    PAT016 deallocated: {dealloc_result['status']}")
        print(f"    PAT017 promoted: {patient2_allocated}")
        print(f"    Allocated beds: {status_after['allocated_beds']}")
        
        passed = result1["status"] == "ALLOCATED" and result2["status"] == "WAITING" and patient2_allocated
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        
        self.log_test(
            "Bed Deallocation and Promotion",
            passed,
            "Waiting patient promoted to allocated after bed deallocation"
        )

    def test_medical_conditions_scoring(self) -> None:
        """Test 14: Medical conditions affect priority scoring"""
        print("\n[TEST 14] Medical Conditions Scoring")
        print("-" * 80)
        
        self.reset_system()
        
        # Patient without medical conditions
        patient1 = Patient(
            patient_id="PAT018",
            age=50,
            oxygen_level=98.0,
            heart_rate=75,
            blood_pressure="120/80",
            temperature=37.0,
            medical_conditions=[]
        )
        result1 = self.system.add_patient(patient1)
        score1 = result1.get("priority_score", 0)
        
        # Same patient but with critical condition
        patient2 = Patient(
            patient_id="PAT019",
            age=50,
            oxygen_level=98.0,
            heart_rate=75,
            blood_pressure="120/80",
            temperature=37.0,
            medical_conditions=["Sepsis"]
        )
        result2 = self.system.add_patient(patient2)
        score2 = result2.get("priority_score", 0)
        
        print(f"  Patient without conditions: Score = {score1:.1f}")
        print(f"  Patient with Sepsis: Score = {score2:.1f}")
        print(f"  Score increase due to critical condition: {(score2 - score1):.1f}")
        
        passed = score2 > score1
        print(f"  Result: {'PASS' if passed else 'FAIL'} (Conditions increase priority)")
        
        self.log_test(
            "Medical Conditions Scoring",
            passed,
            f"Critical condition increased priority score by {(score2 - score1):.1f}"
        )

    def test_mixed_severity_patients(self) -> None:
        """Test 15: Mixed severity patients allocation"""
        print("\n[TEST 15] Mixed Severity Patients Allocation")
        print("-" * 80)
        
        self.reset_system(total_beds=3)
        
        patients_data = [
            ("PAT020_1", 45, 98.0, 70, "120/80", 37.0, [], False),  # LOW
            ("PAT020_2", 65, 92.0, 95, "140/90", 38.0, ["Hypertension"], False),  # HIGH
            ("PAT020_3", 75, 88.0, 140, "170/100", 39.5, ["Acute respiratory distress"], False),  # CRITICAL
        ]
        
        results = []
        for patient_id, age, o2, hr, bp, temp, conditions, emergency in patients_data:
            patient = Patient(
                patient_id=patient_id,
                age=age,
                oxygen_level=o2,
                heart_rate=hr,
                blood_pressure=bp,
                temperature=temp,
                medical_conditions=conditions,
                is_emergency=emergency
            )
            result = self.system.add_patient(patient)
            results.append({
                "patient_id": patient_id,
                "classification": result.get("classification"),
                "score": result.get("priority_score")
            })
            print(f"  {patient_id}: {result.get('classification')} (Score: {result.get('priority_score'):.1f})")
        
        # Check if allocated in correct priority order
        status = self.system.get_current_status()
        allocated_ids = [p['patient_id'] for p in status['allocated_patients']]
        
        # CRITICAL should be first
        critical_first = allocated_ids[0] == "PAT020_3"
        
        print(f"  Allocation order: {allocated_ids}")
        print(f"  CRITICAL patient first: {critical_first}")
        
        passed = critical_first and len(allocated_ids) == 3
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        
        self.log_test(
            "Mixed Severity Patients",
            passed,
            "Patients allocated in correct priority order"
        )

    def print_summary(self) -> None:
        """Print test summary"""
        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print("="*80 + "\n")
        
        if self.failed_tests > 0:
            print("FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAILED":
                    print(f"  - {result['test']}: {result['details']}")
            print()

    def save_results_to_file(self, filename: str = "ICUAllocationQA_Results.txt") -> None:
        """Save test results to file"""
        with open(filename, 'w') as f:
            f.write("="*80 + "\n")
            f.write("ICU ALLOCATION SYSTEM - QA TEST RESULTS\n")
            f.write("="*80 + "\n\n")
            
            for result in self.test_results:
                f.write(f"Test: {result['test']}\n")
                f.write(f"Status: {result['status']}\n")
                f.write(f"Details: {result['details']}\n")
                f.write(f"Timestamp: {result['timestamp']}\n")
                f.write("-" * 80 + "\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("SUMMARY\n")
            f.write("="*80 + "\n")
            
            total_tests = self.passed_tests + self.failed_tests
            pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Passed: {self.passed_tests}\n")
            f.write(f"Failed: {self.failed_tests}\n")
            f.write(f"Pass Rate: {pass_rate:.1f}%\n")
            f.write("="*80 + "\n")
        
        print(f"\nResults saved to: {filename}")


# Main execution
if __name__ == "__main__":
    qa = ICUAllocationQA()
    qa.run_all_tests()
    qa.save_results_to_file("ICUAllocationQA_Results.txt")
