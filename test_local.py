"""
Local testing script for Google Earth KML service
Tests Airtable connection and KML generation without deploying
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file FIRST (before importing app)
load_dotenv()

# Now import from app (after env vars are loaded)
from app import fetch_airtable_records, generate_kml_document, parse_coordinates

def test_env_vars():
    """Test that required environment variables are set"""
    print("=" * 60)
    print("Testing Environment Variables")
    print("=" * 60)
    
    required_vars = [
        'AIRTABLE_BASE_ID',
        'AIRTABLE_TABLE_NAME',
        'AIRTABLE_TOKEN',
        'REFRESH_INTERVAL_MINUTES'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # Mask token for security
            if 'TOKEN' in var:
                display_value = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else "***"
            else:
                display_value = value
            print(f"✓ {var}: {display_value}")
        else:
            print(f"✗ {var}: NOT SET")
            all_set = False
    
    print()
    return all_set


def test_coordinate_parsing():
    """Test coordinate parsing function"""
    print("=" * 60)
    print("Testing Coordinate Parsing")
    print("=" * 60)
    
    test_cases = [
        ("34.258707, -79.802132", (34.258707, -79.802132)),
        ("40.7128, -74.0060", (40.7128, -74.0060)),
        ("invalid", None),
        ("", None),
        ("100, 200", None),  # Out of valid range
    ]
    
    all_passed = True
    for coord_string, expected in test_cases:
        result = parse_coordinates(coord_string)
        passed = result == expected
        status = "✓" if passed else "✗"
        print(f"{status} '{coord_string}' -> {result} (expected: {expected})")
        if not passed:
            all_passed = False
    
    print()
    return all_passed


def test_airtable_connection():
    """Test connection to Airtable and fetch records"""
    print("=" * 60)
    print("Testing Airtable Connection")
    print("=" * 60)
    
    print(f"\nTesting with:")
    print(f"  Base ID: {os.environ.get('AIRTABLE_BASE_ID')}")
    print(f"  Table: {os.environ.get('AIRTABLE_TABLE_NAME')}")
    print(f"  Token: {os.environ.get('AIRTABLE_TOKEN', '')[:15]}...")
    print()
    
    try:
        records = fetch_airtable_records()
        print(f"✓ Successfully connected to Airtable")
        print(f"✓ Fetched {len(records)} records")
        
        # Analyze records
        if records:
            print("\nRecord Analysis:")
            valid_coords = 0
            status_counts = {}
            
            for record in records:
                fields = record.get('fields', {})
                
                # Check coordinates
                coord_string = fields.get('Latitude and Longitude', '')
                if parse_coordinates(coord_string):
                    valid_coords += 1
                
                # Count statuses (handle both string and list types)
                status = fields.get('Zoning Status', 'Unknown')
                # If status is a list, join it or take first item
                if isinstance(status, list):
                    status = ', '.join(str(s) for s in status) if status else 'Unknown'
                elif not status:
                    status = 'Unknown'
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"  - Records with valid coordinates: {valid_coords}/{len(records)}")
            print(f"  - Records missing coordinates: {len(records) - valid_coords}")
            print("\n  Status distribution:")
            for status, count in sorted(status_counts.items()):
                print(f"    • {status}: {count}")
            
            # Show sample record
            if records:
                print("\n  Sample record fields:")
                sample_fields = records[0].get('fields', {})
                for field_name in sorted(sample_fields.keys()):
                    value = sample_fields[field_name]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"    • {field_name}: {value}")
        else:
            print("⚠ Warning: No records found in table")
        
        print()
        return True
        
    except Exception as e:
        print(f"✗ Error connecting to Airtable: {str(e)}")
        print()
        return False


def test_kml_generation():
    """Test KML generation"""
    print("=" * 60)
    print("Testing KML Generation")
    print("=" * 60)
    
    try:
        records = fetch_airtable_records()
        base_url = "http://localhost:5000"
        kml = generate_kml_document(records, base_url)
        
        # Basic validation
        checks = [
            ('<?xml version="1.0"' in kml, "XML declaration"),
            ('<kml xmlns="http://www.opengis.net/kml/2.2">' in kml, "KML namespace"),
            ('<Document>' in kml, "Document element"),
            ('<Style id=' in kml, "Style definitions"),
            ('<Placemark>' in kml or len(records) == 0, "Placemarks (or empty)"),
        ]
        
        all_passed = True
        for check, description in checks:
            status = "✓" if check else "✗"
            print(f"{status} {description}")
            if not check:
                all_passed = False
        
        # Save to file for inspection
        output_file = "test_output.kml"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(kml)
        print(f"\n✓ KML saved to {output_file} for inspection")
        print(f"  You can open this file in Google Earth Pro to test")
        
        print()
        return all_passed
        
    except Exception as e:
        print(f"✗ Error generating KML: {str(e)}")
        print()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Google Earth KML Service - Local Test Suite")
    print("=" * 60 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Environment Variables", test_env_vars()))
    results.append(("Coordinate Parsing", test_coordinate_parsing()))
    results.append(("Airtable Connection", test_airtable_connection()))
    results.append(("KML Generation", test_kml_generation()))
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed! Ready to deploy.")
        print("\nNext steps:")
        print("1. Start local server: python app.py")
        print("2. Test in browser: http://localhost:5000")
        print("3. Download KML: http://localhost:5000/kml")
        print("4. Test in Google Earth Pro")
        print("5. Deploy to production (see DEPLOYMENT.md)")
    else:
        print("✗ Some tests failed. Please fix issues before deploying.")
        print("\nCommon issues:")
        print("- Check .env file exists and has correct values")
        print("- Verify Airtable token is valid")
        print("- Ensure Base ID and Table Name are correct")
        print("- Check Airtable has 'Latitude and Longitude' field")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    exit(main())
