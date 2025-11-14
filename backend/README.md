# Diabuddies Backend

Python Flask backend with LangGraph multi-agent system for diabetes management.

## 📁 Structure

```
backend/
├── agents/              # LangGraph agents
│   ├── buddy_agent.py      # Conversation agent
│   ├── extractor_agent.py  # Data extraction
│   ├── risk_agent.py       # Risk assessment
│   ├── summary_agent.py    # Summary generation
│   └── orchestrator.py     # Workflow orchestration
├── data/                # JSON data storage (auto-created)
├── main.py              # Flask app & API endpoints
├── models.py            # Data models
├── storage.py           # Storage layer
├── services.py          # Business logic
└── requirements.txt     # Dependencies
```

## 🚀 Setup

1. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Create `.env` file**
   ```bash
   OPENAI_API_KEY=your_api_key_here
   PORT=5000
   ```

3. **Run server**
   ```bash
   python3 main.py
   ```

## 🏗️ Architecture

### Multi-Agent System (LangGraph)

**Conversation Flow:**
```
UserMessage → BuddyAgent → ExtractorAgent → RiskAgent → SummaryAgent → Response
```

**Fast Mode (reduced latency):**
```
UserMessage → BuddyAgent → Response
```

### Agents

1. **BuddyAgent** - Personalized friendly conversations using care plan context
2. **ExtractorAgent** - Extracts structured data (glucose, meds, mood, symptoms)
3. **RiskAgent** - Assesses health risk (low/moderate/high/critical)
4. **SummaryAgent** - Generates friendly daily summaries

### Data Models

- `Patient` - Patient information and care plan
- `Doctor` - Healthcare provider information
- `CarePlan` - Medications, targets, goals
- `GlucoseLog`, `MedicationLog`, `MealLog`, `ActivityLog` - Data logs
- `Alert` - System alerts
- `Reminder` - Scheduled reminders

### Storage

JSON-based file storage in `data/` directory. Easily upgradeable to database.

## 📡 API Endpoints

See [API Documentation](../docs/API_DOCUMENTATION.md) for complete details.

### Core
- `POST /api/diabuddies` - Chat endpoint
- `POST /api/insights` - Generate insights

### Patients
- `POST /api/patients` - Create patient
- `GET /api/patients/{id}` - Get patient
- `POST /api/patients/{id}/glucose` - Log glucose
- `POST /api/patients/{id}/medication` - Log medication
- `POST /api/patients/{id}/meal` - Log meal
- `POST /api/patients/{id}/activity` - Log activity
- `GET /api/patients/{id}/logs` - Get all logs
- `GET /api/patients/{id}/alerts` - Get alerts
- `POST /api/patients/{id}/emergency` - Emergency contact

### Doctors
- `POST /api/doctors` - Create doctor
- `GET /api/doctors/{id}/patients` - Get patients
- `POST /api/doctors/{id}/patients/{pid}/care-plan` - Setup care plan
- `GET /api/doctors/{id}/patients/{pid}/report/weekly` - Weekly report
- `GET /api/doctors/{id}/patients/{pid}/report/monthly` - Monthly report

## 🔧 Services

- **Alert System**: Automatic detection of missed doses, high/low glucose
- **Reminder System**: Medication, glucose check, exercise reminders
- **Reporting**: Weekly/monthly reports with analytics
- **Emergency Response**: Critical alert handling and doctor notification

## 📝 Notes

- Data persists in `backend/data/` as JSON files
- Sessions stored in-memory (resets on restart)
- All safety rules enforced (no medical advice)
- Emergency protocols in place

