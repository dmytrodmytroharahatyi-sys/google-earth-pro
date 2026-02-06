# Detailed Deployment Guide

This document provides step-by-step instructions for deploying the Google Earth KML service to various hosting platforms.

## Table of Contents
1. [Vercel Deployment (Recommended)](#vercel-deployment)
2. [AWS Lambda Deployment](#aws-lambda-deployment)
3. [Google Cloud Run Deployment](#google-cloud-run-deployment)
4. [Heroku Deployment](#heroku-deployment)
5. [Post-Deployment Steps](#post-deployment-steps)

---

## Vercel Deployment

Vercel is recommended for its simplicity, free tier, and automatic HTTPS.

### Prerequisites
- Node.js installed (for Vercel CLI)
- Vercel account (free): https://vercel.com/signup

### Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

### Step 2: Login to Vercel
```bash
vercel login
```
Follow the prompts to authenticate via email or GitHub.

### Step 3: Configure Project

The `vercel.json` file is already configured. It should look like this:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ]
}
```

### Step 4: Set Environment Variables

Option A: Using Vercel CLI (recommended)
```bash
vercel env add AIRTABLE_BASE_ID production
# When prompted, enter: appZOdJaRPiwcygdR

vercel env add AIRTABLE_TABLE_NAME production
# When prompted, enter: Table 1

vercel env add AIRTABLE_TOKEN production
# When prompted, enter: patqR9ByQIKeyzjcO.7eabbc1c8af38378316e098d193a4a9fa09f304a99f062e616f2f930f79cc76f

vercel env add REFRESH_INTERVAL_MINUTES production
# When prompted, enter: 30
```

Option B: Using Vercel Dashboard
1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to Settings → Environment Variables
4. Add each variable with the values above

### Step 5: Deploy
```bash
# Deploy to production
vercel --prod

# Or let Vercel prompt you through the process
vercel
```

### Step 6: Get Your URL
After deployment, Vercel will display your URL:
```
https://your-project-name.vercel.app
```

### Step 7: Test Deployment
```bash
# Test status page
curl https://your-project-name.vercel.app/

# Test health endpoint
curl https://your-project-name.vercel.app/health

# Download KML to test
curl https://your-project-name.vercel.app/kml -o test.kml
```

---

## AWS Lambda Deployment

### Prerequisites
- AWS account
- AWS CLI installed and configured
- SAM CLI installed

### Step 1: Install AWS SAM CLI
```bash
pip install aws-sam-cli
```

### Step 2: Create SAM Template

Create `template.yaml`:
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Parameters:
  AirtableBaseId:
    Type: String
    Default: appZOdJaRPiwcygdR
  AirtableTableName:
    Type: String
    Default: "Table 1"
  AirtableToken:
    Type: String
    NoEcho: true
  RefreshInterval:
    Type: Number
    Default: 30

Resources:
  KMLFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: app.app
      Runtime: python3.11
      Timeout: 30
      MemorySize: 512
      Environment:
        Variables:
          AIRTABLE_BASE_ID: !Ref AirtableBaseId
          AIRTABLE_TABLE_NAME: !Ref AirtableTableName
          AIRTABLE_TOKEN: !Ref AirtableToken
          REFRESH_INTERVAL_MINUTES: !Ref RefreshInterval
      Events:
        Root:
          Type: Api
          Properties:
            Path: /
            Method: ANY
        Proxy:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY

Outputs:
  ApiUrl:
    Description: "API Gateway endpoint URL"
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/"
```

### Step 3: Create Lambda Entry Point

Create `lambda_handler.py`:
```python
from app import app
import awsgi

def lambda_handler(event, context):
    return awsgi.response(app, event, context)
```

### Step 4: Update requirements.txt
Add to `requirements.txt`:
```
aws-wsgi==0.2.7
```

### Step 5: Build and Deploy
```bash
# Build
sam build

# Deploy (guided first time)
sam deploy --guided

# Follow prompts:
# - Stack Name: kml-service
# - AWS Region: us-east-1 (or your preferred region)
# - Parameter AirtableToken: [paste your token]
# - Confirm changes: Y
# - Allow SAM CLI IAM role creation: Y
# - Save arguments to configuration file: Y
```

### Step 6: Get Your URL
After deployment, SAM will output your API Gateway URL:
```
https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/Prod/
```

---

## Google Cloud Run Deployment

### Prerequisites
- Google Cloud account
- gcloud CLI installed and configured
- Docker installed

### Step 1: Create Dockerfile

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Cloud Run expects PORT env var
ENV PORT=8080

# Run with gunicorn
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 120 app:app
```

### Step 2: Create .dockerignore

Create `.dockerignore`:
```
.env
.env.local
__pycache__/
*.pyc
.git/
.vscode/
.idea/
venv/
env/
```

### Step 3: Build Container
```bash
# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com

# Build and push to Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/kml-service
```

### Step 4: Deploy to Cloud Run
```bash
gcloud run deploy kml-service \
  --image gcr.io/YOUR_PROJECT_ID/kml-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars AIRTABLE_BASE_ID=appZOdJaRPiwcygdR \
  --set-env-vars AIRTABLE_TABLE_NAME="Table 1" \
  --set-env-vars AIRTABLE_TOKEN=patqR9ByQIKeyzjcO.7eabbc1c8af38378316e098d193a4a9fa09f304a99f062e616f2f930f79cc76f \
  --set-env-vars REFRESH_INTERVAL_MINUTES=30
```

### Step 5: Get Your URL
Cloud Run will output your service URL:
```
https://kml-service-xxxxxxxxxx-uc.a.run.app
```

---

## Heroku Deployment

### Prerequisites
- Heroku account
- Heroku CLI installed

### Step 1: Install Heroku CLI
```bash
# macOS
brew install heroku/brew/heroku

# Windows
# Download from: https://devcenter.heroku.com/articles/heroku-cli
```

### Step 2: Login to Heroku
```bash
heroku login
```

### Step 3: Create Heroku App
```bash
heroku create your-kml-service
# or let Heroku generate a name:
heroku create
```

### Step 4: Set Environment Variables
```bash
heroku config:set AIRTABLE_BASE_ID=appZOdJaRPiwcygdR
heroku config:set AIRTABLE_TABLE_NAME="Table 1"
heroku config:set AIRTABLE_TOKEN=patqR9ByQIKeyzjcO.7eabbc1c8af38378316e098d193a4a9fa09f304a99f062e616f2f930f79cc76f
heroku config:set REFRESH_INTERVAL_MINUTES=30
```

### Step 5: Initialize Git (if not already)
```bash
git init
git add .
git commit -m "Initial commit"
```

### Step 6: Deploy
```bash
# Add Heroku remote
heroku git:remote -a your-kml-service

# Deploy
git push heroku main
```

### Step 7: Get Your URL
```
https://your-kml-service.herokuapp.com
```

---

## Post-Deployment Steps

### 1. Verify Deployment

Test all endpoints:
```bash
# Replace YOUR_URL with your actual deployment URL

# Test status page
curl https://YOUR_URL/

# Test health check
curl https://YOUR_URL/health

# Should return:
# {"status":"healthy","airtable_connection":"ok","records_count":X}

# Test KML endpoint
curl https://YOUR_URL/kml

# Test data endpoint
curl https://YOUR_URL/kml/data
```

### 2. Configure Google Earth Pro

1. Open Google Earth Pro
2. Go to **File** → **Open** → **Network Link**
3. Fill in:
   - **Name**: "Live Zoning Projects"
   - **Link**: `https://YOUR_URL/kml`
   - **Refresh**: Should auto-configure from KML (verify it shows 30 minutes)
4. Click **OK**

### 3. Verify Auto-Refresh

In Google Earth Pro:
1. Right-click on "Live Zoning Projects" in Places panel
2. Select **Properties**
3. Go to **Refresh** tab
4. Verify:
   - **Time-Based Refresh**: Checked
   - **Refresh**: 30 minutes

### 4. Monitor Health

Set up monitoring (choose one):

**Option A: Simple uptime monitoring**
- Use a service like UptimeRobot (free)
- Monitor URL: `https://YOUR_URL/health`
- Check interval: Every 5 minutes

**Option B: Custom monitoring script**
```bash
#!/bin/bash
# save as monitor.sh

ENDPOINT="https://YOUR_URL/health"
RESPONSE=$(curl -s $ENDPOINT)
STATUS=$(echo $RESPONSE | jq -r '.status')

if [ "$STATUS" != "healthy" ]; then
    echo "Service unhealthy: $RESPONSE"
    # Send alert (email, Slack, etc.)
fi
```

### 5. Set Up Webhook (Optional)

If you want real-time updates triggered by Airtable changes:

1. In Airtable, go to Automations
2. Create new automation:
   - **Trigger**: When record updated
   - **Action**: Send webhook
   - **URL**: `https://YOUR_URL/webhook/refresh`
   - **Method**: POST

### 6. Document for Client

Provide client with:
1. **KML URL**: `https://YOUR_URL/kml`
2. **Status page**: `https://YOUR_URL/`
3. **Login credentials** for hosting platform (if they own the account)
4. **Instructions** for Google Earth Pro setup (from README.md)

### 7. Security Checklist

- [ ] Environment variables are set (not hardcoded)
- [ ] `.env` file is in `.gitignore`
- [ ] Airtable token is scoped (not a personal access token)
- [ ] HTTPS is enabled (automatic on all platforms)
- [ ] Deployment URL is documented and shared only with authorized team

---

## Updating the Application

### Update Code

1. Make changes to `app.py`
2. Test locally:
   ```bash
   python app.py
   ```
3. Deploy update:

**Vercel:**
```bash
vercel --prod
```

**AWS Lambda:**
```bash
sam build && sam deploy
```

**Google Cloud Run:**
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/kml-service
gcloud run deploy kml-service --image gcr.io/YOUR_PROJECT_ID/kml-service
```

**Heroku:**
```bash
git add .
git commit -m "Update description"
git push heroku main
```

### Update Environment Variables

**Vercel:**
```bash
vercel env rm AIRTABLE_TOKEN production
vercel env add AIRTABLE_TOKEN production
```

**AWS Lambda:**
```bash
sam deploy --parameter-overrides AirtableToken=NEW_TOKEN
```

**Google Cloud Run:**
```bash
gcloud run services update kml-service --set-env-vars AIRTABLE_TOKEN=NEW_TOKEN
```

**Heroku:**
```bash
heroku config:set AIRTABLE_TOKEN=NEW_TOKEN
```

---

## Troubleshooting Deployments

### Vercel: "Build Failed"
- Check `vercel.json` syntax
- Ensure `requirements.txt` is valid
- View build logs: `vercel logs`

### AWS Lambda: "Timeout"
- Increase timeout in `template.yaml` (currently 30s)
- Check CloudWatch Logs for errors

### Google Cloud Run: "Container failed to start"
- Check Dockerfile syntax
- Verify PORT environment variable
- View logs: `gcloud run logs read --service kml-service`

### Heroku: "Application Error"
- Check `Procfile` syntax
- Verify buildpack: `heroku buildpacks`
- View logs: `heroku logs --tail`

### All Platforms: "Airtable Connection Error"
- Verify `AIRTABLE_TOKEN` is set correctly
- Check token hasn't expired
- Verify `AIRTABLE_BASE_ID` is correct
- Test token manually with curl

---

## Cost Estimates

All platforms offer free tiers suitable for this use case:

- **Vercel**: Free tier includes 100GB bandwidth/month, plenty for KML files
- **AWS Lambda**: Free tier includes 1M requests/month (you'll use ~50/month)
- **Google Cloud Run**: Free tier includes 2M requests/month
- **Heroku**: Free tier available (sleeps after 30 min inactivity, wakes on request)

**Recommended for production**: Vercel or Google Cloud Run (no sleep, better performance)

---

## Backup and Recovery

### Backup Configuration
Save these in a secure location:
- Environment variable values
- Deployment configuration files
- Source code repository URL

### Recovery Steps
1. Clone/extract source code
2. Restore environment variables
3. Redeploy using steps above

---

For additional support or questions, refer to the main README.md or contact the development team.
