# Google Earth KML Service with Password Protection

Secure, auto-updating Google Earth Pro integration with Airtable data, protected by password authentication.

## Features

✅ **Password Protected** - Basic Authentication via Vercel Edge Middleware  
✅ **Auto-Updating** - NetworkLink refreshes every 30 minutes  
✅ **Color-Coded Status** - Visual status indicators on the map  
✅ **Airtable Links** - Click through to records from Google Earth  
✅ **Secure by Default** - No unauthorized access to your data  

## Security Overview

This application uses **HTTP Basic Authentication** to protect all endpoints. Only users with valid credentials can access:
- The KML files
- The status page
- Any data from your Airtable base

### How It Works

1. **Edge Middleware** intercepts every request
2. Checks for valid username/password
3. Blocks unauthorized access (returns 401 error)
4. Allows authenticated requests through

Compatible with:
- ✅ Web browsers (Chrome, Firefox, Safari, Edge)
- ✅ Google Earth Pro desktop application
- ✅ API clients (curl, Postman, etc.)

## Quick Deployment

### 1. Set Environment Variables in Vercel

Go to your Vercel project → **Settings → Environment Variables** and add:

```
AUTH_USERNAME=your-username
AUTH_PASSWORD=YourSecurePassword123!
AIRTABLE_BASE_ID=appZOdJaRPiwcygdR
AIRTABLE_TABLE_NAME=Table 1
AIRTABLE_TOKEN=your_airtable_token
REFRESH_INTERVAL_MINUTES=30
```

**🔒 Security Tips:**
- Use a strong password (12+ characters, mixed case, numbers, symbols)
- Do NOT use "admin/password" in production
- Store credentials in a password manager

### 2. Deploy

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

Or push to your connected Git repository.

### 3. Test Authentication

```bash
# Should fail (401)
curl https://your-project.vercel.app/

# Should succeed
curl -u username:password https://your-project.vercel.app/
```

## Usage

### In Google Earth Pro

1. Open Google Earth Pro (desktop application)
2. Go to **File → Open → Network Link**
3. Enter URL: `https://your-project.vercel.app/kml`
4. When prompted:
   - **Username:** (your AUTH_USERNAME)
   - **Password:** (your AUTH_PASSWORD)
5. Click **OK**

The map will load and automatically update every 30 minutes.

### In Web Browser

1. Visit `https://your-project.vercel.app`
2. Enter credentials when prompted
3. View the status page with all endpoints

## Status Legend

🔴 **Red Circle** - Zoning submittals not made  
🟡 **Yellow Circle** - Zoning Submittal Made  
🔵 **Light Blue Circle** - Zoning Board Meeting Scheduled  
🟢 **Green Circle** - Zoning Complete - Letter Received  
⭐ **Red Star** - Zoning Denied  
⭐ **Green Star** - Preliminary Site Plan Created  

## Sharing Access

### With Team Members

**Securely share credentials:**
1. Use a password manager's sharing feature (recommended)
2. Send via encrypted communication
3. Never email credentials in plain text

**Provide these instructions:**
```
Access URL: https://your-project.vercel.app/kml
Username: [provided separately]
Password: [provided separately]

Instructions:
1. Open Google Earth Pro
2. File → Open → Network Link
3. Paste the URL above
4. Enter the username and password
5. Map loads and auto-updates every 30 minutes
```

### Revoking Access

1. Change `AUTH_PASSWORD` in Vercel environment variables
2. Redeploy (automatic if using Git integration)
3. Only share new password with authorized users

## Endpoints

All endpoints require authentication:

| Endpoint | Description |
|----------|-------------|
| `/` | Status page with documentation |
| `/kml` | NetworkLink KML (use this in Google Earth) |
| `/kml/data` | Data endpoint (auto-refreshed) |
| `/health` | Health check |
| `/webhook/refresh` | Manual refresh trigger |

## File Structure

```
google-earth-pro/
├── app.py                 # Flask application (KML generation)
├── middleware.js          # Vercel Edge Middleware (authentication)
├── vercel.json           # Vercel configuration
├── package.json          # Node.js dependencies (for middleware)
├── requirements.txt      # Python dependencies
├── .env                  # Local environment variables (DO NOT COMMIT)
├── .gitignore           # Git ignore rules
├── README.md            # This file
├── DEPLOYMENT.md        # Detailed deployment guide
└── QUICKSTART.md        # Quick start guide
```

## Local Development

### Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### Run Locally

```bash
python app.py
```

Visit: `http://localhost:5000`

**Note:** Authentication middleware only runs on Vercel, not locally. For local testing, authentication is automatically disabled if `AUTH_PASSWORD` is not set.

## Troubleshooting

### "Authentication required" keeps appearing

**Browser:**
- Clear cached credentials
- Use browser's private/incognito mode
- Verify you're using the correct password

**Google Earth Pro:**
- Remove the Network Link and re-add it
- Check for typos in the URL
- Ensure credentials don't have special characters

### 401 Errors After Deployment

1. Check Vercel environment variables are set correctly
2. Verify variable names match exactly: `AUTH_USERNAME`, `AUTH_PASSWORD`
3. Redeploy after changing environment variables
4. Test with curl: `curl -u user:pass https://your-project.vercel.app/`

### Network Link Not Updating

1. Check refresh interval setting (default: 30 minutes)
2. Verify Airtable token has read permissions
3. Check `/health` endpoint for errors
4. Look at Vercel deployment logs

## Technical Details

### Authentication Flow

```
Request → Edge Middleware → Check Authorization Header
                            ↓
                     Valid? Yes → Allow → Flask App
                            ↓
                     Valid? No → 401 Error + Auth Prompt
```

### Why Edge Middleware?

- **Fast:** Runs on Vercel's global Edge Network
- **Secure:** Checks auth before any code executes
- **Universal:** Works with all HTTP clients
- **Free:** Included in all Vercel plans

### Alternative: Vercel Password Protection

Vercel offers built-in Password Protection (Pro/Enterprise plans), but Edge Middleware is preferred because:
- ✅ Works on Free plan
- ✅ More flexible (can add IP whitelisting, custom logic)
- ✅ Compatible with Google Earth Pro
- ✅ Standard HTTP Basic Auth (universal support)

## Security Best Practices

1. ✅ **Use strong passwords** (12+ characters, mixed case, numbers, symbols)
2. ✅ **Rotate passwords regularly** (every 90 days recommended)
3. ✅ **Use HTTPS only** (Vercel provides free SSL)
4. ✅ **Store credentials securely** (use a password manager)
5. ✅ **Limit sharing** (only authorized team members)
6. ✅ **Monitor access** (check Vercel logs regularly)
7. ✅ **Keep .env out of Git** (already in .gitignore)

## Future Enhancements

Potential additions:
- Property boundary visualization from KML files
- IP whitelisting for additional security
- Multi-factor authentication (MFA)
- Audit logging for access tracking
- Custom domain with SSL

## Support

For issues or questions:
1. Check `DEPLOYMENT.md` for detailed documentation
2. Review Vercel deployment logs
3. Test endpoints with curl for debugging
4. Check Airtable API status

## License

Private/Proprietary - Not for public distribution

---

**🔒 Remember:** Keep your credentials secure and never commit `.env` files to Git!
