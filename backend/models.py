"""Data models for Diabuddies system."""
from datetime import datetime, time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import json


@dataclass
class Medication:
    """Medication information."""
    name: str
    dosage: str
    frequency: str  # e.g., "twice daily", "once daily", "before meals"
    times: List[str]  # e.g., ["08:00", "20:00"]
    start_date: str
    notes: Optional[str] = None


@dataclass
class GlucoseTarget:
    """Blood glucose targets."""
    fasting_min: int = 80
    fasting_max: int = 130
    post_meal_min: int = 80
    post_meal_max: int = 180
    hba1c_target: Optional[float] = None


@dataclass
class HealthGoals:
    """Personal health goals."""
    weight_target: Optional[float] = None
    activity_minutes_per_week: Optional[int] = None
    dietary_goals: Optional[str] = None
    other_goals: Optional[str] = None


@dataclass
class CarePlan:
    """Patient care plan set by doctor."""
    patient_id: str
    doctor_id: str
    created_at: str
    medications: List[Medication]
    glucose_targets: GlucoseTarget
    health_goals: HealthGoals
    dietary_recommendations: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self):
        return {
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'created_at': self.created_at,
            'medications': [asdict(m) for m in self.medications],
            'glucose_targets': asdict(self.glucose_targets),
            'health_goals': asdict(self.health_goals),
            'dietary_recommendations': self.dietary_recommendations,
            'notes': self.notes
        }


@dataclass
class Patient:
    """Patient information."""
    patient_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    doctor_id: Optional[str] = None
    care_plan: Optional[CarePlan] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'patient_id': self.patient_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth,
            'doctor_id': self.doctor_id,
            'care_plan': self.care_plan.to_dict() if self.care_plan else None,
            'created_at': self.created_at
        }


@dataclass
class Doctor:
    """Doctor/Healthcare provider information."""
    doctor_id: str
    name: str
    email: str
    phone: Optional[str] = None
    specialty: Optional[str] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'doctor_id': self.doctor_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'specialty': self.specialty,
            'created_at': self.created_at
        }


@dataclass
class GlucoseLog:
    """Blood glucose reading log."""
    log_id: str
    patient_id: str
    reading: float
    timestamp: str
    reading_type: str  # "fasting", "post_meal", "random", "bedtime"
    notes: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class MedicationLog:
    """Medication intake log."""
    log_id: str
    patient_id: str
    medication_name: str
    dosage: str
    timestamp: str
    taken: bool
    notes: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class MealLog:
    """Meal logging."""
    log_id: str
    patient_id: str
    meal_type: str  # "breakfast", "lunch", "dinner", "snack"
    description: str
    timestamp: str
    carbs_estimate: Optional[float] = None
    notes: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class ActivityLog:
    """Physical activity log."""
    log_id: str
    patient_id: str
    activity_type: str
    duration_minutes: int
    intensity: str  # "light", "moderate", "vigorous"
    timestamp: str
    notes: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class Alert:
    """System alert."""
    alert_id: str
    patient_id: str
    alert_type: str  # "missed_dose", "high_glucose", "low_glucose", "critical", "reminder"
    severity: str  # "low", "medium", "high", "critical"
    message: str
    timestamp: str
    acknowledged: bool = False
    doctor_notified: bool = False
    
    def to_dict(self):
        return asdict(self)


@dataclass
class Reminder:
    """Scheduled reminder."""
    reminder_id: str
    patient_id: str
    reminder_type: str  # "medication", "glucose_check", "exercise", "dietary"
    message: str
    scheduled_time: str  # ISO format
    frequency: str  # "daily", "weekly", "one_time"
    active: bool = True
    
    def to_dict(self):
        return asdict(self)

