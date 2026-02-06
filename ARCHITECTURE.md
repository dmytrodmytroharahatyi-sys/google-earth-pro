# System Architecture

This document provides a technical overview of the Google Earth KML service architecture.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Earth Pro Client                  │
│                                                             │
│  User opens NetworkLink → Loads every 30 minutes           │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTPS
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Cloud Hosting Platform                         │
│         (Vercel / AWS Lambda / Cloud Run)                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │            Flask Application (app.py)               │  │
│  │                                                     │  │
│  │  Routes:                                           │  │
│  │  • GET  /           → Status page                  │  │
│  │  • GET  /kml        → NetworkLink KML (root)       │  │
│  │  • GET  /kml/data   → Data KML (with placemarks)   │  │
│  │  • GET  /health     → Health check                 │  │
│  │  • POST /webhook    → Manual refresh trigger       │  │
│  │                                                     │  │
│  │  Functions:                                        │  │
│  │  • fetch_airtable_records()                        │  │
│  │  • parse_coordinates()                             │  │
│  │  • generate_kml_document()                         │  │
│  │  • generate_network_link_kml()                     │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTPS + Bearer Token
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Airtable REST API                       │
│                                                             │
│  Base: appZOdJaRPiwcygdR                                   │
│  Table: Table 1                                            │
│  Fields:                                                    │
│  • Latitude and Longitude (text: "lat, long")             │
│  • Zoning Status (single select)                          │
│  • Other fields (displayed in placemark description)       │
└─────────────────────────────────────────────────────────────┘
```

---

## Request Flow

### User Loads NetworkLink in Google Earth Pro

```
1. User: File → Open → Network Link
   URL: https://your-app.vercel.app/kml

2. Google Earth Pro → GET /kml
   ↓
3. Server returns root KML with:
   <NetworkLink>
     <href>https://your-app.vercel.app/kml/data</href>
     <refreshMode>onInterval</refreshMode>
     <refreshInterval>1800</refreshInterval>  <!-- 30 min -->
   </NetworkLink>

4. Google Earth Pro → GET /kml/data (immediately)
   ↓
5. Server:
   a. Fetches records from Airtable API
   b. Parses coordinates
   c. Maps statuses to colors
   d. Generates KML with placemarks
   e. Returns KML document
   ↓
6. Google Earth Pro displays placemarks

7. Every 30 minutes:
   Google Earth Pro → GET /kml/data (automatic)
   → Server repeats steps 5a-5e
   → Display updates
```

---

## Component Details

### 1. Flask Application (`app.py`)

**Technology:** Python 3.11 + Flask 3.0.0

**Key Components:**

```python
# Core Data Functions
fetch_airtable_records()      # Fetches all records with pagination
parse_coordinates()            # Validates and parses "lat, long" format
get_style_for_status()        # Maps status to color/icon

# KML Generation Functions
generate_kml_styles()         # Creates Style definitions for all statuses
generate_placemark()          # Converts Airtable record → KML placemark
generate_kml_document()       # Builds complete data KML with all placemarks
generate_network_link_kml()   # Builds root KML with NetworkLink config

# Flask Routes
@app.route('/')               # Status/info page (HTML)
@app.route('/kml')           # Root NetworkLink KML
@app.route('/kml/data')      # Data KML (called by NetworkLink)
@app.route('/health')        # Health check (JSON)
@app.route('/webhook/refresh') # Manual trigger (POST)
```

**Design Patterns:**
- **Stateless**: No server-side data storage
- **On-demand**: Fetches fresh data on each request
- **Fail-safe**: Returns error KML on failure (won't break Google Earth)
- **Configurable**: All settings via environment variables

### 2. Airtable Integration

**API Version:** Airtable REST API v0

**Endpoints Used:**
```
GET https://api.airtable.com/v0/{baseId}/{tableName}
```

**Authentication:**
```
Authorization: Bearer {scopedToken}
```

**Pagination Handling:**
```python
all_records = []
offset = None
while True:
    response = requests.get(url, params={'offset': offset})
    data = response.json()
    all_records.extend(data['records'])
    offset = data.get('offset')
    if not offset:
        break
```

**Rate Limiting:**
- Airtable free tier: 5 requests/second per base
- This app: ~2 requests/hour (well within limits)
- No client-side rate limiting needed

### 3. KML Generation

**KML Version:** 2.2 (Google Earth standard)

**Structure:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>...</name>
    <description>...</description>
    
    <!-- Style Definitions -->
    <Style id="status_id">
      <IconStyle>
        <color>aabbggrr</color>  <!-- KML color format -->
        <Icon><href>icon_url</href></Icon>
      </IconStyle>
      <LabelStyle>...</LabelStyle>
    </Style>
    
    <!-- Placemarks -->
    <Folder>
      <Placemark>
        <name>...</name>
        <description>...</description>
        <styleUrl>#status_id</styleUrl>
        <Point>
          <coordinates>lon,lat,0</coordinates>
        </Point>
      </Placemark>
      <!-- More placemarks... -->
    </Folder>
  </Document>
</kml>
```

**Color Format:**
- KML uses `aabbggrr` (alpha, blue, green, red)
- Example: `ff0000ff` = opaque red
- Alpha: `ff` = opaque, `00` = transparent

**Coordinate Format:**
- KML: `longitude,latitude,altitude`
- Airtable: `latitude, longitude` (text)
- Conversion: Parse string, swap order, add altitude 0

### 4. NetworkLink Mechanism

**Two-KML Architecture:**

**Root KML** (`/kml`):
- Contains NetworkLink configuration
- Loaded once by user
- Points to data endpoint
- Configures refresh behavior

**Data KML** (`/kml/data`):
- Contains actual placemarks
- Fetched automatically by Google Earth
- Regenerated on each request
- Fresh data from Airtable

**Why This Design?**
- Allows server-side updates without user action
- Google Earth handles refresh timing
- User doesn't need to manually reload
- Standard pattern for dynamic KML

---

## Data Flow Diagrams

### Initial Load

```
User Action: Add NetworkLink
         ↓
    GET /kml
         ↓
    Return Root KML
    (contains NetworkLink to /kml/data)
         ↓
Google Earth parses NetworkLink
         ↓
    GET /kml/data
         ↓
    fetch_airtable_records()
         ↓
    Airtable API call
         ↓
    Parse & validate records
         ↓
    Generate KML with placemarks
         ↓
    Return Data KML
         ↓
Google Earth displays placemarks
```

### Automatic Refresh (Every 30 Minutes)

```
Timer expires (30 min)
         ↓
Google Earth: GET /kml/data
         ↓
    fetch_airtable_records()
         ↓
    Airtable API call
         ↓
    Generate fresh KML
         ↓
    Return Data KML
         ↓
Google Earth updates display
```

### Webhook Trigger (Optional)

```
Airtable Automation
         ↓
    POST /webhook/refresh
         ↓
    fetch_airtable_records()
         ↓
    Airtable API call
         ↓
    Return JSON status
         ↓
(Google Earth still refreshes on schedule)
```

**Note:** Webhook doesn't push to Google Earth, only validates data is fresh. Google Earth still polls on schedule.

---

## Deployment Architectures

### Vercel (Serverless)

```
┌─────────────────────────────────────┐
│         Vercel Edge Network         │
│                                     │
│  Global CDN                         │
│  Automatic HTTPS                    │
│  Environment Variables              │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      Serverless Function            │
│                                     │
│  • Python runtime                   │
│  • Stateless execution              │
│  • Auto-scaling                     │
│  • Sub-second cold start            │
└─────────────────────────────────────┘
```

**Pros:**
- Zero configuration
- No cold starts (effectively)
- Automatic HTTPS
- Free tier sufficient

**Cons:**
- 10-second execution limit (not an issue for this app)

### AWS Lambda + API Gateway

```
┌─────────────────────────────────────┐
│         API Gateway                 │
│                                     │
│  • REST API endpoint                │
│  • Request routing                  │
│  • Throttling                       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│         AWS Lambda                  │
│                                     │
│  • Python 3.11 runtime              │
│  • Environment variables            │
│  • CloudWatch logs                  │
│  • Warm/cold starts                 │
└─────────────────────────────────────┘
```

**Pros:**
- Full AWS ecosystem integration
- Detailed monitoring (CloudWatch)
- IAM security

**Cons:**
- More complex setup
- Cold starts (1-2 second delay)

### Google Cloud Run

```
┌─────────────────────────────────────┐
│      Cloud Load Balancer            │
│                                     │
│  • HTTPS termination                │
│  • Global distribution              │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│       Cloud Run Service             │
│                                     │
│  • Container execution              │
│  • Auto-scaling 0-N                 │
│  • Request-based billing            │
└─────────────────────────────────────┘
```

**Pros:**
- Container-based (flexible)
- Scales to zero
- Good integration with GCP

**Cons:**
- Requires Docker knowledge
- Cold starts possible

---

## Security Architecture

### Authentication Flow

**Current (No Auth):**
```
Client → HTTPS → Server → Airtable
```

**With API Key (Optional):**
```
Client + API Key → HTTPS → Server validates key → Airtable
```

**With IP Whitelist (Optional):**
```
Client from allowed IP → HTTPS → Server checks IP → Airtable
```

### Data Security

**In Transit:**
- Client ↔ Server: HTTPS (TLS 1.3)
- Server ↔ Airtable: HTTPS + Bearer Token

**At Rest:**
- No data stored on server (stateless)
- Credentials in environment variables (encrypted by platform)

**Airtable Token:**
- Scoped to specific base
- Read-only permissions (recommended)
- Stored as environment variable
- Never in code or logs

---

## Performance Characteristics

### Response Times

| Endpoint | Typical Response Time | Notes |
|----------|----------------------|-------|
| `/` | 10-50ms | Static HTML |
| `/kml` | 10-50ms | Small static KML |
| `/kml/data` | 200-800ms | Depends on Airtable |
| `/health` | 200-800ms | Tests Airtable connection |

**Airtable API latency:**
- Average: 200-400ms
- With pagination: +200ms per 100 records
- This is acceptable for 30-minute refresh cycle

### Scalability

**Current Load:**
- Users: ~10-20 team members
- Requests: ~2/hour (from Google Earth auto-refresh)
- Data: <100 records

**Can Scale To:**
- Users: 1000s (all platforms auto-scale)
- Requests: 1000s/hour (limited by Airtable rate limits)
- Data: 1000s of records (pagination handles this)

**Bottleneck:**
- Airtable API rate limits (5 req/sec free tier)
- Not an issue for this use case

### Caching Considerations

**Current Design: No Caching**
- Ensures data freshness
- Simple architecture
- Acceptable performance for 30-min refresh

**Could Add Caching:**
- Server-side: Cache Airtable response for 5 minutes
- Would reduce Airtable API calls
- Trade-off: Slightly stale data

**Not Recommended Because:**
- 30-minute refresh means fresh data not critical
- Adds complexity
- Current performance is acceptable

---

## Error Handling

### Error Flow

```python
try:
    records = fetch_airtable_records()
    kml = generate_kml_document(records)
    return Response(kml, mimetype='application/vnd.google-earth.kml+xml')
except Exception as e:
    # Log error server-side
    logger.error(f"Error: {e}")
    
    # Return error KML (won't break Google Earth)
    error_kml = generate_error_kml(str(e))
    return Response(error_kml, status=500)
```

**Error KML:**
- Valid KML structure (won't crash Google Earth)
- Contains error message in description
- Empty placemarks list

**Benefits:**
- Google Earth continues to function
- User sees error message in placemark
- Doesn't break NetworkLink

---

## Monitoring & Observability

### Health Check Endpoint

```json
GET /health

Response (healthy):
{
  "status": "healthy",
  "airtable_connection": "ok",
  "records_count": 25,
  "timestamp": "2026-02-05T12:00:00"
}

Response (unhealthy):
{
  "status": "unhealthy",
  "error": "Airtable API error: ...",
  "timestamp": "2026-02-05T12:00:00"
}
```

### Logging

**Structured Logging:**
- Request: Method, path, status code, response time
- Errors: Full traceback, context
- Airtable: Request count, response time

**Platform Integration:**
- Vercel: Built-in logging
- AWS: CloudWatch Logs
- GCP: Cloud Logging

### Metrics to Monitor

| Metric | Normal Range | Alert Threshold |
|--------|--------------|-----------------|
| Response time | 200-800ms | >2000ms |
| Error rate | <1% | >5% |
| Airtable errors | 0 | >0 |
| Request count | 2-50/hour | >1000/hour |

---

## Development Workflow

### Local Development

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with credentials

# Test
python test_local.py

# Run
python app.py

# Access
http://localhost:5000
```

### Testing Strategy

**Unit Tests:** (in `test_local.py`)
- Environment variable validation
- Coordinate parsing
- Airtable connection
- KML generation

**Integration Testing:**
- Load in Google Earth Pro
- Verify placemarks appear
- Test auto-refresh
- Verify colors match statuses

**Production Validation:**
- Health check returns 200
- KML is valid XML
- Placemarks match Airtable records

---

## Future Architecture Considerations

### Enhancements Not Implemented (But Possible)

1. **Caching Layer:**
   - Redis/Memcached for Airtable responses
   - Reduces API calls
   - Trade-off: Added complexity

2. **Database Layer:**
   - Store historical status changes
   - Enable trend analysis
   - Trade-off: Data storage costs

3. **Push Updates:**
   - WebSocket to Google Earth Web
   - Real-time updates
   - Trade-off: Google Earth Pro doesn't support WebSockets

4. **Multi-Tenant:**
   - Support multiple Airtable bases
   - User-specific views
   - Trade-off: Authentication complexity

5. **Analytics:**
   - Track placemark views
   - User engagement metrics
   - Trade-off: Privacy concerns

---

## Technical Decisions & Rationale

### Why Flask?
- ✅ Lightweight (perfect for simple API)
- ✅ Easy to deploy serverless
- ✅ Excellent for XML generation
- ✅ Minimal dependencies

**Alternatives considered:**
- FastAPI: Overkill for this use case
- Django: Too heavy
- Express.js: Requires Node.js

### Why Python?
- ✅ Excellent XML handling
- ✅ Simple Airtable API integration
- ✅ Easy to maintain
- ✅ Client's preference

### Why NetworkLink vs Static KML?
- ✅ Automatic updates (no user action)
- ✅ Always shows fresh data
- ✅ Standard Google Earth pattern
- ❌ Slightly more complex setup

### Why No Database?
- ✅ Simpler architecture
- ✅ Airtable is source of truth
- ✅ No data sync issues
- ✅ Lower maintenance

### Why No Caching?
- ✅ Always fresh data
- ✅ Simpler code
- ✅ Performance is acceptable
- ✅ 30-min refresh doesn't need caching

---

## Conclusion

The architecture is designed for:
- **Simplicity**: Easy to understand and maintain
- **Reliability**: Fail-safe error handling
- **Security**: Token protection, HTTPS
- **Scalability**: Can handle 100x current load
- **Flexibility**: Easy to deploy anywhere

All design decisions prioritize maintainability and reliability over premature optimization.

---

**Last Updated:** February 5, 2026
