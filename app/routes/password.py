from flask import request,flash,redirect,url_for,render_template,Blueprint,session,jsonify
from flask_babel import gettext as _
from ..models.db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import re
from email.mime.text import MIMEText
import random
import smtplib
import os
import time
from .auth_routes import login_required
password = Blueprint("password", __name__)

def hash_password(password):
    return generate_password_hash(password)

def verify_password(password, stored_hash):
    return check_password_hash(stored_hash, password)

# ── Validation helpers ────────────────────────────────────────────────────────

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# ── API: check email availability (used via fetch in register form) ───────────
@password.route("/api/check-email")
def check_email():
    email = request.args.get("email", "").strip().lower()
    if not EMAIL_RE.match(email):
        return jsonify({"available": False, "error": _("Invalid email")})
    db    = get_db()
    found = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    return jsonify({"available": found is None})


# ── Admin: list all users (protected, dev only) ───────────────────────────────
@password.route("/admin/users")
@login_required
def admin_users():
    if session.get("user_email") != "youradmin@email.com":
        return jsonify({"error": _("Unauthorized")}), 403

    db = get_db()
    users = db.execute(
        "SELECT id, full_name, email FROM users"
    ).fetchall()

    return jsonify([dict(u) for u in users])

def send_email_otp(email, otp):
    
    app_password = "vwlxwehaqkcgzfpp"
    sender_email = "agrosmart.support@gmail.com"
    
    subject = _("Password Reset OTP")
    body = _("""Dear User,

We received a request to reset your password for your AgroSmart account.

To proceed with the password reset process, please use the One-Time Password (OTP) provided below:

🔐 OTP: %(otp)s

This OTP is valid for a limited time and should not be shared with anyone for security reasons.

If you did not request a password reset, please ignore this email. Your account will remain secure, and no changes will be made.

For your safety, we strongly recommend not sharing this OTP with anyone, including AgroSmart support staff.

If you face any issues or need further assistance, feel free to contact our support team.

Thank you for using AgroSmart.

Best regards,  
AgroSmart Support Team  
Email: agrosmart.support@gmail.com""", otp=otp)

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()

        print("OTP email sent successfully")

    except Exception as e:
        print("Error sending email:", e)


@password.route("/forgot-password", methods=["GET","POST"])
def forgot_password():

    if request.method == "POST":
        identifier = request.form.get("identifier")
        
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email=? OR phone=?",
            (identifier, identifier)
        ).fetchone()

        if not user:
            flash(_("User not found"), "error")
            return redirect(url_for("password.forgot_password"))

        otp = str(random.randint(100000,999999))
        session["otp_time"] = time.time()
        session["reset_otp"] = otp
        session["reset_user"] = user["id"]

        print("OTP:", otp)   # for testing

        if user["email"]:
            send_email_otp(user["email"], otp)
        else:
            flash(_("No email linked to this account"), "error")
            return redirect(url_for("password.forgot_password"))
        return redirect(url_for("password.verify_otp"))

    return render_template("forgot_password.html")


@password.route("/verify-otp", methods=["GET","POST"])
def verify_otp():

    if request.method == "POST":
        user_otp = request.form.get("otp")
        if time.time() - session.get("otp_time", 0) > 300:
            flash(_("OTP expired"), "error")
            return redirect(url_for("password.forgot_password"))
        if user_otp == session.get("reset_otp"):
            return redirect(url_for("password.reset_password"))
        else:
            flash(_("Invalid OTP"), "error")

    return render_template("verify_otp.html")

@password.route("/reset-password", methods=["GET","POST"])
def reset_password():

    if request.method == "POST":
        if "reset_user" not in session:
            flash(_("Unauthorized access"), "error")
            return redirect(url_for("password.forgot_password"))
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        
        if password != confirm:
            flash(_("Passwords do not match"), "error")
            return redirect(url_for("password.reset_password"))

        hashed = generate_password_hash(password)

        db = get_db()
        db.execute(
            "UPDATE users SET password_hash=? WHERE id=?",
            (hashed, session["reset_user"])
        )
        db.commit()

        session.pop("reset_otp", None)
        session.pop("reset_user", None)
        session.pop("otp_time", None)


        flash(_("Password updated successfully"), "success")

        return redirect(url_for("auth.login"))

    return render_template("reset_password.html")
