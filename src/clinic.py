
from appointment import Appointment, AppointmentStatus


# INVARIANTS:
# 1. Appointment IDs must be unique within the Clinic.
# 2. Person IDs must be unique across different people.
# 3. The internal appointment list must never be exposed directly.
# 4. Patients cannot have two non-cancelled appointments
#    at the same hour.
# 5. Staff appointments must respect their buffer hours.
# 6. Confirmed appointments must never be bumped.
# 7. Waiting-list offers must satisfy all booking rules.
# 8. Every Clinic operation must be logged.


class Clinic:

    def __init__(self, log_file="appointment.log"):
        self.__appointments = []
        self.__waiting_lists = {}
        self.__registered_people = {}
        self.__log_file = log_file
        self.__log = None

    # Logging context manager

    def __enter__(self):
        if self.__log is not None:
            raise RuntimeError("Log is already open.")

        self.__log = open(
            self.__log_file,
            "a",
            encoding="utf-8"
        )

        try:
            print("[log] opened")
            self.__write_log("[log] opened")
        except Exception:
            self.__log.close()
            self.__log = None
            print("[log] closed")
            raise

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.__log is not None:
            try:
                self.__write_log("[log] closed")
            finally:
                self.__log.close()
                self.__log = None
                print("[log] closed")

        return False

    def __write_log(self, message):
        if self.__log is None:
            raise RuntimeError("Clinic log is not open.")

        self.__log.write(message + "\n")
        self.__log.flush()

    def __try_log_failure(self, message):
        # Best effort: the log itself may have failed.
        try:
            self.__write_log(message)
        except OSError:
            pass

    # Reading appointments safely

    def get_appointments(self):
        return self.__appointments.copy()

    def find_appointment(self, appointment_id):
        for appointment in self.__appointments:
            if appointment.appointment_id == appointment_id:
                return appointment

        return None

    # ID management

    def __check_person_id(self, person):
        person_id = person.person_id

    # Check whether this ID is already used by an appointment
        for appointment in self.__appointments:
            if appointment.appointment_id == person_id:
                raise ValueError("Person ID is already used by an appointment.")

    # Check whether this ID belongs to another registered person
        existing = self.__registered_people.get(person_id)

        if existing is not None and existing is not person:
            raise ValueError("Person ID already belongs to someone else.")

    def __register_person(self, person):
        self.__registered_people[person.person_id] = person

    def __check_appointment_id(self, appointment_id):
        if appointment_id <= 0:
            raise ValueError("Appointment ID must be positive.")

        if self.find_appointment(appointment_id) is not None:
            raise ValueError("Appointment ID already exists.")

        if appointment_id in self.__registered_people:
            raise ValueError("ID is already used by a person.")

    def __next_appointment_id(self):
        used_ids = set(self.__registered_people.keys())

        for appointment in self.__appointments:
            used_ids.add(appointment.appointment_id)

        candidate = 1

        while candidate in used_ids:
            candidate += 1

        return candidate

    # Booking conflict checks

    def __patient_has_conflict(self, patient, hour):
        for appointment in self.__appointments:
            if appointment.status == AppointmentStatus.CANCELLED:
                continue

            if (
                appointment.patient is patient
                and appointment.start_hour == hour
            ):
                return True

        return False

    def __staff_conflicts(self, staff, hour):
        conflicts = []

        minimum_difference = 1 + staff.buffer_hours()

        for appointment in self.__appointments:
            if appointment.status == AppointmentStatus.CANCELLED:
                continue

            if appointment.staff is staff:
                difference = abs(appointment.start_hour - hour)

                if difference < minimum_difference:
                    conflicts.append(appointment)

        return conflicts

    def __check_booking_conflicts(self, patient, staff, hour):
        if self.__patient_has_conflict(patient, hour):
            return True

        if self.__staff_conflicts(staff, hour):
            return True

        return False

    # Adding appointments

    def add_appointment(self, appointment):
        try:
            self.__check_appointment_id(appointment.appointment_id)

            self.__check_person_id(appointment.patient)
            self.__check_person_id(appointment.staff)

            if self.__check_booking_conflicts(
                appointment.patient,
                appointment.staff,
                appointment.start_hour
            ):
                raise ValueError("Booking conflict detected.")

            self.__register_person(appointment.patient)
            self.__register_person(appointment.staff)

            self.__appointments.append(appointment)

            self.__write_log(
                f"BOOKED appointment #{appointment.appointment_id}"
            )

        except Exception as error:
            self.__try_log_failure(
                f"FAILED add #{appointment.appointment_id}: {error}"
            )
            raise

    # Question 6: Emergency booking

    def book(
        self,
        appointment_id,
        patient,
        staff,
        start_hour,
        clock,
        emergency=False
    ):
        try:
            self.__check_appointment_id(appointment_id)
            self.__check_person_id(patient)
            self.__check_person_id(staff)

            if self.__patient_has_conflict(patient, start_hour):
                raise ValueError("Patient already has an appointment.")

            staff_conflicts = self.__staff_conflicts(staff, start_hour)

            if staff_conflicts and emergency:
                bump_candidate = None

                for existing in staff_conflicts:
                    if (
                        existing.start_hour == start_hour
                        and existing.status == AppointmentStatus.PENDING
                    ):
                        bump_candidate = existing
                        break

                if bump_candidate is not None:
                    bump_candidate.cancel(clock, reason="bumped")

                    self.__write_log(
                        f"BUMPED appointment #{bump_candidate.appointment_id}"
                    )

                    staff_conflicts = self.__staff_conflicts(
                        staff, start_hour
                    )

            if staff_conflicts:
                raise ValueError(
                    "Staff member is not available at that hour."
                )

            appointment = Appointment(
                appointment_id,
                patient,
                staff,
                start_hour
            )

            self.__register_person(patient)
            self.__register_person(staff)
            self.__appointments.append(appointment)

            self.__write_log(
                f"BOOKED appointment #{appointment_id}"
            )

            if emergency:
                self.__write_log(
                    f"EMERGENCY booking #{appointment_id}"
                )

            return appointment

        except Exception as error:
            self.__try_log_failure(
                f"FAILED booking #{appointment_id}: {error}"
            )
            raise

    # Confirming appointments

    def confirm_appointment(self, appointment_id):
        try:
            appointment = self.find_appointment(appointment_id)

            if appointment is None:
                raise ValueError("Appointment not found.")

            appointment.confirm()

            self.__write_log(
                f"CONFIRMED appointment #{appointment_id}"
            )

        except Exception as error:
            self.__try_log_failure(
                f"FAILED confirm #{appointment_id}: {error}"
            )
            raise

    # Waiting lists

    def join_waiting_list(self, staff, patient):
        try:
            self.__check_person_id(staff)
            self.__check_person_id(patient)

            self.__register_person(staff)
            self.__register_person(patient)

            queue = self.__waiting_lists.setdefault(staff, [])

            queue.append(patient)

            self.__write_log(
                f"WAITING LIST: {patient.name} joined for {staff.name}"
            )

        except Exception as error:
            self.__try_log_failure(
                f"FAILED waiting list: {error}"
            )
            raise

    def __offer_waiting_patient(self, cancelled):
        queue = self.__waiting_lists.get(cancelled.staff, [])

        for patient in queue.copy():

            if self.__patient_has_conflict(
                patient,
                cancelled.start_hour
            ):
                continue

            if self.__staff_conflicts(
                cancelled.staff,
                cancelled.start_hour
            ):
                continue

            new_id = self.__next_appointment_id()

            appointment = Appointment(
                new_id,
                patient,
                cancelled.staff,
                cancelled.start_hour
            )

            self.__appointments.append(appointment)
            queue.remove(patient)

            self.__write_log(
                f"WAITING LIST OFFER: appointment #{new_id} "
                f"created for {patient.name}"
            )

            break

    # Cancelling appointments

    def cancel_appointment(self, appointment_id, clock):
        try:
            appointment = self.find_appointment(appointment_id)

            if appointment is None:
                raise ValueError("Appointment not found.")

            appointment.cancel(clock)

            self.__write_log(
                f"CANCELLED appointment #{appointment_id}"
            )

            self.__offer_waiting_patient(appointment)

        except Exception as error:
            self.__try_log_failure(
                f"FAILED cancel #{appointment_id}: {error}"
            )
            raise
