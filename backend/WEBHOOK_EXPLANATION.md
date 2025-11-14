# What is TWILIO_WEBHOOK_BASE_URL?

## Simple Explanation

**TWILIO_WEBHOOK_BASE_URL** is the **public internet address** where your Flask server is running. Twilio needs this to send requests to your server when:
- A call connects
- The patient speaks (speech input)
- Call status changes

Think of it as your server's "phone number" on the internet that Twilio can call.

## Why It's Needed

When you initiate a call:
1. Your server tells Twilio: "Call this phone number"
2. Twilio calls the patient
3. When patient answers, Twilio needs to ask YOUR server: "What should I say?"
4. Your server responds with TwiML (instructions)
5. When patient speaks, Twilio sends the speech to YOUR server
6. Your server processes it and sends back a response

**Twilio can only reach your server if it has a public URL!**

## Examples

### Development (Local Testing)

If your server runs on `localhost:5000`, Twilio can't reach it directly because `localhost` is only accessible on your computer.

**Solution: Use a tunnel service**

#### Option 1: ngrok (Recommended)
```bash
# Install ngrok: https://ngrok.com/download
# Or: brew install ngrok (on Mac)

# Start your Flask server
cd backend
python3 main.py

# In another terminal, start ngrok
ngrok http 5000
```

You'll get output like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:5000
```

**Use this URL in your `.env`:**
```bash
TWILIO_WEBHOOK_BASE_URL=https://abc123.ngrok.io
```

#### Option 2: localtunnel
```bash
npm install -g localtunnel
lt --port 5000
```

#### Option 3: Cloudflare Tunnel
```bash
cloudflared tunnel --url http://localhost:5000
```

### Production

If you deploy to:
- **Heroku**: `https://your-app.herokuapp.com`
- **AWS/EC2**: `https://your-domain.com`
- **DigitalOcean**: `https://your-droplet-ip` (or domain)
- **Railway**: `https://your-app.railway.app`

Use that URL:
```bash
TWILIO_WEBHOOK_BASE_URL=https://your-app.herokuapp.com
```

## How It Works

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Your      │         │    Twilio    │         │   Patient   │
│   Server    │◄────────┤   Cloud      │────────►│   Phone     │
│             │         │              │         │             │
└─────────────┘         └──────────────┘         └─────────────┘
     ▲                          │
     │                          │
     └── Webhook URL ───────────┘
     (TWILIO_WEBHOOK_BASE_URL)
```

1. Your server initiates call → Twilio
2. Twilio calls patient → Patient answers
3. Twilio sends webhook → `https://your-url.com/api/voice/call`
4. Your server responds with TwiML → Twilio
5. Twilio plays greeting → Patient hears it
6. Patient speaks → Twilio transcribes
7. Twilio sends speech → `https://your-url.com/api/voice/process`
8. Your server processes → Sends response
9. Twilio speaks response → Patient hears it
10. Loop continues...

## Configuration

### Step 1: Get Your Public URL

**For Development:**
```bash
# Terminal 1: Start your server
cd backend
python3 main.py

# Terminal 2: Start ngrok
ngrok http 5000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### Step 2: Update .env

```bash
cd backend
nano .env
```

Add:
```bash
TWILIO_WEBHOOK_BASE_URL=https://abc123.ngrok.io
```

**Important:** 
- Use **HTTPS** (not HTTP) - Twilio requires HTTPS
- Don't include trailing slash
- Don't include the `/api/voice/call` path - just the base URL

### Step 3: Restart Server

```bash
# Stop server (Ctrl+C)
# Restart
python3 main.py
```

## Full Example

### Your .env file:
```bash
OPENAI_API_KEY=sk-...
PORT=5000

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_BASE_URL=https://abc123.ngrok.io
```

### What Happens:

When you call `/api/voice/call/initiate`:
1. Server reads `TWILIO_WEBHOOK_BASE_URL=https://abc123.ngrok.io`
2. Builds webhook URL: `https://abc123.ngrok.io/api/voice/call`
3. Tells Twilio: "When call connects, go to this URL"
4. Twilio can now reach your server through ngrok

## Common Issues

### "Webhook URL not accessible"
- **Problem:** Twilio can't reach your server
- **Solution:** 
  - Make sure ngrok/tunnel is running
  - Check URL is correct (HTTPS, no trailing slash)
  - Verify server is running on correct port

### "404 Not Found" from Twilio
- **Problem:** URL path is wrong
- **Solution:** 
  - Base URL should NOT include `/api/voice/call`
  - Code automatically adds the path
  - Check your `.env` has just the base URL

### "Connection refused"
- **Problem:** Server not running or wrong port
- **Solution:**
  - Verify server is running: `python3 main.py`
  - Check port matches: `PORT=5000` in `.env`
  - Verify ngrok points to same port: `ngrok http 5000`

## Testing

### Test if your webhook is accessible:

```bash
# Replace with your actual webhook URL
curl https://abc123.ngrok.io/api/voice/call
```

Should return TwiML XML (even if it's an error, it means Twilio can reach it).

### Test full flow:

1. Start server: `python3 main.py`
2. Start ngrok: `ngrok http 5000`
3. Update `.env` with ngrok URL
4. Restart server
5. Make test call:
   ```bash
   curl -X POST http://localhost:5000/api/voice/call/initiate \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "+YOUR_PHONE"}'
   ```

## Summary

- **TWILIO_WEBHOOK_BASE_URL** = Your server's public internet address
- **Required** for Twilio to communicate with your server
- **For development:** Use ngrok or similar tunnel
- **For production:** Use your actual domain/URL
- **Must be HTTPS** (Twilio requirement)
- **No trailing slash**, no paths - just the base URL

Example values:
- ✅ `https://abc123.ngrok.io`
- ✅ `https://your-app.herokuapp.com`
- ✅ `https://api.yourdomain.com`
- ❌ `http://localhost:5000` (not public)
- ❌ `https://abc123.ngrok.io/` (trailing slash)
- ❌ `https://abc123.ngrok.io/api/voice/call` (includes path)

