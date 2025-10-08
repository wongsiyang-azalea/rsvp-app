#!/usr/bin/env python3
"""
Azalea Air Flight Configuration CLI
Configure flight departure date and other settings at runtime.
"""

import argparse
import sqlite3
import sys
from datetime import datetime, date
import os

def get_db_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect('rsvp_database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_config_table():
    """Initialize the configuration table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flight_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def set_departure_date(departure_date_str):
    """Set the departure date for the flight."""
    try:
        # Validate date format
        departure_date = datetime.strptime(departure_date_str, '%Y-%m-%d').date()
        
        # Check if date is in the future
        if departure_date < date.today():
            print(f"❌ Error: Departure date {departure_date_str} is in the past.")
            print(f"   Today is {date.today()}. Please choose a future date.")
            return False
        
        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO flight_config (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', ('departure_date', departure_date_str))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Flight departure date set to: {departure_date_str}")
        print(f"   Formatted: {departure_date.strftime('%A, %B %d, %Y')}")
        return True
        
    except ValueError as e:
        print(f"❌ Error: Invalid date format '{departure_date_str}'")
        print("   Please use YYYY-MM-DD format (e.g., 2025-12-15)")
        return False
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False

def get_departure_date():
    """Get the currently configured departure date."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT value, updated_at FROM flight_config 
            WHERE key = 'departure_date'
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            departure_date = datetime.strptime(result['value'], '%Y-%m-%d').date()
            updated_at = result['updated_at']
            return departure_date, updated_at
        else:
            return None, None
            
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return None, None

def set_flight_info(flight_number=None, destination=None):
    """Set flight number and destination."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if flight_number:
            cursor.execute('''
                INSERT OR REPLACE INTO flight_config (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', ('flight_number', flight_number))
            print(f"✅ Flight number set to: {flight_number}")
        
        if destination:
            cursor.execute('''
                INSERT OR REPLACE INTO flight_config (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', ('destination', destination))
            print(f"✅ Destination set to: {destination}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        conn.close()
        return False

def show_status():
    """Show current flight configuration."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT key, value, updated_at FROM flight_config ORDER BY key')
        configs = cursor.fetchall()
        conn.close()
        
        print("✈️  Azalea Air Flight Configuration Status")
        print("=" * 45)
        
        if not configs:
            print("⚠️  No configuration found. Please set departure date first.")
            return
        
        config_dict = {row['key']: row for row in configs}
        
        # Display departure date
        if 'departure_date' in config_dict:
            date_str = config_dict['departure_date']['value']
            departure_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            updated_at = config_dict['departure_date']['updated_at']
            
            print(f"📅 Departure Date: {date_str}")
            print(f"   Formatted: {departure_date.strftime('%A, %B %d, %Y')}")
            print(f"   Updated: {updated_at}")
            
            # Check if date is still valid
            days_until = (departure_date - date.today()).days
            if days_until < 0:
                print(f"   ⚠️  WARNING: Date is {abs(days_until)} days in the past!")
            elif days_until == 0:
                print(f"   🚨 DEPARTURE DAY: Flight departs today!")
            else:
                print(f"   ⏳ {days_until} days until departure")
        else:
            print("📅 Departure Date: Not configured")
        
        # Display flight number
        if 'flight_number' in config_dict:
            flight_number = config_dict['flight_number']['value']
        else:
            flight_number = 'AA-2025 (default)'
        print(f"🛫 Flight Number: {flight_number}")
        
        # Display destination
        if 'destination' in config_dict:
            destination = config_dict['destination']['value']
        else:
            destination = 'Not specified'
        print(f"🌍 Destination: {destination}")
        
        # Show passenger count  
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM rsvp')
        passenger_count = cursor.fetchone()['count']
        conn.close()
        
        print(f"👥 Current Passengers: {passenger_count}")
        
    except Exception as e:
        print(f"❌ Error retrieving configuration: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description='Azalea Air Flight Configuration CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python configure.py --set-date 2025-12-15
  python configure.py --flight-number "AA-2025" --destination "New York"
  python configure.py --status
  python configure.py --set-date 2025-12-15 --flight-number "AA-3045"
        '''
    )
    
    parser.add_argument('--set-date', 
                       help='Set departure date (YYYY-MM-DD format)')
    parser.add_argument('--flight-number', 
                       help='Set flight number (e.g., AA-2025)')
    parser.add_argument('--destination', 
                       help='Set destination city/airport')
    parser.add_argument('--status', action='store_true',
                       help='Show current configuration status')
    
    args = parser.parse_args()
    
    # Initialize configuration table
    init_config_table()
    
    # If no arguments, show help
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    success = True
    
    # Set departure date
    if args.set_date:
        success &= set_departure_date(args.set_date)
    
    # Set flight info
    if args.flight_number or args.destination:
        success &= set_flight_info(args.flight_number, args.destination)
    
    # Show status
    if args.status or success:
        print()  # Empty line for readability
        show_status()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()