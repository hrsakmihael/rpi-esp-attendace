import mysql.connector
import paho.mqtt.client as mqtt

db = mysql.connector.connect(
    host="localhost",
    user="user",
    password="password",
    database="rfid"
)

cursor = db.cursor()

print("Baza spojena")

publisher = mqtt.Client()
publisher.connect("localhost", 1883)

def on_message(client, userdata, msg):

    data = msg.payload.decode().strip()
    device_code, uid = data.split(":")

    print("\n===================")
    print("Uređaj:", device_code)
    print("UID:", uid)

    cursor.execute(
        """
        SELECT state, active_course_id, active_professor_id
        FROM devices
        WHERE device_code = %s
        """,
        (device_code,)
    )

    device = cursor.fetchone()

    if not device:
        print("Nepoznata prostorija")
        return

    room_state = device[0]
    active_course_id = device[1]
    active_professor_id = device[2]

    print("Status prostorije:", room_state)

    cursor.execute(
        "SELECT id, name FROM professors WHERE uid = %s",
        (uid,)
    )

    professor = cursor.fetchone()

    if professor:

        professor_id = professor[0]
        professor_name = professor[1]

        print("Profesor:", professor_name)

        if room_state == "LOCKED":

            cursor.execute(
                "SELECT id, name FROM courses WHERE professor_id = %s LIMIT 1",
                (professor_id,)
            )

            course = cursor.fetchone()

            if not course:
                print("Profesor nema kolegij")
                return

            course_id = course[0]
            course_name = course[1]

            cursor.execute(
                """
                UPDATE devices
                SET state = 'UNLOCKED',
                    active_course_id = %s,
                    active_professor_id = %s
                WHERE device_code = %s
                """,
                (course_id, professor_id, device_code)
            )

            db.commit()

            publisher.publish("door/control", "OPEN")

            print("Prostorija otključana")
            print("Kolegij aktivan:", course_name)

            return

        if room_state == "UNLOCKED" and active_professor_id == professor_id:

            cursor.execute(
                """
                UPDATE devices
                SET state = 'LOCKED',
                    active_course_id = NULL,
                    active_professor_id = NULL
                WHERE device_code = %s
                """,
                (device_code,)
            )

            db.commit()

            publisher.publish("door/control", "CLOSE")

            print("Prostorija zaključana")

            return

        print("Drugi profesor ili već aktivno")
        return

    cursor.execute(
        "SELECT id, name FROM students WHERE uid = %s",
        (uid,)
    )

    student = cursor.fetchone()

    if student:

        student_id = student[0]
        student_name = student[1]

        print("Student:", student_name)

        if room_state == "LOCKED":
            print("Prostorija je zaključana")
            return

        cursor.execute(
            """
            SELECT *
            FROM enrollments
            WHERE student_id = %s
            AND course_id = %s
            """,
            (student_id, active_course_id)
        )

        enrolled = cursor.fetchone()

        if not enrolled:
            print("Student nije upisan na kolegij")
            return

        cursor.execute(
            """
            INSERT INTO attendance (student_id, course_id)
            VALUES (%s, %s)
            """,
            (student_id, active_course_id)
        )

        db.commit()

        print("Attendance upisan")

        return

    print("Nepoznata kartica")

client = mqtt.Client()

client.on_message = on_message

client.connect("localhost", 1883)

client.subscribe("rfid/tag")

print("Čekam poruke...")

client.loop_forever()
