
from abc import ABC, abstractmethod


class Person(ABC):
    initialization_count = 0

    def __init__(self, name, person_id, **kwargs):
        if not name or not name.strip():
            raise ValueError("Name cannot be empty.")

        if person_id <= 0:
            raise ValueError("ID must be positive.")

        Person.initialization_count += 1

        self.__name = name.strip()
        self.__id = person_id

        super().__init__(**kwargs)

    @property
    def name(self):
        return self.__name

    @property
    def person_id(self):
        return self.__id

    @abstractmethod
    def role(self):
        pass


class Patient(Person):
    def payment_rate(self):
        return 1.0

    def role(self):
        return "Patient"


class StudentPatient(Patient):
    def payment_rate(self):
        return 0.50


class StaffMemberPatient(Patient):
    def payment_rate(self):
        return 0.0


class VisitorPatient(Patient):
    def payment_rate(self):
        return 1.0



class Staff(Person, ABC):
    def __init__(self, name, person_id, **kwargs):
        super().__init__(name, person_id, **kwargs)

    @abstractmethod
    def fee(self, p):
        pass

    def buffer_hours(self):
        return 0


class Doctor(Staff):
    def __init__(self, name, person_id, **kwargs):
        super().__init__(name, person_id, **kwargs)

    def role(self):
        return "Doctor"

    def fee(self, p):
        return 40 + 5 * (p % 5)

    def buffer_hours(self):
        return 2


class Nurse(Staff):
    def role(self):
        return "Nurse"

    def fee(self, p):
        return 10 + (p % 3)

    def buffer_hours(self):
        return 1


class Pharmacist(Staff):
    def role(self):
        return "Pharmacist"

    def fee(self, p):
        return 5


class Lecturer(Person):
    def __init__(self, name, person_id, module_name, **kwargs):
        self.__module_name = module_name
        super().__init__(name, person_id, **kwargs)

    @property
    def module_name(self):
        return self.__module_name

    def role(self):
        return "Lecturer"


class MedicalLecturer(Doctor, Lecturer):
    def __init__(self, name, person_id, module_name):
        super().__init__(
            name,
            person_id,
            module_name=module_name
        )

    def role(self):
        return "Doctor and Lecturer"
