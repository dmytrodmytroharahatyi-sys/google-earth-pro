# Security Guidelines

This document outlines security considerations and best practices for the Google Earth KML service.

## Authentication & Authorization

### Airtable Token Security

**Current Setup:**
- Using scoped token (recommended): `patqR9ByQIKeyzjcO...`
- Token is restricted to specific base only
- Token does not provide access to entire Airtable account

**Best Practices:**
1. **NEVER** commit tokens to version control
2. **ALWAYS** use environment variables
3. Store tokens in secure password manager
4. Rotate tokens periodically (every 90 days recommended)

### Token Storage

**✅ Correct:**
```bash
# In .env file (NOT committed)
AIRTABLE_TOKEN=patqR9ByQIKeyzjcO...

# In hosting platform
vercel env add AIRTABLE_TOKEN production
```

**❌ Wrong:**
```python
# Hardcoded in app.py
AIRTABLE_TOKEN = "patqR9ByQIKeyzjcO..."  # NEVER DO THIS
```

## Access Control

### Current Configuration
- Public KML endpoints (no authentication)
- Designed for internal team access only
- Relies on URL obscurity

### Adding Authentication (If Needed)

If you need to restrict access to authorized users only:

#### Option 1: API Key Authentication

1. **Update app.py:**

```python
from functools import wraps
from flask import request, abort
import os

API_KEY = os.environ.get('API_KEY')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        provided_key = request.headers.get('X-API-Key')
        if not API_KEY or provided_key != API_KEY:
            abort(401, 'Unauthorized')
        return f(*args, **kwargs)
    return decorated_function

# Apply to KML endpoints
@app.route('/kml')
@require_api_key
def network_link_kml():
    # ... existing code

@app.route('/kml/data')
@require_api_key
def data_kml():
    # ... existing code
```

2. **Set API key:**
```bash
vercel env add API_KEY production
# Enter a strong random key
```

3. **Configure Google Earth Pro:**
- Add NetworkLink as usual
- In NetworkLink properties, add HTTP header:
  - Name: `X-API-Key`
  - Value: `your_api_key_here`

#### Option 2: IP Whitelist

For AWS/GCP deployments, restrict access by IP:

**AWS Lambda:**
```yaml
# In template.yaml, add API Gateway resource policy
ApiGatewayResourcePolicy:
  Type: AWS::ApiGateway::RestApi
  Properties:
    Policy:
      Statement:
        - Effect: Allow
          Principal: '*'
          Action: 'execute-api:Invoke'
          Resource: '*'
          Condition:
            IpAddress:
              aws:SourceIp:
                - "YOUR_OFFICE_IP/32"
                - "YOUR_VPN_IP/32"
```

**Google Cloud Run:**
```bash
# Use Cloud Armor for IP filtering
gcloud compute security-policies create kml-policy
gcloud compute security-policies rules create 1000 \
    --security-policy kml-policy \
    --expression "origin.ip in ['YOUR_IP']" \
    --action allow
```

#### Option 3: Basic Authentication

1. **Update app.py:**
```python
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash

auth = HTTPBasicAuth()

users = {
    "admin": generate_password_hash(os.environ.get('ADMIN_PASSWORD', ''))
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

@app.route('/kml')
@auth.login_required
def network_link_kml():
    # ... existing code
```

2. **Update requirements.txt:**
```
Flask-HTTPAuth==4.8.0
```

3. **Google Earth Pro configuration:**
- Unfortunately, Google Earth Pro doesn't support Basic Auth well
- Consider using API key method instead

## Data Security

### In Transit
- **All hosting platforms provide HTTPS by default**
- Data encrypted between Airtable, server, and Google Earth Pro
- Google Earth Pro requires HTTPS for secure NetworkLinks

### At Rest
- No data is stored permanently on the server
- Each request fetches fresh data from Airtable
- No local database or cache (serverless architecture)

### Sensitive Data Handling

**If your Airtable contains sensitive information:**

1. **Review what's included in KML:**
   - By default, all Airtable fields are included in placemark descriptions
   - Consider filtering sensitive fields

2. **Update `generate_placemark()` in app.py:**
```python
def generate_placemark(record):
    fields = record.get('fields', {})
    
    # Define fields to EXCLUDE from KML
    SENSITIVE_FIELDS = [
        'Owner Name',
        'Contact Phone',
        'Email',
        'Internal Notes',
        'Budget'
    ]
    
    # Build description with filtered fields
    excluded_fields = ['Latitude and Longitude', 'Zoning Status'] + SENSITIVE_FIELDS
    for field_name, field_value in fields.items():
        if field_name not in excluded_fields and field_value:
            description_parts.append(f"<b>{escape(field_name)}:</b> {escape(str(field_value))}<br/>")
    
    # ... rest of function
```

## Airtable API Security

### Rate Limiting
- Airtable free tier: 5 requests/second per base
- Current usage: ~2 requests/hour (well within limits)
- No rate limiting implemented in app (not needed)

### Error Handling
- API errors are caught and logged
- Errors don't expose sensitive information to end users
- Returns generic error KML on failure

### Token Scoping
**Current token is scoped to:**
- Specific base: `appZOdJaRPiwcygdR`
- Specific permissions: Read-only (recommended)

**To verify/update scope:**
1. Go to https://airtable.com/account/tokens
2. Find your token
3. Verify scope is limited to necessary base and permissions

## Hosting Platform Security

### Environment Variables
All platforms support secure environment variable storage:

**Vercel:**
- Encrypted at rest
- Access restricted to project collaborators
- Audit logs available

**AWS Lambda:**
- Encrypted with AWS KMS
- IAM policy controls access
- CloudTrail logs all access

**Google Cloud Run:**
- Encrypted at rest and in transit
- IAM permissions required
- Cloud Audit Logs track access

**Heroku:**
- Encrypted in Dyno filesystem
- Access restricted to app collaborators
- Audit trail available

### Deployment Access

**Restrict who can deploy:**

**Vercel:**
```bash
# Only invite necessary team members
vercel teams add user@example.com
```

**AWS:**
```bash
# Use IAM policies to restrict deployment
# Only grant Lambda update permissions to specific users/roles
```

**Google Cloud:**
```bash
# Use IAM roles
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:deployer@example.com" \
  --role="roles/run.developer"
```

## Monitoring & Auditing

### Access Logs

**Enable access logging:**

**Vercel:**
- Automatic request logs
- View: `vercel logs --follow`

**AWS Lambda:**
- CloudWatch Logs automatically enabled
- View: AWS Console → CloudWatch → Logs

**Google Cloud Run:**
- Cloud Logging automatically enabled
- View: Cloud Console → Logging

### Security Monitoring

**Set up alerts for:**
1. Unusual request patterns
2. Failed authentication attempts (if auth is enabled)
3. Airtable API errors
4. Service health check failures

**Example CloudWatch Alarm (AWS):**
```yaml
ErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmDescription: Alert on function errors
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 5
    ComparisonOperator: GreaterThanThreshold
```

## Incident Response

### If Token is Compromised

1. **Immediately revoke token:**
   - Go to https://airtable.com/account/tokens
   - Find the compromised token
   - Click "Revoke"

2. **Generate new token:**
   - Create new scoped token
   - Update environment variables in hosting platform
   - Redeploy application

3. **Audit access:**
   - Review Airtable audit logs
   - Check for unauthorized data access
   - Review application logs for suspicious activity

### If Endpoint is Abused

**Signs of abuse:**
- Sudden spike in requests
- Unusual geographic access patterns
- Service degradation

**Response:**
1. **Check logs** for suspicious patterns
2. **Enable rate limiting** (see below)
3. **Add authentication** (see Access Control section)
4. **Contact hosting provider** if DDoS suspected

**Add rate limiting:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/kml/data')
@limiter.limit("10 per minute")
def data_kml():
    # ... existing code
```

## Security Checklist

Before deployment:
- [ ] Environment variables are configured (not hardcoded)
- [ ] `.env` file is in `.gitignore`
- [ ] Airtable token is scoped (not full account access)
- [ ] HTTPS is enabled (check deployment URL)
- [ ] No sensitive data exposed in KML
- [ ] Access controls implemented (if required)
- [ ] Monitoring and logging enabled
- [ ] Team members briefed on security practices

After deployment:
- [ ] Test all endpoints with proper credentials
- [ ] Verify HTTPS certificate is valid
- [ ] Confirm environment variables are set correctly
- [ ] Document token and configuration in secure location
- [ ] Set up monitoring alerts
- [ ] Review access logs weekly

## Security Updates

### Keep Dependencies Updated

**Check for updates:**
```bash
pip list --outdated
```

**Update dependencies:**
```bash
pip install --upgrade flask requests gunicorn
pip freeze > requirements.txt
```

**Recommended schedule:**
- Check monthly for updates
- Apply security patches immediately
- Test thoroughly before deploying

### Vulnerability Scanning

**Use safety to check for known vulnerabilities:**
```bash
pip install safety
safety check --file requirements.txt
```

## Compliance Considerations

### Data Privacy
- No personal data is stored by the application
- Data is fetched from Airtable on-demand
- No cookies or tracking
- No user accounts or profiles

### GDPR Compliance (if applicable)
- Document what data is processed (coordinates, status)
- Ensure Airtable data complies with GDPR
- Implement data access controls as needed
- Provide data deletion mechanism if required

## Contact

For security concerns or to report vulnerabilities:
1. **Do not** open public GitHub issues
2. Contact the development team directly
3. Provide detailed information about the issue
4. Allow 48 hours for initial response

---

**Last Updated**: February 5, 2026
**Version**: 1.0
