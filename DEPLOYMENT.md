# Deployment Guide - Google Earth KML Service

## Security Features

This application includes **Basic Authentication** via Vercel Edge Middleware to protect your sensitive Airtable data from unauthorized access.

## Deployment Steps

### 1. Set Environment Variables in Vercel

Before deploying, you **MUST** set these environment variables in your Vercel project settings:

1. Go to your Vercel project dashboard
2. Navigate to **Settings → Environment Variables**
3. Add the following variables:

```
AIRTABLE_BASE_ID=appZOdJaRPiwcygdR
AIRTABLE_TABLE_NAME=Table 1
AIRTABLE_TOKEN=your_airtable_token_here
REFRESH_INTERVAL_MINUTES=30
AUTH_USERNAME=your_chosen_username
AUTH_PASSWORD=your_secure_password_here
```

### 2. Important Security Notes

#### Change Default Credentials
- **CRITICAL:** Change `AUTH_USERNAME` and `AUTH_PASSWORD` from the default values
- Use a strong password (at least 12 characters with letters, numbers, and symbols)
- Do NOT use "admin" / "password" in production

#### Keep Credentials Secure
- Share credentials only with authorized team members via secure channels (password manager, encrypted email)
- Do NOT commit `.env` or `.env.local` files to Git (already in `.gitignore`)
- Store credentials securely (use a password manager like 1Password, LastPass, etc.)

### 3. Deploy to Vercel

```bash
# Install Vercel CLI (if not already installed)
npm i -g vercel

# Deploy
vercel --prod
```

Or push to your connected GitHub repository for automatic deployment.

### 4. Using the Protected Service

#### In Web Browser
- Visit your Vercel URL (e.g., `https://your-project.vercel.app`)
- A login popup will appear
- Enter the username and password you configured
- Click OK

#### In Google Earth Pro
When adding the Network Link:
1. Go to **File → Open → Network Link**
2. Enter the URL: `https://your-project.vercel.app/kml`
3. When prompted for credentials, enter your username and password
4. Click OK

The credentials will be saved in Google Earth Pro and used for automatic updates.

### 5. Testing Authentication

After deployment, test that authentication is working:

1. **Test without credentials:**
   ```bash
   curl https://your-project.vercel.app/
   ```
   Should return: `401 Authentication required`

2. **Test with credentials:**
   ```bash
   curl -u username:password https://your-project.vercel.app/
   ```
   Should return: Status page HTML

3. **Test with wrong credentials:**
   ```bash
   curl -u wrong:credentials https://your-project.vercel.app/
   ```
   Should return: `401 Invalid credentials`

## How Authentication Works

### Edge Middleware
- Runs on Vercel's Edge Network (fast, globally distributed)
- Checks **every** request before reaching your application
- Uses HTTP Basic Authentication (standard protocol)
- Compatible with browsers, Google Earth Pro, and API clients

### Authentication Flow
1. User/client makes request to any endpoint
2. Middleware intercepts the request
3. Checks for `Authorization` header with valid credentials
4. If valid → allows request to proceed
5. If invalid/missing → returns 401 error with authentication prompt

### What's Protected
All endpoints are protected:
- `/` - Status page
- `/kml` - Network Link KML
- `/kml/data` - Data endpoint
- `/webhook/refresh` - Webhook endpoint
- `/health` - Health check endpoint

## Sharing Access with Team Members

When sharing access with your team:

1. **Share credentials securely:**
   - Use a password manager's sharing feature
   - Send via encrypted email
   - Or provide in-person / via secure chat

2. **Instructions for team members:**
   ```
   Google Earth KML Service Access:
   
   URL: https://your-project.vercel.app/kml
   Username: [provided separately]
   Password: [provided separately]
   
   Steps:
   1. Open Google Earth Pro
   2. Go to File → Open → Network Link
   3. Paste the URL above
   4. When prompted, enter the username and password
   5. The map will load and auto-update every 30 minutes
   ```

3. **Revoking access:**
   - Change the password in Vercel environment variables
   - Redeploy the application
   - Only share new password with authorized users

## Troubleshooting

### "Authentication required" keeps appearing
- Clear your browser's cached credentials
- Google Earth Pro: Remove the Network Link and re-add it
- Ensure you're using the correct, up-to-date credentials

### Can't authenticate in Google Earth Pro
- Verify the URL is correct (must be HTTPS)
- Try accessing the URL in a browser first to test credentials
- Check that credentials don't contain special characters that need escaping

### 401 errors after deployment
- Verify environment variables are set in Vercel dashboard
- Check that `AUTH_PASSWORD` is set (authentication is disabled if not set)
- Ensure there are no typos in the variable names

## Alternative: IP Whitelisting

If you want to restrict access by IP address instead of/in addition to passwords, the middleware can be extended to check the requesting IP against an allowlist. Contact support for implementation.

## Cost & Performance

- Edge Middleware runs on Vercel's Edge Network (included in all plans)
- Minimal performance impact (<10ms added latency)
- No additional costs for authentication
- Works with Vercel Free, Pro, and Enterprise plans
