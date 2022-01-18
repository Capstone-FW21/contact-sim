from building import Building
from room import Room
from course import Course
from student import Student
import numpy as np
import psycopg2
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


def sim_setup(num_buildings, num_rooms, num_students, min_course, max_course, conn):
    buildings = []
    rooms = []
    courses = []
    students = []
    for i in range(num_buildings):
        building = Building(i)
        buildings.append(building)
        for x in range(num_rooms):
            room = Room(building.id * 100 + x + 1)
            print(room.id)
            # code = add_room(f"room_{room.id}", 100, f"building_{building.id}", conn)
            building.add_room(room)
            rooms.append(room)

    for room in rooms:
        num_courses = np.random.randint(min_course, max_course)
        used_times = []
        for i in range(num_courses):
            time = random_time()

            if time in used_times:
                i -= 1
                continue

            c = Course(i + room.id * 10, time, room, 0.5)
            used_times.append(time)
            courses.append(c)

    for i in range(num_students):
        stud = Student(i, np.random.choice(courses, random.randint(2, 4), replace=False))
        students.append(stud)
        # add_person(stud.fname, stud.lname, stud.id, conn)
        # stud.set_email(email)

    return buildings, rooms, courses, students


def get_students_in_course(students, course):
    studs = []
    for stud in students:
        if course in stud.courses:
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


def get_courses_by_dow(all_courses, dow):
    courses = []
    for course in all_courses:
        if dow_equals(course.dow, dow):
            courses.append(course)

    return courses


def sim_step_day(courses, students, day_date: datetime, conn):
    # Get the current Day_of_Week integer from python's Date Time object.
    # We add +1 because for the simulation Monday = 1.
    dow = day_date.weekday() + 1

    # Get all courses that are supposed to be on this DoW
    courses = get_courses_by_dow(courses, dow)
    logs = []

    # Start going through the day hour by hour.
    for hour in range(24):
        for course in courses:
            # Check if our subset of courses start on this hour.
            if course.time == hour:
                # If our course does start, then get a list of all students in this course.
                studs_in_course = get_students_in_course(students, course)
                # Generate a record for each student in the course.
                for sic in studs_in_course:
                    log = f"{sic.email},{course.id},{course.room.id},{day_date + timedelta(hours=hour)}"
                    # add_scan(sic.email, f"room_{course.room.id}", conn)
                    logs.append(log)
    # Return all logs generated from the day.
    return logs


def generate_flatfile_data(buildings, rooms, courses, students):
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

        for course in courses:
            file.write(f"{course.id},{course.room},{course.dow},{course.time}\n")

    with open("students.csv", "w+") as file:
        file.write("student_id\n")
        for student in students:
            student: Student
            file.write(f"{student.id}\n")

    with open("student_courses.csv", "w+") as file:
        file.write("student_id,course_id\n")

        for student in students:
            for course in student.courses:
                file.write(f"{student.id},{course.id}\n")


def reset_sim_psql_data(con):
    # Clear the database for new run.
    _execute_statement(con, "DELETE FROM scans")
    _execute_statement(con, "DELETE FROM rooms")
    _execute_statement(con, "DELETE FROM people")


def batch_insert_people(students: list, con):
    stud_tuples = [stud.to_sql_tuple() for stud in students]

    cur = con.cursor()
    query = "INSERT INTO people (email,name,student_id) VALUES"
    query = build_query(query, "(%s,%s,%s)", stud_tuples, cur)
    cur.execute(query)


def batch_insert_rooms(rooms: list, con):
    room_tuples = [room.to_sql_tuple() for room in rooms]

    cur = con.cursor()
    query = "INSERT INTO rooms (room_id, capacity, building_name) VALUES"
    query = build_query(query, "(%s,%s,%s)", room_tuples, cur)
    cur.execute(query)


def batch_insert_scan(scans: list, con):

    scan_tuples = []
    for scan in scans:
        data = scan.split(",")

        email = data[0]
        room_id = data[2]
        date = data[3]

        scan_tuples.append((email, date, room_id))

    query = "INSERT INTO scans (scan_id, person_email, scan_time, room_id) VALUES"
    value_str = "(DEFAULT, %s, TIMESTAMP %s, %s)"
    cur = con.cursor()
    query = build_query(query, value_str, scan_tuples, cur)

    cur.execute(query)


def build_query(query: str, value_str: str, data: list, cur):
    values = ",".join([cur.mogrify(value_str, x).decode("utf-8") for x in data])

    return query + " " + values


if __name__ == "__main__":
    # PARAMETER SETUP
    RESET_DATA = True
    num_buildings = 1
    num_rooms = 50
    min_course = 1
    max_course = 4
    num_students = 3000
    num_days = 14
    start_date = datetime(year=2022, month=1, day=3, hour=0, minute=0)

    # Connection
    con = connect_to_db()
    if RESET_DATA:
        reset_sim_psql_data(con)

    # Generate all our initial objects, such as students, buildings, rooms, courses
    buildings, rooms, courses, students = sim_setup(
        num_buildings, num_rooms, num_students, min_course, max_course, con
    )

    batch_insert_people(students, con)
    batch_insert_rooms(rooms, con)

    con.commit()
    # Store all logs we see in the record list
    records = []

    # Generates a CSV for each "table" as if they were SQL tables.
    generate_flatfile_data(buildings, rooms, courses, students)

    # with open("records.csv", "w+") as file:
    # file.write("student_id,course_id,room_id,datetime\n")

    # Start of simulation, loops for every day given by the duration parameter
    for i in range(num_days):
        # Simulates a Single day from the given start_date, students, and courses.
        # Returns a list of logs generated by that day.
        new_logs = sim_step_day(courses, students, start_date, con)

        # Add 24 hours to the current start_date for the next day.
        start_date += timedelta(hours=24)

        # Append the newly generated logs by the simulated day to overall record list.
        records += new_logs

    batch_insert_scan(records, con)
    con.commit()
    # Write all records out to the csv file.
    # for record in records:
    #    file.write(record + "\n")
