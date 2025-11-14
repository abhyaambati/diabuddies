# Voice Call Setup Guide

## Overview

Diabuddies now supports voice calls! The system can make outbound calls to patients and have natural conversations using speech-to-text and text-to-speech.

## Prerequisites

1. **Twilio Account** - Sign up at https://www.twilio.com
2. **Twilio Phone Number** - Purchase a phone number from Twilio
3. **Public URL** - Your server needs to be publicly accessible for Twilio webhooks

## Setup Steps

### 1. Get Twilio Credentials

1. Sign up for Twilio: https://www.twilio.com/try-twilio
2. Get your Account SID and Auth Token from the Twilio Console
3. Purchase a phone number (Voice-enabled)

### 2. Configure Environment Variables

Add to `backend/.env`:

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890  # Your Twilio phone number (E.164 format)
TWILIO_WEBHOOK_BASE_URL=https://your-domain.com  # Your public server URL
```

### 3. Install Dependencies

```bash
cd backend
pip3 install -r requirements.txt
```

### 4. Make Server Publicly Accessible

**What is TWILIO_WEBHOOK_BASE_URL?**
It's the public internet address where your server is accessible. Twilio needs this to send webhook requests to your server when calls connect or when speech is received.

**For development, use a tunneling service:**

#### Using ngrok (Recommended):
```bash
# Install ngrok: https://ngrok.com/download
# Or: brew install ngrok (on Mac)

# Terminal 1: Start your server
cd backend
python3 main.py

# Terminal 2: Start ngrok
ngrok http 5000
```

You'll see output like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:5000
```

**Copy the HTTPS URL** and add to `.env`:
```bash
TWILIO_WEBHOOK_BASE_URL=https://abc123.ngrok.io
```

**Important:**
- Use the **HTTPS** URL (not HTTP)
- No trailing slash
- Just the base URL (don't include `/api/voice/call`)

#### Other options:
- **localtunnel**: `lt --port 5000`
- **Cloudflare Tunnel**: `cloudflared tunnel --url http://localhost:5000`

**See [WEBHOOK_EXPLANATION.md](WEBHOOK_EXPLANATION.md) for detailed explanation.**

### 5. Configure Twilio Webhooks

In Twilio Console:
1. Go to Phone Numbers → Manage → Active Numbers
2. Click your phone number
3. Under "Voice & Fax", set:
   - **A CALL COMES IN**: `https://your-domain.com/api/voice/call`
   - **STATUS CALLBACK URL**: `https://your-domain.com/api/voice/status`

## Usage

### Initiate a Call

**API Endpoint:**
```http
POST /api/voice/call/initiate
Content-Type: application/json

{
  "phone_number": "+1234567890",
  "patient_id": "optional-patient-id"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/voice/call/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "patient_id": "patient-123"
  }'
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

### How It Works

1. **Call Initiation**: System calls patient's phone
2. **Answer**: Patient answers, hears personalized greeting
3. **Speech Recognition**: Twilio transcribes patient's speech
4. **AI Processing**: Speech → Text → LangGraph Agents → Response
5. **Text-to-Speech**: Response converted to speech and played
6. **Conversation Loop**: Continues until patient hangs up or says goodbye

### Features

- **Natural Conversation**: Full LangGraph multi-agent system
- **Personalized**: Uses patient's care plan for context
- **Emergency Detection**: Automatically detects emergencies
- **Speech Recognition**: Twilio's advanced speech recognition
- **Text-to-Speech**: Natural-sounding voice (Alice voice)

## Testing

### Test with ngrok (Development)

1. **Start your server:**
   ```bash
   cd backend
   python3 main.py
   ```

2. **Start ngrok:**
   ```bash
   ngrok http 5000
   ```

3. **Update .env:**
   ```
   TWILIO_WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok.io
   ```

4. **Restart server** to load new env vars

5. **Make a test call:**
   ```bash
   curl -X POST http://localhost:5000/api/voice/call/initiate \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "+YOUR_PHONE_NUMBER"}'
   ```

### Test Call Flow

1. System calls your phone
2. You answer
3. Hear: "Hi, this is Diabuddies. I'm calling to check in with you today. How are you doing?"
4. Speak your response
5. System processes and responds
6. Conversation continues naturally

## Phone Number Format

Phone numbers must be in **E.164 format**:
- ✅ `+1234567890` (US)
- ✅ `+441234567890` (UK)
- ❌ `123-456-7890` (wrong format)
- ❌ `(123) 456-7890` (wrong format)

## Troubleshooting

### "Twilio not configured" error
- Check `.env` file has all Twilio credentials
- Restart server after updating `.env`

### "Invalid phone number" error
- Ensure phone number is in E.164 format (+country code + number)
- Example: `+1234567890` for US

### Webhook not receiving calls
- Ensure server is publicly accessible
- Check `TWILIO_WEBHOOK_BASE_URL` is correct
- Verify Twilio webhook URLs in console
- Check server logs for incoming requests

### No speech recognition
- Check Twilio account has speech recognition enabled
- Verify webhook URL is accessible
- Check server logs for errors

## Production Deployment

For production:

1. **Use HTTPS**: Twilio requires HTTPS for webhooks
2. **Set up proper domain**: Use your actual domain, not ngrok
3. **Environment variables**: Use secure secret management
4. **Monitoring**: Set up logging and monitoring
5. **Rate limiting**: Implement rate limiting for API endpoints

## Cost Considerations

- **Twilio charges** per minute for calls
- **Speech recognition** may have additional costs
- Check Twilio pricing: https://www.twilio.com/pricing

## Security

- **Never commit** `.env` file with credentials
- **Use environment variables** in production
- **Validate phone numbers** before making calls
- **Implement authentication** for API endpoints
- **Rate limit** call initiation endpoints

