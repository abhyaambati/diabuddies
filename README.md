# Diabuddies - Multi-Agent Diabetes Management System

A comprehensive diabetes management platform powered by LangGraph multi-agent AI, providing personalized support, real-time monitoring, and healthcare provider integration.

## 🏗️ Project Structure

```
diabuddies-2/
├── backend/                 # Python Flask backend
│   ├── agents/             # LangGraph multi-agent system
│   │   ├── buddy_agent.py      # Friendly conversation agent
│   │   ├── extractor_agent.py  # Data extraction agent
│   │   ├── risk_agent.py       # Risk assessment agent
│   │   ├── summary_agent.py    # Summary generation agent
│   │   └── orchestrator.py     # LangGraph workflow orchestrator
│   ├── data/               # JSON data storage (auto-created)
│   ├── main.py             # Flask application & API endpoints
│   ├── models.py           # Data models (Patient, Doctor, CarePlan, etc.)
│   ├── storage.py          # Data storage layer
│   ├── services.py         # Business logic (alerts, reminders, reports)
│   ├── requirements.txt    # Python dependencies
│   └── README.md          # Backend documentation
│
├── frontend/               # Frontend application
│   └── public/
│       └── index.html      # Main UI (served by Flask)
│
└── docs/                   # Documentation
    ├── API_DOCUMENTATION.md
    └── FEATURES.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key ([Get one here](https://platform.openai.com/account/api-keys))

### Installation & Running

1. **Navigate to project directory**
   ```bash
   cd diabuddies-2/backend
   ```

2. **Install Python dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create or edit `backend/.env` file:
   ```bash
   OPENAI_API_KEY=sk-your-actual-api-key-here
   PORT=5000
   ```

4. **Run the server**
   ```bash
   python3 main.py
   ```

5. **Open in browser**
   ```
   http://localhost:5000
   ```

**For detailed instructions and troubleshooting, see [QUICKSTART.md](QUICKSTART.md)**

## ✨ Features

### Multi-Agent AI System
- **BuddyAgent**: Personalized friendly conversations
- **ExtractorAgent**: Structured data extraction
- **RiskAgent**: Health risk assessment
- **SummaryAgent**: Daily summaries

### Patient Features
- Personalized care plans
- Medication, glucose, meal, and activity logging
- Real-time alerts (missed doses, high/low glucose)
- Reminders (medications, glucose checks, exercise)
- Emergency contact with doctor
- **Voice calls** - Diabuddies can call patients for check-ins

### Doctor Features
- Patient management
- Care plan setup
- Weekly/monthly reports
- Alert monitoring
- Pattern analysis

### Data & Analytics
- Medication adherence tracking
- Glucose trend analysis
- Activity goal tracking
- Comprehensive reporting

## 📚 Documentation

- **[Product Description](docs/PRODUCT_DESCRIPTION.md)** - Comprehensive product vision and user experience
- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete API reference
- **[Features List](docs/FEATURES.md)** - Detailed feature documentation
- **[Implementation Gaps](docs/IMPLEMENTATION_GAPS.md)** - Features to be implemented
- **[Backend README](backend/README.md)** - Backend setup and architecture

## 🔧 API Endpoints

### Core Endpoints
- `POST /api/diabuddies` - Chat with Diabuddies
- `POST /api/insights` - Generate insights from conversation

### Patient Endpoints
- `POST /api/patients` - Create patient
- `GET /api/patients/{id}` - Get patient info
- `POST /api/patients/{id}/glucose` - Log glucose reading
- `POST /api/patients/{id}/medication` - Log medication
- `POST /api/patients/{id}/meal` - Log meal
- `POST /api/patients/{id}/activity` - Log activity
- `GET /api/patients/{id}/logs` - Get all logs
- `GET /api/patients/{id}/alerts` - Get alerts
- `POST /api/patients/{id}/emergency` - Emergency contact

### Doctor Endpoints
- `POST /api/doctors` - Create doctor
- `GET /api/doctors/{id}/patients` - Get doctor's patients
- `POST /api/doctors/{id}/patients/{pid}/care-plan` - Setup care plan
- `GET /api/doctors/{id}/patients/{pid}/report/weekly` - Weekly report
- `GET /api/doctors/{id}/patients/{pid}/report/monthly` - Monthly report

### Voice Call Endpoints
- `POST /api/voice/call/initiate` - Initiate outbound call to patient

See [API Documentation](docs/API_DOCUMENTATION.md) for complete details.
See [Voice Setup Guide](backend/VOICE_SETUP.md) for voice call configuration.

## 🏥 Workflow

1. **Doctor Setup**: Create doctor → Create patient → Setup care plan
2. **Patient Daily Use**: Log data → Chat with Diabuddies → Receive reminders
3. **System Monitoring**: Automatic alerts → Pattern detection → Reports
4. **Doctor Review**: View reports → Analyze patterns → Adjust care plans

## 🛡️ Safety

- No medical advice or dosing instructions
- Emergency protocols in place
- Doctor notification for critical alerts
- All safety rules enforced in AI agents

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]
