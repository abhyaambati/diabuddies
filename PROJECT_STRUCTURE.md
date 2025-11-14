# Project Structure

```
diabuddies-2/
│
├── backend/                    # Python Flask Backend
│   ├── agents/                # LangGraph Multi-Agent System
│   │   ├── __init__.py
│   │   ├── buddy_agent.py     # Friendly conversation agent
│   │   ├── extractor_agent.py # Data extraction agent
│   │   ├── risk_agent.py      # Risk assessment agent
│   │   ├── summary_agent.py   # Summary generation agent
│   │   └── orchestrator.py    # LangGraph workflow orchestrator
│   │
│   ├── data/                  # JSON data storage (auto-created)
│   │   ├── patients.json
│   │   ├── doctors.json
│   │   ├── glucose_logs.json
│   │   ├── medication_logs.json
│   │   ├── meal_logs.json
│   │   ├── activity_logs.json
│   │   ├── alerts.json
│   │   └── reminders.json
│   │
│   ├── main.py                # Flask application & API endpoints
│   ├── models.py              # Data models (Patient, Doctor, CarePlan, etc.)
│   ├── storage.py             # Data storage layer
│   ├── services.py            # Business logic (alerts, reminders, reports)
│   ├── requirements.txt       # Python dependencies
│   ├── README.md              # Backend documentation
│   └── .env                   # Environment variables (create this)
│
├── frontend/                  # Frontend Application
│   └── public/
│       └── index.html         # Main UI (served by Flask)
│
├── docs/                      # Documentation
│   ├── API_DOCUMENTATION.md    # Complete API reference
│   └── FEATURES.md            # Detailed feature documentation
│
├── .gitignore                 # Git ignore rules
├── README.md                  # Main project README
└── PROJECT_STRUCTURE.md       # This file
```

## Key Files

### Backend
- **main.py**: Flask app with all API endpoints
- **models.py**: Data models (Patient, Doctor, CarePlan, Logs, Alerts, Reminders)
- **storage.py**: JSON-based storage system
- **services.py**: Business logic (alert checking, reminder generation, reporting)
- **agents/**: LangGraph multi-agent system

### Frontend
- **frontend/public/index.html**: Single-page application UI

### Documentation
- **docs/API_DOCUMENTATION.md**: Complete API reference with examples
- **docs/FEATURES.md**: Feature list and workflows
- **README.md**: Quick start and overview
- **backend/README.md**: Backend-specific documentation

## Data Storage

All data is stored in `backend/data/` as JSON files:
- Patient and doctor records
- All logs (glucose, medication, meals, activity)
- Alerts and reminders
- Care plans

**Note**: For production, consider upgrading to a database (PostgreSQL, MongoDB, etc.)

## Environment Setup

Create `backend/.env`:
```
OPENAI_API_KEY=your_api_key_here
PORT=5000
```

## Running the Project

```bash
cd backend
pip3 install -r requirements.txt
python3 main.py
```

Then open `http://localhost:5000` in your browser.

