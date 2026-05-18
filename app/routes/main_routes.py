from flask import request,flash,redirect,url_for,render_template,Blueprint,session
from ..models.db import get_db
from flask_babel import _, get_locale, lazy_gettext as _l
from .auth_routes import login_required
main = Blueprint("main", __name__)

FAQS = [
    {"q": _l("How does the crop recommendation feature work?"), "a": _l("It uses inputs like temperature, humidity, soil pH, rainfall, and nutrients (Nitrogen, Phosphorus, Potassium) to suggest the most suitable crops using machine learning models.")},
    {"q": _l("How accurate are the predictions?"), "a": _l("AgroSmart provides highly accurate predictions based on trained datasets, but results may vary due to changing weather and field conditions.")},
    {"q": _l("Can AgroSmart predict crop prices?"), "a": _l("Yes, AgroSmart analyzes historical data and market trends to provide estimated crop price predictions.")},
    {"q": _l("Can I use AgroSmart on my mobile phone?"), "a": _l("Yes, AgroSmart is fully responsive and works smoothly on mobile phones, tablets, and desktops.")},
    {"q": _l("How can I contact support?"), "a": _l("You can use the contact form available on the Support page to reach out to the AgroSmart support team.")},
    {"q": _l("What should I do if I get incorrect results?"), "a": _l("Ensure that you have entered correct and realistic data. If the issue persists, contact support for help.")},
]
@main.route("/contact-form", methods=["POST"])
def contact_form():

    name = request.form.get("name")
    email = request.form.get("email")
    subject = request.form.get("subject")
    message = request.form.get("message")

    db = get_db()

    db.execute(
        "INSERT INTO contact (name, email, subject, message) VALUES (?, ?, ?, ?)",
        (name, email, subject, message)
    )

    db.commit()

    flash(_("Message sent successfully! ✅"))
    return redirect(url_for("main.contact"))

@main.route('/')
def index():
    print("Current locale:", get_locale())
    return render_template('home.html')

@main.route("/about")
def about():
    return render_template('about.html')
@main.route("/support")
def support():
    return render_template('support.html',faqs=FAQS)


@main.route("/contact")
def contact():
    return render_template('contact.html')

@main.route('/weather_page')
def weather_page():
    return render_template('weather.html')

@main.route('/settings')
@login_required
def settings():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    return render_template('setting.html', user=user)

@main.route('/save_profile', methods=['POST'])
@login_required
def save_profile():
    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip().lower()

    if not full_name or not phone or not email:
        flash(_("All fields are required!"), "error")
        return redirect(url_for("main.settings"))

    if not phone.isdigit() or len(phone) != 10:
        flash(_("Phone number must be 10 digits!"), "error")
        return redirect(url_for("main.settings"))

    db = get_db()
    try:
        db.execute(
            "UPDATE users SET full_name = ?, phone = ?, email = ? WHERE id = ?",
            (full_name, phone, email, session["user_id"])
        )
        db.commit()
        session["user_name"] = full_name
        session["user_email"] = email
        flash(_("Profile updated successfully! ✅"), "success")
    except Exception as e:
        db.rollback()
        flash(_("Error updating profile. Email or phone might already be in use."), "error")
    
    return redirect(url_for("main.settings"))

@main.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['en', 'hi', 'mr']:
        session['lang'] = lang
        flash(_("Language changed successfully!"), "success")
    return redirect(request.referrer or url_for('main.index'))

@main.route('/nutrient_concept')
def nutrient_concept():
    return render_template('nutrient_concept.html')

@main.route("/sustainable_guide")
def sustainable_guide():
    return render_template('sustainable.html')

@main.route("/soil_science")
def soil_science():
    return render_template('soil_science.html')

@main.route("/crop_growth")
def crop_growth():
    return render_template('crop_growth.html')

@main.route('/water_management')
def water_management():
    return render_template('water_management.html')

@main.route('/climate')
def climate():
    return render_template('climate.html')

@main.route('/schemes')
def schemes():
    return render_template('schemes.html')