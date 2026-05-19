from flask import request,flash,redirect,url_for,render_template,Blueprint,session,jsonify
from flask_babel import gettext as _
import re
import random
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import requests
from ..models.db import get_db

auth = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def validate_registration(form):
    errors = []
    full_name = form.get("full_name", "").strip()
    email     = form.get("email", "").strip().lower()
    password  = form.get("password", "")
    confirm   = form.get("confirm_password", "")

    if len(full_name) < 2:
        errors.append(_("Full name must be at least 2 characters."))
    if email and not EMAIL_RE.match(email):
        errors.append(_("Please enter a valid email address."))
    if len(password) < 8:
        errors.append(_("Password must be at least 8 characters."))
    if password != confirm:
        errors.append(_("Passwords do not match."))
    return errors


# ── Auth decorator ─────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash(_("Please sign in to access that page."), "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


@auth.route("/send_otp", methods=["POST"])
def send_otp():
    data = request.get_json()

    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()

    if not email and not phone:
        return jsonify({"success": False, "message": str(_("Email or phone required"))}), 400

    # Generate OTP
    otp = str(random.randint(100000, 999999))
    print("Generated OTP:", otp)

    # Store in session
    session["otp"] = otp
    session["otp_email"] = email
    session["otp_phone"] = phone

    # Send Email
    if email:
        try:
            # We use Brevo (Sendinblue) API to bypass Render's SMTP block
            brevo_api_key = os.environ.get("BREVO_API_KEY")
            
            if not brevo_api_key:
                print("EMAIL ERROR: BREVO_API_KEY is not set in environment variables.")
                return jsonify({"success": False, "message": "Email service is not configured. Please add BREVO_API_KEY."}), 500

            subject = _("AgroSmart - OTP Verification")

            body = _("""Dear User,

We received a request to verify your identity for your AgroSmart account.

Please use the One-Time Password (OTP) below to proceed:

🔐 OTP: %(otp)s

This OTP is valid for a limited time and should not be shared with anyone for security reasons.

If you did not request this OTP, please ignore this email. Your account will remain safe and no action will be taken.

For security purposes, AgroSmart will never ask for your OTP via phone or message.

If you need any assistance, feel free to contact our support team.

Thank you for choosing AgroSmart.

Best regards,  
AgroSmart Support Team  
Email: agrosmart.support@gmail.com""", otp=otp)

            headers = {
                "accept": "application/json",
                "api-key": brevo_api_key,
                "content-type": "application/json"
            }
            
            payload = {
                "sender": {"name": "AgroSmart Support", "email": "agrosmart.support@gmail.com"},
                "to": [{"email": email}],
                "subject": subject,
                "textContent": body
            }

            response = requests.post("https://api.brevo.com/v3/smtp/email", headers=headers, json=payload, timeout=10)
            
            if response.status_code >= 400:
                print(f"Brevo API Error: {response.status_code} - {response.text}")
                return jsonify({"success": False, "message": "Failed to send OTP via email service."}), 500

            print("Email sent successfully via Brevo API")

        except Exception as e:
            print("EMAIL ERROR:", repr(e))
            return jsonify({"success": False, "message": str(e)}), 500

    elif not email and phone:
        return jsonify({"success": False, "message": str(_("Only Email OTP is currently supported."))}), 400

    return jsonify({"success": True, "message": str(_("OTP sent successfully"))})

@auth.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":
        identifier  = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email = ? OR phone=?",
            (identifier ,identifier ,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["full_name"]
            session["user_email"] = user["email"]


            flash(_("Welcome back, %(name)s! 🌱", name=user['full_name'].split()[0]), "success")
            return redirect(url_for("auth.dashboard"))
        else:
            flash(_("Invalid email or password."), "error")

    return render_template("login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():


    if "user_id" in session:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":

        errors = validate_registration(request.form)

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("register.html", form=request.form)

        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip().lower()
        phone = request.form["phone"].strip()

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        otp = request.form.get("otp")

        # At least one required
        if not email and not phone:
            flash("Please enter email or phone number.", "error")
            return render_template("register.html", form=request.form)

        # Password check
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html", form=request.form)

        # OTP verification
        if otp != session.get("otp"):
            flash("Invalid or expired OTP.", "error")
            return render_template("register.html", form=request.form)

        # Check OTP matches email/phone used
        if email != session.get("otp_email") or phone != session.get("otp_phone"):
            flash("OTP not requested for this email or phone.", "error")
            return render_template("register.html", form=request.form)

        db = get_db()

        # Check if email already exists
        if email:
            existing_email = db.execute(
                "SELECT id FROM users WHERE email = ?",
                (email,)
            ).fetchone()

            if existing_email:
                flash("An account with this email already exists.", "error")
                return render_template("register.html", form=request.form)

        # Check if phone already exists
        if phone:
            existing_phone = db.execute(
                "SELECT id FROM users WHERE phone = ?",
                (phone,)
            ).fetchone()

            if existing_phone:
                flash("An account with this phone number already exists.", "error")
                return render_template("register.html", form=request.form)

        # Hash password
        pw_hash = generate_password_hash(password)

        db.execute("""
            INSERT INTO users (full_name, email, phone, password_hash)
            VALUES (?, ?, ?, ?)
        """, (full_name, email or None, phone or None, pw_hash))

        db.commit()

        # Clear OTP session
        session.pop("otp", None)
        session.pop("otp_email", None)
        session.pop("otp_phone", None)

        flash("Account created successfully! Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form={})



@auth.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    return render_template("dashboard.html", user=user)



@auth.route("/logout")
@login_required
def logout():
    session.clear()
    flash(_("You've been signed out. See you soon! 🌿"), "info")
    return redirect(url_for("auth.login"))
