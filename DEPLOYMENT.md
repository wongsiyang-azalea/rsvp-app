# 🚀 Azalea Air Setup Guide

## Steps

- Create a virtual environment: `python -m venv venv`
- Run `pip install -r requirements.txt`
- Run `python init_db.py`
- Run `python configure.py --set-date 2025-10-30 --flight-number "AA-3010" --destination "Padang"`
- Run `python app.py`

Ensure that the rsvp_database.db is created.
The application will be hosted on port 5000.