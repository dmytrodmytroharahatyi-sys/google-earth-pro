# Google Earth KML with Airtable Integration

This application generates dynamic KML files for Google Earth Pro that automatically update with data from Airtable. It uses NetworkLink for automatic refresh every 30 minutes, with color-coded placemarks based on zoning status.

## Features

- ✅ **Dynamic KML Generation**: Fetches real-time data from Airtable
- ✅ **NetworkLink Support**: Automatic refresh in Google Earth Pro (30-minute intervals)
- ✅ **Color-Coded Status**: Visual indicators based on zoning status
- ✅ **Secure Configuration**: API tokens stored as environment variables
- ✅ **Multiple Deployment Options**: Works with Vercel, AWS Lambda, Google Cloud Run, Heroku
- ✅ **Health Monitoring**: Built-in health check endpoints
- ✅ **Webhook Support**: Optional real-time refresh triggers

## Project Configuration

### Airtable Setup
- **Base ID**: `appZOdJaRPiwcygdR`
- **Table Name**: `Table 1`
- **Coordinates Field**: `Latitude and Longitude` (format: "lat, long")
- **Status Field**: `Zoning Status`
- **Refresh Interval**: 30 minutes

### Status Color Mapping

| Status | Color | Icon |
|--------|-------|------|
| Zoning submittals not made | 🔴 Red | Red Circle |
| Zoning Submittal Made | 🟡 Yellow | Yellow Circle |
| Zoning Board Meeting Scheduled | 🔵 Light Blue | Light Blue Circle |
| Zoning Complete - Letter Received | 🟢 Green | Green Circle |
| Zoning Denied | ⭐ Dark Red | Red Star |
| Preliminary Site Plan Created | ⭐ Green | Green Star |

## Quick Start

### Prerequisites
- Python 3.11 or higher
- Airtable account with API token
- Google Earth Pro (desktop application)

### Local Development

1. **Clone or extract the project files**

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Copy `.env.example` to `.env` and update with your credentials:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env`:
   ```
   AIRTABLE_BASE_ID=appZOdJaRPiwcygdR
   AIRTABLE_TABLE_NAME=Table 1
   AIRTABLE_TOKEN=patqR9ByQIKeyzjcO.7eabbc1c8af38378316e098d193a4a9fa09f304a99f062e616f2f930f79cc76f
   REFRESH_INTERVAL_MINUTES=30
   PORT=5000
   ```

5. **Run the application**
   ```bash
   python app.py
   ```
   
   The server will start at `http://localhost:5000`

6. **Test locally**
   - Open browser: `http://localhost:5000`
   - View KML: `http://localhost:5000/kml`
   - Check health: `http://localhost:5000/health`

## Deployment Options

### Option 1: Vercel (Recommended - Easiest)

Vercel provides free hosting for serverless Python applications with automatic HTTPS.

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Set environment variables**
   ```bash
   vercel env add AIRTABLE_BASE_ID
   # Enter: appZOdJaRPiwcygdR
   
   vercel env add AIRTABLE_TABLE_NAME
   # Enter: Table 1
   
   vercel env add AIRTABLE_TOKEN
   # Enter: your_token_here
   
   vercel env add REFRESH_INTERVAL_MINUTES
   # Enter: 30
   ```

4. **Deploy**
   ```bash
   vercel --prod
   ```

5. **Get your URL**
   Vercel will provide a URL like: `https://your-project.vercel.app`

### Option 2: AWS Lambda + API Gateway

1. **Install AWS SAM CLI**
   ```bash
   pip install aws-sam-cli
   ```

2. **Create `template.yaml`** (see deployment folder)

3. **Deploy**
   ```bash
   sam build
   sam deploy --guided
   ```

4. **Set environment variables** in AWS Console → Lambda → Configuration → Environment variables

### Option 3: Google Cloud Run

1. **Install Google Cloud SDK**

2. **Create `Dockerfile`**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY app.py .
   
   CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 120 app:app
   ```

3. **Build and deploy**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT/kml-service
   gcloud run deploy kml-service --image gcr.io/YOUR_PROJECT/kml-service --platform managed
   ```

4. **Set environment variables** in Cloud Run console

### Option 4: Heroku

1. **Install Heroku CLI**

2. **Create Heroku app**
   ```bash
   heroku create your-kml-app
   ```

3. **Set environment variables**
   ```bash
   heroku config:set AIRTABLE_BASE_ID=appZOdJaRPiwcygdR
   heroku config:set AIRTABLE_TABLE_NAME="Table 1"
   heroku config:set AIRTABLE_TOKEN=your_token_here
   heroku config:set REFRESH_INTERVAL_MINUTES=30
   ```

4. **Deploy**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   heroku git:remote -a your-kml-app
   git push heroku main
   ```

## Using with Google Earth Pro

### Method 1: Direct NetworkLink (Recommended)

1. Open **Google Earth Pro** (desktop application)
2. Go to **File** → **Open** → **Network Link**
3. Enter your deployment URL + `/kml`:
   ```
   https://your-deployment-url.com/kml
   ```
4. Click **OK**
5. The map will appear and automatically refresh every 30 minutes

### Method 2: Download and Open

1. Open your browser and navigate to:
   ```
   https://your-deployment-url.com/kml
   ```
2. Save the file as `zoning-map.kml`
3. Open the file in Google Earth Pro
4. The NetworkLink will maintain automatic updates

## API Endpoints

### `GET /`
Status page with usage instructions

### `GET /kml`
Root NetworkLink KML file - load this URL in Google Earth Pro

### `GET /kml/data`
Data endpoint (called automatically by NetworkLink)

### `GET /health`
Health check endpoint
```json
{
  "status": "healthy",
  "airtable_connection": "ok",
  "records_count": 25,
  "timestamp": "2026-02-05T12:00:00"
}
```

### `POST /webhook/refresh`
Manual refresh trigger (optional)
```bash
curl -X POST https://your-deployment-url.com/webhook/refresh
```

## Security Considerations

### Environment Variables
- **NEVER** commit `.env` file to version control
- Use environment variable management in your hosting platform
- The provided Airtable token is scoped to specific base only

### Access Control
If you need to restrict access to the KML endpoint:

1. **Add authentication middleware** (example for API key):
   ```python
   from functools import wraps
   from flask import request, abort
   
   def require_api_key(f):
       @wraps(f)
       def decorated_function(*args, **kwargs):
           api_key = request.headers.get('X-API-Key')
           if api_key != os.environ.get('API_KEY'):
               abort(401)
           return f(*args, **kwargs)
       return decorated_function
   
   @app.route('/kml')
   @require_api_key
   def network_link_kml():
       # ... existing code
   ```

2. **Configure in Google Earth**:
   - When adding NetworkLink, click "Add HTTP Header"
   - Add: `X-API-Key: your_secret_key`

### HTTPS/SSL
- All deployment platforms (Vercel, AWS, GCP, Heroku) provide free SSL
- Google Earth Pro requires HTTPS for secure NetworkLinks
- Local development uses HTTP (for testing only)

## Monitoring and Maintenance

### Health Checks
Set up automated monitoring with the `/health` endpoint:
```bash
# Example with curl
curl https://your-deployment-url.com/health
```

### Logs
Check application logs in your hosting platform:
- **Vercel**: `vercel logs`
- **AWS Lambda**: CloudWatch Logs
- **Google Cloud Run**: Cloud Logging
- **Heroku**: `heroku logs --tail`

### Airtable Rate Limits
- Free plan: 5 requests/second per base
- Plus plan: 10 requests/second per base
- With 30-minute refresh: ~2 requests/hour (well within limits)

## Troubleshooting

### Issue: No placemarks appearing in Google Earth

**Check:**
1. Verify Airtable token is valid
2. Check that "Latitude and Longitude" field has valid data
3. Test the data endpoint: `https://your-url.com/kml/data`
4. Check coordinates format is "lat, long" (e.g., "34.258707, -79.802132")

### Issue: Map not updating automatically

**Check:**
1. Using Google Earth **Pro** (desktop), not Google Earth Web
2. NetworkLink was added, not just a static KML file
3. Check NetworkLink properties: should show refresh interval of 1800 seconds (30 minutes)

### Issue: Wrong colors/icons

**Check:**
1. Verify "Zoning Status" field values match exactly (case-sensitive)
2. Check status mapping in `STATUS_STYLES` dictionary
3. View raw KML to confirm styles are applied

### Issue: Airtable connection errors

**Check:**
1. Token is correctly set in environment variables
2. Token has not expired
3. Base ID and Table Name are correct
4. Network connectivity from hosting platform

## Customization

### Change Refresh Interval
Update `REFRESH_INTERVAL_MINUTES` environment variable:
```bash
# Vercel
vercel env add REFRESH_INTERVAL_MINUTES
# Enter: 15 (for 15 minutes)

# Heroku
heroku config:set REFRESH_INTERVAL_MINUTES=15
```

### Add New Status Colors
Edit `STATUS_STYLES` in `app.py`:
```python
STATUS_STYLES = {
    'New Status': {
        'color': 'ff00ff00',  # aabbggrr format
        'icon': 'http://maps.google.com/mapfiles/kml/paddle/grn-circle.png',
        'description': 'New Status Description'
    },
    # ... existing statuses
}
```

### Customize Icons
Browse available icons: http://kml4earth.appspot.com/icons.html

Common icon URLs:
```
http://maps.google.com/mapfiles/kml/paddle/red-circle.png
http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png
http://maps.google.com/mapfiles/kml/paddle/grn-circle.png
http://maps.google.com/mapfiles/kml/paddle/blu-circle.png
http://maps.google.com/mapfiles/kml/paddle/wht-circle.png
```

## Technical Details

### Architecture
```
User (Google Earth Pro)
    ↓ (loads NetworkLink)
    ↓ (refreshes every 30 min)
Flask Application (app.py)
    ↓ (fetches data)
Airtable API
```

### KML Structure
1. **Root KML** (`/kml`): Contains NetworkLink configuration
2. **Data KML** (`/kml/data`): Contains actual placemarks and styles

### Data Flow
1. Google Earth Pro loads root NetworkLink KML
2. Root KML points to data endpoint with 30-minute refresh
3. Data endpoint fetches records from Airtable
4. Records are parsed and converted to KML placemarks
5. Placemarks are styled based on status field
6. Complete KML document is returned to Google Earth

## Support and Contact

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs in your hosting platform
3. Test endpoints directly in browser
4. Verify Airtable data structure and credentials

## License

This project is provided as-is for the client's internal use.

## Version History

- **v1.0** (2026-02-05): Initial release
  - Airtable integration
  - NetworkLink support
  - Color-coded status markers
  - Multiple deployment options
  - Health monitoring

---

**Note**: This application is configured for internal team access only. The Airtable token and data should be kept secure and not shared publicly.
