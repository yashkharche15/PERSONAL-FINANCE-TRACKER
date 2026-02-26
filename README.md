# WealthWise | Personal Finance Tracker

A premium, modern personal finance management application built with **Flask** and **SQLite**.

## Features
- **User Authentication**: Secure register/login system.
- **Transaction Tracking**: Add and manage income and expenses.
- **Dashboard**: High-level overview of monthly balance, income, and spending.
- **Data Visualization**: Interactive Doughnut charts using **Chart.js**.
- **Budget Alerts**: Set monthly limits per category and get visual warnings when approaching or exceeding limits.
- **Glassmorphism UI**: A stunning, modern dark-themed interface.

## Tech Stack
- **Backend**: Python 3.x, Flask, SQLAlchemy
- **Database**: SQLite
- **Frontend**: Vanilla CSS (Custom Design System), Jinja2 Templates
- **Charts**: Chart.js

## Installation & Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python app.py
   ```

3. **Access the App**:
   Open your browser and navigate to `http://127.0.0.1:5000`

## Project Structure
- `app.py`: Main application logic and routes.
- `models.py`: Database schema and SQLAlchemy models.
- `static/`: Contains CSS and assets.
- `templates/`: Jinja2 HTML templates.
- `instance/`: Contains the SQLite database file (created on first run).
