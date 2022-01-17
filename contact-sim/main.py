from building import Building
from room import Room
from course import Course
from student import Student
import numpy as np
import random
import csv
from datetime import datetime, timedelta
from ctdb_utility_lib.utility import (
    _execute_statement,
    connect_to_db,
    add_person,
    add_room,
    add_scan,
)


def random_time():
    tod = random.randint(9, 20)

    chance = random.random()

    if chance <= 0.65:
        dow = random.randint(6, 7)
    else:
        dow = random.randint(1, 5)

    return dow * 100 + tod


def sim_setup(num_buildings, num_rooms, num_students, min_class, max_class, conn):
    buildings = []
    rooms = []
    classes = []
    students = []
    for i in range(num_buildings):
        building = Building(i)
        buildings.append(building)
        for x in range(num_rooms):
            room = Room(building.id * 100 + x)
            code = add_room(f"room_{room.id}", 100, f"building_{building.id}", conn)
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
        stud = Student(i, np.random.choice(classes, random.randint(2, 4), replace=False))
        students.append(stud)
        email = add_person(stud.fname, stud.lname, stud.id, conn)
        stud.set_email(email)

    return buildings, rooms, classes, students


def get_students_in_class(students, course):
    studs = []
    for stud in students:
        if course in stud.classes:
            studs.append(stud)

    return studs


def dow_equals(dow_int: int, dow_dt: int):
    # dow_int represents our simulation's dow integer value for a course.
    # dow_dt represents python's datetime .weekday() + 1 return value.

    # If the datetime falls on a Saturday/Sunday we automatically know
    # A course never falls on those days and can return false.
    if dow_dt >= 6:
        return False

    # If our internal DoW is equal to 6
    # That means Monday/Wednesday and we should return true for either of those days.
    if dow_int == 6:
        return dow_dt == 1 or dow_dt == 3
    # If our internal DoW is equal to 7
    # That means Tuesday/Thursday and we should return true for either of those days.
    if dow_int == 7:
        return dow_dt == 2 or dow_dt == 4

    # Otherwise, no special days/codes are in play and we can just directly compare the two integers.
    return dow_int == dow_dt


def get_classes_by_dow(classes, dow):
    courses = []
    for course in classes:
        if dow_equals(course.dow, dow):
            courses.append(course)

    return courses


def sim_step_day(classes, students, day_date: datetime, conn):
    # Get the current Day_of_Week integer from python's Date Time object.
    # We add +1 because for the simulation Monday = 1.
    dow = day_date.weekday() + 1

    # Get all courses that are supposed to be on this DoW
    courses = get_classes_by_dow(classes, dow)
    logs = []

    # Start going through the day hour by hour.
    for hour in range(24):
        for course in courses:
            # Check if our subset of courses start on this hour.
            if course.time == hour:
                # If our course does start, then get a list of all students in this course.
                studs_in_course = get_students_in_class(students, course)
                # Generate a record for each student in the course.
                for sic in studs_in_course:
                    log = f"{sic.id},{course.id},{course.room.id},{day_date + timedelta(hours=hour)}"
                    add_scan(sic.email, f"room_{course.room.id}", conn)
                    logs.append(log)
    # Return all logs generated from the day.
    return logs


def generate_flatfile_data(buildings, rooms, classes, students):
    with open("buildings.csv", "w+") as file:
        file.write("building_id\n")
        for building in buildings:
            file.write(f"{building.id}\n")

    with open("rooms.csv", "w+") as file:
        file.write("room_id,building_id\n")
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


def reset_sim_psql_data(con):
    # Clear the database for new run.
    _execute_statement(con, "DELETE FROM scans")
    _execute_statement(con, "DELETE FROM rooms")
    _execute_statement(con, "DELETE FROM people")


if __name__ == "__main__":
    # PARAMETER SETUP
    RESET_DATA = True
    num_buildings = 1
    num_rooms = 5
    min_class = 1
    max_class = 4
    num_students = 100
    num_days = 14
    start_date = datetime(year=2022, month=1, day=3, hour=0, minute=0)

    # Connection
    con = connect_to_db()
    if RESET_DATA:
        reset_sim_psql_data(con)

    # Generate all our initial objects, such as students, buildings, rooms, courses
    buildings, rooms, classes, students = sim_setup(
        num_buildings, num_rooms, num_students, min_class, max_class, con
    )

    # Store all logs we see in the record list
    records = []

    # Generates a CSV for each "table" as if they were SQL tables.
    generate_flatfile_data(buildings, rooms, classes, students)

    with open("records.csv", "w+") as file:
        file.write("student_id,course_id,room_id,datetime\n")

        # Start of simulation, loops for every day given by the duration parameter
        for i in range(num_days):
            # Simulates a Single day from the given start_date, students, and classes.
            # Returns a list of logs generated by that day.
            new_logs = sim_step_day(classes, students, start_date, con)

            # Add 24 hours to the current start_date for the next day.
            start_date += timedelta(hours=24)

            # Append the newly generated logs by the simulated day to overall record list.
            records += new_logs

        # Write all records out to the csv file.
        for record in records:
            file.write(record + "\n")
