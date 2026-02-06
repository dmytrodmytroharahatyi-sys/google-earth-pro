"""
Direct Airtable API Test
Tests the Airtable connection with detailed debugging information
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID', '')
AIRTABLE_TABLE_NAME = os.environ.get('AIRTABLE_TABLE_NAME', '')
AIRTABLE_TOKEN = os.environ.get('AIRTABLE_TOKEN', '')

print("=" * 70)
print("Airtable API Connection Diagnostics")
print("=" * 70)
print()

print("Configuration:")
print(f"  Base ID: {AIRTABLE_BASE_ID}")
print(f"  Table Name: {AIRTABLE_TABLE_NAME}")
print(f"  Token (first 15 chars): {AIRTABLE_TOKEN[:15]}...")
print(f"  Token length: {len(AIRTABLE_TOKEN)} characters")
print()

# Construct URL
url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}'
print(f"Request URL: {url}")
print()

# Prepare headers
headers = {
    'Authorization': f'Bearer {AIRTABLE_TOKEN}',
    'Content-Type': 'application/json'
}

print("Making request to Airtable...")
print()

try:
    # Make request
    response = requests.get(url, headers=headers)
    
    print(f"Response Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        print("✅ SUCCESS! Connection successful.")
        data = response.json()
        records = data.get('records', [])
        print(f"✅ Fetched {len(records)} records")
        
        if records:
            print()
            print("Sample record fields:")
            sample_fields = records[0].get('fields', {})
            for field_name in sorted(sample_fields.keys()):
                print(f"  • {field_name}")
        
    elif response.status_code == 401:
        print("❌ ERROR 401: Unauthorized")
        print()
        print("This means the token is invalid or has been revoked.")
        print()
        print("Solutions:")
        print("1. Check if the token has expired or been revoked")
        print("2. Go to: https://airtable.com/account/tokens")
        print("3. Verify your token is still active")
        print("4. If revoked, generate a new scoped token")
        
    elif response.status_code == 403:
        print("❌ ERROR 403: Forbidden")
        print()
        print("This means the token doesn't have permission to access this resource.")
        print()
        print("Possible causes:")
        print("1. Token doesn't have access to this specific base")
        print("2. Token scope doesn't include 'data.records:read' permission")
        print("3. Base ID is incorrect")
        print("4. Table name is incorrect (case-sensitive!)")
        print()
        print("Solutions:")
        print("1. Go to: https://airtable.com/account/tokens")
        print("2. Check your token's scope includes:")
        print("   - Base: appZOdJaRPiwcygdR")
        print("   - Permissions: data.records:read")
        print("3. Verify the base ID in Airtable (check URL when viewing the base)")
        print("4. Verify table name exactly matches (including spaces, capitalization)")
        
    elif response.status_code == 404:
        print("❌ ERROR 404: Not Found")
        print()
        print("This means the base or table doesn't exist.")
        print()
        print("Solutions:")
        print("1. Verify Base ID: appZOdJaRPiwcygdR")
        print("2. Verify Table Name: 'Table 1' (case-sensitive)")
        print("3. Check if you have access to this base in Airtable")
        
    else:
        print(f"❌ ERROR {response.status_code}: {response.reason}")
        print()
        print("Response body:")
        print(response.text)
    
    # Show response details
    if response.status_code != 200:
        print()
        print("Response Headers:")
        for header, value in response.headers.items():
            if header.lower() not in ['authorization', 'set-cookie']:
                print(f"  {header}: {value}")
        
        print()
        print("Response Body:")
        try:
            error_data = response.json()
            print(f"  {error_data}")
        except:
            print(f"  {response.text[:500]}")
    
except requests.exceptions.RequestException as e:
    print(f"❌ Network Error: {e}")
    print()
    print("Check your internet connection and try again.")

print()
print("=" * 70)

# Additional checks
print()
print("Additional Checks:")
print()

print("1. Token Format Check:")
if AIRTABLE_TOKEN.startswith('pat'):
    print("   ✅ Token appears to be a Personal Access Token (starts with 'pat')")
elif AIRTABLE_TOKEN.startswith('key'):
    print("   ⚠️  Token appears to be a legacy API Key (starts with 'key')")
    print("      Consider using a scoped Personal Access Token instead")
else:
    print("   ❌ Token format is unexpected")

print()
print("2. Base ID Format Check:")
if AIRTABLE_BASE_ID.startswith('app') and len(AIRTABLE_BASE_ID) == 17:
    print("   ✅ Base ID format looks correct")
else:
    print("   ⚠️  Base ID format looks unusual")
    print("      Expected: 'app' + 14 characters (e.g., 'appZOdJaRPiwcygdR')")

print()
print("3. Table Name Check:")
print(f"   Table name: '{AIRTABLE_TABLE_NAME}'")
print("   Remember: Table names are case-sensitive and must match exactly")

print()
print("=" * 70)
print()

print("Next Steps:")
print()
print("If you see a 403 error:")
print("  1. Log into Airtable: https://airtable.com")
print("  2. Open your base (appZOdJaRPiwcygdR)")
print("  3. Verify the table is named exactly: 'Table 1'")
print("  4. Go to: https://airtable.com/account/tokens")
print("  5. Check your token has access to this base")
print("  6. Generate a new scoped token if needed")
print()
print("If you need to generate a new token:")
print("  1. Go to: https://airtable.com/create/tokens")
print("  2. Name: 'Google Earth KML Service'")
print("  3. Scopes: data.records:read")
print("  4. Access: Select your base (appZOdJaRPiwcygdR)")
print("  5. Copy the new token")
print("  6. Update AIRTABLE_TOKEN in .env file")
print()
print("=" * 70)
