from building import Building
from room import Room
from course import Course
from student import Student
import numpy as np
import random
import csv
from datetime import datetime, timedelta


def random_time():
    tod = random.randint(0, 23)

    dow = random.randint(1, 7)

    return dow * 100 + tod


def sim_setup(num_buildings, num_rooms, num_students, min_class, max_class):
    buildings = []
    rooms = []
    classes = []
    students = []
    for i in range(num_buildings):
        building = Building(i)
        buildings.append(building)
        for x in range(num_rooms):
            room = Room(building.id * 100 + x)
            building.add_room(room)
            rooms.append(room)

    for room in rooms:
        num_classes = np.random.randint(min_class, max_class)
        used_times = []
        for i in range(num_classes):
            time = random_time()

            if time in used_times:
                i -= 1
                continue

            c = Course(i + room.id * 10, time, room, 0.5)
            used_times.append(time)
            classes.append(c)

    for i in range(num_students):
        stud = Student(i, np.random.choice(classes, 3, replace=False))
        students.append(stud)

    return buildings, rooms, classes, students


def get_students_in_class(students, course):
    studs = []
    for stud in students:
        if course in stud.classes:
            studs.append(stud)

    return studs


def dow_equals(dow_int: int, dow_dt: int):

    if dow_dt >= 6:
        return False

    if dow_int == 6:
        return dow_dt == 1 or dow_dt == 3

    if dow_int == 7:
        return dow_dt == 2 or dow_dt == 4

    return dow_int == dow_dt


def get_classes_by_dow(classes, dow):
    courses = []
    for course in classes:
        if dow_equals(course.dow, dow):
            courses.append(course)

    return courses


def sim_step_day(classes, students, day_date: datetime):

    dow = day_date.weekday() + 1
    courses = get_classes_by_dow(classes, dow)
    logs = []
    for hour in range(24):
        for course in courses:
            if course.time == hour:
                studs_in_course = get_students_in_class(students, course)
                for sic in studs_in_course:
                    log = f"{sic.id},{course.id},{course.room.id},{day_date + timedelta(hours=hour)}"
                    logs.append(log)

    return logs


def generate_base_data(buildings, rooms, classes, students):
    with open("buildings.csv", "w+") as file:
        file.write("building_id")
        for building in buildings:
            file.write(f"{building.id}\n")

    with open("rooms.csv", "w+") as file:
        file.write("room_id,building_id,\n")
        for room in rooms:
            file.write(f"{room.id}, {room.building.id}\n")

    with open("courses.csv", "w+") as file:
        file.write("course_id,room_id,dow_id,hour\n")

        for course in classes:
            file.write(f"{course.id},{course.room},{course.dow},{course.time}\n")

    with open("students.csv", "w+") as file:
        file.write("student_id\n")
        for student in students:
            student: Student
            file.write(f"{student.id}\n")

    with open("student_courses.csv", "w+") as file:
        file.write("student_id,course_id\n")

        for student in students:
            for course in student.classes:
                file.write(f"{student.id},{course.id}\n")


def simulate_positive_test(student: Student, logs):
    rooms = []
    for log in logs:
        log: str
        data = log.split(",")
        std_id = data[0]
        if std_id != str(student.id):
            continue

        room_id = data[2]
        dtime = data[3]
        rooms.append((room_id, dtime))
    affected = []
    for log in logs:
        data = log.split(",")
        std_id = data[0]
        if std_id == str(student.id):
            continue
        course_id = data[1]
        room_id = data[2]
        dtime = data[3]
        if (room_id, dtime) in rooms and f"{std_id},{course_id}" not in affected:
            affected.append(f"{std_id},{course_id}")

    return affected


if __name__ == "__main__":
    num_buildings = 1
    num_rooms = 10
    min_class = 1
    max_class = 3
    num_students = 100
    buildings, rooms, classes, students = sim_setup(
        num_buildings, num_rooms, num_students, min_class, max_class
    )
    records = []
    generate_base_data(buildings, rooms, classes, students)
    start_date = datetime(year=2022, month=1, day=3, hour=0, minute=0)
    with open("records.csv", "w+") as file:
        file.write("student_id,course_id,room_id,datetime\n")
        for i in range(7):
            new_logs = sim_step_day(classes, students, start_date)
            start_date += timedelta(hours=24)
            for log in new_logs:
                records.append(log)
                file.write(log + "\n")
