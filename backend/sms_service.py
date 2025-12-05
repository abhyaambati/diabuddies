"""SMS service for sending alerts and reminders via Twilio."""
import os
from typing import Optional, List

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    Client = None


class SMSService:
    """Service for sending SMS messages via Twilio."""
    
    def __init__(self):
        if not TWILIO_AVAILABLE:
            self.available = False
            return
        
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            self.available = False
            return
        
        try:
            self.client = Client(self.account_sid, self.auth_token)
            self.available = True
        except Exception as e:
            print(f"Error initializing Twilio SMS client: {e}")
            self.available = False
    
    def send_sms(self, to_phone: str, message: str) -> dict:
        """Send SMS message to phone number.
        
        Args:
            to_phone: Phone number in E.164 format (e.g., +1234567890)
            message: Message text to send
            
        Returns:
            dict with 'success' (bool) and 'error' (str if failed)
        """
        if not self.available:
            return {
                'success': False,
                'error': 'SMS service not available. Configure Twilio credentials.'
            }
        
        if not to_phone:
            return {
                'success': False,
                'error': 'Phone number is required'
            }
        
        try:
            # Ensure phone number is in E.164 format
            if not to_phone.startswith('+'):
                # Try to format it (basic - in production, use a proper phone library)
                to_phone = '+' + to_phone.lstrip('+')
            
            message_obj = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to_phone
            )
            
            return {
                'success': True,
                'message_sid': message_obj.sid,
                'status': message_obj.status
            }
        except Exception as e:
            print(f"Error sending SMS: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_critical_alert(self, patient_phone: str, emergency_contact: Optional[str], 
                           reading: float, reading_type: str) -> dict:
        """Send critical glucose alert via SMS.
        
        Args:
            patient_phone: Patient's phone number
            emergency_contact: Emergency contact phone number (optional)
            reading: Glucose reading value
            reading_type: Type of reading (fasting, post_meal, etc.)
            
        Returns:
            dict with results for patient and emergency contact
        """
        results = {}
        
        # Determine message based on reading
        if reading < 70:
            message = f"🚨 CRITICAL LOW BLOOD SUGAR ALERT: {reading} mg/dL\n\n" \
                     f"Treat immediately with 15g of fast-acting carbs (glucose tablets, juice, or candy).\n" \
                     f"Re-check in 15 minutes. If still low, repeat treatment.\n\n" \
                     f"If symptoms worsen or you can't treat yourself, call 911 immediately."
        elif reading > 300:
            message = f"🚨 CRITICAL HIGH BLOOD SUGAR ALERT: {reading} mg/dL\n\n" \
                     f"Your glucose is dangerously high. Contact your doctor immediately.\n" \
                     f"If you have symptoms like nausea, vomiting, or confusion, go to the emergency room.\n\n" \
                     f"Emergency: Call 911 if symptoms are severe."
        else:
            message = f"⚠️ Blood Sugar Alert: {reading} mg/dL\n\n" \
                     f"Your reading is outside the target range. Please check with your care plan and contact your doctor if needed."
        
        # Send to patient
        if patient_phone:
            results['patient'] = self.send_sms(patient_phone, message)
        
        # Send to emergency contact if provided
        if emergency_contact:
            emergency_message = f"URGENT: {patient_phone if patient_phone else 'Patient'} has a critical blood sugar reading of {reading} mg/dL. Please check on them immediately."
            results['emergency_contact'] = self.send_sms(emergency_contact, emergency_message)
        
        return results
    
    def send_medication_reminder(self, patient_phone: str, medication_name: str, 
                                dosage: str, time: str) -> dict:
        """Send medication reminder via SMS.
        
        Args:
            patient_phone: Patient's phone number
            medication_name: Name of medication
            dosage: Dosage information
            time: Time to take medication
            
        Returns:
            dict with 'success' and 'error' fields
        """
        message = f"💊 Medication Reminder\n\n" \
                 f"Time to take: {medication_name} ({dosage})\n" \
                 f"Scheduled time: {time}\n\n" \
                 f"Please take your medication as prescribed."
        
        return self.send_sms(patient_phone, message)
    
    def send_glucose_check_reminder(self, patient_phone: str, reminder_type: str = "routine") -> dict:
        """Send glucose check reminder via SMS.
        
        Args:
            patient_phone: Patient's phone number
            reminder_type: Type of reminder (routine, before_driving, before_meal, etc.)
            
        Returns:
            dict with 'success' and 'error' fields
        """
        messages = {
            'routine': "📊 Time to check your blood sugar. Please take a reading now.",
            'before_driving': "🚗 Important: Check your blood sugar before driving. Ensure it's above 100 mg/dL.",
            'before_meal': "🍽️ Check your blood sugar before your meal.",
            'bedtime': "🌙 Bedtime glucose check: Please take a reading before going to sleep."
        }
        
        message = messages.get(reminder_type, messages['routine'])
        return self.send_sms(patient_phone, message)


# Global SMS service instance
sms_service = SMSService()

