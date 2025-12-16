import os
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
# from nsepython import get_fao_participant_oi # Placeholder for real NSE data fetching

# --- Configuration ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
# Using SQLite for a simple, file-based database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'fii_data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 1. Database Model ---
# This class defines the structure of the data stored daily.
class FiiPosition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    long_contracts = db.Column(db.Integer, nullable=False)
    short_contracts = db.Column(db.Integer, nullable=False)
    net_contracts = db.Column(db.Integer, nullable=False)
    long_ratio = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'date': self.date.strftime('%Y-%m-%d'),
            'long_contracts': self.long_contracts,
            'short_contracts': self.short_contracts,
            'net_contracts': self.net_contracts,
            'long_ratio': round(self.long_ratio, 2)
        }

# --- 2. Data Fetching and Processing (Conceptual) ---
def update_fii_data():
    """
    Conceptual function to fetch, process, and store daily FII data.
    In a real application, this would run as a daily CRON job.
    """
    # Replace this with your actual data fetching logic using an NSE API wrapper
    # Example using hypothetical data for today
    today = datetime.now().date()
    
    # Check if data for today already exists
    if FiiPosition.query.filter_by(date=today).first():
        print(f"Data for {today} already exists.")
        return

    # --- MOCK DATA SIMULATION ---
    # In reality, this data comes from get_fao_participant_oi(date)
    MOCK_FII_LONG = 190000 
    MOCK_FII_SHORT = 180000 
    # --- END MOCK DATA ---
    
    long_contracts = MOCK_FII_LONG
    short_contracts = MOCK_FII_SHORT
    net_contracts = long_contracts - short_contracts
    total_oi = long_contracts + short_contracts
    long_ratio = (long_contracts / total_oi) * 100
    
    # Create and add the new record to the database
    new_data = FiiPosition(
        date=today,
        long_contracts=long_contracts,
        short_contracts=short_contracts,
        net_contracts=net_contracts,
        long_ratio=long_ratio
    )
    db.session.add(new_data)
    db.session.commit()
    print(f"Successfully added FII data for {today}.")


# --- 3. Flask Routes ---

@app.route('/')
def index():
    """Renders the main dashboard page."""
    # Ensure database is created (run once)
    with app.app_context():
        db.create_all()
        # Call the update function when the page loads for demonstration
        # In production, this is done via a scheduled CRON job, not on page load!
        update_fii_data() 
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    """API endpoint to serve the last 30 days of data for Chart.js."""
    # Query the last 30 records, ordered by date descending
    latest_data = FiiPosition.query.order_by(FiiPosition.date.desc()).limit(30).all()
    
    # Format the data for Chart.js (reverse list to show chronologically)
    data_list = [item.to_dict() for item in latest_data]
    data_list.reverse()
    
    # Get the latest single data point for the gauge/card
    latest_single = data_list[-1] if data_list else {}

    return jsonify({
        'history': data_list,
        'latest': latest_single
    })

if __name__ == '__main__':
    # Initialize the database and run the app
    with app.app_context():
        db.create_all()
    app.run(debug=True)
