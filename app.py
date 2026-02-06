"""
Google Earth KML Generator with Airtable Integration
Generates dynamic KML with NetworkLink support for automatic updates
"""

from flask import Flask, Response, request
import requests
import os
from datetime import datetime
from xml.sax.saxutils import escape

# Load environment variables from .env file if present (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed (production environments use platform env vars)
    pass

app = Flask(__name__)

# Airtable Configuration
AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID', 'appZOdJaRPiwcygdR')
AIRTABLE_TABLE_NAME = os.environ.get('AIRTABLE_TABLE_NAME', 'Table 1')
AIRTABLE_TOKEN = os.environ.get('AIRTABLE_TOKEN', '')
REFRESH_INTERVAL_MINUTES = int(os.environ.get('REFRESH_INTERVAL_MINUTES', '30'))

# Airtable API endpoint
AIRTABLE_API_URL = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}'

# Status to color mapping (Google Earth KML color format: aabbggrr)
# Colors chosen for high visibility and standard status indicators
STATUS_STYLES = {
    'Zoning submittals not made': {
        'color': 'ff0000ff',  # Red
        'icon': 'http://maps.google.com/mapfiles/kml/paddle/red-circle.png',
        'description': 'Not Started'
    },
    'Zoning Submittal Made': {
        'color': 'ff00ffff',  # Yellow
        'icon': 'http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png',
        'description': 'Submittal Made'
    },
    'Zoning Board Meeting Scheduled': {
        'color': 'ffff8800',  # Light Blue
        'icon': 'http://maps.google.com/mapfiles/kml/paddle/ltblu-circle.png',
        'description': 'Meeting Scheduled'
    },
    'Zoning Complete - Letter Received': {
        'color': 'ff00ff00',  # Green
        'icon': 'http://maps.google.com/mapfiles/kml/paddle/grn-circle.png',
        'description': 'Complete'
    },
    'Zoning Denied': {
        'color': 'ff000088',  # Dark Red
        'icon': 'http://maps.google.com/mapfiles/kml/paddle/red-stars.png',
        'description': 'Denied'
    },
    'Preliminary Site Plan Created': {
        'color': 'ff00ff00',  # Green
        'icon': 'http://maps.google.com/mapfiles/kml/paddle/grn-stars.png',
        'description': 'Site Plan Created'
    }
}

# Default style for unknown statuses
DEFAULT_STYLE = {
    'color': 'ffffffff',  # White
    'icon': 'http://maps.google.com/mapfiles/kml/paddle/wht-blank.png',
    'description': 'Unknown Status'
}


def fetch_airtable_records():
    """
    Fetch all records from Airtable table
    Returns list of records or raises exception on error
    """
    if not AIRTABLE_TOKEN:
        raise ValueError("AIRTABLE_TOKEN environment variable not set")
    
    headers = {
        'Authorization': f'Bearer {AIRTABLE_TOKEN}',
    }
    
    all_records = []
    offset = None
    
    # Handle pagination
    while True:
        params = {}
        if offset:
            params['offset'] = offset
            
        response = requests.get(AIRTABLE_API_URL, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        all_records.extend(data.get('records', []))
        
        offset = data.get('offset')
        if not offset:
            break
    
    return all_records


def parse_coordinates(coord_string):
    """
    Parse coordinate string in format "lat, long"
    Returns tuple (latitude, longitude) or None if invalid
    """
    if not coord_string:
        return None
    
    try:
        parts = coord_string.split(',')
        if len(parts) != 2:
            return None
        
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        
        # Validate ranges
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return (lat, lon)
        return None
    except (ValueError, AttributeError):
        return None


def get_style_for_status(status):
    """
    Get KML style configuration for a given status
    """
    return STATUS_STYLES.get(status, DEFAULT_STYLE)


def generate_kml_styles():
    """
    Generate KML Style definitions for all status types
    """
    styles_xml = []
    
    for status, style_config in STATUS_STYLES.items():
        # Create a safe style ID (remove spaces and special chars)
        style_id = status.replace(' ', '_').replace('-', '_').replace(',', '')
        
        style_xml = f'''
    <Style id="{style_id}">
        <IconStyle>
            <color>{style_config['color']}</color>
            <scale>1.1</scale>
            <Icon>
                <href>{style_config['icon']}</href>
            </Icon>
        </IconStyle>
        <LabelStyle>
            <color>{style_config['color']}</color>
            <scale>0.9</scale>
        </LabelStyle>
        <BalloonStyle>
            <text><![CDATA[
                <h3>$[name]</h3>
                <p><b>Status:</b> $[description]</p>
                <p><b>Coordinates:</b> {style_config['description']}</p>
            ]]></text>
        </BalloonStyle>
    </Style>'''
        styles_xml.append(style_xml)
    
    # Add default style
    default_style_xml = f'''
    <Style id="default">
        <IconStyle>
            <color>{DEFAULT_STYLE['color']}</color>
            <scale>1.1</scale>
            <Icon>
                <href>{DEFAULT_STYLE['icon']}</href>
            </Icon>
        </IconStyle>
        <LabelStyle>
            <scale>0.9</scale>
        </LabelStyle>
    </Style>'''
    styles_xml.append(default_style_xml)
    
    return '\n'.join(styles_xml)


def generate_placemark(record):
    """
    Generate KML Placemark from Airtable record
    """
    fields = record.get('fields', {})
    record_id = record.get('id', 'unknown')
    
    # Get coordinates
    coord_string = fields.get('Latitude and Longitude', '')
    coords = parse_coordinates(coord_string)
    
    if not coords:
        # Skip records without valid coordinates
        return None
    
    lat, lon = coords
    
    # Get status and styling (handle list or string)
    status_raw = fields.get('Zoning Status', '')
    # If status is a list (multi-select field), take the first item or join them
    if isinstance(status_raw, list):
        status = status_raw[0] if status_raw else ''
    else:
        status = status_raw if status_raw else ''
    
    style_config = get_style_for_status(status)
    style_id = status.replace(' ', '_').replace('-', '_').replace(',', '') if status in STATUS_STYLES else 'default'
    
    # Create a name for the placemark (use Site Name or record ID)
    # Try multiple field names that might contain the site/project name
    name_raw = fields.get('Site Name', fields.get('Name', fields.get('Project Name', fields.get('Address', f'Record {record_id[:8]}'))))
    # Handle if name is a list
    if isinstance(name_raw, list):
        name = name_raw[0] if name_raw else f'Record {record_id[:8]}'
    else:
        name = name_raw if name_raw else f'Record {record_id[:8]}'
    name_escaped = escape(str(name))
    
    # Build description with all relevant fields
    status_display = escape(str(status)) if status else 'No status'
    description_parts = [f"<b>Zoning Status:</b> {status_display}<br/>"]
    description_parts.append(f"<b>Coordinates:</b> {lat}, {lon}<br/>")
    
    # Add other fields to description
    excluded_fields = ['Latitude and Longitude', 'Zoning Status', 'Name', 'Project Name', 'Site Name', 'Address']
    for field_name, field_value in fields.items():
        if field_name not in excluded_fields and field_value:
            # Handle lists and other complex types
            if isinstance(field_value, list):
                # For lists, join with commas or show first few items
                if all(isinstance(v, (str, int, float)) for v in field_value):
                    field_value_str = ', '.join(str(v) for v in field_value[:5])
                    if len(field_value) > 5:
                        field_value_str += f' ... (+{len(field_value) - 5} more)'
                else:
                    field_value_str = f'{len(field_value)} items'
            elif isinstance(field_value, dict):
                # For dictionaries, show keys or first few entries
                field_value_str = f'{len(field_value)} entries'
            else:
                field_value_str = str(field_value)
            
            # Truncate very long values
            if len(field_value_str) > 200:
                field_value_str = field_value_str[:200] + '...'
            
            description_parts.append(f"<b>{escape(field_name)}:</b> {escape(field_value_str)}<br/>")
    
    description = ''.join(description_parts)
    
    placemark_xml = f'''
    <Placemark>
        <name>{name_escaped}</name>
        <description><![CDATA[{description}]]></description>
        <styleUrl>#{style_id}</styleUrl>
        <Point>
            <coordinates>{lon},{lat},0</coordinates>
        </Point>
    </Placemark>'''
    
    return placemark_xml


def generate_kml_document(records, base_url):
    """
    Generate complete KML document with NetworkLink support
    """
    placemarks = []
    valid_count = 0
    invalid_count = 0
    
    for record in records:
        placemark = generate_placemark(record)
        if placemark:
            placemarks.append(placemark)
            valid_count += 1
        else:
            invalid_count += 1
    
    placemarks_xml = '\n'.join(placemarks)
    styles_xml = generate_kml_styles()
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    kml = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>Zoning Projects Map</name>
        <description>
            Live zoning project status map. Updates automatically every {REFRESH_INTERVAL_MINUTES} minutes.
            Last updated: {timestamp}
            Active projects: {valid_count}
        </description>
        
        {styles_xml}
        
        <Folder>
            <name>Zoning Projects</name>
            <description>All active zoning projects with current status</description>
            {placemarks_xml}
        </Folder>
    </Document>
</kml>'''
    
    return kml


def generate_network_link_kml(base_url):
    """
    Generate root KML with NetworkLink for auto-refresh
    This is the file users load into Google Earth Pro
    """
    kml = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>Live Zoning Projects</name>
        <description>
            This map automatically updates every {REFRESH_INTERVAL_MINUTES} minutes with the latest data from Airtable.
            Color coding:
            🔴 Red = Zoning submittals not made
            🟡 Yellow = Zoning Submittal Made
            🔵 Light Blue = Zoning Board Meeting Scheduled
            🟢 Green = Zoning Complete - Letter Received
            ⭐ Red Star = Zoning Denied
            ⭐ Green Star = Preliminary Site Plan Created
        </description>
        
        <NetworkLink>
            <name>Auto-Updating Zoning Data</name>
            <description>Data refreshes every {REFRESH_INTERVAL_MINUTES} minutes</description>
            <refreshVisibility>0</refreshVisibility>
            <flyToView>0</flyToView>
            <Link>
                <href>{base_url}/kml/data</href>
                <refreshMode>onInterval</refreshMode>
                <refreshInterval>{REFRESH_INTERVAL_MINUTES * 60}</refreshInterval>
                <viewRefreshMode>never</viewRefreshMode>
            </Link>
        </NetworkLink>
    </Document>
</kml>'''
    
    return kml


@app.route('/')
def index():
    """
    Simple status page
    """
    status_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Google Earth KML Service</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                line-height: 1.6;
            }}
            h1 {{
                color: #333;
            }}
            .endpoint {{
                background: #f4f4f4;
                padding: 10px;
                margin: 10px 0;
                border-left: 4px solid #4CAF50;
            }}
            .status {{
                background: #e8f5e9;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            code {{
                background: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
            }}
        </style>
    </head>
    <body>
        <h1>Google Earth KML Service</h1>
        
        <div class="status">
            <strong>Service Status:</strong> ✓ Online<br>
            <strong>Refresh Interval:</strong> {REFRESH_INTERVAL_MINUTES} minutes<br>
            <strong>Last Check:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
        </div>
        
        <h2>Available Endpoints</h2>
        
        <div class="endpoint">
            <strong>Main NetworkLink KML:</strong><br>
            <code>{request.url_root}kml</code><br>
            <small>Load this URL in Google Earth Pro for auto-updating map</small>
        </div>
        
        <div class="endpoint">
            <strong>Data KML:</strong><br>
            <code>{request.url_root}kml/data</code><br>
            <small>Direct data endpoint (refreshed automatically via NetworkLink)</small>
        </div>
        
        <div class="endpoint">
            <strong>Webhook Trigger:</strong><br>
            <code>POST {request.url_root}webhook/refresh</code><br>
            <small>Manual refresh trigger (optional)</small>
        </div>
        
        <h2>Usage Instructions</h2>
        <ol>
            <li>Open Google Earth Pro (desktop application)</li>
            <li>Go to File → Open → Network Link</li>
            <li>Paste the Main NetworkLink KML URL above</li>
            <li>Click OK</li>
            <li>The map will update automatically every {REFRESH_INTERVAL_MINUTES} minutes</li>
        </ol>
        
        <h2>Status Legend</h2>
        <ul>
            <li>🔴 <strong>Red Circle:</strong> Zoning submittals not made</li>
            <li>🟡 <strong>Yellow Circle:</strong> Zoning Submittal Made</li>
            <li>🔵 <strong>Light Blue Circle:</strong> Zoning Board Meeting Scheduled</li>
            <li>🟢 <strong>Green Circle:</strong> Zoning Complete - Letter Received</li>
            <li>⭐ <strong>Red Star:</strong> Zoning Denied</li>
            <li>⭐ <strong>Green Star:</strong> Preliminary Site Plan Created</li>
        </ul>
    </body>
    </html>
    '''
    return status_html


@app.route('/kml')
def network_link_kml():
    """
    Root KML with NetworkLink - this is what users load into Google Earth
    """
    base_url = request.url_root.rstrip('/')
    kml = generate_network_link_kml(base_url)
    
    return Response(kml, mimetype='application/vnd.google-earth.kml+xml')


@app.route('/kml/data')
def data_kml():
    """
    Dynamic KML data endpoint - fetched automatically by NetworkLink
    """
    try:
        # Fetch records from Airtable
        records = fetch_airtable_records()

        # Generate KML
        base_url = request.url_root.rstrip('/')
        kml = generate_kml_document(records, base_url)
        
        return Response(kml, mimetype='application/vnd.google-earth.kml+xml')
    
    except Exception as e:
        # Return error KML
        error_kml = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>Error</name>
        <description>Error fetching data: {escape(str(e))}</description>
    </Document>
</kml>'''
        return Response(error_kml, mimetype='application/vnd.google-earth.kml+xml', status=500)


@app.route('/webhook/refresh', methods=['POST'])
def webhook_refresh():
    """
    Optional webhook endpoint for triggering immediate refresh
    Can be called from Airtable automations or external systems
    """
    try:
        records = fetch_airtable_records()
        return {
            'status': 'success',
            'records_fetched': len(records),
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }, 500


@app.route('/health')
def health_check():
    """
    Health check endpoint for monitoring
    """
    try:
        # Test Airtable connection
        records = fetch_airtable_records()
        
        return {
            'status': 'healthy',
            'airtable_connection': 'ok',
            'records_count': len(records),
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }, 500


if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
