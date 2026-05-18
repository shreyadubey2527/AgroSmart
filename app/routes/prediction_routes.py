from flask import request,Blueprint,jsonify,render_template
from .auth_routes import login_required
from flask_babel import gettext as _
import pandas as pd
import os
import joblib
import requests
import math

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # goes to app/

recommend_model = joblib.load(os.path.join(BASE_DIR, "ml", "recommend_model.pkl"))
recommend_pipeline = joblib.load(os.path.join(BASE_DIR, "ml", "recommend_pipeline.pkl"))

yield_model = joblib.load(os.path.join(BASE_DIR, "ml", "yield_model.pkl"))
yeild_pipeline = joblib.load(os.path.join(BASE_DIR, "ml", "yeild_pipeline.pkl"))

price_model = joblib.load(os.path.join(BASE_DIR, "ml", "price_model.pkl"))
price_pipeline = joblib.load(os.path.join(BASE_DIR, "ml", "price_pipeline.pkl"))


predict = Blueprint("predict", __name__)

CROPS_DB = {
    "rice": {"temp_range": (20, 35), "humidity_range": (70, 90), "ph_range": (5.0, 7.0), "rainfall": (150, 300)},
    "maize": {"temp_range": (18, 27), "humidity_range": (60, 80), "ph_range": (5.5, 7.5), "rainfall": (50, 100)},
    "chickpea": {"temp_range": (18, 30), "humidity_range": (40, 60), "ph_range": (6.0, 7.5), "rainfall": (40, 90)},
    "kidneybeans": {"temp_range": (15, 30), "humidity_range": (50, 70), "ph_range": (5.5, 6.5), "rainfall": (60, 120)},
    "pigeonpeas": {"temp_range": (18, 35), "humidity_range": (50, 75), "ph_range": (5.5, 7.0), "rainfall": (60, 150)},
    "mothbeans": {"temp_range": (24, 32), "humidity_range": (40, 60), "ph_range": (6.0, 7.5), "rainfall": (30, 80)},
    "mungbean": {"temp_range": (25, 35), "humidity_range": (60, 80), "ph_range": (6.2, 7.2), "rainfall": (60, 120)},
    "blackgram": {"temp_range": (25, 35), "humidity_range": (60, 80), "ph_range": (6.0, 7.5), "rainfall": (60, 120)},
    "lentil": {"temp_range": (18, 30), "humidity_range": (40, 65), "ph_range": (6.0, 7.5), "rainfall": (40, 100)},
    "pomegranate": {"temp_range": (20, 35), "humidity_range": (50, 70), "ph_range": (5.5, 7.5), "rainfall": (50, 120)},
    "banana": {"temp_range": (26, 35), "humidity_range": (75, 90), "ph_range": (5.5, 7.5), "rainfall": (100, 250)},
    "mango": {"temp_range": (24, 35), "humidity_range": (50, 80), "ph_range": (5.5, 7.5), "rainfall": (75, 200)},
    "grapes": {"temp_range": (20, 30), "humidity_range": (50, 70), "ph_range": (6.0, 7.5), "rainfall": (50, 120)},
    "watermelon": {"temp_range": (24, 32), "humidity_range": (60, 80), "ph_range": (6.0, 7.5), "rainfall": (40, 100)},
    "muskmelon": {"temp_range": (24, 32), "humidity_range": (60, 80), "ph_range": (6.0, 7.5), "rainfall": (40, 100)},
    "apple": {"temp_range": (15, 24), "humidity_range": (60, 75), "ph_range": (5.5, 6.8), "rainfall": (100, 200)},
    "orange": {"temp_range": (20, 30), "humidity_range": (60, 80), "ph_range": (5.5, 7.5), "rainfall": (75, 150)},
    "papaya": {"temp_range": (25, 35), "humidity_range": (70, 90), "ph_range": (6.0, 7.5), "rainfall": (100, 200)},
    "coconut": {"temp_range": (25, 35), "humidity_range": (70, 90), "ph_range": (5.0, 8.0), "rainfall": (150, 300)},
    "cotton": {"temp_range": (21, 30), "humidity_range": (50, 80), "ph_range": (5.8, 8.0), "rainfall": (60, 120)},
    "jute": {"temp_range": (24, 37), "humidity_range": (70, 90), "ph_range": (6.0, 7.5), "rainfall": (150, 300)},
    "coffee": {"temp_range": (18, 28), "humidity_range": (60, 80), "ph_range": (6.0, 6.5), "rainfall": (150, 250)}
}

def safe_float(value):
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return 0.0
        return f
    except (TypeError, ValueError):
        return 0.0

def calculate_crop_score(crop_data, temp, humidity, ph, rainfall):
    """Calculate suitability score for a crop"""
    score = 0
    
    # Temperature score
    if crop_data['temp_range'][0] <= temp <= crop_data['temp_range'][1]:
        score += 25
    else:
        diff = min(abs(temp - crop_data['temp_range'][0]), abs(temp - crop_data['temp_range'][1]))
        score += max(0, 25 - diff * 2)
    
    # Humidity score
    if crop_data['humidity_range'][0] <= humidity <= crop_data['humidity_range'][1]:
        score += 25
    else:
        diff = min(abs(humidity - crop_data['humidity_range'][0]), abs(humidity - crop_data['humidity_range'][1]))
        score += max(0, 25 - diff * 0.5)
    
    # pH score
    if crop_data['ph_range'][0] <= ph <= crop_data['ph_range'][1]:
        score += 25
    else:
        diff = min(abs(ph - crop_data['ph_range'][0]), abs(ph - crop_data['ph_range'][1]))
        score += max(0, 25 - diff * 5)
    
    # Rainfall score
    if crop_data['rainfall'][0] <= rainfall <= crop_data['rainfall'][1]:
        score += 25
    else:
        diff = min(abs(rainfall - crop_data['rainfall'][0]), abs(rainfall - crop_data['rainfall'][1]))
        score += max(0, 25 - diff * 0.2)
    
    return round(score, 2)

def explain_crop_choice(crop_name, crop_data, temp, humidity, ph, rainfall):

    reasons = []

    if crop_data["temp_range"][0] <= temp <= crop_data["temp_range"][1]:
        reasons.append(_("Temperature is ideal"))

    if crop_data["humidity_range"][0] <= humidity <= crop_data["humidity_range"][1]:
        reasons.append(_("Humidity is suitable"))

    if crop_data["ph_range"][0] <= ph <= crop_data["ph_range"][1]:
        reasons.append(_("Soil pH is optimal"))

    if crop_data["rainfall"][0] <= rainfall <= crop_data["rainfall"][1]:
        reasons.append(_("Rainfall conditions are favorable"))

    return reasons

@predict.route('/recommend', methods=['POST'])
@login_required
def recommend_crop():
    try:
        data = request.get_json(silent=True) or request.form.to_dict()
        print("Incoming Data:", data)

        def safe_float(val):
            try:
                return float(val)
            except:
                return 0.0

        temp = safe_float(data.get('temperature'))
        humidity = safe_float(data.get('humidity'))
        ph = safe_float(data.get('ph'))
        rainfall = safe_float(data.get('rainfall'))
        nitrogen = safe_float(data.get('nitrogen'))
        phosphorus = safe_float(data.get('phosphorus'))
        potassium = safe_float(data.get('potassium'))

        features = pd.DataFrame([{
            "N": nitrogen,
            "P": phosphorus,
            "K": potassium,
            "temperature": temp,
            "humidity": humidity,
            "ph": ph,
            "rainfall": rainfall
        }])

        transformed = recommend_pipeline.transform(features)
        prediction = recommend_model.predict(transformed)
        ml_crop = prediction[0]

        prob = recommend_model.predict_proba(transformed)
        confidence = round(max(prob[0]) * 100, 2)

        # ✅ RETURN ONLY MAIN RESULT
        return jsonify({
            "predicted_crop": ml_crop.capitalize(),
            "confidence": confidence
        })

    except Exception as e:
        print("🚨 Recommendation Error:", str(e))
        return jsonify({"error": str(e)}), 500



@predict.route('/predict_yield', methods=['POST'])
@login_required
def predict_yield():
    try:
        # 📥 Get data (JSON first, fallback to form)
        data = request.get_json(silent=True) or request.form.to_dict()
        print("Incoming Data:", data)

        # 🛠️ Extract and normalize text fields
        crop = str(data.get('crop', '')).strip().lower()
        season = str(data.get('season', '')).strip().lower()

        # ❌ Validate required text fields
        if not crop or not season:
            return jsonify({
                'error': "Crop and season are required",
                'predicted_yield': "0.00",
                'confidence': 0
            }), 400

        # 🔢 Safe numeric conversion
        def safe_float(val):
            try:
                return float(val)
            except (TypeError, ValueError):
                return 0.0

        area = safe_float(data.get('area'))
        rainfall = safe_float(data.get('rainfall'))
        temperature = safe_float(data.get('temperature'))
        fertilizer_rate = safe_float(data.get('fertilizer'))

        print("Processed Values:", area, rainfall, temperature, fertilizer_rate)

        # ❌ Validate numeric values (AFTER conversion)
        if area <= 0:
            return jsonify({'error': "Area must be greater than 0"}), 400

        if rainfall <= 0:
            return jsonify({'error': "Rainfall must be greater than 0"}), 400

        if temperature <= 0:
            return jsonify({'error': "Temperature must be valid"}), 400

        if fertilizer_rate < 0:
            return jsonify({'error': "Fertilizer must be valid"}), 400

        # 🧮 Unit conversion (kg/ha → total tonnes)
        total_fertilizer = (fertilizer_rate * area) / 1000

        # 📊 Prepare model input
        input_df = pd.DataFrame([{
            "Crop": crop,
            "Season": season,
            "Area": area,
            "Fertilizer": total_fertilizer,
            "Temperature": temperature,
            "rainfall": rainfall
        }])

        # 🤖 Prediction
        processed = yeild_pipeline.transform(input_df)
        prediction = yield_model.predict(processed)[0]

        # 🔁 Convert output (Quintals → Tonnes)
        predicted_yield_tonnes = max(0, float(prediction) / 10.0)

        # ✅ Success response
        return jsonify({
            'predicted_yield': round(predicted_yield_tonnes, 2),
            'unit': 'tons per hectare',
            'confidence': 90
        })

    except Exception as e:
        print("🚨 Prediction Error:", str(e))
        return jsonify({
            'error': f"Prediction error: {str(e)}",
            'predicted_yield': "0.00",
            'confidence': 0
        }), 500
@predict.route('/predict_price', methods=['POST'])
@login_required
def predict_price():
    try:
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict()

        print("Incoming Data:", data)

        state = str(data.get('state', '')).strip().lower()
        crop = str(data.get('crop', '')).strip().lower()
        quantity = safe_float(data.get('quantity'))
        
        if quantity <= 0:
            return jsonify({"error": _("Quantity must be greater than 0")}), 400

        # Prepare input
        input_df = pd.DataFrame({
            "State": [state],
            "Commodity": [crop]
        })

        # Transform
        X_prepared = price_pipeline.transform(input_df)

        # Predict price per ton
        price_per_unit = price_model.predict(X_prepared)[0]

        # Total price
        total_value = price_per_unit * quantity

        return jsonify({
            'current_price': round(price_per_unit, 2),   # JS expects this key
            'predicted_price_3m': round(price_per_unit * 1.05, 2),  # example 5% increase
            'predicted_price_6m': round(price_per_unit * 1.10, 2),  # example 10% increase
            'total_value': round(total_value, 2),
            'unit': _('₹/quintal')
        })

    except Exception as e:
        print("🚨 Price Prediction Error:", str(e))
        return jsonify({"error": str(e)}), 500



# apiKey = "295d8d37cb3270037c275c4ff236df63"
# @predict.route('/weather', methods=['GET'])
# def get_weather():
#     city = request.args.get('city')

#     # ✅ Check city input
#     if not city:
#         return jsonify({"error": "City is required"}), 400

#     try:
#         # ✅ API URL
#         url = "https://api.openweathermap.org/data/2.5/weather"
#         params = {
#             "q": city,
#             "appid": apiKey,
#             "units": "metric"
#         }

#         response = requests.get(url, params=params)
#         data = response.json()

#         # ❌ Invalid city / API error
#         if response.status_code != 200:
#             return jsonify({
#                 "error": data.get("message", "City not found")
#             }), 404

#         # ✅ Safe data extraction
#         temperature = data.get('main', {}).get('temp', 0)
#         humidity = data.get('main', {}).get('humidity', 0)
#         rainfall = data.get('rain', {}).get('1h', 0)

#         # Optional extra data
#         weather_desc = data.get('weather', [{}])[0].get('description', "clear")

#         return jsonify({
#             "city": city.title(),
#             "temperature": round(temperature, 1),
#             "humidity": humidity,
#             "rainfall": rainfall,
#             "description": weather_desc
#         })

#     except requests.exceptions.RequestException:
#         return jsonify({"error": "Weather API not reachable"}), 500

#     except Exception as e:
#         print("ERROR:", e)
#         return jsonify({"error": "Server error"}), 500

apiKey = "295d8d37cb3270037c275c4ff236df63"
@predict.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')

    # ✅ Check city input
    if not city:
        return jsonify({"error": "City is required"}), 400

    try:
        # ✅ API URL
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": apiKey,
            "units": "metric"
        }

        response = requests.get(url, params=params)
        data = response.json()

        # ❌ Invalid city / API error
        if response.status_code != 200:
            return jsonify({
                "error": data.get("message", "City not found")
            }), 404

        # ✅ Safe data extraction
        main_data = data.get('main') or {}
        rain_data = data.get('rain') or {}
        
        temperature = safe_float(main_data.get('temp'))
        humidity = safe_float(main_data.get('humidity'))
        rainfall = safe_float(rain_data.get('1h'))

        # Optional extra data
        weather_desc = data.get('weather', [{}])[0].get('description', "clear")

        return jsonify({
            "city": city.title(),
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "rainfall": round(rainfall, 1),
            "description": weather_desc
        })

    except requests.exceptions.RequestException:
        return jsonify({"error": "Weather API not reachable"}), 500

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": "Server error"}), 500