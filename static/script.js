document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('rsvpForm');
    const submitBtn = document.getElementById('submitBtn');
    const messageDiv = document.getElementById('message');
    const departureInfo = document.getElementById('departureInfo');
    const dietarySelect = document.getElementById('dietary_option');
    // Legacy special dietary elements removed from DOM; keep variables null-safe
    const specialDietaryGroup = null;
    const specialDietaryInput = null;

    // Load flight configuration
    loadFlightConfig();
    
    // No dynamic special dietary field now

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form data (no longer including event_date)
        const formData = new FormData(form);
        const data = {
            email: formData.get('email'),
            dietary_option: formData.get('dietary_option')
        };
        
        // No special dietary free-text for new bento choices

        // Validate passenger information
        if (!data.email || !data.dietary_option) {
            showMessage('🚨 Please complete all passenger information fields before boarding.', 'error');
            return;
        }

        // Validate email format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(data.email)) {
            showMessage('✉️ Please provide a valid email address for your booking confirmation.', 'error');
            return;
        }

        // Disable submit button and show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="btn-text">✈️ Processing Booking...</span>';

        try {
            const response = await fetch('/api/rsvp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                showMessage('🎉 Boarding pass confirmed! Your flight reservation has been successfully processed.', 'success');
                form.reset();
                
                // Display boarding pass if provided
                if (result.boarding_pass) {
                    displayBoardingPass(result.boarding_pass);
                }
            } else {
                showMessage('❌ Booking Error: ' + (result.error || 'We encountered an issue processing your reservation. Please try again or contact Azalea Air customer service.'), 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showMessage('🌐 Connection Error: Unable to connect to Azalea Air booking system. Please check your internet connection and try again.', 'error');
        } finally {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span class="btn-text">🎫 Complete Booking</span>';
        }
    });

    function showMessage(text, type) {
        messageDiv.textContent = text;
        messageDiv.className = `message ${type}`;
        messageDiv.style.display = 'block';
        
        // Hide message after 5 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        }
        
        // Only scroll to message if it's not visible in viewport (gentler approach)
        const messageRect = messageDiv.getBoundingClientRect();
        const isVisible = messageRect.top >= 0 && messageRect.bottom <= window.innerHeight;
        
        if (!isVisible) {
            messageDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    async function loadFlightConfig() {
        try {
            const response = await fetch('/api/flight-config');
            const config = await response.json();

            if (response.ok && config.configured) {
                // Display flight information
                departureInfo.innerHTML = `
                    <div class="departure-date">${config.departure_date}</div>
                    <div class="departure-formatted">${config.formatted_date}</div>
                    <div class="flight-info">Flight ${config.flight_number} to ${config.destination}</div>
                `;
            } else {
                // Show error message
                departureInfo.innerHTML = `
                    <div style="color: #721c24; font-weight: bold;">
                        ⚠️ Flight information not available
                    </div>
                `;
                // Disable form
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="btn-text">❌ Booking Unavailable</span>';
            }
        } catch (error) {
            console.error('Error loading flight config:', error);
            departureInfo.innerHTML = `
                <div style="color: #721c24; font-weight: bold;">
                    🌐 Unable to load flight information
                </div>
            `;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="btn-text">❌ Connection Error</span>';
        }
    }

    // Boarding Pass Functions
    function displayBoardingPass(boardingPass) {
        // Populate boarding pass data
        document.getElementById('confirmationCode').textContent = boardingPass.confirmation_code;
        document.getElementById('flightNumber').textContent = boardingPass.flight_number;
        document.getElementById('destination').textContent = boardingPass.destination;
        document.getElementById('departureTime').textContent = boardingPass.departure_time;
        document.getElementById('gate').textContent = boardingPass.gate;
        document.getElementById('seatNumber').textContent = boardingPass.seat_number;
        document.getElementById('boardingTime').textContent = boardingPass.boarding_time;
        document.getElementById('passengerEmail').textContent = boardingPass.passenger_email;
        document.getElementById('departureDate').textContent = boardingPass.formatted_departure;
        
        // Format meal preference
        const mealOptions = {
            'shrimp-aglio-olio': '🍤 Shrimp Linguine Aglio Olio',
            'creamy-chicken-pomodoro': '🍗 Creamy Chicken Pomodoro',
            'carbonara-funghi': '🍄 Carbonara al Funghi (V)',
            // legacy fallback labels
            'none': '🍽️ Standard Meal Service',
            'vegetarian': '🥗 Vegetarian Meal (VGML)',
            'vegan': '🌱 Vegan Meal (VEGN)',
            'gluten-free': '🌾 Gluten-Free Meal (GFML)',
            'dairy-free': '🥛 Dairy-Free Meal (DFML)',
            'nut-free': '🥜 Nut-Free Meal (NFML)',
            'other': '👨‍🍳 Special Dietary Request'
        };
        
        let mealText = mealOptions[boardingPass.meal_preference] || boardingPass.meal_preference;
        if (boardingPass.meal_preference === 'other' && boardingPass.special_dietary_details) {
            mealText += `: ${boardingPass.special_dietary_details}`;
        }
        document.getElementById('mealPreference').textContent = mealText;
        
        // Generate barcode-like pattern
        const barcodePattern = generateBarcode(boardingPass.confirmation_code);
        document.getElementById('barcode').textContent = barcodePattern;
        
        // Show modal
        document.getElementById('boardingPassModal').style.display = 'block';
    }

    function generateBarcode(confirmationCode) {
        // Generate a simple barcode-like pattern based on confirmation code
        let barcode = '';
        for (let i = 0; i < confirmationCode.length; i++) {
            const char = confirmationCode.charCodeAt(i);
            const pattern = char % 5;
            switch (pattern) {
                case 0: barcode += '||||| '; break;
                case 1: barcode += '|||| '; break;
                case 2: barcode += '||||| |'; break;
                case 3: barcode += '|| |||'; break;
                case 4: barcode += '| ||||'; break;
            }
        }
        return barcode.trim();
    }

    // Boarding pass event handlers
    document.getElementById('closeBoardingPass').addEventListener('click', function() {
        document.getElementById('boardingPassModal').style.display = 'none';
    });

    document.getElementById('printBoardingPass').addEventListener('click', function() {
        window.print();
    });

    // Close modal when clicking outside
    document.getElementById('boardingPassModal').addEventListener('click', function(e) {
        if (e.target === this) {
            this.style.display = 'none';
        }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.getElementById('boardingPassModal').style.display = 'none';
        }
    });
});