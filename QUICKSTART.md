# Quick Start Guide

## Step-by-Step Instructions to Run Diabuddies

### 1. Navigate to the Project
```bash
cd /Users/abhyaambati/diabuddies-2
```

### 2. Install Python Dependencies
```bash
cd backend
pip3 install -r requirements.txt
```

**Note:** If you get permission errors, use:
```bash
pip3 install --user -r requirements.txt
```

### 3. Set Up Environment Variables

Check if `.env` file exists in the `backend` directory:
```bash
ls -la backend/.env
```

If it doesn't exist or you need to update it, create/edit it:
```bash
cd backend
nano .env
```

Add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
PORT=5000
```

**Get your API key from:** https://platform.openai.com/account/api-keys

### 4. Run the Server

From the `backend` directory:
```bash
python3 main.py
```

You should see output like:
```
 * Serving Flask app 'main'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### 5. Open in Browser

Open your web browser and go to:
```
http://localhost:5000
```

You should see the Diabuddies chat interface!

---

## Voice Calls Setup (Optional)

To enable voice/phone call functionality:

### 1. Install Twilio
```bash
pip3 install twilio
```

### 2. Get Twilio Credentials
1. Sign up at https://www.twilio.com
2. Get Account SID and Auth Token
3. Purchase a phone number

### 3. Add to `.env`
```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_BASE_URL=https://your-public-url.com
```

### 4. Make Server Public
Use ngrok or similar:
```bash
ngrok http 5000
```
Update `TWILIO_WEBHOOK_BASE_URL` with ngrok URL.

### 5. Initiate a Call
```bash
curl -X POST http://localhost:5000/api/voice/call/initiate \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "patient_id": "optional-id"}'
```

**See [Voice Setup Guide](backend/VOICE_SETUP.md) for detailed instructions.**

---

## Troubleshooting

### "Module not found" errors
Make sure you installed all dependencies:
```bash
cd backend
pip3 install -r requirements.txt
```

### "Invalid API key" error
1. Check your `.env` file has the correct API key
2. Make sure there are no extra spaces or quotes
3. Restart the server after updating `.env`

### Port already in use
If port 5000 is busy, change it in `.env`:
```
PORT=5001
```
Then access at `http://localhost:5001`

### Python version issues
Check your Python version:
```bash
python3 --version
```
Should be Python 3.8 or higher.

### Voice calls not working
- Check Twilio is installed: `pip3 install twilio`
- Verify all Twilio credentials in `.env`
- Ensure server is publicly accessible for webhooks
- See [Voice Setup Guide](backend/VOICE_SETUP.md)

---

## Testing the API

Once the server is running, you can test it:

### Test the chat endpoint:
```bash
curl -X POST http://localhost:5000/api/diabuddies \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test123",
    "message": "Hello, how are you?"
  }'
```

### Test health endpoint:
```bash
curl http://localhost:5000/health
```

### Test voice call (if configured):
```bash
curl -X POST http://localhost:5000/api/voice/call/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "patient_id": "optional-patient-id"
  }'
```

---

## Next Steps

1. **Try the chat interface** - Open `http://localhost:5000` and start chatting
2. **Create a patient** - Use the API to create a patient record
3. **Set up a care plan** - Create a doctor and set up a care plan for a patient
4. **Log data** - Try logging glucose readings, medications, etc.
5. **Try voice calls** - Set up Twilio and make a test call

See the [API Documentation](docs/API_DOCUMENTATION.md) for all available endpoints.
