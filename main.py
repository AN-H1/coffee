import json
from flask import (
    Flask,
    flash,
    render_template,
    request,
    redirect,
    send_from_directory,
    session,
    jsonify,
    Response,
)
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_bcrypt import Bcrypt
import subprocess
import os
import tempfile
import cv2
import asyncio
from flask import Flask, render_template, url_for
import time


# Path to the shared file for detected objects
detected_objects_file = os.path.join(tempfile.gettempdir(), "detected_objects.json")

# from object.object import set_stop_signal
from object2.object2 import ObjectDetection

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///ums.sqlite"  # Adjust your database URI
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "65b0b774279de460f1cc5c92"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['TEMPLATES_AUTO_RELOAD'] = True

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
Session(app)

process = None  # Global variable to manage the scanning subprocess
final_detected_objects = []  # Store the results of object detection

camera_obj = None

# User Class
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(255), nullable=False)
    lname = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    edu = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Integer, default=0, nullable=False)
    scanned_objects = db.Column(db.Text, nullable=True)  # New field

    def __repr__(self):
        return f'User("{self.id}", "{self.fname}", "{self.lname}", "{self.email}", "{self.edu}", "{self.username}", "{self.status}")'


# Admin Class
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'Admin("{self.username}", "{self.id}")'
    



def create_tables():
    with app.app_context():
        db.create_all()
        # Check if admin already exists
        if not Admin.query.first():
            admin = Admin(
                username="hilal123",
                password=bcrypt.generate_password_hash("hilal123", 10),
            )
            db.session.add(admin)
            db.session.commit()


# Call create_tables to create the database tables
# create_tables()


# Main index
@app.route("/")
def index():
    return render_template("index.html", title="")


# Admin login
@app.route("/admin/", methods=["POST", "GET"])
def adminIndex():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "" and password == "":
            flash("Please fill all the fields", "danger")
            return redirect("/admin/")
        else:
            admins = Admin.query.filter_by(username=username).first()
            if admins and bcrypt.check_password_hash(admins.password, password):
                session["admin_id"] = admins.id
                session["admin_name"] = admins.username
                flash("Login Successfully", "success")
                return redirect("/admin/dashboard")
            else:
                flash("Invalid Username and Password", "danger")
                return redirect("/admin/")
    else:
        return render_template("admin/index.html", title="Admin Login")


# Admin Dashboard
@app.route("/admin/dashboard")
def adminDashboard():
    if not session.get("admin_id"):
        return redirect("/admin/")
    totalUser = User.query.count()
    totalApprove = User.query.filter_by(status=1).count()
    NotTotalApprove = User.query.filter_by(status=0).count()
    return render_template(
        "admin/dashboard.html",
        title="Admin Dashboard",
        totalUser=totalUser,
        totalApprove=totalApprove,
        NotTotalApprove=NotTotalApprove,
    )


# Admin get all users
@app.route("/admin/get-all-user", methods=["POST", "GET"])
def adminGetAllUser():
    if not session.get("admin_id"):
        return redirect("/admin/")
    if request.method == "POST":
        search = request.form.get("search")
        users = User.query.filter(User.username.like("%" + search + "%")).all()
        return render_template("admin/all-user.html", title="Approve User", users=users)
    else:
        users = User.query.all()
        return render_template("admin/all-user.html", title="Approve User", users=users)


@app.route("/admin/approve-user/<int:id>")
def adminApprove(id):
    if not session.get("admin_id"):
        return redirect("/admin/")
    User.query.filter_by(id=id).update(dict(status=1))
    db.session.commit()
    flash("Approve Successfully", "success")
    return redirect("/admin/get-all-user")


# Change admin password
@app.route("/admin/change-admin-password", methods=["POST", "GET"])
def adminChangePassword():
    admin = Admin.query.get(1)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "" or password == "":
            flash("Please fill the field", "danger")
            return redirect("/admin/change-admin-password")
        else:
            Admin.query.filter_by(username=username).update(
                dict(password=bcrypt.generate_password_hash(password, 10))
            )
            db.session.commit()
            flash("Admin Password updated successfully", "success")
            return redirect("/admin/change-admin-password")
    else:
        return render_template(
            "admin/admin-change-password.html",
            title="Admin Change Password",
            admin=admin,
        )


# Admin logout@app.route("/admin/logout")
def adminLogout():
    if not session.get("admin_id"):
        return redirect("/admin/")
    session.pop("admin_id", None)
    session.pop("admin_name", None)
    return redirect("/")


# ------------------------- User Area ----------------------------


# User login
@app.route("/user/", methods=["POST", "GET"])
def userIndex():
    if session.get("user_id"):
        return redirect("/user/dashboard")
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        users = User.query.filter_by(email=email).first()
        if users and bcrypt.check_password_hash(users.password, password):
            if users.status == 0:
                flash("Your Account is not approved by Admin", "danger")
                return redirect("/user/")
            else:
                session["user_id"] = users.id
                session["username"] = users.username
                flash("Login Successfully", "success")
                return redirect("/user/dashboard")
        else:
            flash("Invalid Email and Password", "danger")
            return redirect("/user/")
    else:
        return render_template("user/index.html", title="User Login")


# User Register
@app.route("/user/signup", methods=["POST", "GET"])
def userSignup():
    if session.get("user_id"):
        return redirect("/user/dashboard")
    if request.method == "POST":
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        email = request.form.get("email")
        username = request.form.get("username")
        edu = request.form.get("edu")
        password = request.form.get("password")
        if (
            fname == ""
            or lname == ""
            or email == ""
            or password == ""
            or username == ""
            or edu == ""
        ):
            flash("Please fill all the fields", "danger")
            return redirect("/user/signup")
        else:
            is_email = User.query.filter_by(email=email).first()
            if is_email:
                flash("Email already exists", "danger")
                return redirect("/user/signup")
            else:
                hash_password = bcrypt.generate_password_hash(password, 10)
                user = User(
                    fname=fname,
                    lname=lname,
                    email=email,
                    password=hash_password,
                    edu=edu,
                    username=username,
                )
                db.session.add(user)
                db.session.commit()
                flash(
                    "Account Created Successfully! Admin will approve your account in 10 to 30 minutes",
                    "success",
                )
                return redirect("/user/")
    else:
        return render_template("user/signup.html", title="User Signup")


# Route to handle image scanning
@app.route("/scan", methods=["GET", "POST"])
def scan_page():
    if request.method == "POST":
        print("JANSEL PINGUEL")
    return render_template("user/scan.html", title="Object Scanning")


# ---------------- Object Detection Integration -----------------

final_detected_objects = []  # Store the results of object detection

@app.route("/run_object_py", methods=["GET"])
def run_object_py():
    """Start the object scanning process."""
    global process, final_detected_objects
    final_detected_objects = []  # Reset detected objects for a new session
    try:
        script_path = (
            r"C:\Users\user\OneDrive\Desktop\CoffeeBeanProject\object\object.py"
        )
        process = subprocess.Popen(["python", script_path])
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))


# =============================== LIVE VIDEO ==================================================================
@app.route("/check_camera")
def check_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        # Release the camera if it was not opened
        cap.release()
        # Raise an error and return JSON or render an error page
        return jsonify({"error": "Camera not detected. Please check your device and permissions."})
    cap.release()
    return jsonify({"success": "Camera not detected. Please check your device and permissions."})

@app.route("/video_feed")
def video_feed():    
    start = cv2.VideoCapture(0)
    if not start.isOpened():
        # Release the camera if it was not opened
        start.release()
        # Raise an error and return JSON or render an error page
        return jsonify({"error": "Camera not detected. Please check your device and permissions."})
    
    return Response(
        gen(start), mimetype="multipart/x-mixed-replace; boundary=frame"
    )

def gen(camera):
    global camera_obj
    camera_obj = ObjectDetection(camera)
    camera_obj.start()
    try:
        while True:
            frame = camera_obj.get_frames()
            if frame:
                yield (
                    b"--frame\r\n" b"Content-Type: image/png\r\n\r\n" + frame + b"\r\n"
                )
            else:
                break
    except Exception as err:
        print(err)
        print("NO CAMEREA DETECETED")
        return jsonify(error="no camera detected")
    finally:
        print("CLOSING")
        camera_obj.stop()
        
@app.route("/stop_object_py")
def stop_object_py():
    global camera_obj
    try:
        camera_obj.get_last_frame()
        print("SUCCESS UPDATING FRAME FILE")        
        return jsonify(success=True, message="Scanning")
    except Exception as e:
        return jsonify(success=False, message=str(e))
    
@app.route("/get_defects")
def get_defects():
    global camera_obj
    defects = camera_obj.defects
    print("DEFEFCT:",defects)
    return render_template('user/partials/defect_result.html', defects=defects)

# LIVE VIDEO=========== END============================================



@app.route("/get_final_results", methods=["GET"])
def get_final_results():
    """Return the detected objects after scanning."""
    global final_detected_objects
    return jsonify({"objects": final_detected_objects})


def send_detected_objects(objects):
    """Receive detected objects from the scanning script."""
    global final_detected_objects
    final_detected_objects = [
        {"object_name": obj, "confidence": "N/A"} for obj in objects
    ]


# screenshot
@app.route("/get_latest_screenshot", methods=["GET"])
def get_latest_screenshot():
    screenshot_path = os.path.join("./static/images/", "latest_screenshot.jpg")
    if os.path.exists(screenshot_path):
        return send_from_directory("./static/images/", "latest_screenshot.jpg")
    else:
        return jsonify({"error": "No screenshot available"}), 404


@app.route("/get_detected_objects", methods=["GET"])
def get_detected_objects():
    """Retrieve the final detected objects after scanning."""
    try:
        if os.path.exists(detected_objects_file):
            with open(detected_objects_file, "r") as f:
                objects = json.load(f)
            return jsonify(
                success=True, objects=objects
            )  # Ensure `objects` is a list of dictionaries
        else:
            return jsonify(success=False, message="No detected objects found.")
    except Exception as e:
        return jsonify(success=False, message=str(e))


# update scanned object (screenshots saved)
@app.route("/update_scanned_objects", methods=["POST"])
def update_scanned_objects():
    data = request.get_json()
    user_id = data.get("user_id")
    objects = data.get("objects")

    if not user_id or not objects:
        return jsonify({"error": "Invalid data"}), 400

    user = User.query.get(user_id)
    if user:
        user.scanned_objects = ", ".join(
            objects
        )  # Save objects as a comma-separated string
        db.session.commit()
        return jsonify({"success": "Objects updated successfully"}), 200
    else:
        return jsonify({"error": "User not found"}), 404


# =============================== END CV ===============================


# User dashboard
@app.route("/user/dashboard")
def userDashboard():
    print("CAMERA OBJ:", camera_obj)
    if not session.get("user_id"):
        return redirect("/user/")
    id = session.get("user_id")
    users = User.query.filter_by(id=id).first()
    return render_template("user/dashboard.html", title="User Dashboard", users=users)

# User logout
@app.route("/user/logout")
def userLogout():
    if not session.get("user_id"):
        return redirect("/user/")
    session.pop("user_id", None)
    session.pop("username", None)
    return redirect("/")


# User change password
@app.route("/user/change-password", methods=["POST", "GET"])
def userChangePassword():
    if not session.get("user_id"):
        return redirect("/user/")
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if email == "" or password == "":
            flash("Please fill the field", "danger")
            return redirect("/user/change-password")
        else:
            users = User.query.filter_by(email=email).first()
            if users:
                hash_password = bcrypt.generate_password_hash(password, 10)
                User.query.filter_by(email=email).update(dict(password=hash_password))
                db.session.commit()
                flash("Password Changed Successfully", "success")
                return redirect("/user/change-password")
            else:
                flash("Invalid Email", "danger")
                return redirect("/user/change-password")
    else:
        return render_template("user/change-password.html", title="Change Password")


if __name__ == "__main__":
    app.run(debug=True)
