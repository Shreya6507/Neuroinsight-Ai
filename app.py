import io
import os
import datetime
import json
import zipfile
from pathlib import Path
import cv2
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash, send_from_directory
from werkzeug.utils import secure_filename
from model.dummy_model import analyze_mri

app = Flask(__name__)
app.secret_key = "replace-with-a-secure-random-key"
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=7)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.before_request
def make_session_permanent():
    session.permanent = True

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp"}
VALID_USERS = {
    "doctor@example.com": "password123",
    "test@example.com": "test123",
}
USER_STORE_PATH = Path(app.root_path) / "users.json"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_users():
    if not USER_STORE_PATH.exists():
        return {}
    try:
        with open(USER_STORE_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def save_users(users):
    with open(USER_STORE_PATH, "w", encoding="utf-8") as handle:
        json.dump(users, handle, indent=2)


def get_user_profile(email):
    users = load_users()
    return users.get(email.lower())


def create_user_profile(email, password, full_name, age, specialty, notes):
    users = load_users()
    email_key = email.lower()
    if email_key in users:
        return None
    profile = {
        "email": email_key,
        "password": password,
        "full_name": full_name,
        "age": age,
        "specialty": specialty,
        "notes": notes,
    }
    users[email_key] = profile
    save_users(users)
    return profile


def create_highlight_image(image_path, filename, suspicious=False):
    try:
        image = cv2.imread(image_path)
        if image is None:
            return None

        output = image.copy()
        if not suspicious:
            cv2.putText(output, "No suspicious lesion", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            stem = Path(filename).stem
            output_path = os.path.join(app.config["UPLOAD_FOLDER"], f"highlight_{datetime.datetime.utcnow().timestamp()}_{stem}.png")
            cv2.imwrite(output_path, output)
            return output_path

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, threshold = cv2.threshold(blurred, 120, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(contour)
            if area > 500:
                x, y, w, h = cv2.boundingRect(contour)
                pad = max(10, min(w, h) // 3)
                x1, y1 = max(0, x - pad), max(0, y - pad)
                x2, y2 = min(image.shape[1], x + w + pad), min(image.shape[0], y + h + pad)
                cv2.rectangle(output, (x1, y1), (x2, y2), (0, 255, 255), 2)
                cv2.putText(output, "Tumor region", (x1, max(20, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            else:
                cv2.putText(output, "No clear lesion", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        else:
            cv2.putText(output, "No clear lesion", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        stem = Path(filename).stem
        output_path = os.path.join(app.config["UPLOAD_FOLDER"], f"highlight_{datetime.datetime.utcnow().timestamp()}_{stem}.png")
        cv2.imwrite(output_path, output)
        return output_path
    except Exception as exc:
        print(f"⚠️  Could not generate highlight image: {exc}")
        return None


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if VALID_USERS.get(email) == password:
            session["user"] = email
            session["user_profile"] = {"full_name": "Demo User", "email": email}
            return redirect(url_for("dashboard"))

        profile = get_user_profile(email)
        if profile and profile.get("password") == password:
            session["user"] = email
            session["user_profile"] = profile
            return redirect(url_for("dashboard"))

        flash("Invalid credentials. Create an account first if you are a new user.", "error")

    if session.get("user"):
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("user"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        age = request.form.get("age", "").strip()
        specialty = request.form.get("specialty", "").strip()
        notes = request.form.get("notes", "").strip()

        if not full_name or not email or not password:
            flash("Please fill in your name, email and password.", "error")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return redirect(url_for("signup"))

        profile = create_user_profile(email, password, full_name, age, specialty, notes)
        if profile is None:
            flash("An account with that email already exists. Please sign in instead.", "error")
            return redirect(url_for("signup"))

        session["user"] = email
        session["user_profile"] = profile
        flash("Account created successfully. You can now analyze scans.", "success")
        return redirect(url_for("dashboard"))

    return render_template("signup.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("user"):
        return redirect(url_for("login"))

    analysis = session.get("analysis")
    message = None

    if request.method == "POST":
        if "mri_image" not in request.files:
            flash("Please upload an MRI image file.", "error")
            return redirect(url_for("dashboard"))

        file = request.files["mri_image"]
        if file.filename == "" or not allowed_file(file.filename):
            flash("Upload a valid image file (PNG, JPG, JPEG, GIF, BMP).", "error")
            return redirect(url_for("dashboard"))

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"{datetime.datetime.utcnow().timestamp()}_{filename}")
        file.save(filepath)

        analysis = analyze_mri(filepath)
        analysis["filename"] = filename
        analysis["uploaded_at"] = datetime.datetime.now(datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S IST")
        analysis["image_path"] = filepath
        highlight_path = create_highlight_image(filepath, filename, suspicious=bool(analysis.get("present")))
        analysis["highlight_path"] = highlight_path
        analysis["highlight_filename"] = os.path.basename(highlight_path) if highlight_path else None

        patient_name = request.form.get("patient_name", "").strip()
        patient_age = request.form.get("patient_age", "").strip()

        analysis["patient_name"] = patient_name or "Not provided"
        analysis["patient_age"] = patient_age or "Not provided"
        analysis["patient_specialty"] = "Not provided"
        analysis["staff_name"] = session.get("user_profile", {}).get("full_name", session.get("user"))
        analysis["staff_specialty"] = session.get("user_profile", {}).get("specialty", "Not provided")
        session["analysis"] = analysis
        message = "Analysis complete. Download your report below."

    user_profile = session.get("user_profile", {})
    return render_template("dashboard.html", user=user_profile.get("full_name", session.get("user")), user_profile=user_profile, analysis=analysis, message=message)


@app.route("/download-report")
def download_report():
    if not session.get("user") or not session.get("analysis"):
        return redirect(url_for("dashboard"))

    analysis = session["analysis"]
    user_profile = session.get("user_profile", {})
    content = (
        f"NeuroInsight AI MRI Report\n"
        f"Generated: {datetime.datetime.now(datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d %H:%M:%S IST')}\n"
        f"Patient: {analysis.get('patient_name', 'Not provided')}\n"
        f"Patient Age: {analysis.get('patient_age', 'Not provided')}\n"
        f"Patient Specialty/Department: {analysis.get('patient_specialty', 'Not provided')}\n"
        f"Reported by: {analysis.get('staff_name', user_profile.get('full_name', session.get('user')))}\n"
        f"Reporter Specialty: {analysis.get('staff_specialty', user_profile.get('specialty', 'Not provided'))}\n"
        f"Email: {session.get('user')}\n"
        f"MRI File: {analysis.get('filename')}\n"
        f"Uploaded at: {analysis.get('uploaded_at')}\n"
        f"\n"
        f"Tumor detected: {'Yes' if analysis.get('present') else 'No'}\n"
        f"Tumor type: {analysis.get('type')}\n"
        f"Severity: {analysis.get('severity')}\n"
        f"Clinical summary: {analysis.get('description', 'No summary available')}\n"
        f"Confidence: {analysis.get('confidence') * 100:.1f}%\n"
        f"Recommendation: {analysis.get('recommendation', 'Review with a radiology specialist')}\n"
        f"Notes:\n{analysis.get('notes')}\n"
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("neuroinsight_report.txt", content)
        highlight_path = analysis.get("highlight_path")
        if highlight_path and os.path.exists(highlight_path):
            with open(highlight_path, "rb") as handle:
                archive.writestr("highlighted_scan.png", handle.read())
        else:
            archive.writestr("highlighted_scan.png", b"")

    buffer.seek(0)
    filename = f"neuroinsight-report-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.zip"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/zip")


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
