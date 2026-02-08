"""
Google Earth KML Generator with Airtable Integration
Generates dynamic KML with NetworkLink support for automatic updates
"""

from flask import Flask, Response, request
from functools import wraps
import requests
import os
from datetime import datetime
from xml.sax.saxutils import escape
import base64
import zipfile
import io
from xml.etree import ElementTree as ET

# Load environment variables from .env file if present (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed (production environments use platform env vars)
    pass

app = Flask(__name__)

# Authentication Configuration
AUTH_USERNAME = os.environ.get('AUTH_USERNAME', 'admin')
AUTH_PASSWORD = os.environ.get('AUTH_PASSWORD', '')

# Airtable Configuration
AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID', 'appZOdJaRPiwcygdR')
AIRTABLE_TABLE_NAME = os.environ.get('AIRTABLE_TABLE_NAME', 'Table 1')
AIRTABLE_TOKEN = os.environ.get('AIRTABLE_TOKEN', '')
REFRESH_INTERVAL_MINUTES = int(os.environ.get('REFRESH_INTERVAL_MINUTES', '30'))

# Airtable API endpoint
AIRTABLE_API_URL = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}'


def check_auth(username, password):
    """
    Check if username/password combination is valid
    """
    return username == AUTH_USERNAME and password == AUTH_PASSWORD


def authenticate():
    """
    Send 401 response to request authentication
    """
    return Response(
        'Authentication required. Please provide valid credentials.',
        401,
        {'WWW-Authenticate': 'Basic realm="Secure Area"'}
    )


def requires_auth(f):
    """
    Decorator to require HTTP Basic Authentication for routes
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Skip authentication if AUTH_PASSWORD is not set (development mode)
        if not AUTH_PASSWORD:
            return f(*args, **kwargs)
        
        auth = request.authorization
        
        # If no authorization header or invalid credentials
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        
        return f(*args, **kwargs)
    return decorated

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

# Property boundary style (yellow outline with transparent fill)
PROPERTY_BOUNDARY_STYLE = {
    'line_color': 'ff00ffff',  # Yellow (aabbggrr format)
    'line_width': 3,
    'fill_color': '3300ffff',  # 20% transparent yellow (20% = 0x33)
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


def fetch_kml_from_url(url):
    """
    Download and parse KML/KMZ file from URL
    Returns parsed KML content or None if error
    """
    try:
        print(f"Fetching KML from: {url[:80]}...")
        response = requests.get(url, timeout=5)  # Reduced timeout to 5 seconds
        response.raise_for_status()
        print(f"  ✓ Downloaded: {len(response.content)} bytes")
        
        # Check if it's a KMZ (zipped KML)
        if url.lower().endswith('.kmz') or response.headers.get('content-type') == 'application/vnd.google-earth.kmz':
            # Extract KML from KMZ
            with zipfile.ZipFile(io.BytesIO(response.content)) as kmz:
                # Find the main KML file (usually doc.kml or first .kml file)
                kml_files = [f for f in kmz.namelist() if f.lower().endswith('.kml')]
                if not kml_files:
                    return None
                
                # Read the first KML file
                kml_content = kmz.read(kml_files[0])
                print(f"  ✓ Extracted KML from KMZ")
        else:
            # It's a plain KML file
            kml_content = response.content
        
        print(f"  ✓ KML parsing complete")
        return kml_content
    except Exception as e:
        print(f"  ✗ Error fetching KML: {e}")
        return None


def extract_polygons_from_kml(kml_content):
    """
    Extract polygon coordinates from KML content
    Returns list of polygon coordinate strings suitable for KML output
    """
    if not kml_content:
        return []
    
    try:
        # Parse KML XML
        root = ET.fromstring(kml_content)
        
        # KML uses a namespace
        namespaces = {
            'kml': 'http://www.opengis.net/kml/2.2',
            'gx': 'http://www.google.com/kml/ext/2.2'
        }
        
        polygons = []
        
        # Find all Polygon elements (with and without namespace)
        for polygon in root.iter('{http://www.opengis.net/kml/2.2}Polygon'):
            # Extract coordinates from outerBoundaryIs
            coords_elem = polygon.find('.//{http://www.opengis.net/kml/2.2}outerBoundaryIs//{http://www.opengis.net/kml/2.2}coordinates')
            if coords_elem is not None and coords_elem.text:
                polygons.append({
                    'type': 'polygon',
                    'coordinates': coords_elem.text.strip()
                })
        
        # Also check for polygons without namespace (some KML files don't use it)
        for polygon in root.iter('Polygon'):
            coords_elem = polygon.find('.//outerBoundaryIs//coordinates')
            if coords_elem is not None and coords_elem.text:
                coord_text = coords_elem.text.strip()
                # Avoid duplicates
                if not any(p['coordinates'] == coord_text for p in polygons):
                    polygons.append({
                        'type': 'polygon',
                        'coordinates': coord_text
                    })
        
        # Also extract LineStrings (for property lines drawn as lines, not polygons)
        for linestring in root.iter('{http://www.opengis.net/kml/2.2}LineString'):
            coords_elem = linestring.find('.//{http://www.opengis.net/kml/2.2}coordinates')
            if coords_elem is not None and coords_elem.text:
                polygons.append({
                    'type': 'linestring',
                    'coordinates': coords_elem.text.strip()
                })
        
        for linestring in root.iter('LineString'):
            coords_elem = linestring.find('.//coordinates')
            if coords_elem is not None and coords_elem.text:
                coord_text = coords_elem.text.strip()
                if not any(p['coordinates'] == coord_text for p in polygons):
                    polygons.append({
                        'type': 'linestring',
                        'coordinates': coord_text
                    })
        
        return polygons
    except Exception as e:
        print(f"Error parsing KML: {e}")
        return []


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
    
    # Add property boundary style
    boundary_style_xml = f'''
    <Style id="property_boundary">
        <LineStyle>
            <color>{PROPERTY_BOUNDARY_STYLE['line_color']}</color>
            <width>{PROPERTY_BOUNDARY_STYLE['line_width']}</width>
        </LineStyle>
        <PolyStyle>
            <color>{PROPERTY_BOUNDARY_STYLE['fill_color']}</color>
            <fill>1</fill>
            <outline>1</outline>
        </PolyStyle>
    </Style>'''
    styles_xml.append(boundary_style_xml)
    
    return '\n'.join(styles_xml)


def generate_placemark(record):
    """
    Generate KML Placemark(s) from Airtable record
    Returns a folder containing the point marker and property boundary (if available)
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
    
    # Add link to Airtable record
    airtable_record_url = f"https://airtable.com/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}/{record_id}"
    description_parts.append(f"<br/><a href='{airtable_record_url}' target='_blank'>📋 View in Airtable</a><br/><br/>")
    
    # Add other fields to description (excluding Google Earth KMZ/KML from display)
    excluded_fields = ['Latitude and Longitude', 'Zoning Status', 'Name', 'Project Name', 'Site Name', 'Address', 'Google Earth KMZ/KML']
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
    
    # Start building the folder
    placemarks = []
    
    # Add the point marker
    point_placemark = f'''
        <Placemark>
            <name>{name_escaped}</name>
            <description><![CDATA[{description}]]></description>
            <styleUrl>#{style_id}</styleUrl>
            <Point>
                <coordinates>{lon},{lat},0</coordinates>
            </Point>
        </Placemark>'''
    placemarks.append(point_placemark)
    
    # Try to get property boundary from Google Earth KMZ/KML field
    google_earth_file = fields.get('Google Earth KMZ/KML', [])
    if google_earth_file and isinstance(google_earth_file, list) and len(google_earth_file) > 0:
        # Airtable attachments are stored as a list of objects with 'url' field
        file_url = google_earth_file[0].get('url', '')
        
        print(f"\nProcessing property boundary for: {name}")
        
        if file_url:
            # Fetch and parse the KML file
            kml_content = fetch_kml_from_url(file_url)
            if kml_content:
                polygons = extract_polygons_from_kml(kml_content)
                
                # Add each polygon as a placemark
                for idx, polygon_data in enumerate(polygons):
                    polygon_name = f"Property Line - {name}"
                    if len(polygons) > 1:
                        polygon_name += f" ({idx + 1})"
                    
                    if polygon_data['type'] == 'polygon':
                        polygon_placemark = f'''
        <Placemark>
            <name>{escape(polygon_name)}</name>
            <description><![CDATA[{description}]]></description>
            <styleUrl>#property_boundary</styleUrl>
            <Polygon>
                <outerBoundaryIs>
                    <LinearRing>
                        <coordinates>{polygon_data['coordinates']}</coordinates>
                    </LinearRing>
                </outerBoundaryIs>
            </Polygon>
        </Placemark>'''
                        placemarks.append(polygon_placemark)
                    elif polygon_data['type'] == 'linestring':
                        line_placemark = f'''
        <Placemark>
            <name>{escape(polygon_name)}</name>
            <description><![CDATA[{description}]]></description>
            <styleUrl>#property_boundary</styleUrl>
            <LineString>
                <coordinates>{polygon_data['coordinates']}</coordinates>
            </LineString>
        </Placemark>'''
                        placemarks.append(line_placemark)
    
    # Wrap in a folder if there are multiple placemarks
    if len(placemarks) > 1:
        folder_xml = f'''
    <Folder>
        <name>{name_escaped}</name>
        <description>Project with property boundary</description>
        {''.join(placemarks)}
    </Folder>'''
        return folder_xml
    else:
        return placemarks[0]


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
            <name>Zoning Projects with Property Lines</name>
            <description>All active zoning projects with current status and property boundaries</description>
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
        <name>Live Zoning Projects with Property Lines</name>
        <description>
            This map automatically updates every {REFRESH_INTERVAL_MINUTES} minutes with the latest data from Airtable.
            
            Features:
            • Color-coded project status markers
            • Property boundary outlines (when available)
            • Clickable links to Airtable records
            
            Color coding:
            🔴 Red = Zoning submittals not made
            🟡 Yellow = Zoning Submittal Made
            🔵 Light Blue = Zoning Board Meeting Scheduled
            🟢 Green = Zoning Complete - Letter Received
            ⭐ Red Star = Zoning Denied
            ⭐ Green Star = Preliminary Site Plan Created
            
            Property boundaries shown in yellow when Google Earth KMZ/KML file is available in Airtable.
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
@requires_auth
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
            .feature {{
                background: #e3f2fd;
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
        <h1>Google Earth KML Service with Property Lines</h1>
        
        <div class="status">
            <strong>Service Status:</strong> ✓ Online<br>
            <strong>Refresh Interval:</strong> {REFRESH_INTERVAL_MINUTES} minutes<br>
            <strong>Last Check:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
        </div>
        
        <div class="feature">
            <strong>✨ New Features:</strong><br>
            • Color-coded project status markers<br>
            • Property boundary visualization (from Google Earth Files)<br>
            • Direct links to Airtable records<br>
            • Automatic updates every {REFRESH_INTERVAL_MINUTES} minutes<br>
            • Password protected access
        </div>
        
        <h2>Available Endpoints</h2>
        
        <div class="endpoint">
            <strong>Main NetworkLink KML:</strong><br>
            <code>{request.url_root}kml</code><br>
            <small>Load this URL in Google Earth Pro for auto-updating map with property boundaries</small>
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
            <li>Enter your username and password when prompted</li>
            <li>Click OK</li>
            <li>The map will update automatically every {REFRESH_INTERVAL_MINUTES} minutes</li>
        </ol>
        
        <h2>What You'll See</h2>
        <ul>
            <li><strong>Project Markers:</strong> Color-coded points showing project status</li>
            <li><strong>Property Boundaries:</strong> Yellow outlines showing property lines (when Google Earth File is available)</li>
            <li><strong>Interactive Popups:</strong> Click any marker or boundary to see project details and link to Airtable</li>
        </ul>
        
        <h2>Status Legend</h2>
        <ul>
            <li>🔴 <strong>Red Circle:</strong> Zoning submittals not made</li>
            <li>🟡 <strong>Yellow Circle:</strong> Zoning Submittal Made</li>
            <li>🔵 <strong>Light Blue Circle:</strong> Zoning Board Meeting Scheduled</li>
            <li>🟢 <strong>Green Circle:</strong> Zoning Complete - Letter Received</li>
            <li>⭐ <strong>Red Star:</strong> Zoning Denied</li>
            <li>⭐ <strong>Green Star:</strong> Preliminary Site Plan Created</li>
        </ul>
        
        <h2>Property Boundaries</h2>
        <p>
            Property boundaries are automatically extracted from the "Google Earth KMZ/KML" field in Airtable.
            They appear as <strong>yellow outlines</strong> with semi-transparent fill around each project marker.
        </p>
        <ul>
            <li>Supports KML and KMZ file formats</li>
            <li>Handles polygons and line strings</li>
            <li>Projects without a Google Earth KMZ/KML file will show marker only</li>
            <li>Click boundary or marker to see the same project details</li>
        </ul>
    </body>
    </html>
    '''
    return status_html


@app.route('/kml')
@requires_auth
def network_link_kml():
    """
    Root KML with NetworkLink - this is what users load into Google Earth
    """
    base_url = request.url_root.rstrip('/')
    kml = generate_network_link_kml(base_url)
    
    return Response(kml, mimetype='application/vnd.google-earth.kml+xml')


@app.route('/kml/data')
@requires_auth
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
@requires_auth
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
@requires_auth
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
