"""Voice call handler for Diabuddies phone conversations."""
try:
    from twilio.twiml.voice_response import VoiceResponse, Gather
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    # Create dummy classes for when Twilio is not installed
    class VoiceResponse:
        def __init__(self): pass
        def say(self, *args, **kwargs): pass
        def append(self, *args): pass
        def hangup(self): pass
        def __str__(self): return ''
    class Gather:
        def __init__(self, *args, **kwargs): pass
        def say(self, *args, **kwargs): pass
    Client = None

from agents.orchestrator import conversation_graph
from storage import storage
import os
from urllib.parse import unquote

# Import sessions from main (circular import workaround)
def get_sessions():
    """Get sessions dict from main module."""
    import main
    return main.sessions


class VoiceCallHandler:
    """Handles voice calls using Twilio."""
    
    def __init__(self):
        if not TWILIO_AVAILABLE:
            self.client = None
            return
            
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
        self.client = None
        
        if self.account_sid and self.auth_token and Client:
            try:
                self.client = Client(self.account_sid, self.auth_token)
            except Exception as e:
                print(f"Error initializing Twilio client: {e}")
                self.client = None
    
    def initiate_call(self, patient_phone: str, patient_id: str = None) -> dict:
        """
        Initiate an outbound call to a patient.
        
        Args:
            patient_phone: Patient's phone number (E.164 format: +1234567890)
            patient_id: Optional patient ID for personalized conversation
        
        Returns:
            Call SID and status
        """
        if not self.client:
            return {'error': 'Twilio not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER'}
        
        # Get the webhook URL (should be your server URL + /api/voice/call)
        webhook_url = os.environ.get('TWILIO_WEBHOOK_BASE_URL', 'http://localhost:5000')
        webhook_url = f"{webhook_url}/api/voice/call"
        
        # Add patient_id as a parameter
        webhook_url += f"?patient_id={patient_id}" if patient_id else ""
        
        try:
            call = self.client.calls.create(
                to=patient_phone,
                from_=self.phone_number,
                url=webhook_url,
                method='POST',
                record=False
            )
            
            return {
                'call_sid': call.sid,
                'status': call.status,
                'to': call.to,
                'from': call.from_
            }
        except Exception as e:
            return {'error': str(e)}
    
    def handle_incoming_call(self, patient_id: str = None) -> str:
        """
        Generate TwiML for incoming call (when patient answers).
        
        Args:
            patient_id: Optional patient ID for personalized greeting
        
        Returns:
            TwiML XML string
        """
        if not TWILIO_AVAILABLE:
            return '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Service unavailable</Say></Response>'
        
        response = VoiceResponse()
        
        # Get patient info if available
        patient_name = None
        if patient_id:
            patient = storage.get_patient(patient_id)
            if patient:
                patient_name = patient.name.split()[0] if patient.name else None
        
        # Personalized greeting
        greeting = f"Hi, this is Diabuddies"
        if patient_name:
            greeting += f", {patient_name}"
        greeting += ". I'm calling to check in with you today. How are you doing?"
        
        # Use Gather to collect speech input
        gather = Gather(
            input='speech',
            action='/api/voice/process',
            method='POST',
            speech_timeout='auto',
            language='en-US',
            hints='good, bad, fine, okay, great, terrible, blood sugar, glucose, medication, medicine, taken, not taken, yes, no',
            partial_result_callback='/api/voice/partial',
            partial_result_callback_method='POST'
        )
        
        # Add patient_id to action URL if available
        if patient_id:
            gather.action = f"/api/voice/process?patient_id={patient_id}"
        
        gather.say(greeting, voice='alice', language='en-US')
        response.append(gather)
        
        # If no input, say goodbye
        response.say("I didn't hear anything. Please call back when you're ready. Take care!", voice='alice')
        response.hangup()
        
        return str(response)
    
    def process_speech(self, speech_result: str, patient_id: str = None, call_sid: str = None) -> str:
        """
        Process speech input through the conversation agent and return TwiML response.
        
        Args:
            speech_result: Transcribed speech from Twilio
            patient_id: Optional patient ID
            call_sid: Twilio call SID for session tracking
        
        Returns:
            TwiML XML string
        """
        if not TWILIO_AVAILABLE:
            return '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Service unavailable</Say></Response>'
        
        response = VoiceResponse()
        
        if not speech_result or speech_result.strip() == '':
            response.say("I'm sorry, I didn't catch that. Could you repeat?", voice='alice')
            # Re-gather input
            gather = Gather(
                input='speech',
                action=f'/api/voice/process?patient_id={patient_id}' if patient_id else '/api/voice/process',
                method='POST',
                speech_timeout='auto',
                language='en-US'
            )
            response.append(gather)
            return str(response)
        
        # Decode URL-encoded speech
        user_message = unquote(speech_result).strip()
        
        # Use call_sid as session_id for conversation history
        session_id = call_sid or f"voice_{patient_id or 'unknown'}"
        
        # Get or create session
        sessions = get_sessions()
        if session_id not in sessions:
            sessions[session_id] = {
                'conversation_history': [],
                'patient_id': patient_id,
                'call_sid': call_sid
            }
        
        session = sessions[session_id]
        
        # Get patient context if available
        care_plan_context = None
        if patient_id:
            patient = storage.get_patient(patient_id)
            if patient and patient.care_plan:
                care_plan = patient.care_plan
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
        
        # Prepare state for LangGraph
        initial_state = {
            'user_message': user_message,
            'conversation_history': session['conversation_history'],
            'reply': '',
            'extracted': {},
            'risk': {},
            'summary': '',
            'is_emergency': False,
            'patient_id': patient_id,
            'care_plan_context': care_plan_context
        }
        
        # Run conversation graph
        try:
            result = conversation_graph.invoke(initial_state)
            reply = result.get('reply', "I'm here to help. How can I assist you today?")
            
            # Check for emergency
            if result.get('is_emergency', False):
                # For emergencies, provide immediate guidance
                emergency_msg = reply + " If this is an emergency, please hang up and call 911 or go to the nearest emergency room."
                response.say(emergency_msg, voice='alice')
                response.hangup()
                return str(response)
            
            # Update conversation history
            session['conversation_history'].append({
                'role': 'user',
                'content': user_message
            })
            session['conversation_history'].append({
                'role': 'assistant',
                'content': reply
            })
            
            # Speak the reply
            response.say(reply, voice='alice', language='en-US')
            
            # Continue conversation - gather next input
            gather = Gather(
                input='speech',
                action=f'/api/voice/process?patient_id={patient_id}&call_sid={call_sid}' if patient_id or call_sid else '/api/voice/process',
                method='POST',
                speech_timeout='auto',
                language='en-US',
                hints='good, bad, fine, okay, great, blood sugar, glucose, medication, medicine, taken, not taken, yes, no, thank you, goodbye, bye'
            )
            response.append(gather)
            
            # If no response, end gracefully
            response.say("Thank you for talking with me today. Take care and have a great day!", voice='alice')
            response.hangup()
            
        except Exception as e:
            print(f"Error processing speech: {e}")
            import traceback
            traceback.print_exc()
            response.say("I'm sorry, I'm having trouble right now. Please try calling back later.", voice='alice')
            response.hangup()
        
        return str(response)
    
    def handle_call_status(self, call_sid: str, status: str):
        """Handle call status updates (optional logging)."""
        print(f"Call {call_sid} status: {status}")
        # Could log to database, send notifications, etc.


# Global voice handler instance
voice_handler = VoiceCallHandler()
