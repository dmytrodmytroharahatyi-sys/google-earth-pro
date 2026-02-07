# Quick Start: Deploying with Password Protection

## Step 1: Update Your Credentials

**IMPORTANT:** Before deploying, choose a strong password and update it in your Vercel project.

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Go to **Settings → Environment Variables**
4. Add these variables:

```
AUTH_USERNAME=your-username-here
AUTH_PASSWORD=YourStrongPassword123!
AIRTABLE_BASE_ID=appZOdJaRPiwcygdR
AIRTABLE_TABLE_NAME=Table 1
AIRTABLE_TOKEN=patqR9ByQIKeyzjcO.7eabbc1c8af38378316e098d193a4a9fa09f304a99f062e616f2f930f79cc76f
REFRESH_INTERVAL_MINUTES=30
```

**🔒 CRITICAL:** Set both `AUTH_USERNAME` and `AUTH_PASSWORD` in Vercel! Without them, the site will be unprotected.

## Step 2: Deploy

Push your code to GitHub or run:

```bash
vercel --prod
```

## Step 3: Test

Visit your Vercel URL - you should see a login prompt. Enter your credentials.

```bash
# Test with PowerShell
$cred = Get-Credential
Invoke-WebRequest -Uri "https://your-project.vercel.app/" -Credential $cred

# Or with curl (if installed)
curl -u username:password https://your-project.vercel.app/
```

## Step 4: Use in Google Earth Pro

1. Open Google Earth Pro
2. File → Open → Network Link
3. URL: `https://your-project.vercel.app/kml`
4. Enter username and password when prompted

Done! Your data is now protected with password authentication.

---

For detailed documentation, see `DEPLOYMENT.md`
