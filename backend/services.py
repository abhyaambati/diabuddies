"""Business logic services for Diabuddies."""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid
from models import (
    Alert, Reminder, GlucoseLog, MedicationLog, CarePlan, Medication
)
from storage import storage
try:
    from sms_service import sms_service
    SMS_AVAILABLE = True
except ImportError:
    SMS_AVAILABLE = False
    sms_service = None


def check_missed_doses(patient_id: str) -> List[Alert]:
    """Check for missed medication doses and create alerts."""
    alerts = []
    care_plan = storage.get_care_plan(patient_id)
    if not care_plan or not care_plan.medications:
        return alerts
    
    now = datetime.now()
    today = now.date()
    
    # Get medication logs for today
    medication_logs = storage.get_medication_logs(patient_id, days=1)
    today_logs = {
        (log.medication_name, log.timestamp[:10]): log.taken
        for log in medication_logs
        if log.timestamp[:10] == today.isoformat()
    }
    
    # Check each medication
    for med in care_plan.medications:
        for med_time in med.times:
            # Parse time (e.g., "08:00")
            hour, minute = map(int, med_time.split(':'))
            scheduled_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
            
            # Check if it's past the scheduled time (with 30 min grace period)
            if now > scheduled_time + timedelta(minutes=30):
                key = (med.name, today.isoformat())
                if key not in today_logs or not today_logs[key]:
                    # Check if we already created an alert for this
                    existing_alerts = storage.get_alerts(patient_id, unacknowledged_only=True)
                    alert_exists = any(
                        a.alert_type == 'missed_dose' and
                        med.name in a.message and
                        a.timestamp[:10] == today.isoformat()
                        for a in existing_alerts
                    )
                    
                    if not alert_exists:
                        alert = Alert(
                            alert_id=str(uuid.uuid4()),
                            patient_id=patient_id,
                            alert_type='missed_dose',
                            severity='medium',
                            message=f"Missed {med.name} dose scheduled for {med_time}",
                            timestamp=now.isoformat()
                        )
                        storage.create_alert(alert)
                        alerts.append(alert)
    
    return alerts


def check_glucose_alerts(patient_id: str, reading: float, reading_type: str) -> Optional[Alert]:
    """Check glucose reading and create alert if needed."""
    care_plan = storage.get_care_plan(patient_id)
    if not care_plan:
        return None
    
    targets = care_plan.glucose_targets
    severity = 'low'
    alert_type = 'low_glucose'
    message = ""
    
    if reading_type == 'fasting':
        if reading < targets.fasting_min:
            severity = 'high' if reading < 70 else 'medium'
            alert_type = 'low_glucose'
            message = f"Low fasting glucose: {reading} mg/dL (target: {targets.fasting_min}-{targets.fasting_max})"
        elif reading > targets.fasting_max:
            severity = 'high' if reading > 250 else 'medium'
            alert_type = 'high_glucose'
            message = f"High fasting glucose: {reading} mg/dL (target: {targets.fasting_min}-{targets.fasting_max})"
    else:  # post_meal or random
        if reading < targets.post_meal_min:
            severity = 'critical' if reading < 70 else 'high'
            alert_type = 'low_glucose'
            message = f"Low glucose: {reading} mg/dL (target: {targets.post_meal_min}-{targets.post_meal_max})"
        elif reading > targets.post_meal_max:
            severity = 'critical' if reading > 300 else 'high'
            alert_type = 'high_glucose'
            message = f"High glucose: {reading} mg/dL (target: {targets.post_meal_min}-{targets.post_meal_max})"
    
    if message:
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            patient_id=patient_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.now().isoformat()
        )
        storage.create_alert(alert)
        
        # If critical, notify doctor immediately and send SMS
        if severity == 'critical':
            alert.doctor_notified = True
            storage.save()
            
            # Send SMS alert to patient and emergency contact
            if SMS_AVAILABLE and sms_service and sms_service.available:
                patient = storage.get_patient(patient_id)
                if patient and patient.phone:
                    emergency_contact = patient.emergency_contact_phone if hasattr(patient, 'emergency_contact_phone') else None
                    sms_service.send_critical_alert(
                        patient.phone,
                        emergency_contact,
                        reading,
                        reading_type
                    )
        
        return alert
    
    return None


def generate_reminders(patient_id: str) -> List[Reminder]:
    """Generate reminders based on care plan."""
    care_plan = storage.get_care_plan(patient_id)
    if not care_plan:
        return []
    
    reminders = []
    now = datetime.now()
    today = now.date()
    
    # Medication reminders
    for med in care_plan.medications:
        for med_time in med.times:
            hour, minute = map(int, med_time.split(':'))
            reminder_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
            
            # Only create reminder if it's in the future (within next hour)
            if now < reminder_time < now + timedelta(hours=1):
                # Check if reminder already exists
                existing = storage.get_reminders(patient_id, active_only=True)
                reminder_exists = any(
                    r.reminder_type == 'medication' and
                    med.name in r.message and
                    r.scheduled_time[:16] == reminder_time.isoformat()[:16]
                    for r in existing
                )
                
                if not reminder_exists:
                    reminder = Reminder(
                        reminder_id=str(uuid.uuid4()),
                        patient_id=patient_id,
                        reminder_type='medication',
                        message=f"Time to take {med.name} ({med.dosage})",
                        scheduled_time=reminder_time.isoformat(),
                        frequency='daily'
                    )
                    storage.create_reminder(reminder)
                    reminders.append(reminder)
                    
                    # Send SMS reminder if enabled
                    if SMS_AVAILABLE and sms_service and sms_service.available:
                        patient = storage.get_patient(patient_id)
                        if patient and patient.phone and (hasattr(patient, 'sms_medication_reminders') and patient.sms_medication_reminders or not hasattr(patient, 'sms_medication_reminders')):
                            sms_service.send_medication_reminder(
                                patient.phone,
                                med.name,
                                med.dosage,
                                med_time
                            )
    
    return reminders


def calculate_time_in_range(patient_id: str, days: int = 7) -> Dict:
    """Calculate Time In Range (TIR) - percentage of readings within target range."""
    care_plan = storage.get_care_plan(patient_id)
    if not care_plan:
        return {'tir_percentage': None, 'total_readings': 0, 'in_range': 0}
    
    glucose_logs = storage.get_glucose_logs(patient_id, days=days)
    targets = care_plan.glucose_targets
    
    if not glucose_logs:
        return {'tir_percentage': None, 'total_readings': 0, 'in_range': 0}
    
    in_range_count = 0
    total_readings = len(glucose_logs)
    
    for log in glucose_logs:
        reading = log.reading
        reading_type = log.reading_type
        
        # Determine target range based on reading type
        if reading_type == 'fasting':
            min_target = targets.fasting_min
            max_target = targets.fasting_max
        else:  # post_meal, random, bedtime
            min_target = targets.post_meal_min
            max_target = targets.post_meal_max
        
        # Check if reading is in range
        if min_target <= reading <= max_target:
            in_range_count += 1
    
    tir_percentage = (in_range_count / total_readings * 100) if total_readings > 0 else 0
    
    return {
        'tir_percentage': round(tir_percentage, 1),
        'total_readings': total_readings,
        'in_range': in_range_count,
        'below_range': len([log for log in glucose_logs if log.reading < (targets.fasting_min if log.reading_type == 'fasting' else targets.post_meal_min)]),
        'above_range': len([log for log in glucose_logs if log.reading > (targets.fasting_max if log.reading_type == 'fasting' else targets.post_meal_max)])
    }


def generate_weekly_report(patient_id: str) -> Dict:
    """Generate weekly report for doctor."""
    care_plan = storage.get_care_plan(patient_id)
    if not care_plan:
        return {}
    
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    
    # Get logs
    glucose_logs = [log for log in storage.get_glucose_logs(patient_id, days=7)
                    if datetime.fromisoformat(log.timestamp) >= week_ago]
    medication_logs = [log for log in storage.get_medication_logs(patient_id, days=7)
                      if datetime.fromisoformat(log.timestamp) >= week_ago]
    meal_logs = storage.get_meal_logs(patient_id, days=7)
    activity_logs = storage.get_activity_logs(patient_id, days=7)
    alerts = [a for a in storage.get_alerts(patient_id)
              if datetime.fromisoformat(a.timestamp) >= week_ago]
    
    # Calculate statistics
    glucose_readings = [log.reading for log in glucose_logs]
    avg_glucose = sum(glucose_readings) / len(glucose_readings) if glucose_readings else None
    
    # Calculate Time In Range (TIR)
    tir_data = calculate_time_in_range(patient_id, days=7)
    
    # Medication adherence
    total_doses = len([m for m in care_plan.medications for _ in m.times]) * 7
    taken_doses = len([log for log in medication_logs if log.taken])
    adherence_rate = (taken_doses / total_doses * 100) if total_doses > 0 else 0
    
    # Activity
    total_activity_minutes = sum(log.duration_minutes for log in activity_logs)
    
    # Alerts
    critical_alerts = [a for a in alerts if a.severity == 'critical']
    high_severity_alerts = [a for a in alerts if a.severity == 'high']
    
    return {
        'patient_id': patient_id,
        'period': {
            'start': week_ago.isoformat(),
            'end': now.isoformat()
        },
        'glucose': {
            'average': avg_glucose,
            'readings_count': len(glucose_readings),
            'readings': [log.to_dict() for log in glucose_logs[-10:]],  # Last 10
            'time_in_range': tir_data
        },
        'medication_adherence': {
            'rate': round(adherence_rate, 1),
            'taken': taken_doses,
            'total_expected': total_doses
        },
        'activity': {
            'total_minutes': total_activity_minutes,
            'goal_minutes': care_plan.health_goals.activity_minutes_per_week,
            'logs': [log.to_dict() for log in activity_logs]
        },
        'alerts': {
            'total': len(alerts),
            'critical': len(critical_alerts),
            'high': len(high_severity_alerts),
            'recent': [a.to_dict() for a in alerts[:10]]
        },
        'meals_logged': len(meal_logs)
    }


def generate_monthly_report(patient_id: str) -> Dict:
    """Generate monthly report for doctor."""
    care_plan = storage.get_care_plan(patient_id)
    if not care_plan:
        return {}
    
    now = datetime.now()
    month_ago = now - timedelta(days=30)
    
    # Get logs
    glucose_logs = storage.get_glucose_logs(patient_id, days=30)
    medication_logs = storage.get_medication_logs(patient_id, days=30)
    activity_logs = storage.get_activity_logs(patient_id, days=30)
    alerts = storage.get_alerts(patient_id)
    
    # Calculate statistics
    glucose_readings = [log.reading for log in glucose_logs]
    avg_glucose = sum(glucose_readings) / len(glucose_readings) if glucose_readings else None
    
    # Calculate Time In Range (TIR)
    tir_data = calculate_time_in_range(patient_id, days=30)
    
    # Medication adherence
    total_doses = len([m for m in care_plan.medications for _ in m.times]) * 30
    taken_doses = len([log for log in medication_logs if log.taken])
    adherence_rate = (taken_doses / total_doses * 100) if total_doses > 0 else 0
    
    # Activity
    total_activity_minutes = sum(log.duration_minutes for log in activity_logs)
    avg_per_week = total_activity_minutes / 4.3  # Approximate weeks in month
    
    # Enhanced Pattern Detection
    high_glucose_days = len(set(log.timestamp[:10] for log in glucose_logs if log.reading > care_plan.glucose_targets.post_meal_max))
    low_glucose_days = len(set(log.timestamp[:10] for log in glucose_logs if log.reading < care_plan.glucose_targets.post_meal_min))
    
    # Time-of-day patterns
    patterns = {
        'morning_spikes': 0,  # Dawn phenomenon
        'evening_spikes': 0,   # Post-dinner
        'nighttime_lows': 0,    # Nocturnal hypoglycemia
        'post_meal_spikes': 0
    }
    
    if glucose_logs:
        for log in glucose_logs:
            hour = datetime.fromisoformat(log.timestamp).hour
            reading = log.reading
            
            # Morning (6-12): Check for dawn phenomenon
            if 6 <= hour < 12 and reading > care_plan.glucose_targets.fasting_max:
                patterns['morning_spikes'] += 1
            
            # Evening (17-22): Check for post-dinner spikes
            if 17 <= hour < 22 and reading > care_plan.glucose_targets.post_meal_max:
                patterns['evening_spikes'] += 1
            
            # Nighttime (22-6): Check for lows
            if (hour >= 22 or hour < 6) and reading < care_plan.glucose_targets.fasting_min:
                patterns['nighttime_lows'] += 1
            
            # Post-meal spikes (any time after meal logging)
            if log.reading_type == 'post_meal' and reading > care_plan.glucose_targets.post_meal_max:
                patterns['post_meal_spikes'] += 1
    
    # Pattern summary
    pattern_summary = []
    if patterns['morning_spikes'] > len(glucose_logs) * 0.3:  # >30% of readings
        pattern_summary.append(f"Consistent morning glucose spikes detected ({patterns['morning_spikes']} occurrences) - possible dawn phenomenon")
    if patterns['evening_spikes'] > len(glucose_logs) * 0.3:
        pattern_summary.append(f"Consistent evening glucose spikes ({patterns['evening_spikes']} occurrences) - review dinner timing and carb intake")
    if patterns['nighttime_lows'] > len(glucose_logs) * 0.2:  # >20% of readings
        pattern_summary.append(f"Nighttime hypoglycemia detected ({patterns['nighttime_lows']} occurrences) - consider adjusting evening medication")
    if patterns['post_meal_spikes'] > len(glucose_logs) * 0.4:
        pattern_summary.append(f"Frequent post-meal spikes ({patterns['post_meal_spikes']} occurrences) - review meal composition and timing")
    
    return {
        'patient_id': patient_id,
        'period': {
            'start': month_ago.isoformat(),
            'end': now.isoformat()
        },
        'glucose': {
            'average': avg_glucose,
            'readings_count': len(glucose_readings),
            'high_days': high_glucose_days,
            'low_days': low_glucose_days,
            'time_in_range': tir_data,
            'patterns': patterns,
            'pattern_summary': pattern_summary
        },
        'medication_adherence': {
            'rate': round(adherence_rate, 1),
            'taken': taken_doses,
            'total_expected': total_doses
        },
        'activity': {
            'total_minutes': total_activity_minutes,
            'average_per_week': round(avg_per_week, 1),
            'goal_minutes': care_plan.health_goals.activity_minutes_per_week
        },
        'alerts': {
            'total': len(alerts),
            'by_type': {}
        },
        'summary': f"Patient showed {high_glucose_days} days with high glucose and {low_glucose_days} days with low glucose. Medication adherence: {round(adherence_rate, 1)}%. Time In Range: {tir_data['tir_percentage']}%. " + (' '.join(pattern_summary) if pattern_summary else 'No significant patterns detected.')
    }

