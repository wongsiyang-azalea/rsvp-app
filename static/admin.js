document.addEventListener('DOMContentLoaded', function() {
    const refreshBtn = document.getElementById('refreshBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const loadingDiv = document.getElementById('loading');
    const rsvpListDiv = document.getElementById('rsvpList');
    const noDataDiv = document.getElementById('noData');
    const summarySection = document.getElementById('summarySection');
    const summaryContent = document.getElementById('summaryContent');

    // Load RSVPs on page load
    loadRSVPs();
    loadSummary();

    // Refresh button click handler
    refreshBtn.addEventListener('click', function() {
        loadRSVPs();
        loadSummary();
    });

    // Download button click handler
    downloadBtn.addEventListener('click', function() {
        downloadManifest();
    });

    async function loadRSVPs() {
        // Show loading state
        loadingDiv.style.display = 'block';
        rsvpListDiv.innerHTML = '';
        noDataDiv.style.display = 'none';
        refreshBtn.disabled = true;
        refreshBtn.textContent = '📡 Loading Manifest...';

        try {
            const response = await fetch('/api/rsvp');
            const rsvps = await response.json();

            if (response.ok) {
                displayRSVPs(rsvps);
            } else {
                console.error('Error loading passenger manifest:', rsvps.error);
                rsvpListDiv.innerHTML = '<div class="error-message">❌ Error loading passenger manifest. Please try again.</div>';
            }
        } catch (error) {
            console.error('Error:', error);
            rsvpListDiv.innerHTML = '<div class="error-message">🌐 Connection Error: Unable to load passenger manifest. Please check your connection and try again.</div>';
        } finally {
            // Hide loading state
            loadingDiv.style.display = 'none';
            refreshBtn.disabled = false;
            refreshBtn.textContent = '🔄 Refresh Passenger List';
        }
    }

    function displayRSVPs(rsvps) {
        if (rsvps.length === 0) {
            noDataDiv.style.display = 'block';
            return;
        }

        let html = `<h2>✈️ Total Passengers Booked: ${rsvps.length}</h2>`;
        
        rsvps.forEach(rsvp => {
            const createdDate = new Date(rsvp.date_created);
            const eventDate = new Date(rsvp.event_date);
            
            html += `
                <div class="rsvp-item">
                    <div class="rsvp-header">
                        <div class="rsvp-email">${escapeHtml(rsvp.email)}</div>
                        <div class="rsvp-date">Booked: ${formatDateTime(createdDate)}</div>
                    </div>
                    <div class="rsvp-details">
                        <div class="rsvp-detail">
                            <div class="rsvp-detail-label">🍽️ Meal Service</div>
                            <div class="rsvp-detail-value">
                                ${formatDietaryOption(rsvp.dietary_option)}
                                ${rsvp.dietary_option === 'other' && rsvp.special_dietary_details ? 
                                    `<br><small class="special-dietary-details">Details: ${escapeHtml(rsvp.special_dietary_details)}</small>` : ''}
                            </div>
                        </div>
                        <div class="rsvp-detail">
                            <div class="rsvp-detail-label">✈️ Departure Date</div>
                            <div class="rsvp-detail-value">${formatDate(eventDate)}</div>
                        </div>
                    </div>
                </div>
            `;
        });

        rsvpListDiv.innerHTML = html;
    }

    function formatDateTime(date) {
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    function formatDate(date) {
        return date.toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
    }

    function formatDietaryOption(option) {
        const options = {
            'shrimp-aglio-olio': '🍤 Shrimp Linguine Aglio Olio',
            'creamy-chicken-pomodoro': '🍗 Creamy Chicken Pomodoro',
            'carbonara-funghi': '🍄 Carbonara al Funghi (V)',
            // legacy
            'none': '🍽️ Standard Meal Service',
            'vegetarian': '🥗 Vegetarian Meal (VGML)',
            'vegan': '🌱 Vegan Meal (VEGN)',
            'gluten-free': '🌾 Gluten-Free Meal (GFML)',
            'dairy-free': '🥛 Dairy-Free Meal (DFML)',
            'nut-free': '🥜 Nut-Free Meal (NFML)',
            'other': '👨‍🍳 Special Dietary Request'
        };
        return options[option] || option;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async function downloadManifest() {
        downloadBtn.disabled = true;
        downloadBtn.textContent = '📥 Downloading...';

        try {
            const response = await fetch('/api/rsvp/download');
            
            if (response.ok) {
                // Get the filename from the response headers
                const contentDisposition = response.headers.get('content-disposition');
                let filename = 'AzaleaAir_Passenger_Manifest.csv';
                
                if (contentDisposition) {
                    const matches = contentDisposition.match(/filename=(.+)/);
                    if (matches) {
                        filename = matches[1];
                    }
                }

                // Create blob and download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                // Show success message briefly
                downloadBtn.textContent = '✅ Downloaded!';
                setTimeout(() => {
                    downloadBtn.textContent = '📋 Download Manifest';
                }, 2000);
            } else {
                const error = await response.json();
                console.error('Download error:', error);
                downloadBtn.textContent = '❌ Download Failed';
                setTimeout(() => {
                    downloadBtn.textContent = '📋 Download Manifest';
                }, 3000);
            }
        } catch (error) {
            console.error('Download error:', error);
            downloadBtn.textContent = '❌ Download Failed';
            setTimeout(() => {
                downloadBtn.textContent = '📋 Download Manifest';
            }, 3000);
        } finally {
            downloadBtn.disabled = false;
        }
    }

    async function loadSummary() {
        try {
            const response = await fetch('/api/rsvp/summary');
            const summary = await response.json();

            if (response.ok) {
                displaySummary(summary);
            } else {
                console.error('Error loading summary:', summary.error);
                summarySection.style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading summary:', error);
            summarySection.style.display = 'none';
        }
    }

    function displaySummary(summary) {
        if (summary.total_passengers === 0) {
            summarySection.style.display = 'none';
            return;
        }

        summarySection.style.display = 'block';
        
        let html = `
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-label">✈️ Total Passengers</div>
                    <div class="summary-value">${summary.total_passengers}</div>
                </div>
        `;

        // Add meal summary items
        for (const [option, data] of Object.entries(summary.meal_summary)) {
            html += `
                <div class="summary-item">
                    <div class="summary-label">${data.label}</div>
                    <div class="summary-value">${data.count}</div>
                </div>
            `;
        }

        html += '</div>';
        summaryContent.innerHTML = html;
    }
});