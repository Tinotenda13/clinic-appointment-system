
from person import (
    Doctor,
    Nurse,
    Pharmacist,
    StudentPatient,
    StaffMemberPatient,
    VisitorPatient,
    MedicalLecturer,
    Person
)

from clock import FakeClock
from clinic import Clinic


# Temporary assignment value.
P = 7

print("===== QUESTION 3: STAFF FEES =====")

staff_members = [
    Doctor("Dr Smith", 201),
    Nurse("Nurse Jane", 202),
    Pharmacist("Mr Brown", 203)
]

for staff in staff_members:
    print(staff.role(), "Fee:", staff.fee(P))


print("\n===== QUESTION 5: MULTIPLE INHERITANCE =====")

before = Person.initialization_count

medical_lecturer = MedicalLecturer(
    "Dr Jones",
    301,
    "Computer Science"
)

after = Person.initialization_count

print("Name:", medical_lecturer.name)
print("Module:", medical_lecturer.module_name)
print("Role:", medical_lecturer.role())
print("Person constructor calls:", after - before)
print("Medical lecturer fee:", medical_lecturer.fee(P))


print("\n===== QUESTION 6: DISCOUNTS =====")

doctor = staff_members[0]

patients = [
    StudentPatient("Student One", 101),
    StaffMemberPatient("Staff Patient", 102),
    VisitorPatient("Visitor One", 103)
]

for patient in patients:
    # Demonstrate the price calculation without booking.
    from appointment import Appointment

    example = Appointment(
        100 + patient.person_id,
        patient,
        doctor,
        30
    )

    print(
        patient.name,
        "Price:",
        example.calculate_price(P)
    )


print("\n===== QUESTION 4 AND 6: CLINIC =====")

clock = FakeClock(10)

patient = StudentPatient("Student Two", 104)
waiting_patient = VisitorPatient("Visitor Two", 105)

with Clinic() as clinic:

    appointment = clinic.book(
        1,
        patient,
        doctor,
        14,
        clock
    )

    clinic.confirm_appointment(1)

    clinic.join_waiting_list(doctor, waiting_patient)

    clinic.cancel_appointment(1, clock)

    print(
        "Original appointment status:",
        appointment.status.value
    )

    print("Appointments in Clinic:")

    for item in clinic.get_appointments():
        print(
            item.appointment_id,
            item.patient.name,
            item.status.value
        )
