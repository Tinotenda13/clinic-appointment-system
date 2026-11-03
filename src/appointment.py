
from enum import Enum


class AppointmentStatus(Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


# INVARIANTS:
# 1. Every appointment lasts exactly one hour.
# 2. The starting hour must be between 0 and 167.
# 3. Every appointment starts as PENDING.
# 4. A CANCELLED appointment can never become active again.
# 5. A CONFIRMED appointment cannot be cancelled less than
#    two hours before its starting time.
# 6. No appointment can be cancelled once it has started.
# 7. Appointment status can only change through valid methods.


class Appointment:

    def __init__(self, appointment_id, patient, staff, start_hour):
        if appointment_id <= 0:
            raise ValueError("Appointment ID must be positive.")

        if not isinstance(start_hour, int):
            raise ValueError("Starting hour must be a whole number.")

        if start_hour < 0 or start_hour >= 168:
            raise ValueError("Starting hour must be between 0 and 167.")

        self.__appointment_id = appointment_id
        self.__patient = patient
        self.__staff = staff
        self.__start_hour = start_hour
        self.__status = AppointmentStatus.PENDING
        self.__cancellation_reason = None

    @property
    def appointment_id(self):
        return self.__appointment_id

    @property
    def patient(self):
        return self.__patient

    @property
    def staff(self):
        return self.__staff

    @property
    def start_hour(self):
        return self.__start_hour

    @property
    def status(self):
        return self.__status

    @property
    def cancellation_reason(self):
        return self.__cancellation_reason

    def confirm(self):
        if self.__status != AppointmentStatus.PENDING:
            raise ValueError("Only pending appointments can be confirmed.")

        self.__status = AppointmentStatus.CONFIRMED

    def cancel(self, clock, reason="cancelled"):
        if self.__status == AppointmentStatus.CANCELLED:
            raise ValueError("Appointment is already cancelled.")

        current_time = clock.now()

        if current_time >= self.__start_hour:
            raise ValueError("Cannot cancel an appointment that has started.")

        if self.__status == AppointmentStatus.CONFIRMED:
            if self.__start_hour - current_time < 2:
                raise ValueError("Too late to cancel a confirmed appointment.")

        self.__status = AppointmentStatus.CANCELLED
        self.__cancellation_reason = reason

    def calculate_price(self, p):
        return self.__staff.fee(p) * self.__patient.payment_rate()
        
