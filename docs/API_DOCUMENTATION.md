# Diabuddies API Documentation

Complete API documentation for the Diabuddies diabetes management system.

## Overview

The Diabuddies system provides:
- Multi-agent conversational AI for patient support
- Doctor/Healthcare provider management
- Personalized care plans
- Data logging (glucose, medications, meals, activity)
- Real-time alerts and reminders
- Weekly/monthly reporting for doctors
- Emergency contact and appointment booking

## Base URL

```
http://localhost:5000
```

---

## Patient Endpoints

### Create Patient
```http
POST /api/patients
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "date_of_birth": "1980-01-01",
  "doctor_id": "optional-doctor-id"
}
```

### Get Patient
```http
GET /api/patients/{patient_id}
```

---

## Doctor Endpoints

### Create Doctor
```http
POST /api/doctors
Content-Type: application/json

{
  "name": "Dr. Jane Smith",
  "email": "jane.smith@hospital.com",
  "phone": "+1234567890",
  "specialty": "Endocrinology"
}
```

### Get Doctor's Patients
```http
GET /api/doctors/{doctor_id}/patients
```

### Setup Care Plan
```http
POST /api/doctors/{doctor_id}/patients/{patient_id}/care-plan
Content-Type: application/json

{
  "medications": [
    {
      "name": "Metformin",
      "dosage": "500mg",
      "frequency": "twice daily",
      "times": ["08:00", "20:00"],
      "start_date": "2025-01-01",
      "notes": "Take with meals"
    }
  ],
  "glucose_targets": {
    "fasting_min": 80,
    "fasting_max": 130,
    "post_meal_min": 80,
    "post_meal_max": 180,
    "hba1c_target": 7.0
  },
  "health_goals": {
    "weight_target": 180,
    "activity_minutes_per_week": 150,
    "dietary_goals": "Low carb, high fiber",
    "other_goals": "Walk 30 minutes daily"
  },
  "dietary_recommendations": "Focus on whole grains, vegetables, and lean proteins",
  "notes": "Patient needs to monitor glucose before meals"
}
```

### Get Weekly Report
```http
GET /api/doctors/{doctor_id}/patients/{patient_id}/report/weekly
```

### Get Monthly Report
```http
GET /api/doctors/{doctor_id}/patients/{patient_id}/report/monthly
```

---

## Data Logging Endpoints

### Log Glucose Reading
```http
POST /api/patients/{patient_id}/glucose
Content-Type: application/json

{
  "reading": 120.5,
  "reading_type": "fasting",  // "fasting", "post_meal", "random", "bedtime"
  "timestamp": "2025-01-15T08:00:00",
  "notes": "Before breakfast"
}
```

**Response includes alert if reading is out of target range:**
```json
{
  "log": { ... },
  "alert": {
    "alert_type": "high_glucose",
    "severity": "medium",
    "message": "High fasting glucose: 150 mg/dL..."
  }
}
```

### Log Medication
```http
POST /api/patients/{patient_id}/medication
Content-Type: application/json

{
  "medication_name": "Metformin",
  "dosage": "500mg",
  "taken": true,
  "timestamp": "2025-01-15T08:00:00",
  "notes": "Taken with breakfast"
}
```

### Log Meal
```http
POST /api/patients/{patient_id}/meal
Content-Type: application/json

{
  "meal_type": "breakfast",  // "breakfast", "lunch", "dinner", "snack"
  "description": "Oatmeal with berries",
  "carbs_estimate": 45,
  "timestamp": "2025-01-15T08:30:00",
  "notes": "Felt good after meal"
}
```

### Log Activity
```http
POST /api/patients/{patient_id}/activity
Content-Type: application/json

{
  "activity_type": "walking",
  "duration_minutes": 30,
  "intensity": "moderate",  // "light", "moderate", "vigorous"
  "timestamp": "2025-01-15T18:00:00",
  "notes": "Evening walk in park"
}
```

### Get All Logs
```http
GET /api/patients/{patient_id}/logs?days=30
```

---

## Alert Endpoints

### Get Alerts
```http
GET /api/patients/{patient_id}/alerts?unacknowledged_only=true
```

### Acknowledge Alert
```http
POST /api/patients/{patient_id}/alerts/{alert_id}/acknowledge
```

### Check for Alerts (Missed Doses, etc.)
```http
POST /api/patients/{patient_id}/alerts/check
```

**Alert Types:**
- `missed_dose` - Medication not taken on schedule
- `high_glucose` - Glucose reading above target
- `low_glucose` - Glucose reading below target
- `critical` - Emergency situation

**Severity Levels:**
- `low` - Informational
- `medium` - Needs attention
- `high` - Important
- `critical` - Emergency

---

## Reminder Endpoints

### Get Reminders
```http
GET /api/patients/{patient_id}/reminders?active_only=true
```

### Generate Reminders
```http
POST /api/patients/{patient_id}/reminders/generate
```

Generates reminders based on care plan (medications, glucose checks, etc.)

**Reminder Types:**
- `medication` - Time to take medication
- `glucose_check` - Time to check glucose
- `exercise` - Exercise reminder
- `dietary` - Meal/dietary check-in

---

## Appointment & Emergency Endpoints

### Request Appointment (Non-Emergency)
```http
POST /api/patients/{patient_id}/appointments
Content-Type: application/json

{
  "preferred_date": "2025-01-20",
  "reason": "Routine check-up"
}
```

### Emergency Contact
```http
POST /api/patients/{patient_id}/emergency
```

Creates critical alert and provides doctor contact information immediately.

---

## Conversation Endpoint

### Chat with Diabuddies
```http
POST /api/diabuddies
Content-Type: application/json

{
  "sessionId": "unique-session-id",
  "message": "How are you doing today?",
  "patient_id": "optional-patient-id",  // Links session to patient for personalized care
  "generateInsights": false  // Set to true to generate full insights
}
```

**Response:**
```json
{
  "reply": "I'm doing well, thank you for asking!",
  "is_emergency": false,
  "extracted": { ... },  // Only if generateInsights=true or emergency
  "risk": { ... },
  "summary": "..."
}
```

### Generate Insights
```http
POST /api/insights
Content-Type: application/json

{
  "sessionId": "unique-session-id"
}
```

---

## Data Storage

All data is stored in JSON files in the `backend/data/` directory:
- `patients.json`
- `doctors.json`
- `glucose_logs.json`
- `medication_logs.json`
- `meal_logs.json`
- `activity_logs.json`
- `alerts.json`
- `reminders.json`

**Note:** For production, consider upgrading to a proper database (PostgreSQL, MongoDB, etc.)

---

## Workflow Example

1. **Doctor Setup:**
   - Create doctor: `POST /api/doctors`
   - Create patient: `POST /api/patients`
   - Setup care plan: `POST /api/doctors/{id}/patients/{id}/care-plan`

2. **Patient Daily Use:**
   - Log glucose: `POST /api/patients/{id}/glucose`
   - Log medication: `POST /api/patients/{id}/medication`
   - Log meals/activity: `POST /api/patients/{id}/meal` or `/activity`
   - Chat with Diabuddies: `POST /api/diabuddies` (with `patient_id`)

3. **System Automatically:**
   - Checks for missed doses
   - Alerts on high/low glucose
   - Generates reminders based on care plan
   - Provides personalized conversation based on care plan

4. **Doctor Reviews:**
   - Weekly report: `GET /api/doctors/{id}/patients/{id}/report/weekly`
   - Monthly report: `GET /api/doctors/{id}/patients/{id}/report/monthly`
   - View alerts: `GET /api/patients/{id}/alerts`

---

## Error Responses

All endpoints return standard HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `500` - Server Error

Error response format:
```json
{
  "error": "Error message",
  "details": "Additional details if available"
}
```

---

## Voice Call Endpoints

### Initiate Voice Call
```http
POST /api/voice/call/initiate
Content-Type: application/json

{
  "phone_number": "+1234567890",  // E.164 format required
  "patient_id": "optional-patient-id"
}
```

**Response:**
```json
{
  "success": true,
  "call_sid": "CAxxxxxxxxxxxx",
  "status": "queued",
  "message": "Call initiated to +1234567890"
}
```

### Twilio Webhooks (Internal)

These endpoints are called by Twilio automatically:

- `POST /api/voice/call` - Handles incoming call, returns TwiML
- `POST /api/voice/process` - Processes speech input, returns TwiML response
- `POST /api/voice/status` - Call status updates
- `POST /api/voice/partial` - Partial speech results (optional)

**Note:** See [VOICE_SETUP.md](../backend/VOICE_SETUP.md) for complete voice call setup instructions.

