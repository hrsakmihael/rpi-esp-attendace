import tornado.ioloop
import tornado.web
import tornado.websocket
import os
import json
import paho.mqtt.client as mqtt

from database import get_connection


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class StudentsHandler(tornado.web.RequestHandler):
    def get(self):
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, uid
            FROM students
            ORDER BY name
        """)

        students = cursor.fetchall()

        cursor.close()
        db.close()

        self.render("students.html", students=students)


class ProfessorsHandler(tornado.web.RequestHandler):
    def get(self):
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, uid
            FROM professors
            ORDER BY name
        """)

        professors = cursor.fetchall()

        cursor.close()
        db.close()

        self.render("professors.html", professors=professors)


class CoursesHandler(tornado.web.RequestHandler):
    def get(self):
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT courses.id,
                   courses.name,
                   professors.name AS professor_name
            FROM courses
            LEFT JOIN professors
                ON courses.professor_id = professors.id
            ORDER BY courses.name
        """)

        courses = cursor.fetchall()

        cursor.execute("""
            SELECT id, name
            FROM professors
            ORDER BY name
        """)

        professors = cursor.fetchall()

        cursor.execute("""
            SELECT id, name
            FROM students
            ORDER BY name
        """)

        students = cursor.fetchall()

        cursor.execute("""
            SELECT
                enrollments.student_id,
                enrollments.course_id,
                students.name AS student_name,
                courses.name AS course_name
            FROM enrollments
            JOIN students
                ON enrollments.student_id = students.id
            JOIN courses
                ON enrollments.course_id = courses.id
            ORDER BY courses.name, students.name
        """)

        enrollments = cursor.fetchall()

        cursor.close()
        db.close()

        self.render(
            "courses.html",
            courses=courses,
            professors=professors,
            students=students,
            enrollments=enrollments
        )

class AttendanceHandler(tornado.web.RequestHandler):
    def get(self):
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT attendance.id,
                   students.name AS student_name,
                   courses.name AS course_name,
                   attendance.timestamp
            FROM attendance
            LEFT JOIN students
                ON attendance.student_id = students.id
            LEFT JOIN courses
                ON attendance.course_id = courses.id
            ORDER BY attendance.timestamp DESC
        """)

        attendance = cursor.fetchall()

        cursor.close()
        db.close()

        self.render("attendance.html", attendance=attendance)


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    clients = set()

    def open(self):
        WebSocketHandler.clients.add(self)
        print("WebSocket klijent spojen")

    def on_message(self, message):

        try:
            data = json.loads(message)

            message_type = data.get("type")

            # =========================================================
            # DODAVANJE PROFESORA
            # =========================================================

            if message_type == "add_professor":

                name = data.get("name", "").strip()
                uid = data.get("uid", "").strip()

                if not name or not uid:

                    self.write_message({
                        "type": "error",
                        "message": "Ime i UID su obavezni."
                    })

                    return

                db = get_connection()
                cursor = db.cursor()

                try:

                    cursor.execute(
                        """
                        INSERT INTO professors (name, uid)
                        VALUES (%s, %s)
                        """,
                        (name, uid)
                    )

                    db.commit()

                    self.write_message({
                        "type": "success",
                        "message": "Profesor uspješno dodan."
                    })

                except Exception as e:

                    db.rollback()

                    self.write_message({
                        "type": "error",
                        "message": "Greška: " + str(e)
                    })

                finally:

                    cursor.close()
                    db.close()


            # =========================================================
            # DODAVANJE STUDENTA
            # =========================================================

            elif message_type == "add_student":

                name = data.get("name", "").strip()
                uid = data.get("uid", "").strip()

                if not name or not uid:

                    self.write_message({
                        "type": "error",
                        "message": "Ime i UID su obavezni."
                    })

                    return

                db = get_connection()
                cursor = db.cursor()

                try:

                    cursor.execute(
                        """
                        INSERT INTO students (name, uid)
                        VALUES (%s, %s)
                        """,
                        (name, uid)
                    )

                    db.commit()

                    self.write_message({
                        "type": "success",
                        "message": "Student uspješno dodan."
                    })

                except Exception as e:

                    db.rollback()

                    self.write_message({
                        "type": "error",
                        "message": "Greška: " + str(e)
                    })

                finally:

                    cursor.close()
                    db.close()


            # =========================================================
            # DODAVANJE PREDMETA
            # =========================================================

            elif message_type == "add_course":

                name = data.get("name", "").strip()
                professor_id = data.get("professor_id")

                if not name or not professor_id:

                    self.write_message({
                        "type": "error",
                        "message": "Naziv predmeta i profesor su obavezni."
                    })

                    return

                db = get_connection()
                cursor = db.cursor()

                try:

                    cursor.execute(
                        """
                        INSERT INTO courses (name, professor_id)
                        VALUES (%s, %s)
                        """,
                        (name, professor_id)
                    )

                    db.commit()

                    self.write_message({
                        "type": "success",
                        "message": "Predmet uspješno dodan."
                    })

                except Exception as e:

                    db.rollback()

                    self.write_message({
                        "type": "error",
                        "message": "Greška: " + str(e)
                    })

                finally:

                    cursor.close()
                    db.close()


            # =========================================================
            # UPIS STUDENTA NA PREDMET
            # =========================================================

            elif message_type == "enroll_student":

                student_id = data.get("student_id")
                course_id = data.get("course_id")

                if not student_id or not course_id:

                    self.write_message({
                        "type": "error",
                        "message": "Student i predmet su obavezni."
                    })

                    return

                db = get_connection()
                cursor = db.cursor()

                try:

                    cursor.execute(
                        """
                        INSERT INTO enrollments
                            (student_id, course_id)
                        VALUES
                            (%s, %s)
                        """,
                        (student_id, course_id)
                    )

                    db.commit()

                    self.write_message({
                        "type": "success",
                        "message": "Student uspješno upisan na predmet."
                    })

                except Exception as e:

                    db.rollback()

                    if "Duplicate entry" in str(e):

                        self.write_message({
                            "type": "error",
                            "message": "Student je već upisan na ovaj predmet."
                        })

                    else:

                        self.write_message({
                            "type": "error",
                            "message": "Greška: " + str(e)
                        })

                finally:

                    cursor.close()
                    db.close()


            # =========================================================
            # NEPOZNAT TIP PORUKE
            # =========================================================

            else:

                self.write_message({
                    "type": "error",
                    "message": "Nepoznata vrsta zahtjeva."
                })

        except Exception as e:

            print("WebSocket greška:", e)

            self.write_message({
                "type": "error",
                "message": "Greška pri obradi zahtjeva."
            })


    def on_close(self):

        WebSocketHandler.clients.discard(self)

        print("WebSocket klijent odspojen")


# =============================================================
# TORNADO APLIKACIJA
# =============================================================

def make_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/studenti", StudentsHandler),
            (r"/profesori", ProfessorsHandler),
            (r"/predmeti", CoursesHandler),
            (r"/evidencija", AttendanceHandler),
            (r"/ws", WebSocketHandler),
        ],

        template_path=os.path.join(
            os.path.dirname(__file__),
            "templates"
        ),

        static_path=os.path.join(
            os.path.dirname(__file__),
            "static"
        )
    )

# =============================================================
# MQTT
# =============================================================

def mqtt_on_connect(client, userdata, flags, rc):

    print("Web MQTT spojen")

    client.subscribe("rfid/tag")


def mqtt_on_message(client, userdata, msg):

    data = msg.payload.decode().strip()

    print("WEB MQTT:", data)

    main_loop.add_callback(
        send_to_websockets,
        data
    )


def send_to_websockets(data):

    for websocket in WebSocketHandler.clients:

        websocket.write_message(data)


# =============================================================
# POKRETANJE SERVERA
# =============================================================

if __name__ == "__main__":

    app = make_app()

    main_loop = tornado.ioloop.IOLoop.current()

    mqtt_client = mqtt.Client()

    mqtt_client.on_connect = mqtt_on_connect
    mqtt_client.on_message = mqtt_on_message

    mqtt_client.connect(
        "localhost",
        1883
    )

    mqtt_client.loop_start()

    app.listen(8888)

    print("Server pokrenut na portu 8888")

    main_loop.start()
