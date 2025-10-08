from flask import Flask, request, jsonify, render_template, Response
import sqlite3
from datetime import datetime
import os
import csv
from io import StringIO
from collections import Counter
import string
import random

app = Flask(__name__)

def get_db_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect('rsvp_database.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def init_database():
    """Initialize the database if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create RSVP table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rsvp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            email TEXT NOT NULL,
            dietary_option TEXT NOT NULL,
            event_date DATE NOT NULL,
            special_dietary_details TEXT
        )
    ''')
    
    # Add special_dietary_details column if it doesn't exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE rsvp ADD COLUMN special_dietary_details TEXT')
    except:
        pass  # Column already exists
    
    # Create configuration table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flight_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_flight_config(key, default=None):
    """Get a configuration value from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM flight_config WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        
        return result['value'] if result else default
    except:
        return default

def get_departure_date():
    """Get the configured departure date."""
    return get_flight_config('departure_date')

def is_departure_date_configured():
    """Check if departure date is configured."""
    return get_departure_date() is not None

def generate_confirmation_code():
    """Generate a 6-character confirmation code."""
    return '4Z4L34'

def generate_seat_number():
    """Generate seat assignment - STANDING for this airline."""
    return "STANDING"

def format_boarding_time(departure_date_str):
    """Calculate departure and arrival times."""
    try:
        # Departure at 12:00, Estimated Arrival at 14:00
        departure_date = datetime.strptime(departure_date_str, '%Y-%m-%d').date()
        departure_time = "12:00"
        boarding_time = "14:00"  # This will be used as arrival time
        gate = f"A{random.randint(1, 20)}"
        
        return {
            'departure_time': departure_time,
            'boarding_time': boarding_time,
            'gate': gate
        }
    except:
        return {
            'departure_time': "14:30",
            'boarding_time': "13:45", 
            'gate': "A12"
        }

@app.route('/')
def index():
    """Serve the main RSVP form page."""
    # Check if departure date is configured
    if not is_departure_date_configured():
        return render_template('config_required.html')
    return render_template('index.html')

@app.route('/api/flight-config')
def get_flight_config_api():
    """Get flight configuration information."""
    try:
        departure_date = get_departure_date()
        flight_number = get_flight_config('flight_number', 'AA-2025')
        destination = get_flight_config('destination', 'Destination TBD')
        
        if not departure_date:
            return jsonify({'error': 'Flight departure date not configured'}), 400
        
        # Format departure date for display
        from datetime import datetime
        date_obj = datetime.strptime(departure_date, '%Y-%m-%d').date()
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        return jsonify({
            'departure_date': departure_date,
            'formatted_date': formatted_date,
            'flight_number': flight_number,
            'destination': destination,
            'configured': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rsvp', methods=['POST'])
def create_rsvp():
    """Create a new RSVP entry."""
    try:
        data = request.get_json()
        
        # Check if departure date is configured
        configured_date = get_departure_date()
        if not configured_date:
            return jsonify({'error': 'Flight departure date not configured. Please contact airline administration.'}), 400
        
        # Validate required fields (event_date no longer required from user)
        required_fields = ['email', 'dietary_option']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # New meal choices are fixed bento options; allow legacy submissions to still work.
        valid_meal_choices = {
            'shrimp-aglio-olio': '🍤 Shrimp Linguine Aglio Olio',
            'creamy-chicken-pomodoro': '🍗 Creamy Chicken Pomodoro',
            'carbonara-funghi': '🍄 Carbonara al Funghi (V)'
        }

        # Map possible legacy values to new (do not reject old data already stored)
        legacy_values = set(['none','vegetarian','vegan','gluten-free','dairy-free','nut-free','other'])
        if data['dietary_option'] not in valid_meal_choices and data['dietary_option'] not in legacy_values:
            return jsonify({'error': 'Invalid meal selection'}), 400

        # Special dietary free-text no longer required; ignore incoming unless legacy "other" was used
        if data['dietary_option'] == 'other':
            # Keep previous behavior but make details optional (graceful degradation)
            special_text = data.get('special_dietary_details')
            if not special_text:
                # Accept but store None now
                data['special_dietary_details'] = None
        
        # Use configured departure date instead of user input
        event_date = configured_date
        
        # Generate boarding pass data
        confirmation_code = generate_confirmation_code()
        seat_number = generate_seat_number()
        flight_times = format_boarding_time(event_date)
        
        # Insert into database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Preserve legacy special dietary details only if legacy "other" option used
        special_dietary_details = data.get('special_dietary_details') if data['dietary_option'] == 'other' else None

        cursor.execute('''
            INSERT INTO rsvp (email, dietary_option, event_date, special_dietary_details)
            VALUES (?, ?, ?, ?)
        ''', (data['email'], data['dietary_option'], event_date, special_dietary_details))
        
        conn.commit()
        rsvp_id = cursor.lastrowid
        conn.close()
        
        # Get flight configuration for boarding pass
        flight_number = get_flight_config('flight_number', 'AA-2025')
        destination = get_flight_config('destination', 'Destination TBD')
        
        # Format departure date for display
        departure_date_obj = datetime.strptime(event_date, '%Y-%m-%d').date()
        formatted_departure = departure_date_obj.strftime('%B %d, %Y')
        
        # Create boarding pass data
        boarding_pass = {
            'confirmation_code': confirmation_code,
            'passenger_email': data['email'],
            'flight_number': flight_number,
            'departure_date': event_date,
            'formatted_departure': formatted_departure,
            'destination': destination,
            'seat_number': seat_number,
            'gate': flight_times['gate'],
            'boarding_time': flight_times['boarding_time'],
            'departure_time': flight_times['departure_time'],
            'meal_preference': data['dietary_option'],
            'special_dietary_details': special_dietary_details,
            'meal_display': valid_meal_choices.get(data['dietary_option'], data['dietary_option'])
        }
        
        return jsonify({
            'message': 'RSVP submitted successfully!',
            'rsvp_id': rsvp_id,
            'departure_date': event_date,
            'boarding_pass': boarding_pass
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rsvp', methods=['GET'])
def get_rsvps():
    """Get all RSVP entries."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, date_created, email, dietary_option, event_date
            FROM rsvp
            ORDER BY date_created DESC
        ''')
        
        rsvps = []
        for row in cursor.fetchall():
            rsvps.append({
                'id': row['id'],
                'date_created': row['date_created'],
                'email': row['email'],
                'dietary_option': row['dietary_option'],
                'event_date': row['event_date']
            })
        
        conn.close()
        return jsonify(rsvps)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin')
def admin():
    """Serve the admin page to view all RSVPs."""
    return render_template('admin.html')

@app.route('/api/rsvp/download')
def download_rsvp_csv():
    """Download RSVP data as CSV with summary statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, date_created, email, dietary_option, event_date
            FROM rsvp
            ORDER BY date_created DESC
        ''')
        
        rsvps = cursor.fetchall()
        conn.close()
        
        if not rsvps:
            return jsonify({'error': 'No passenger data available for download'}), 404
        
        # Create CSV content
        output = StringIO()
        
        # Write summary statistics first
        total_passengers = len(rsvps)
        dietary_counts = Counter([rsvp['dietary_option'] for rsvp in rsvps])
        
        # Write header comments with summary
        output.write(f"# Azalea Air Flight AA-2025 - Passenger Manifest\n")
        output.write(f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write(f"# \n")
        output.write(f"# FLIGHT SUMMARY\n")
        output.write(f"# Total Passengers: {total_passengers}\n")
        output.write(f"# \n")
        output.write(f"# MEAL SERVICE SUMMARY\n")
        
        # Format dietary options for summary
        # Bento box + legacy mapping
        dietary_labels = {
            'shrimp-aglio-olio': 'Shrimp Linguine Aglio Olio',
            'creamy-chicken-pomodoro': 'Creamy Chicken Pomodoro',
            'carbonara-funghi': 'Carbonara al Funghi (V)',
            # legacy
            'none': 'Standard Meal Service',
            'vegetarian': 'Vegetarian Meals (VGML)',
            'vegan': 'Vegan Meals (VEGN)',
            'gluten-free': 'Gluten-Free Meals (GFML)',
            'dairy-free': 'Dairy-Free Meals (DFML)',
            'nut-free': 'Nut-Free Meals (NFML)',
            'other': 'Special Dietary Requests'
        }
        
        for option, count in dietary_counts.items():
            label = dietary_labels.get(option, option)
            output.write(f"# {label}: {count}\n")
        
        output.write(f"# \n")
        output.write(f"# ================================================\n")
        output.write(f"# PASSENGER MANIFEST DATA\n")
        output.write(f"# ================================================\n")
        
        # Write CSV header
        writer = csv.writer(output)
        writer.writerow([
            'Passenger ID',
            'Booking Date',
            'Passenger Email',
            'Meal Preference',
            'Departure Date'
        ])
        
        # Write passenger data
        for rsvp in rsvps:
            writer.writerow([
                rsvp['id'],
                rsvp['date_created'],
                rsvp['email'],
                dietary_labels.get(rsvp['dietary_option'], rsvp['dietary_option']),
                rsvp['event_date']
            ])
        
        # Create response
        csv_content = output.getvalue()
        output.close()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'AzaleaAir_Flight_AA2025_Manifest_{timestamp}.csv'
        
        response = Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rsvp/summary')
def get_rsvp_summary():
    """Get summary statistics for RSVP data."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT dietary_option FROM rsvp')
        dietary_options = [row['dietary_option'] for row in cursor.fetchall()]
        
        cursor.execute('SELECT COUNT(*) as total FROM rsvp')
        total_count = cursor.fetchone()['total']
        
        conn.close()
        
        # Count dietary options
        dietary_counts = Counter(dietary_options)
        
        # Format response
        summary = {
            'total_passengers': total_count,
            'meal_summary': {}
        }
        
        dietary_labels = {
            'shrimp-aglio-olio': 'Shrimp Linguine Aglio Olio',
            'creamy-chicken-pomodoro': 'Creamy Chicken Pomodoro',
            'carbonara-funghi': 'Carbonara al Funghi (V)',
            # legacy
            'none': 'Standard Meal Service',
            'vegetarian': 'Vegetarian Meals (VGML)',
            'vegan': 'Vegan Meals (VEGN)',
            'gluten-free': 'Gluten-Free Meals (GFML)',
            'dairy-free': 'Dairy-Free Meals (DFML)',
            'nut-free': 'Nut-Free Meals (NFML)',
            'other': 'Special Dietary Requests'
        }
        
        for option, count in dietary_counts.items():
            label = dietary_labels.get(option, option)
            summary['meal_summary'][option] = {
                'label': label,
                'count': count
            }
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/boarding-pass/<int:rsvp_id>')
def get_boarding_pass(rsvp_id):
    """Get boarding pass information for a specific RSVP."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, email, dietary_option, event_date, date_created
            FROM rsvp WHERE id = ?
        ''', (rsvp_id,))
        
        rsvp = cursor.fetchone()
        conn.close()
        
        if not rsvp:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Generate boarding pass data (in production, this would be stored)
        confirmation_code = f"AZ{str(rsvp['id']).zfill(4)}"  # More consistent confirmation code
        seat_number = generate_seat_number()
        flight_times = format_boarding_time(rsvp['event_date'])
        
        # Get flight configuration
        flight_number = get_flight_config('flight_number', 'AA-2025')
        destination = get_flight_config('destination', 'Destination TBD')
        
        # Format departure date
        departure_date_obj = datetime.strptime(rsvp['event_date'], '%Y-%m-%d').date()
        formatted_departure = departure_date_obj.strftime('%B %d, %Y')
        
        boarding_pass = {
            'confirmation_code': confirmation_code,
            'passenger_email': rsvp['email'],
            'flight_number': flight_number,
            'departure_date': rsvp['event_date'],
            'formatted_departure': formatted_departure,
            'destination': destination,
            'seat_number': seat_number,
            'gate': flight_times['gate'],
            'boarding_time': flight_times['boarding_time'],
            'departure_time': flight_times['departure_time'],
            'meal_preference': rsvp['dietary_option'],
            'booking_date': rsvp['date_created']
        }
        
        return jsonify(boarding_pass)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    
    # Get debug mode from environment
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)