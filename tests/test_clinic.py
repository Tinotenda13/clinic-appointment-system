
import os
import sys
import tempfile
import unittest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from person import (
    Person,
    Patient,
    StudentPatient,
    StaffMemberPatient,
    VisitorPatient,
    Doctor,
    Nurse,
    Pharmacist,
    MedicalLecturer
)

from appointment import Appointment, AppointmentStatus
from clock import FakeClock
from clinic import Clinic


class ClinicTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(
            self.temp_dir.name,
            "appointment.log"
        )

        self.patient = Patient("John", 101)
        self.doctor = Doctor("Dr Smith", 201)
        self.clock = FakeClock(10)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_empty_name_is_rejected(self):
        with self.assertRaises(ValueError):
            Patient("", 101)

    def test_non_positive_person_id_is_rejected(self):
        with self.assertRaises(ValueError):
            Patient("John", 0)

    def test_appointment_starts_pending(self):
        appointment = Appointment(
            1, self.patient, self.doctor, 14
        )

        self.assertEqual(
            appointment.status,
            AppointmentStatus.PENDING
        )

    def test_cancelled_appointment_cannot_be_confirmed(self):
        appointment = Appointment(
            1, self.patient, self.doctor, 14
        )

        appointment.cancel(self.clock)

        with self.assertRaises(ValueError):
            appointment.confirm()

    def test_confirmed_appointment_can_be_cancelled_two_hours_before(self):
        appointment = Appointment(
            1, self.patient, self.doctor, 14
        )

        appointment.confirm()
        self.clock.set_time(12)

        appointment.cancel(self.clock)

        self.assertEqual(
            appointment.status,
            AppointmentStatus.CANCELLED
        )

    def test_confirmed_appointment_cannot_be_cancelled_one_hour_before(self):
        appointment = Appointment(
            1, self.patient, self.doctor, 14
        )

        appointment.confirm()
        self.clock.set_time(13)

        with self.assertRaises(ValueError):
            appointment.cancel(self.clock)

    def test_appointment_cannot_be_cancelled_after_start(self):
        appointment = Appointment(
            1, self.patient, self.doctor, 14
        )

        self.clock.set_time(14)

        with self.assertRaises(ValueError):
            appointment.cancel(self.clock)

    def test_clinic_prevents_duplicate_appointment_ids(self):
        first = Appointment(
            1, self.patient, self.doctor, 14
        )

        second_patient = Patient("Mary", 102)

        second = Appointment(
            1, second_patient, self.doctor, 20
        )

        with Clinic(self.log_file) as clinic:
            clinic.add_appointment(first)

            with self.assertRaises(ValueError):
                clinic.add_appointment(second)

    def test_clinic_returns_a_copy_of_appointment_list(self):
        appointment = Appointment(
            1, self.patient, self.doctor, 14
        )

        with Clinic(self.log_file) as clinic:
            clinic.add_appointment(appointment)

            returned_list = clinic.get_appointments()
            returned_list.clear()

            self.assertEqual(len(clinic.get_appointments()), 1)

    def test_doctor_buffer_is_enforced(self):
        first_patient = Patient("John", 101)
        second_patient = Patient("Mary", 102)

        with Clinic(self.log_file) as clinic:
            clinic.book(
                1, first_patient, self.doctor, 10, self.clock
            )

            with self.assertRaises(ValueError):
                clinic.book(
                    2, second_patient, self.doctor, 12, self.clock
                )

    def test_pharmacist_has_no_extra_buffer(self):
        pharmacist = Pharmacist("Mr Brown", 203)
        first_patient = Patient("John", 101)
        second_patient = Patient("Mary", 102)

        with Clinic(self.log_file) as clinic:
            clinic.book(
                1, first_patient, pharmacist, 10, self.clock
            )

            clinic.book(
                2, second_patient, pharmacist, 11, self.clock
            )

            self.assertEqual(len(clinic.get_appointments()), 2)

    def test_emergency_can_bump_pending_appointment(self):
        original_patient = Patient("John", 101)
        emergency_patient = Patient("Mary", 102)

        with Clinic(self.log_file) as clinic:
            original = clinic.book(
                1, original_patient, self.doctor, 14, self.clock
            )

            emergency = clinic.book(
                2,
                emergency_patient,
                self.doctor,
                14,
                self.clock,
                emergency=True
            )

            self.assertEqual(
                original.status,
                AppointmentStatus.CANCELLED
            )

            self.assertEqual(
                original.cancellation_reason,
                "bumped"
            )

            self.assertEqual(
                emergency.status,
                AppointmentStatus.PENDING
            )

    def test_emergency_cannot_bump_confirmed_appointment(self):
        original_patient = Patient("John", 101)
        emergency_patient = Patient("Mary", 102)

        with Clinic(self.log_file) as clinic:
            original = clinic.book(
                1, original_patient, self.doctor, 14, self.clock
            )

            clinic.confirm_appointment(1)

            with self.assertRaises(ValueError):
                clinic.book(
                    2,
                    emergency_patient,
                    self.doctor,
                    14,
                    self.clock,
                    emergency=True
                )

            self.assertEqual(
                original.status,
                AppointmentStatus.CONFIRMED
            )

    def test_waiting_list_receives_cancelled_slot(self):
        waiting_patient = Patient("Mary", 102)

        with Clinic(self.log_file) as clinic:
            original = clinic.book(
                1, self.patient, self.doctor, 14, self.clock
            )

            clinic.join_waiting_list(
                self.doctor,
                waiting_patient
            )

            clinic.cancel_appointment(1, self.clock)

            appointments = clinic.get_appointments()

            self.assertEqual(len(appointments), 2)
            self.assertEqual(
                appointments[1].patient.name,
                "Mary"
            )
            self.assertEqual(
                appointments[1].status,
                AppointmentStatus.PENDING
            )

    def test_patient_discount_calculations(self):
        doctor = Doctor("Dr Smith", 201)

        student = StudentPatient("Student", 101)
        staff_patient = StaffMemberPatient("Staff", 102)
        visitor = VisitorPatient("Visitor", 103)

        student_appointment = Appointment(
            1, student, doctor, 14
        )

        staff_appointment = Appointment(
            2, staff_patient, doctor, 14
        )

        visitor_appointment = Appointment(
            3, visitor, doctor, 14
        )

        # P = 7 gives a doctor fee of 50.
        self.assertEqual(student_appointment.calculate_price(7), 25)
        self.assertEqual(staff_appointment.calculate_price(7), 0)
        self.assertEqual(visitor_appointment.calculate_price(7), 50)

    def test_medical_lecturer_initialises_person_once(self):
        before = Person.initialization_count

        medical_lecturer = MedicalLecturer(
            "Dr Jones", 301, "Computer Science"
        )

        after = Person.initialization_count

        self.assertEqual(after - before, 1)
        self.assertEqual(
            medical_lecturer.role(),
            "Doctor and Lecturer"
        )

    def test_log_records_open_and_close(self):
        with Clinic(self.log_file):
            pass

        with open(self.log_file, "r", encoding="utf-8") as file:
            contents = file.read()

        self.assertEqual(contents.count("[log] opened"), 1)
        self.assertEqual(contents.count("[log] closed"), 1)

    def test_failed_cancellation_is_logged(self):
        appointment = Appointment(
            1, self.patient, self.doctor, 14
        )

        appointment.confirm()
        self.clock.set_time(13)

        with Clinic(self.log_file) as clinic:
            clinic.add_appointment(appointment)

            with self.assertRaises(ValueError):
                clinic.cancel_appointment(1, self.clock)

        with open(self.log_file, "r", encoding="utf-8") as file:
            contents = file.read()

        self.assertIn("FAILED cancel #1", contents)


if __name__ == "__main__":
    unittest.main()
