"""Simple JSON-based storage for Diabuddies system."""
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from models import (
    Patient, Doctor, CarePlan, Medication, GlucoseTarget, HealthGoals,
    GlucoseLog, MedicationLog, MealLog, ActivityLog, Alert, Reminder,
    CommunityPost, Comment, DoctorMessage
)


class Storage:
    """Simple file-based storage (can be upgraded to database later)."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
    
    def _load_data(self):
        """Load all data from files."""
        self.patients: Dict[str, Patient] = {}
        self.doctors: Dict[str, Doctor] = {}
        self.glucose_logs: Dict[str, List[GlucoseLog]] = {}
        self.medication_logs: Dict[str, List[MedicationLog]] = {}
        self.meal_logs: Dict[str, List[MealLog]] = {}
        self.activity_logs: Dict[str, List[ActivityLog]] = {}
        self.alerts: Dict[str, List[Alert]] = {}
        self.reminders: Dict[str, List[Reminder]] = {}
        self.community_posts: List[CommunityPost] = []
        self.comments: Dict[str, List[Comment]] = {}  # post_id -> comments
        self.doctor_messages: Dict[str, List[DoctorMessage]] = {}  # patient_id -> messages
        
        # Load from files if they exist
        self._load_file('patients.json', self.patients, Patient)
        self._load_file('doctors.json', self.doctors, Doctor)
        self._load_file('glucose_logs.json', self.glucose_logs, GlucoseLog, is_list=True)
        self._load_file('medication_logs.json', self.medication_logs, MedicationLog, is_list=True)
        self._load_file('meal_logs.json', self.meal_logs, MealLog, is_list=True)
        self._load_file('activity_logs.json', self.activity_logs, ActivityLog, is_list=True)
        self._load_file('alerts.json', self.alerts, Alert, is_list=True)
        self._load_file('reminders.json', self.reminders, Reminder, is_list=True)
        # Load community posts (special handling for global list)
        filepath = os.path.join(self.data_dir, 'community_posts.json')
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if 'posts' in data:
                        self.community_posts = [self._dict_to_model(item, CommunityPost) for item in data['posts']]
            except Exception as e:
                print(f"Error loading community_posts.json: {e}")
        
        self._load_file('comments.json', self.comments, Comment, is_list=True)
        self._load_file('doctor_messages.json', self.doctor_messages, DoctorMessage, is_list=True)
    
    def _load_file(self, filename: str, storage: Dict, model_class, is_list: bool = False):
        """Load data from JSON file."""
        filepath = os.path.join(self.data_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if is_list:
                        for key, items in data.items():
                            storage[key] = [self._dict_to_model(item, model_class) for item in items]
                    else:
                        for key, item in data.items():
                            storage[key] = self._dict_to_model(item, model_class)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    def _dict_to_model(self, data: Dict, model_class):
        """Convert dict to model instance."""
        if model_class == Patient:
            care_plan_data = data.get('care_plan')
            if care_plan_data:
                care_plan = self._dict_to_care_plan(care_plan_data)
                data['care_plan'] = care_plan
            return Patient(**{k: v for k, v in data.items() if k != 'care_plan' or v})
        elif model_class == Doctor:
            return Doctor(**data)
        elif model_class == GlucoseLog:
            return GlucoseLog(**data)
        elif model_class == MedicationLog:
            return MedicationLog(**data)
        elif model_class == MealLog:
            return MealLog(**data)
        elif model_class == ActivityLog:
            return ActivityLog(**data)
        elif model_class == Alert:
            return Alert(**data)
        elif model_class == Reminder:
            return Reminder(**data)
        elif model_class == CommunityPost:
            return CommunityPost(**data)
        elif model_class == Comment:
            return Comment(**data)
        elif model_class == DoctorMessage:
            return DoctorMessage(**data)
        return model_class(**data)
    
    def _dict_to_care_plan(self, data: Dict) -> CarePlan:
        """Convert dict to CarePlan."""
        from models import Medication, GlucoseTarget, HealthGoals
        medications = [Medication(**m) for m in data.get('medications', [])]
        glucose_targets = GlucoseTarget(**data.get('glucose_targets', {}))
        health_goals = HealthGoals(**data.get('health_goals', {}))
        return CarePlan(
            patient_id=data['patient_id'],
            doctor_id=data['doctor_id'],
            created_at=data['created_at'],
            medications=medications,
            glucose_targets=glucose_targets,
            health_goals=health_goals,
            dietary_recommendations=data.get('dietary_recommendations'),
            notes=data.get('notes')
        )
    
    def _save_file(self, filename: str, data: Dict):
        """Save data to JSON file."""
        filepath = os.path.join(self.data_dir, filename)
        serialized = {}
        for key, value in data.items():
            if isinstance(value, list):
                serialized[key] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in value]
            else:
                serialized[key] = value.to_dict() if hasattr(value, 'to_dict') else value
        
        with open(filepath, 'w') as f:
            json.dump(serialized, f, indent=2, default=str)
    
    def save(self):
        """Save all data to files."""
        self._save_file('patients.json', self.patients)
        self._save_file('doctors.json', self.doctors)
        self._save_file('glucose_logs.json', self.glucose_logs)
        self._save_file('medication_logs.json', self.medication_logs)
        self._save_file('meal_logs.json', self.meal_logs)
        self._save_file('activity_logs.json', self.activity_logs)
        self._save_file('alerts.json', self.alerts)
        self._save_file('reminders.json', self.reminders)
        # Save community posts (special handling for global list)
        filepath = os.path.join(self.data_dir, 'community_posts.json')
        with open(filepath, 'w') as f:
            json.dump({'posts': [p.to_dict() for p in self.community_posts]}, f, indent=2, default=str)
        self._save_file('comments.json', self.comments)
        self._save_file('doctor_messages.json', self.doctor_messages)
    
    # Patient methods
    def create_patient(self, patient: Patient) -> Patient:
        """Create a new patient."""
        self.patients[patient.patient_id] = patient
        self.save()
        return patient
    
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Get patient by ID."""
        return self.patients.get(patient_id)
    
    def update_patient(self, patient_id: str, **updates) -> Optional[Patient]:
        """Update patient information."""
        if patient_id not in self.patients:
            return None
        patient = self.patients[patient_id]
        for key, value in updates.items():
            setattr(patient, key, value)
        self.save()
        return patient
    
    # Doctor methods
    def create_doctor(self, doctor: Doctor) -> Doctor:
        """Create a new doctor."""
        self.doctors[doctor.doctor_id] = doctor
        self.save()
        return doctor
    
    def get_doctor(self, doctor_id: str) -> Optional[Doctor]:
        """Get doctor by ID."""
        return self.doctors.get(doctor_id)
    
    def get_doctors_patients(self, doctor_id: str) -> List[Patient]:
        """Get all patients for a doctor."""
        return [p for p in self.patients.values() if p.doctor_id == doctor_id]
    
    # Care plan methods
    def set_care_plan(self, care_plan: CarePlan):
        """Set or update care plan for a patient."""
        patient = self.get_patient(care_plan.patient_id)
        if patient:
            patient.care_plan = care_plan
            self.save()
    
    def get_care_plan(self, patient_id: str) -> Optional[CarePlan]:
        """Get care plan for a patient."""
        patient = self.get_patient(patient_id)
        return patient.care_plan if patient else None
    
    # Logging methods
    def add_glucose_log(self, log: GlucoseLog):
        """Add glucose reading log."""
        if log.patient_id not in self.glucose_logs:
            self.glucose_logs[log.patient_id] = []
        self.glucose_logs[log.patient_id].append(log)
        self.save()
    
    def get_glucose_logs(self, patient_id: str, days: int = 30) -> List[GlucoseLog]:
        """Get glucose logs for a patient."""
        logs = self.glucose_logs.get(patient_id, [])
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        return [log for log in logs if datetime.fromisoformat(log.timestamp).timestamp() > cutoff]
    
    def add_medication_log(self, log: MedicationLog):
        """Add medication log."""
        if log.patient_id not in self.medication_logs:
            self.medication_logs[log.patient_id] = []
        self.medication_logs[log.patient_id].append(log)
        self.save()
    
    def get_medication_logs(self, patient_id: str, days: int = 30) -> List[MedicationLog]:
        """Get medication logs for a patient."""
        logs = self.medication_logs.get(patient_id, [])
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        return [log for log in logs if datetime.fromisoformat(log.timestamp).timestamp() > cutoff]
    
    def add_meal_log(self, log: MealLog):
        """Add meal log."""
        if log.patient_id not in self.meal_logs:
            self.meal_logs[log.patient_id] = []
        self.meal_logs[log.patient_id].append(log)
        self.save()
    
    def get_meal_logs(self, patient_id: str, days: int = 30) -> List[MealLog]:
        """Get meal logs for a patient."""
        logs = self.meal_logs.get(patient_id, [])
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        return [log for log in logs if datetime.fromisoformat(log.timestamp).timestamp() > cutoff]
    
    def add_activity_log(self, log: ActivityLog):
        """Add activity log."""
        if log.patient_id not in self.activity_logs:
            self.activity_logs[log.patient_id] = []
        self.activity_logs[log.patient_id].append(log)
        self.save()
    
    def get_activity_logs(self, patient_id: str, days: int = 30) -> List[ActivityLog]:
        """Get activity logs for a patient."""
        logs = self.activity_logs.get(patient_id, [])
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        return [log for log in logs if datetime.fromisoformat(log.timestamp).timestamp() > cutoff]
    
    # Alert methods
    def create_alert(self, alert: Alert):
        """Create a new alert."""
        if alert.patient_id not in self.alerts:
            self.alerts[alert.patient_id] = []
        self.alerts[alert.patient_id].append(alert)
        self.save()
    
    def get_alerts(self, patient_id: str, unacknowledged_only: bool = False) -> List[Alert]:
        """Get alerts for a patient."""
        alerts = self.alerts.get(patient_id, [])
        if unacknowledged_only:
            alerts = [a for a in alerts if not a.acknowledged]
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def acknowledge_alert(self, patient_id: str, alert_id: str):
        """Acknowledge an alert."""
        alerts = self.alerts.get(patient_id, [])
        for alert in alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                self.save()
                return True
        return False
    
    # Reminder methods
    def create_reminder(self, reminder: Reminder):
        """Create a reminder."""
        if reminder.patient_id not in self.reminders:
            self.reminders[reminder.patient_id] = []
        self.reminders[reminder.patient_id].append(reminder)
        self.save()
    
    def get_reminders(self, patient_id: str, active_only: bool = True) -> List[Reminder]:
        """Get reminders for a patient."""
        reminders = self.reminders.get(patient_id, [])
        if active_only:
            reminders = [r for r in reminders if r.active]
        return reminders
    
    # Community methods
    def create_post(self, post: CommunityPost):
        """Create a community post."""
        self.community_posts.append(post)
        self.save()
    
    def get_posts(self, limit: int = 50) -> List[CommunityPost]:
        """Get all community posts, sorted by newest first."""
        posts = sorted(self.community_posts, key=lambda x: x.created_at, reverse=True)
        return posts[:limit]
    
    def like_post(self, post_id: str):
        """Like a post."""
        for post in self.community_posts:
            if post.post_id == post_id:
                post.likes += 1
                self.save()
                return True
        return False
    
    def add_comment(self, comment: Comment):
        """Add a comment to a post."""
        if comment.post_id not in self.comments:
            self.comments[comment.post_id] = []
        self.comments[comment.post_id].append(comment)
        self.save()
    
    def get_comments(self, post_id: str) -> List[Comment]:
        """Get comments for a post."""
        return sorted(self.comments.get(post_id, []), key=lambda x: x.created_at)
    
    # Doctor messaging methods
    def add_doctor_message(self, message: DoctorMessage):
        """Add a message between patient and doctor."""
        if message.patient_id not in self.doctor_messages:
            self.doctor_messages[message.patient_id] = []
        self.doctor_messages[message.patient_id].append(message)
        self.save()
    
    def get_doctor_messages(self, patient_id: str) -> List[DoctorMessage]:
        """Get all messages for a patient."""
        return sorted(self.doctor_messages.get(patient_id, []), key=lambda x: x.timestamp)


# Global storage instance
storage = Storage()

