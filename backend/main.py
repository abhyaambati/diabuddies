"""Flask backend for Diabuddies multi-agent system."""
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import sys
from agents.orchestrator import conversation_graph, diabuddies_graph
from storage import storage
from models import (
    Patient, Doctor, CarePlan, Medication, GlucoseTarget, HealthGoals,
    GlucoseLog, MedicationLog, MealLog, ActivityLog, Alert, Reminder,
    CommunityPost, Comment, DoctorMessage
)
from services import (
    check_missed_doses, check_glucose_alerts, generate_reminders,
    generate_weekly_report, generate_monthly_report, calculate_time_in_range
)
try:
    from sms_service import sms_service
    SMS_AVAILABLE = True
except ImportError:
    SMS_AVAILABLE = False
    sms_service = None
try:
    from voice_handler import voice_handler
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    voice_handler = None

import uuid
from datetime import datetime
from flask import Response

# Add backend directory to path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Load .env from backend directory
load_dotenv(os.path.join(backend_dir, '.env'))

app = Flask(__name__, static_folder='../frontend/public', static_url_path='')
CORS(app)

# In-memory session store (resets when server restarts)
sessions = {}


@app.route('/api/diabuddies', methods=['POST'])
def diabuddies_endpoint():
    """Main endpoint that runs the LangGraph multi-agent pipeline."""
    try:
        # Check for API key
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key or api_key.startswith('your_') or 'placeholder' in api_key.lower():
            return jsonify({
                'error': 'OpenAI API key not configured',
                'message': 'Please set OPENAI_API_KEY in backend/.env file with your actual API key'
            }), 500
        
        data = request.json
        session_id = data.get('sessionId')
        message = data.get('message')
        specialist_type = data.get('specialist', 'general')  # general, nutrition, fitness, therapist, nurse
        
        if not session_id or not message:
            return jsonify({'error': 'Missing sessionId or message'}), 400
        
        # Initialize session if needed
        if session_id not in sessions:
            sessions[session_id] = {
                'conversation_history': [],
                'patient_id': data.get('patient_id'),  # Optional: link session to patient
                'specialist': specialist_type
            }
        
        session = sessions[session_id]
        # Update specialist if changed
        if specialist_type != session.get('specialist'):
            session['specialist'] = specialist_type
        
        # Check if we should generate insights (only for emergencies during conversation)
        generate_insights = data.get('generateInsights', False)
        
        # Get patient context if session has patient_id
        patient_id = session.get('patient_id')
        care_plan_context = None
        
        if patient_id:
            patient = storage.get_patient(patient_id)
            if patient and patient.care_plan:
                care_plan = patient.care_plan
                # Build care plan context string
                meds_info = "\n".join([
                    f"- {med.name} ({med.dosage}) - {med.frequency} at {', '.join(med.times)}"
                    for med in care_plan.medications
                ])
                glucose_info = f"Targets: Fasting {care_plan.glucose_targets.fasting_min}-{care_plan.glucose_targets.fasting_max} mg/dL, Post-meal {care_plan.glucose_targets.post_meal_min}-{care_plan.glucose_targets.post_meal_max} mg/dL"
                goals_info = ""
                if care_plan.health_goals.activity_minutes_per_week:
                    goals_info += f"Activity goal: {care_plan.health_goals.activity_minutes_per_week} minutes/week. "
                if care_plan.health_goals.weight_target:
                    goals_info += f"Weight goal: {care_plan.health_goals.weight_target}. "
                if care_plan.dietary_recommendations:
                    goals_info += f"Dietary: {care_plan.dietary_recommendations}"
                
                care_plan_context = f"""MEDICATIONS:
{meds_info}

GLUCOSE TARGETS:
{glucose_info}

HEALTH GOALS:
{goals_info}"""
        
        # Prepare initial state for LangGraph
        initial_state = {
            'user_message': message,
            'conversation_history': session['conversation_history'],
            'reply': '',
            'extracted': {},
            'risk': {},
            'summary': '',
            'is_emergency': False,
            'patient_id': patient_id,
            'care_plan_context': care_plan_context,
            'specialist': session.get('specialist', 'general')
        }
        
        # Use fast conversation graph for normal messages, full graph for insights/emergencies
        if generate_insights:
            result = diabuddies_graph.invoke(initial_state)
        else:
            result = conversation_graph.invoke(initial_state)
            # Check if emergency was detected
            if result.get('is_emergency', False):
                # Re-run with full insights for emergencies
                result = diabuddies_graph.invoke(initial_state)
                generate_insights = True
        
        # Update conversation history
        session['conversation_history'].append({
            'role': 'user',
            'content': message
        })
        session['conversation_history'].append({
            'role': 'assistant',
            'content': result.get('reply', '')
        })
        
        # Return structured response
        response = {
            'reply': result.get('reply', ''),
            'is_emergency': result.get('is_emergency', False)
        }
        
        # Only include insights if generated
        if generate_insights:
            response['extracted'] = result.get('extracted', {})
            response['risk'] = result.get('risk', {})
            response['summary'] = result.get('summary', '')
        
        return jsonify(response)
        
    except Exception as e:
        print(f'Error in /api/diabuddies: {e}')
        import traceback
        traceback.print_exc()
        
        # Provide user-friendly error messages
        error_msg = str(e)
        if 'invalid_api_key' in error_msg or '401' in error_msg:
            return jsonify({
                'error': 'Invalid OpenAI API key',
                'message': 'Please check your OPENAI_API_KEY in backend/.env file. Get your key at https://platform.openai.com/account/api-keys'
            }), 500
        
        return jsonify({'error': 'Server error', 'details': str(e)}), 500


@app.route('/')
def index():
    """Serve the frontend."""
    return app.send_static_file('index.html')


@app.route('/provider')
def provider_portal():
    """Serve the provider portal."""
    return app.send_static_file('provider.html')


@app.route('/api/insights', methods=['POST'])
def generate_insights():
    """Generate insights from the full conversation history."""
    try:
        data = request.json
        session_id = data.get('sessionId')
        
        if not session_id:
            return jsonify({'error': 'Missing sessionId'}), 400
        
        if session_id not in sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session = sessions[session_id]
        
        # Use the last user message or combine all messages
        last_user_msg = ""
        if session['conversation_history']:
            for msg in reversed(session['conversation_history']):
                if msg.get('role') == 'user':
                    last_user_msg = msg.get('content', '')
                    break
        
        if not last_user_msg:
            last_user_msg = "Generate insights from this conversation"
        
        initial_state = {
            'user_message': last_user_msg,
            'conversation_history': session['conversation_history'],
            'reply': '',
            'extracted': {},
            'risk': {},
            'summary': '',
            'is_emergency': False
        }
        
        # Run full insights pipeline
        result = diabuddies_graph.invoke(initial_state)
        
        return jsonify({
            'extracted': result.get('extracted', {}),
            'risk': result.get('risk', {}),
            'summary': result.get('summary', '')
        })
        
    except Exception as e:
        print(f'Error in /api/insights: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Server error', 'details': str(e)}), 500


# ==================== DOCTOR ENDPOINTS ====================

@app.route('/api/doctors', methods=['POST'])
def create_doctor():
    """Create a new doctor/healthcare provider."""
    try:
        data = request.json
        doctor = Doctor(
            doctor_id=str(uuid.uuid4()),
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            specialty=data.get('specialty')
        )
        storage.create_doctor(doctor)
        return jsonify(doctor.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/doctors/<doctor_id>', methods=['GET'])
def get_doctor(doctor_id):
    """Get doctor information."""
    try:
        doctor = storage.get_doctor(doctor_id)
        if not doctor:
            return jsonify({'error': 'Doctor not found'}), 404
        return jsonify(doctor.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/doctors/<doctor_id>/patients', methods=['GET'])
def get_doctors_patients(doctor_id):
    """Get all patients for a doctor."""
    try:
        patients = storage.get_doctors_patients(doctor_id)
        return jsonify([p.to_dict() for p in patients])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/doctors/<doctor_id>/patients/<patient_id>/care-plan', methods=['POST'])
def setup_care_plan(doctor_id, patient_id):
    """Doctor sets up care plan for a patient."""
    try:
        data = request.json
        
        # Create medications
        medications = [
            Medication(
                name=med['name'],
                dosage=med['dosage'],
                frequency=med.get('frequency', 'as prescribed'),
                times=med.get('times', []),
                start_date=med.get('start_date', datetime.now().isoformat()),
                notes=med.get('notes')
            )
            for med in data.get('medications', [])
        ]
        
        # Create glucose targets
        glucose_targets = GlucoseTarget(
            fasting_min=data.get('glucose_targets', {}).get('fasting_min', 80),
            fasting_max=data.get('glucose_targets', {}).get('fasting_max', 130),
            post_meal_min=data.get('glucose_targets', {}).get('post_meal_min', 80),
            post_meal_max=data.get('glucose_targets', {}).get('post_meal_max', 180),
            hba1c_target=data.get('glucose_targets', {}).get('hba1c_target')
        )
        
        # Create health goals
        health_goals = HealthGoals(
            weight_target=data.get('health_goals', {}).get('weight_target'),
            activity_minutes_per_week=data.get('health_goals', {}).get('activity_minutes_per_week'),
            dietary_goals=data.get('health_goals', {}).get('dietary_goals'),
            other_goals=data.get('health_goals', {}).get('other_goals')
        )
        
        # Create care plan
        care_plan = CarePlan(
            patient_id=patient_id,
            doctor_id=doctor_id,
            created_at=datetime.now().isoformat(),
            medications=medications,
            glucose_targets=glucose_targets,
            health_goals=health_goals,
            dietary_recommendations=data.get('dietary_recommendations'),
            notes=data.get('notes')
        )
        
        storage.set_care_plan(care_plan)
        
        # Update patient's doctor_id if needed
        patient = storage.get_patient(patient_id)
        if patient:
            if not patient.doctor_id:
                storage.update_patient(patient_id, doctor_id=doctor_id)
        
        return jsonify(care_plan.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/doctors/<doctor_id>/patients/<patient_id>/report/weekly', methods=['GET'])
def get_weekly_report(doctor_id, patient_id):
    """Get weekly report for a patient."""
    try:
        report = generate_weekly_report(patient_id)
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/doctors/<doctor_id>/patients/<patient_id>/report/monthly', methods=['GET'])
def get_monthly_report(doctor_id, patient_id):
    """Get monthly report for a patient."""
    try:
        report = generate_monthly_report(patient_id)
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== PATIENT ENDPOINTS ====================

@app.route('/api/patients', methods=['POST'])
def create_patient():
    """Create a new patient."""
    try:
        data = request.json
        patient = Patient(
            patient_id=str(uuid.uuid4()),
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            date_of_birth=data.get('date_of_birth'),
            doctor_id=data.get('doctor_id')
        )
        storage.create_patient(patient)
        return jsonify(patient.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patients/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Get patient information."""
    try:
        patient = storage.get_patient(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        return jsonify(patient.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== DATA LOGGING ENDPOINTS ====================

@app.route('/api/patients/<patient_id>/glucose', methods=['POST'])
def log_glucose(patient_id):
    """Log blood glucose reading."""
    try:
        data = request.json
        log = GlucoseLog(
            log_id=str(uuid.uuid4()),
            patient_id=patient_id,
            reading=float(data['reading']),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            reading_type=data.get('reading_type', 'random'),
            notes=data.get('notes')
        )
        storage.add_glucose_log(log)
        
        # Check for alerts
        alert = check_glucose_alerts(patient_id, log.reading, log.reading_type)
        
        response = {'log': log.to_dict()}
        if alert:
            response['alert'] = alert.to_dict()
        
        return jsonify(response), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patients/<patient_id>/medication', methods=['POST'])
def log_medication(patient_id):
    """Log medication intake."""
    try:
        data = request.json
        log = MedicationLog(
            log_id=str(uuid.uuid4()),
            patient_id=patient_id,
            medication_name=data['medication_name'],
            dosage=data.get('dosage', ''),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            taken=data.get('taken', True),
            notes=data.get('notes')
        )
        storage.add_medication_log(log)
        return jsonify(log.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patients/<patient_id>/meal', methods=['POST'])
def log_meal(patient_id):
    """Log a meal."""
    try:
        data = request.json
        log = MealLog(
            log_id=str(uuid.uuid4()),
            patient_id=patient_id,
            meal_type=data.get('meal_type', 'meal'),
            description=data['description'],
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            carbs_estimate=data.get('carbs_estimate'),
            notes=data.get('notes')
        )
        storage.add_meal_log(log)
        return jsonify(log.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patients/<patient_id>/activity', methods=['POST'])
def log_activity(patient_id):
    """Log physical activity."""
    try:
        data = request.json
        log = ActivityLog(
            log_id=str(uuid.uuid4()),
            patient_id=patient_id,
            activity_type=data['activity_type'],
            duration_minutes=int(data['duration_minutes']),
            intensity=data.get('intensity', 'moderate'),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            notes=data.get('notes')
        )
        storage.add_activity_log(log)
        return jsonify(log.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patients/<patient_id>/logs', methods=['GET'])
def get_patient_logs(patient_id):
    """Get all logs for a patient."""
    try:
        days = int(request.args.get('days', 30))
        return jsonify({
            'glucose': [log.to_dict() for log in storage.get_glucose_logs(patient_id, days)],
            'medication': [log.to_dict() for log in storage.get_medication_logs(patient_id, days)],
            'meals': [log.to_dict() for log in storage.get_meal_logs(patient_id, days)],
            'activity': [log.to_dict() for log in storage.get_activity_logs(patient_id, days)]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patients/<patient_id>/summary', methods=['GET'])
def get_patient_summary(patient_id):
    """Get aggregated summary for patient (for intelligent sync)."""
    try:
        days = int(request.args.get('days', 7))
        
        # Check if patient has doctor reporting enabled
        patient = storage.get_patient(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        if hasattr(patient, 'doctor_reporting_enabled') and not patient.doctor_reporting_enabled:
            return jsonify({'error': 'Doctor reporting disabled by patient'}), 403
        
        # Get aggregated data
        tir_data = calculate_time_in_range(patient_id, days=days)
        glucose_logs = storage.get_glucose_logs(patient_id, days=days)
        medication_logs = storage.get_medication_logs(patient_id, days=days)
        activity_logs = storage.get_activity_logs(patient_id, days=days)
        meal_logs = storage.get_meal_logs(patient_id, days=days)
        
        # Calculate averages and extremes
        glucose_readings = [log.reading for log in glucose_logs]
        avg_glucose = sum(glucose_readings) / len(glucose_readings) if glucose_readings else None
        min_glucose = min(glucose_readings) if glucose_readings else None
        max_glucose = max(glucose_readings) if glucose_readings else None
        
        # Medication adherence
        care_plan = storage.get_care_plan(patient_id)
        adherence = None
        if care_plan and care_plan.medications:
            total_doses = len([m for m in care_plan.medications for _ in m.times]) * days
            taken_doses = len([log for log in medication_logs if log.taken])
            adherence = (taken_doses / total_doses * 100) if total_doses > 0 else 0
        
        # Activity summary
        total_activity = sum(log.duration_minutes for log in activity_logs)
        
        return jsonify({
            'patient_id': patient_id,
            'period_days': days,
            'time_in_range': tir_data,
            'glucose': {
                'average': round(avg_glucose, 1) if avg_glucose else None,
                'min': min_glucose,
                'max': max_glucose,
                'readings_count': len(glucose_readings)
            },
            'medication_adherence': round(adherence, 1) if adherence is not None else None,
            'activity_minutes': total_activity,
            'meals_logged': len(meal_logs),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== ALERT ENDPOINTS ====================

@app.route('/api/patients/<patient_id>/alerts', methods=['GET'])
def get_alerts(patient_id):
    """Get alerts for a patient."""
    try:
        unacknowledged_only = request.args.get('unacknowledged_only', 'false').lower() == 'true'
        alerts = storage.get_alerts(patient_id, unacknowledged_only=unacknowledged_only)
        return jsonify([a.to_dict() for a in alerts])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patients/<patient_id>/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(patient_id, alert_id):
    """Acknowledge an alert."""
    try:
        success = storage.acknowledge_alert(patient_id, alert_id)
        if success:
            return jsonify({'status': 'acknowledged'})
        return jsonify({'error': 'Alert not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patients/<patient_id>/alerts/check', methods=['POST'])
def check_alerts(patient_id):
    """Manually trigger alert checks (missed doses, etc.)."""
    try:
        missed_dose_alerts = check_missed_doses(patient_id)
        return jsonify({
            'alerts_created': len(missed_dose_alerts),
            'alerts': [a.to_dict() for a in missed_dose_alerts]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== REMINDER ENDPOINTS ====================

@app.route('/api/patients/<patient_id>/reminders', methods=['GET'])
def get_reminders(patient_id):
    """Get reminders for a patient."""
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        reminders = storage.get_reminders(patient_id, active_only=active_only)
        return jsonify([r.to_dict() for r in reminders])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patients/<patient_id>/reminders/generate', methods=['POST'])
def generate_patient_reminders(patient_id):
    """Generate reminders for a patient based on care plan."""
    try:
        reminders = generate_reminders(patient_id)
        return jsonify({
            'reminders_generated': len(reminders),
            'reminders': [r.to_dict() for r in reminders]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patients/<patient_id>/sms/reminder', methods=['POST'])
def send_sms_reminder(patient_id):
    """Send SMS reminder manually."""
    try:
        if not SMS_AVAILABLE or not sms_service or not sms_service.available:
            return jsonify({'error': 'SMS service not available'}), 503
        
        data = request.json
        reminder_type = data.get('type', 'medication')  # medication, glucose_check, meal
        
        patient = storage.get_patient(patient_id)
        if not patient or not patient.phone:
            return jsonify({'error': 'Patient not found or no phone number'}), 404
        
        result = {}
        if reminder_type == 'medication':
            medication_name = data.get('medication_name', 'your medication')
            dosage = data.get('dosage', '')
            time = data.get('time', 'now')
            result = sms_service.send_medication_reminder(patient.phone, medication_name, dosage, time)
        elif reminder_type == 'glucose_check':
            check_type = data.get('check_type', 'routine')
            result = sms_service.send_glucose_check_reminder(patient.phone, check_type)
        else:
            return jsonify({'error': 'Invalid reminder type'}), 400
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== APPOINTMENT ENDPOINTS ====================

@app.route('/api/patients/<patient_id>/appointments', methods=['POST'])
def request_appointment(patient_id):
    """Request an appointment with doctor (non-emergency)."""
    try:
        data = request.json
        patient = storage.get_patient(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        if not patient.doctor_id:
            return jsonify({'error': 'No doctor assigned'}), 400
        
        doctor = storage.get_doctor(patient.doctor_id)
        if not doctor:
            return jsonify({'error': 'Doctor not found'}), 404
        
        # In production, this would integrate with appointment booking system
        # For now, return a confirmation with doctor contact info
        appointment_request = {
            'appointment_id': str(uuid.uuid4()),
            'patient_id': patient_id,
            'doctor_id': patient.doctor_id,
            'requested_date': data.get('preferred_date'),
            'reason': data.get('reason', 'Routine check-up'),
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'doctor_contact': {
                'name': doctor.name,
                'email': doctor.email,
                'phone': doctor.phone
            },
            'message': f'Appointment request submitted. Doctor will contact you at {patient.email or patient.phone}'
        }
        
        return jsonify(appointment_request), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patients/<patient_id>/emergency', methods=['POST'])
def emergency_contact(patient_id):
    """Emergency contact - connects directly to doctor."""
    try:
        patient = storage.get_patient(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        if not patient.doctor_id:
            return jsonify({
                'emergency': True,
                'message': 'No doctor assigned. Please call 911 or go to emergency room immediately.',
                'emergency_services': '911'
            }), 200
        
        doctor = storage.get_doctor(patient.doctor_id)
        if not doctor:
            return jsonify({
                'emergency': True,
                'message': 'Doctor not found. Please call 911 or go to emergency room immediately.',
                'emergency_services': '911'
            }), 200
        
        # Create critical alert
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            patient_id=patient_id,
            alert_type='critical',
            severity='critical',
            message='Emergency contact requested by patient',
            timestamp=datetime.now().isoformat(),
            doctor_notified=True
        )
        storage.create_alert(alert)
        
        return jsonify({
            'emergency': True,
            'alert_id': alert.alert_id,
            'doctor_contact': {
                'name': doctor.name,
                'email': doctor.email,
                'phone': doctor.phone
            },
            'message': f'Emergency alert sent to Dr. {doctor.name}. They will contact you immediately.',
            'backup': 'If unable to reach doctor, call 911 or go to emergency room.'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== VOICE CALL ENDPOINTS ====================

@app.route('/api/voice/call/initiate', methods=['POST'])
def initiate_voice_call():
    """Initiate an outbound phone call to a patient."""
    if not VOICE_AVAILABLE or not voice_handler:
        return jsonify({
            'error': 'Voice calls not available',
            'message': 'Install Twilio: pip3 install twilio and configure TWILIO_* environment variables'
        }), 503
    
    try:
        data = request.json
        patient_phone = data.get('phone_number')
        patient_id = data.get('patient_id')
        
        if not patient_phone:
            return jsonify({'error': 'phone_number is required'}), 400
        
        # Validate phone number format (should be E.164: +1234567890)
        if not patient_phone.startswith('+'):
            return jsonify({
                'error': 'Phone number must be in E.164 format (e.g., +1234567890)',
                'example': '+1234567890'
            }), 400
        
        result = voice_handler.initiate_call(patient_phone, patient_id)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'call_sid': result['call_sid'],
            'status': result['status'],
            'message': f'Call initiated to {result["to"]}'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/call', methods=['POST', 'GET'])
def handle_voice_call():
    """
    Twilio webhook endpoint for incoming calls.
    Returns TwiML to start the conversation.
    """
    if not VOICE_AVAILABLE or not voice_handler:
        return Response('<?xml version="1.0" encoding="UTF-8"?><Response><Say>Service unavailable</Say></Response>', mimetype='text/xml'), 503
    
    try:
        # Get patient_id from query parameter or Twilio request
        patient_id = request.args.get('patient_id') or request.form.get('patient_id')
        call_sid = request.form.get('CallSid')
        
        # Generate TwiML response
        twiml = voice_handler.handle_incoming_call(patient_id)
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"Error handling voice call: {e}")
        if VOICE_AVAILABLE:
            from twilio.twiml.voice_response import VoiceResponse
            response = VoiceResponse()
            response.say("I'm sorry, there was an error. Please try calling back later.", voice='alice')
            response.hangup()
            return Response(str(response), mimetype='text/xml')
        return Response('<?xml version="1.0" encoding="UTF-8"?><Response><Say>Service unavailable</Say></Response>', mimetype='text/xml'), 503


@app.route('/api/voice/process', methods=['POST'])
def process_voice_input():
    """
    Process speech input from Twilio and return TwiML response.
    This is called after each speech input from the user.
    """
    if not VOICE_AVAILABLE or not voice_handler:
        return Response('<?xml version="1.0" encoding="UTF-8"?><Response><Say>Service unavailable</Say></Response>', mimetype='text/xml'), 503
    
    try:
        # Get speech result from Twilio
        speech_result = request.form.get('SpeechResult') or request.form.get('Digits')
        patient_id = request.args.get('patient_id') or request.form.get('patient_id')
        call_sid = request.form.get('CallSid') or request.args.get('call_sid')
        
        # Also check for partial results
        if not speech_result:
            speech_result = request.form.get('UnstableSpeechResult')
        
        # Generate TwiML response with agent's reply
        twiml = voice_handler.process_speech(speech_result, patient_id, call_sid)
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"Error processing voice input: {e}")
        if VOICE_AVAILABLE:
            from twilio.twiml.voice_response import VoiceResponse, Gather
            response = VoiceResponse()
            response.say("I'm sorry, I'm having trouble understanding. Could you repeat that?", voice='alice')
            
            # Re-gather input
            gather = Gather(
                input='speech',
                action='/api/voice/process',
                method='POST',
                speech_timeout='auto',
                language='en-US'
            )
            response.append(gather)
            
            return Response(str(response), mimetype='text/xml')
        return Response('<?xml version="1.0" encoding="UTF-8"?><Response><Say>Service unavailable</Say></Response>', mimetype='text/xml'), 503


@app.route('/api/voice/partial', methods=['POST'])
def handle_partial_speech():
    """
    Handle partial speech results (optional - for real-time feedback).
    """
    try:
        partial_result = request.form.get('UnstableSpeechResult', '')
        # Could log or process partial results for better UX
        return Response('', mimetype='text/xml')
    except:
        return Response('', mimetype='text/xml')


@app.route('/api/voice/status', methods=['POST'])
def handle_call_status():
    """
    Twilio status callback webhook.
    Called when call status changes (ringing, in-progress, completed, etc.).
    """
    try:
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        duration = request.form.get('CallDuration')
        
        voice_handler.handle_call_status(call_sid, call_status)
        
        # Log call completion
        if call_status == 'completed' and duration:
            print(f"Call {call_sid} completed. Duration: {duration} seconds")
        
        return Response('', mimetype='text/xml')
        
    except Exception as e:
        print(f"Error handling call status: {e}")
        return Response('', mimetype='text/xml')


# ==================== COMMUNITY ENDPOINTS ====================

@app.route('/api/community/posts', methods=['GET'])
def get_community_posts():
    """Get all community posts."""
    try:
        posts = storage.get_posts()
        # Add author names and comment counts
        result = []
        for post in posts:
            patient = storage.get_patient(post.patient_id)
            comments = storage.get_comments(post.post_id)
            result.append({
                **post.to_dict(),
                'author_name': patient.name if patient else 'Anonymous',
                'comment_count': len(comments)
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/community/posts', methods=['POST'])
def create_community_post():
    """Create a new community post."""
    try:
        data = request.json
        patient_id = data.get('patient_id')
        content = data.get('content')
        
        if not patient_id or not content:
            return jsonify({'error': 'patient_id and content are required'}), 400
        
        post = CommunityPost(
            post_id=str(uuid.uuid4()),
            patient_id=patient_id,
            content=content,
            created_at=datetime.now().isoformat(),
            likes=0
        )
        storage.create_post(post)
        return jsonify(post.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/community/posts/<post_id>/like', methods=['POST'])
def like_post(post_id):
    """Like a community post."""
    try:
        success = storage.like_post(post_id)
        if success:
            return jsonify({'status': 'liked'})
        return jsonify({'error': 'Post not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/community/posts/<post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    """Get comments for a post."""
    try:
        comments = storage.get_comments(post_id)
        # Add author names
        result = []
        for comment in comments:
            patient = storage.get_patient(comment.patient_id)
            result.append({
                **comment.to_dict(),
                'author_name': patient.name if patient else 'Anonymous'
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/community/posts/<post_id>/comments', methods=['POST'])
def add_comment(post_id):
    """Add a comment to a post."""
    try:
        data = request.json
        patient_id = data.get('patient_id')
        content = data.get('content')
        
        if not patient_id or not content:
            return jsonify({'error': 'patient_id and content are required'}), 400
        
        comment = Comment(
            comment_id=str(uuid.uuid4()),
            post_id=post_id,
            patient_id=patient_id,
            content=content,
            created_at=datetime.now().isoformat()
        )
        storage.add_comment(comment)
        return jsonify(comment.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== DOCTOR MESSAGING ENDPOINTS ====================

@app.route('/api/patients/<patient_id>/messages', methods=['GET'])
def get_doctor_messages(patient_id):
    """Get all messages between patient and doctor."""
    try:
        messages = storage.get_doctor_messages(patient_id)
        # Add doctor names
        result = []
        for msg in messages:
            msg_dict = msg.to_dict()
            if msg.doctor_id:
                doctor = storage.get_doctor(msg.doctor_id)
                if doctor:
                    msg_dict['doctor_name'] = doctor.name
            result.append(msg_dict)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patients/<patient_id>/messages', methods=['POST'])
def send_doctor_message(patient_id):
    """Send a message from patient to doctor or vice versa."""
    try:
        data = request.json
        message_text = data.get('message')
        from_patient = data.get('from_patient', True)
        doctor_id = data.get('doctor_id')
        
        if not message_text:
            return jsonify({'error': 'message is required'}), 400
        
        # If from patient, get their doctor_id
        if from_patient:
            patient = storage.get_patient(patient_id)
            if not patient:
                return jsonify({'error': 'Patient not found'}), 404
            doctor_id = patient.doctor_id
        
        message = DoctorMessage(
            message_id=str(uuid.uuid4()),
            patient_id=patient_id,
            doctor_id=doctor_id,
            message=message_text,
            from_patient=from_patient,
            timestamp=datetime.now().isoformat(),
            read=False
        )
        storage.add_doctor_message(message)
        return jsonify(message.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/doctors/<doctor_id>/patients/<patient_id>/messages', methods=['POST'])
def send_doctor_to_patient_message(doctor_id, patient_id):
    """Doctor sends a message to patient."""
    try:
        data = request.json
        message_text = data.get('message')
        
        if not message_text:
            return jsonify({'error': 'message is required'}), 400
        
        message = DoctorMessage(
            message_id=str(uuid.uuid4()),
            patient_id=patient_id,
            doctor_id=doctor_id,
            message=message_text,
            from_patient=False,
            timestamp=datetime.now().isoformat(),
            read=False
        )
        storage.add_doctor_message(message)
        return jsonify(message.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
