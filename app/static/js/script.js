// =====================
// 🔹 SAFE SELECTOR
// =====================
const $ = (id) => document.getElementById(id);


// =====================
// 🔹 TAB SWITCHING
// =====================
function showTab(tabName, element) {
    document.querySelectorAll('.content-card').forEach(card => {
        card.classList.remove('active');
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    const tab = $(tabName);
    if (tab) tab.classList.add('active');

    if (element) element.classList.add('active');
}


// =====================
// 🌦️ WEATHER + RAIN (COMMON API)
// =====================
async function fetchWeatherAndRain(city) {
    try {
        const apiKey = "295d8d37cb3270037c275c4ff236df63";

        // WEATHER
        const weatherRes = await fetch(
            `https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${apiKey}&units=metric`
        );

        const weatherData = await weatherRes.json();

        if (!weatherRes.ok) {
            alert("❌ " + weatherData.message);
            return null;
        }

        const { temp: temperature, humidity } = weatherData.main;
        const { lat, lon } = weatherData.coord;

        // DATE RANGE
        const today = new Date();
        const endDate = today.toISOString().split("T")[0];

        const pastDate = new Date();
        pastDate.setDate(today.getDate() - 30);
        const startDate = pastDate.toISOString().split("T")[0];

        // RAINFALL
        const rainRes = await fetch(
            `https://archive-api.open-meteo.com/v1/archive?latitude=${lat}&longitude=${lon}&start_date=${startDate}&end_date=${endDate}&daily=precipitation_sum&timezone=auto`
        );

        const rainData = await rainRes.json();

        let rainfall = 0;

        if (rainData?.daily?.precipitation_sum) {
            rainData.daily.precipitation_sum.forEach(r => rainfall += r);
        }

        return {
            temperature,
            humidity,
            rainfall: rainfall.toFixed(2)
        };

    } catch (error) {
        console.error(error);
        alert("⚠️ Failed to fetch weather");
        return null;
    }
}


// =====================
// 🌱 RECOMMEND WEATHER BUTTON
// =====================
const cityBtn = $('city-submit');

if (cityBtn) {
    cityBtn.addEventListener('click', async () => {
        const cityInput = $('city-input');

        if (!cityInput || !cityInput.value.trim()) {
            alert("Please enter a city");
            return;
        }

        const data = await fetchWeatherAndRain(cityInput.value.trim());
        if (!data) return;

        if ($('temperature-input')) $('temperature-input').value = data.temperature;
        if ($('humidity-input')) $('humidity-input').value = data.humidity;
        if ($('rainfall-input')) $('rainfall-input').value = data.rainfall;
    });
}


// =====================
// 🌾 YIELD WEATHER BUTTON
// =====================
const yieldBtn = $('yield-city-btn');

if (yieldBtn) {
    yieldBtn.addEventListener('click', async () => {
        const cityInput = $('yield-city');
        const rainEl = $('yield_rainfall');
        const tempEl = $('yield-temperature');

        if (!cityInput || !cityInput.value.trim()) {
            alert("Please enter a city");
            return;
        }

        const data = await fetchWeatherAndRain(cityInput.value.trim());
        if (!data) return;

        if (tempEl) tempEl.value = data.temperature;
        if (rainEl) rainEl.value = data.rainfall;
    });
}


// =====================
// 🌱 CROP RECOMMENDATION
// =====================
const recommendForm = $('recommendForm');

if (recommendForm) {
    recommendForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const data = Object.fromEntries(new FormData(e.target));

        $('recommendLoading')?.classList.add('show');
        $('recommendResults')?.classList.remove('show');

        try {
            const res = await fetch('/recommend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await res.json();

            displayRecommendations(
                result.predicted_crop,
                result.confidence
            );

        } catch (err) {
            console.error(err);
            alert("Error getting recommendations");
        } finally {
            $('recommendLoading')?.classList.remove('show');
        }
    });
}

function displayRecommendations(crop, confidence) {
    const container = $('recommendResults');
    const parentCard = document.querySelector('.content-card.active');

    if (!container) return;
    if (parentCard) parentCard.classList.add('results-shown');

    const getCropIcon = (crop) => {
        const icons = {
            'rice': '🌾', 'maize': '🌽', 'banana': '🍌',
            'mango': '🥭', 'coconut': '🥥', 'coffee': '☕'
        };
        return icons[crop?.toLowerCase()] || '🌱';
    };

    const icon = getCropIcon(crop);

    const html = `
        <div class="recommend-results-container fade-in">
            <div class="main-result-card">
                <div class="main-result-left">
                    <div class="crop-identity">
                        <div class="crop-icon-large">${icon}</div>
                        <div class="crop-info-text">
                            <h2 class="crop-name-main">${crop}</h2>
                            <span class="best-crop-badge">⭐ Best Crop</span>
                        </div>
                    </div>

                    <div class="progress-container">
                        <div class="progress-label">
                            <span>Confidence Level</span>
                            <span>${confidence}%</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" id="mainProgressBar" style="width: 0%"></div>
                        </div>
                    </div>
                </div>

                <div class="why-section">
                    <h4>Why this crop?</h4>
                    <ul class="why-list">
                        <li>✔ Suitable temperature conditions</li>
                        <li>✔ Soil nutrients match requirements</li>
                        <li>✔ Rainfall is in optimal range</li>
                    </ul>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;
    container.classList.add('show');

    setTimeout(() => {
        const bar = document.getElementById('mainProgressBar');
        if (bar) bar.style.width = confidence + '%';
    }, 100);
}

// =====================
// 🌾 YIELD PREDICTION
// =====================
// Helper shortcut

// Wait for DOM (important)
document.addEventListener("DOMContentLoaded", () => {

    const yieldForm = $('yieldForm');
    if (!yieldForm) return;

    // ✅ Use onsubmit (prevents multiple bindings)
    yieldForm.onsubmit = async (e) => {
        e.preventDefault();

        // ✅ HTML validation
        if (!yieldForm.checkValidity()) {
            yieldForm.reportValidity();
            return;
        }

        const btn = yieldForm.querySelector('button[type="submit"]');
        btn.disabled = true; // ✅ prevent multiple clicks

        const data = Object.fromEntries(new FormData(yieldForm));

        // ✅ Convert to numbers safely
        data.rainfall = parseFloat(data.rainfall) || 0;
        data.area = parseFloat(data.area) || 0;
        data.temperature = parseFloat(data.temperature) || 0;
        data.fertilizer = parseFloat(data.fertilizer) || 0;

        console.log("FINAL DATA:", data);

        $('yieldLoading')?.classList.add('show');
        $('yieldResults')?.classList.remove('show');

        try {
            const res = await fetch('/predict_yield', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await res.json();
            displayYieldPrediction(result, data);

        } catch (err) {
            console.error(err);
            alert("⚠️ Error predicting yield");
        }

        $('yieldLoading')?.classList.remove('show');
        btn.disabled = false; // ✅ re-enable button
    };
});


// ================= DISPLAY RESULT =================

function displayYieldPrediction(result, data) {
    const el = $('yieldResults');
    const parentCard = document.querySelector('.content-card.active');

    if (!el || !parentCard) return;

    // ❌ Error Handling
    if (result.error) {
        el.innerHTML = `
            <div class="error-msg fade-in" style="
                background: rgba(255,0,0,0.1);
                border: 1px solid red;
                padding: 20px;
                border-radius: 15px;
                color: #ff6b6b;
                text-align: center;
                margin-top: 20px;">
                ⚠️ ${result.error}
            </div>`;
        el.classList.add('show');
        return;
    }

    // ✅ Safe values
    const crop = data.crop || "Unknown Crop";
    const city = data.city || "Not Specified";
    const area = data.area || 0;
    const yieldVal = parseFloat(result.predicted_yield || 0);
    const confidence = result.confidence || 0;

    parentCard.classList.add('results-shown');

    // ✅ UI Rendering
    el.innerHTML = `
        <div class="yield-results-container fade-in">
            <div class="yield-result-card">

                <div class="yield-main-info">
                    <h2>🌾 ${crop}</h2>

                    <div class="yield-metric-box">
                        <div>Predicted Yield</div>
                        <div id="yieldNumber">0.00</div>
                        <div>tons per hectare</div>
                    </div>

                    <div>
                        📍 ${city} <br>
                        📐 ${area} Hectares
                    </div>

                    <div>
                        Confidence: ${confidence}%
                        <div style="background:#eee;height:10px;border-radius:10px;">
                            <div id="yieldProgressBar" style="
                                width:0%;
                                height:10px;
                                background:green;
                                border-radius:10px;">
                            </div>
                        </div>
                    </div>
                </div>

                <div>
                    <h4>💡 AI Insight</h4>
                    <ul>
                        <li>Based on current weather & inputs.</li>
                        <li>Conditions look favorable for ${crop}.</li>
                        <li>Better fertilizer use may increase yield.</li>
                    </ul>
                </div>

            </div>
        </div>
    `;

    el.classList.add('show');

    // ✅ Animate after render
    setTimeout(() => {
        const bar = document.getElementById('yieldProgressBar');
        if (bar) bar.style.width = confidence + '%';

        animateValue("yieldNumber", 0, yieldVal, 1500);
    }, 100);
}


// ================= ANIMATION =================

function animateValue(id, start, end, duration) {
    const obj = document.getElementById(id);
    if (!obj) return;

    let startTime = null;

    function step(timestamp) {
        if (!startTime) startTime = timestamp;

        const progress = Math.min((timestamp - startTime) / duration, 1);
        obj.innerHTML = (start + (end - start) * progress).toFixed(2);

        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }

    requestAnimationFrame(step);
}


// =====================
// 💰 PRICE PREDICTION
// =====================
const priceForm = $('priceForm');

if (priceForm) {
    priceForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);

        $('priceLoading')?.classList.add('show');
        $('priceResults')?.classList.remove('show');

        try {
            const res = await fetch('/predict_price', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await res.json();
            displayPricePrediction(result, data);

        } catch {
            alert("⚠️ Error predicting price");
        }

        $('priceLoading')?.classList.remove('show');
    });
}

function displayPricePrediction(result, data) {
    const el = $('priceResults');
    const parentCard = document.querySelector('.content-card.active');
    if (!el || !parentCard) return;

    if (result.error) {
        el.innerHTML = `<div class="error-msg fade-in" style="background: rgba(255,0,0,0.1); border: 1px solid red; padding: 20px; border-radius: 15px; color: #ff6b6b; text-align: center; margin-top: 20px;">
            <i class="fas fa-exclamation-triangle"></i> ${result.error}
        </div>`;
        el.classList.add('show');
        return;
    }

    // 🕶️ Apply Background Enhancement
    parentCard.classList.add('results-shown');

    const crop = data.crop || "Crop";
    const state = data.state || "State";
    const quantity = data.quantity || 0;
    const unit = result.unit || "₹/quintal";

    el.innerHTML = `
        <div class="price-results-container fade-in">
            <div class="price-main-card">
                <div class="price-header">
                    <div class="price-crop-icon">💰</div>
                    <div class="price-title-group">
                        <h2>${crop}</h2>
                        <span class="location-badge"><i class="fas fa-map-marker-alt"></i> ${state}</span>
                    </div>
                </div>

                <div class="price-grid">
                    <div class="price-stat-card main">
                        <label>Current Market Price</label>
                        <div class="price-val">₹<span id="currentPrice">0</span></div>
                        <span class="price-unit">per quintal</span>
                    </div>

                    <div class="price-stat-card total">
                        <label>Total Estimated Value</label>
                        <div class="price-val highlight">₹<span id="totalValue">0</span></div>
                        <span class="price-unit">for ${quantity} quintals</span>
                    </div>
                </div>

                <div class="price-forecast-section">
                    <h3><i class="fas fa-chart-line"></i> Future Price Forecast</h3>
                    <div class="forecast-grid">
                        <div class="forecast-item">
                            <span class="time">3 Months</span>
                            <span class="trend up"><i class="fas fa-arrow-up"></i> +5%</span>
                            <span class="f-price">₹${result.predicted_price_3m}</span>
                        </div>
                        <div class="forecast-item">
                            <span class="time">6 Months</span>
                            <span class="trend up"><i class="fas fa-arrow-up"></i> +10%</span>
                            <span class="f-price">₹${result.predicted_price_6m}</span>
                        </div>
                    </div>
                </div>

                <div class="price-action-footer">
                    <p><i class="fas fa-info-circle"></i> Prices are estimates based on historical market trends and seasonal patterns.</p>
                    <button class="btns" onclick="window.print()">Download Market Report</button>
                </div>
            </div>
        </div>
    `;

    el.classList.add('show');

    // 🚀 Start Animations
    setTimeout(() => {
        animateValue("currentPrice", 0, parseFloat(result.current_price), 1500);
        animateValue("totalValue", 0, parseFloat(result.total_value), 2000);
    }, 100);
}


// =====================
// 🔐 PASSWORD TOGGLE
// =====================
function togglePwd(id) {
    const field = $(id);
    if (field) {
        field.type = field.type === "password" ? "text" : "password";
    }
}


// =====================
// 📩 OTP
// =====================
function sendOTP() {
    const email = $('email')?.value || "";
    const phone = $('phone')?.value || "";

    if (!email && !phone) {
        alert("Enter Email or Phone");
        return;
    }

    fetch("/send_otp", {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, phone })
    })
        .then(res => res.json())
        .then(data => {
            alert(data.message);
            if ($('otp-field')) $('otp-field').style.display = "block";
        });
}


// =====================
// 🎬 PAGE LOAD ANIMATION
// =====================
window.addEventListener("load", () => {
    const guide = document.querySelector(".explain-guide");

    if (guide) {
        guide.classList.add("loaded");

        const steps = document.querySelectorAll(".step");

        steps.forEach((step, index) => {
            setTimeout(() => {
                step.classList.add("show");
            }, index * 200);
        });
    }
});