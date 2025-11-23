document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('city-search');
    const searchBtn = document.getElementById('search-btn');
    const resultsGrid = document.getElementById('results-grid');
    const loading = document.getElementById('loading');
    const errorMsg = document.getElementById('error-msg');

    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            const city = searchInput.value.trim();
            if (city) {
                fetchAQI(city);
            }
        });

        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const city = searchInput.value.trim();
                if (city) {
                    fetchAQI(city);
                }
            }
        });
    }

    async function fetchAQI(city) {
        loading.style.display = 'block';
        errorMsg.style.display = 'none';
        resultsGrid.innerHTML = '';

        // Remove previous timestamp if exists
        const prevTimestamp = document.querySelector('[data-timestamp]');
        if (prevTimestamp) prevTimestamp.remove();

        try {
            const response = await fetch(`/proxy/openaq/?city=${encodeURIComponent(city)}`);
            const data = await response.json();

            loading.style.display = 'none';

            if (data.results && data.results.length > 0) {
                // Display timestamp
                const now = new Date();
                const timeString = now.toLocaleString('en-IN', {
                    dateStyle: 'medium',
                    timeStyle: 'short'
                });
                const timestampDiv = document.createElement('div');
                timestampDiv.setAttribute('data-timestamp', 'true');
                timestampDiv.style.cssText = 'text-align: center; color: #94a3b8; margin: 1rem 0; font-size: 0.9rem;';
                timestampDiv.textContent = `Searched "${city}" at ${timeString}`;
                resultsGrid.parentElement.insertBefore(timestampDiv, resultsGrid);

                displayResults(data.results);
            } else {
                errorMsg.textContent = `No data found for "${city}". Try a different city name.`;
                errorMsg.style.display = 'block';
            }
        } catch (error) {
            console.error('Error fetching AQI:', error);
            loading.style.display = 'none';
            errorMsg.textContent = 'Failed to fetch data. Please try again later.';
            errorMsg.style.display = 'block';
        }
    }

    function getHealthTip(aqi) {
        if (aqi <= 50) {
            return { text: "Great day to go outside!", color: "#10b981" };
        } else if (aqi <= 100) {
            return { text: "Air quality is acceptable for most people.", color: "#f59e0b" };
        } else if (aqi <= 150) {
            return { text: "Sensitive groups should limit outdoor activity.", color: "#f59e0b" };
        } else if (aqi <= 200) {
            return { text: "Everyone should reduce prolonged outdoor exertion.", color: "#ef4444" };
        } else if (aqi <= 300) {
            return { text: "⚠️ Wear a mask if going outside. Avoid outdoor activities.", color: "#ef4444" };
        } else {
            return { text: "🚨 Stay indoors. Wear N95 mask if you must go out.", color: "#dc2626" };
        }
    }

    function displayResults(locations) {
        locations.forEach(location => {
            const card = document.createElement('div');
            card.className = 'aqi-card';

            const pm25 = location.measurements.find(m => m.parameter === 'pm25');
            const pm10 = location.measurements.find(m => m.parameter === 'pm10');
            const usAqi = location.measurements.find(m => m.parameter === 'us_aqi');

            let aqiValue = 0;
            let aqiStatus = 'Unknown';
            let aqiClass = '';

            if (usAqi && usAqi.value) {
                aqiValue = Math.round(usAqi.value);
            } else if (pm25) {
                aqiValue = calculateAQI(pm25.value);
            }

            if (aqiValue > 0) {
                if (aqiValue <= 50) { aqiStatus = 'Good'; aqiClass = 'aqi-good'; }
                else if (aqiValue <= 100) { aqiStatus = 'Moderate'; aqiClass = 'aqi-moderate'; }
                else if (aqiValue <= 150) { aqiStatus = 'Unhealthy for Sensitive Groups'; aqiClass = 'aqi-moderate'; }
                else if (aqiValue <= 200) { aqiStatus = 'Unhealthy'; aqiClass = 'aqi-poor'; }
                else if (aqiValue <= 300) { aqiStatus = 'Very Unhealthy'; aqiClass = 'aqi-poor'; }
                else { aqiStatus = 'Hazardous'; aqiClass = 'aqi-poor'; }
            }

            const healthTip = getHealthTip(aqiValue);

            card.innerHTML = `
                <div class="card-header">
                    <div>
                        <div class="city-name">${location.location}</div>
                        <div style="font-size: 0.9rem; color: #94a3b8;">${location.city}, ${location.country}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 2rem; font-weight: 700; color: var(--primary-color);">${aqiValue}</div>
                        <span class="aqi-badge ${aqiClass}">${aqiStatus}</span>
                    </div>
                </div>
                <div class="measurements">
                    <div class="measurement-item">
                        <span class="m-label">AQI</span>
                        <span class="m-value">${aqiValue > 0 ? aqiValue : 'N/A'}</span>
                    </div>
                    <div class="measurement-item">
                        <span class="m-label">PM2.5</span>
                        <span class="m-value">${pm25 ? pm25.value + ' ' + pm25.unit : 'N/A'}</span>
                    </div>
                    <div class="measurement-item">
                        <span class="m-label">PM10</span>
                        <span class="m-value">${pm10 ? pm10.value + ' ' + pm10.unit : 'N/A'}</span>
                    </div>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 0.75rem; border-radius: 8px; margin-top: 1rem; border-left: 3px solid ${healthTip.color};">
                    <div style="font-size: 0.85rem; color: ${healthTip.color}; font-weight: 500;">${healthTip.text}</div>
                </div>
                <button class="btn-primary btn-block" style="margin-top: 1rem; font-size: 0.9rem;" onclick="showSubscribeModal('${location.city}')">
                    Subscribe to Daily Updates
                </button>
            `;
            resultsGrid.appendChild(card);
        });
    }

    function calculateAQI(pm25) {
        const breakpoints = [
            { cLow: 0.0, cHigh: 12.0, iLow: 0, iHigh: 50 },
            { cLow: 12.1, cHigh: 35.4, iLow: 51, iHigh: 100 },
            { cLow: 35.5, cHigh: 55.4, iLow: 101, iHigh: 150 },
            { cLow: 55.5, cHigh: 150.4, iLow: 151, iHigh: 200 },
            { cLow: 150.5, cHigh: 250.4, iLow: 201, iHigh: 300 },
            { cLow: 250.5, cHigh: 500.4, iLow: 301, iHigh: 500 }
        ];

        for (let bp of breakpoints) {
            if (pm25 >= bp.cLow && pm25 <= bp.cHigh) {
                const aqi = ((bp.iHigh - bp.iLow) / (bp.cHigh - bp.cLow)) * (pm25 - bp.cLow) + bp.iLow;
                return Math.round(aqi);
            }
        }
        return 500;
    }
});

// Subscription modal
window.showSubscribeModal = function (city) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.7); display: flex; align-items: center;
        justify-content: center; z-index: 1000;
    `;

    modal.innerHTML = `
        <div style="background: #1e293b; padding: 2rem; border-radius: 12px; max-width: 400px; width: 90%;">
            <h2 style="margin: 0 0 1rem 0; color: var(--primary-color);">Subscribe to Daily Updates</h2>
            <p style="color: #94a3b8; margin-bottom: 1.5rem;">Get daily air quality updates for ${city} in your inbox.</p>
            <input type="email" id="subscribe-email" placeholder="Enter your email" 
                style="width: 100%; padding: 0.75rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); 
                background: rgba(255,255,255,0.05); color: white; margin-bottom: 1rem; font-size: 1rem;">
            <div style="display: flex; gap: 0.5rem;">
                <button onclick="closeModal()" style="flex: 1; padding: 0.75rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); 
                    background: transparent; color: white; cursor: pointer;">Cancel</button>
                <button onclick="submitSubscription('${city}')" class="btn-primary" style="flex: 1; padding: 0.75rem;">Subscribe</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    modal.onclick = (e) => { if (e.target === modal) closeModal(); };
};

window.closeModal = function () {
    const modal = document.querySelector('div[style*="z-index: 1000"]');
    if (modal) modal.remove();
};

window.submitSubscription = async function (city) {
    const email = document.getElementById('subscribe-email').value.trim();

    if (!email) {
        alert('Please enter your email');
        return;
    }

    if (!email.includes('@')) {
        alert('Please enter a valid email');
        return;
    }

    try {
        const response = await fetch('/subscribe/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ email, city })
        });

        const data = await response.json();

        if (data.status === 'success') {
            alert(`✅ ${data.message}\n\nYou'll receive daily AQI updates for ${city} at ${email}`);
            closeModal();
        } else {
            alert('Subscription failed: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to subscribe. Please try again.');
    }
};

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
