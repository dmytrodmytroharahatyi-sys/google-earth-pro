# Quick Start Guide for Travis Shields

This guide will get you up and running with the Google Earth KML system as quickly as possible.

## What You Have

A complete Python application that:
- Fetches your zoning project data from Airtable
- Generates color-coded KML for Google Earth Pro
- Updates automatically every 30 minutes
- Is ready to deploy to Vercel, AWS, Google Cloud, or Heroku

## Option 1: Test Locally First (Recommended)

### Step 1: Install Python
If you don't have Python 3.11+:
- Download from: https://www.python.org/downloads/
- During installation, check "Add Python to PATH"

### Step 2: Open Terminal/Command Prompt
- Windows: Press Win+R, type `cmd`, press Enter
- Navigate to project folder:
  ```
  cd "D:\google earth kml"
  ```

### Step 3: Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# You should see (venv) in your prompt
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Test the Setup
```bash
python test_local.py
```

This will:
- Verify your Airtable credentials work
- Show how many records were found
- Display status distribution
- Create a test KML file you can inspect

### Step 6: Start Local Server
```bash
python app.py
```

Server will start at: http://localhost:5000

### Step 7: Test in Browser
Open: http://localhost:5000

You should see a status page with:
- Service status
- Available endpoints
- Usage instructions

### Step 8: Download KML for Testing
1. Visit: http://localhost:5000/kml
2. Save the file as `zoning-map.kml`
3. Open in Google Earth Pro

**To test auto-refresh:**
1. In Google Earth Pro: File → Open → Network Link
2. Enter: `http://localhost:5000/kml`
3. Right-click the link → Properties → Refresh tab
4. Should show "Time-Based Refresh" every 30 minutes

Note: Local server must be running for this to work. For production, deploy to cloud.

---

## Option 2: Deploy Immediately to Vercel (Easiest Cloud Option)

### Step 1: Create Vercel Account
1. Go to https://vercel.com/signup
2. Sign up with GitHub, GitLab, or Email (free)

### Step 2: Install Vercel CLI
```bash
npm install -g vercel
```

Don't have npm? Download Node.js: https://nodejs.org/

### Step 3: Login to Vercel
```bash
vercel login
```

### Step 4: Navigate to Project
```bash
cd "D:\google earth kml"
```

### Step 5: Set Environment Variables
```bash
vercel env add AIRTABLE_BASE_ID
# When prompted, enter: appZOdJaRPiwcygdR

vercel env add AIRTABLE_TABLE_NAME
# When prompted, enter: Table 1

vercel env add AIRTABLE_TOKEN
# When prompted, paste your token: patqR9ByQIKeyzjcO.7eabbc1c8af38378316e098d193a4a9fa09f304a99f062e616f2f930f79cc76f

vercel env add REFRESH_INTERVAL_MINUTES
# When prompted, enter: 30
```

**Important:** For each variable, when prompted:
- Choose: **Production** environment
- Press Enter to skip preview/development

### Step 6: Deploy
```bash
vercel --prod
```

Follow prompts:
- Setup and deploy? **Y**
- Which scope? (select your account)
- Link to existing project? **N**
- Project name? (press Enter for default, or choose a name)
- In which directory? **./` (press Enter)
- Override settings? **N**

Deployment takes ~1 minute.

### Step 7: Get Your URL
After deployment, Vercel will show:
```
✅ Production: https://your-project-name.vercel.app
```

**Save this URL!** This is your permanent KML service.

### Step 8: Test Deployment
```bash
# Test status page (replace YOUR-URL)
curl https://your-project-name.vercel.app/

# Test health
curl https://your-project-name.vercel.app/health
```

Or just open in browser: https://your-project-name.vercel.app

### Step 9: Use in Google Earth Pro
1. Open Google Earth Pro
2. File → Open → Network Link
3. Enter your Vercel URL + `/kml`:
   ```
   https://your-project-name.vercel.app/kml
   ```
4. Click OK

**Your map will now:**
- Load immediately with current data
- Update automatically every 30 minutes
- Work from any computer with your Google Earth Pro installation

---

## Understanding the Color Codes

Your placemarks will appear with these colors:

| Color | Status | Meaning |
|-------|--------|---------|
| 🔴 Red Circle | Zoning submittals not made | Not started |
| 🟡 Yellow Circle | Zoning Submittal Made | In progress |
| 🔵 Light Blue Circle | Zoning Board Meeting Scheduled | Meeting pending |
| 🟢 Green Circle | Zoning Complete - Letter Received | Completed |
| ⭐ Red Star | Zoning Denied | Denied |
| ⭐ Green Star | Preliminary Site Plan Created | Site plan ready |

---

## Sharing with Your Team

### Securely Share the KML URL

**Share this with your team:**
```
https://your-project-name.vercel.app/kml
```

**Instructions for team members:**
1. Open Google Earth Pro
2. File → Open → Network Link  
3. Paste the URL above
4. Click OK

**Security note:** Anyone with the URL can view the map. The URL is not guessable, but:
- Don't post it publicly
- Only share with authorized team members
- If you need stricter security, see SECURITY.md for adding authentication

---

## Verifying Everything Works

### Check 1: Airtable Connection
Visit: https://your-project-name.vercel.app/health

Should return:
```json
{
  "status": "healthy",
  "airtable_connection": "ok",
  "records_count": X
}
```

If `records_count` is 0, check that:
- Table "Table 1" has records
- Records have data in "Latitude and Longitude" field

### Check 2: KML Format
Visit: https://your-project-name.vercel.app/kml

Should download a KML file starting with:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
```

### Check 3: Data Updates
1. Update a record in Airtable (change Zoning Status)
2. Wait up to 30 minutes (or restart Google Earth Pro to force refresh)
3. Verify change appears in Google Earth

---

## Troubleshooting

### "No records appear in Google Earth"

**Check:**
1. Does Airtable have records with coordinates?
2. Is "Latitude and Longitude" field formatted correctly? (Example: "34.258707, -79.802132")
3. Test the health endpoint - does it show records?

**Fix:**
- Open Airtable
- Verify "Latitude and Longitude" field contains "lat, long" format
- Example: 34.258707, -79.802132 (not 34.258707 / -79.802132 or other format)

### "Map doesn't update"

**Check:**
1. Are you using Google Earth **Pro** (desktop)? The web version has limited NetworkLink support.
2. Did you add as NetworkLink (not a static file)?

**Fix:**
1. In Google Earth Pro, right-click "Live Zoning Projects" in Places panel
2. Select "Properties"
3. Go to "Refresh" tab
4. Verify "Time-Based Refresh" is checked
5. Verify interval is 1800 seconds (30 minutes)

### "Vercel deployment failed"

**Common causes:**
1. Environment variables not set
2. Python version incompatible

**Fix:**
```bash
# Re-add environment variables
vercel env ls

# If any are missing, add them:
vercel env add AIRTABLE_TOKEN
```

### "Authentication failed with Airtable"

**Check:**
1. Token hasn't expired
2. Token is scoped to correct base

**Fix:**
1. Go to https://airtable.com/account/tokens
2. Verify token status
3. If revoked/expired, create new token
4. Update in Vercel:
   ```bash
   vercel env rm AIRTABLE_TOKEN production
   vercel env add AIRTABLE_TOKEN production
   # Enter new token
   vercel --prod  # Redeploy
   ```

---

## What's Included

Your project contains:

- `app.py` - Main application
- `requirements.txt` - Python dependencies
- `test_local.py` - Local testing script
- `.env` - Your Airtable credentials (KEEP SECURE)
- `README.md` - Full documentation
- `DEPLOYMENT.md` - Detailed deployment instructions for all platforms
- `SECURITY.md` - Security guidelines and best practices
- `vercel.json` - Vercel configuration
- `Procfile` - Heroku configuration
- `.gitignore` - Protects sensitive files

---

## Next Steps After Deployment

1. **Bookmark your KML URL** for easy reference
2. **Test with your team** - have 2-3 people try loading the NetworkLink
3. **Monitor the health endpoint** - set up a bookmark or monitoring service
4. **Update as needed**:
   - Change status colors: Edit `STATUS_STYLES` in `app.py`
   - Change refresh interval: Update `REFRESH_INTERVAL_MINUTES` environment variable
   - Add new fields to display: Modify `generate_placemark()` in `app.py`

---

## Support Resources

- **Full Documentation**: See `README.md`
- **Deployment Options**: See `DEPLOYMENT.md` for AWS, Google Cloud, Heroku
- **Security Setup**: See `SECURITY.md` for adding authentication
- **Source Code**: `app.py` has extensive comments

---

## Getting Help

If you encounter issues:

1. **Check the logs:**
   ```bash
   # Vercel
   vercel logs
   
   # Local
   Check terminal where python app.py is running
   ```

2. **Test locally:**
   ```bash
   python test_local.py
   ```

3. **Verify Airtable data:**
   - Open your Airtable base
   - Check "Latitude and Longitude" field format
   - Verify "Zoning Status" values match expected values

4. **Check health endpoint:**
   ```
   https://your-project-name.vercel.app/health
   ```

---

## Important Notes

- **Keep `.env` file secure** - it contains your API token
- **Don't commit to public Git** - `.gitignore` is configured to protect sensitive files  
- **Share KML URL only with authorized team** - it provides access to your zoning data
- **Token is scoped** - it only accesses "Table 1" in your specified base

---

**Questions?** Review the detailed documentation in README.md, DEPLOYMENT.md, and SECURITY.md.

**Ready to deploy?** Follow Option 1 to test locally or Option 2 to deploy to Vercel immediately.

Good luck with your zoning projects! 🗺️
