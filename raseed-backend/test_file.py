#!/usr/bin/env python3
"""
Test different Google Wallet class configurations to find what works.
This script tries multiple approaches to identify the working configuration.
"""

import os
import json
import uuid
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
ISSUER_ID = "3388000000022971806"
SERVICE_ACCOUNT_FILE = "firebase-service-account.json"
SCOPES = ["https://www.googleapis.com/auth/wallet_object.issuer"]

def get_client():
    """Get wallet API client"""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build('walletobjects', 'v1', credentials=creds)

def test_class_configuration(client, config_name, class_config, object_config):
    """Test a specific class and object configuration"""
    print(f"\n🧪 Testing Configuration: {config_name}")
    print("-" * 50)
    
    class_id = f"{ISSUER_ID}.test_{config_name.lower().replace(' ', '_')}"
    object_id = f"{ISSUER_ID}.obj_{uuid.uuid4().hex[:6]}"
    
    try:
        # Create class
        class_config["id"] = class_id
        print(f"   Creating class: {class_id}")
        
        try:
            client.genericclass().get(resourceId=class_id).execute()
            print("   Class already exists, using existing")
        except HttpError as e:
            if e.resp.status == 404:
                client.genericclass().insert(body=class_config).execute()
                print("   ✅ Class created successfully")
        
        # Create object
        object_config["id"] = object_id
        object_config["classId"] = class_id
        print(f"   Creating object: {object_id}")
        
        response = client.genericobject().insert(body=object_config).execute()
        save_url = f"https://pay.google.com/gp/v/save/{response['id']}"
        
        print(f"   ✅ Object created successfully")
        print(f"   🔗 Save URL: {save_url}")
        return True, save_url
        
    except HttpError as e:
        error_content = e.content.decode() if hasattr(e, 'content') else str(e)
        print(f"   ❌ Failed: {error_content}")
        return False, None

def main():
    """Test multiple configurations"""
    print("🧪 TESTING MULTIPLE WALLET CONFIGURATIONS")
    print("=" * 60)
    
    client = get_client()
    working_configs = []
    
    # Configuration 1: Minimal (DRAFT status)
    config1_class = {
        "issuerName": "Project Raseed",
        "reviewStatus": "DRAFT"
    }
    config1_object = {
        "state": "ACTIVE"
    }
    
    success, url = test_class_configuration(
        client, "Minimal Draft", config1_class, config1_object
    )
    if success:
        working_configs.append(("Minimal Draft", url))
    
    # Configuration 2: Minimal (UNDER_REVIEW status)
    config2_class = {
        "issuerName": "Project Raseed",
        "reviewStatus": "UNDER_REVIEW"
    }
    config2_object = {
        "state": "ACTIVE"
    }
    
    success, url = test_class_configuration(
        client, "Minimal Under Review", config2_class, config2_object
    )
    if success:
        working_configs.append(("Minimal Under Review", url))
    
    # Configuration 3: With basic styling
    config3_class = {
        "issuerName": "Project Raseed",
        "reviewStatus": "DRAFT",
        "hexBackgroundColor": "#4285F4"
    }
    config3_object = {
        "state": "ACTIVE",
        "hexBackgroundColor": "#4285F4"
    }
    
    success, url = test_class_configuration(
        client, "With Styling", config3_class, config3_object
    )
    if success:
        working_configs.append(("With Styling", url))
    
    # Configuration 4: With required display fields
    config4_class = {
        "issuerName": "Project Raseed",
        "reviewStatus": "DRAFT",
        "hexBackgroundColor": "#4285F4"
    }
    config4_object = {
        "state": "ACTIVE",
        "cardTitle": {
            "defaultValue": {
                "language": "en-US",
                "value": "Test Receipt"
            }
        },
        "header": {
            "defaultValue": {
                "language": "en-US",
                "value": "Test Store"
            }
        }
    }
    
    success, url = test_class_configuration(
        client, "With Display Fields", config4_class, config4_object
    )
    if success:
        working_configs.append(("With Display Fields", url))
    
    # Configuration 5: Complete minimal working version
    config5_class = {
        "issuerName": "Project Raseed",
        "reviewStatus": "DRAFT",
        "hexBackgroundColor": "#4285F4",
        "enableSmartTap": False
    }
    config5_object = {
        "state": "ACTIVE",
        "cardTitle": {
            "defaultValue": {
                "language": "en-US",
                "value": "Receipt - $25.99"
            }
        },
        "header": {
            "defaultValue": {
                "language": "en-US",
                "value": "Test Store"
            }
        },
        "textModulesData": [
            {
                "header": "Total",
                "body": "$25.99"
            }
        ]
    }
    
    success, url = test_class_configuration(
        client, "Complete Minimal", config5_class, config5_object
    )
    if success:
        working_configs.append(("Complete Minimal", url))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 CONFIGURATION TEST RESULTS")
    print("=" * 60)
    
    if working_configs:
        print(f"✅ Found {len(working_configs)} working configuration(s):")
        for i, (name, url) in enumerate(working_configs, 1):
            print(f"\n{i}. {name}")
            print(f"   URL: {url}")
            print(f"   🧪 Test this URL in your browser!")
    else:
        print("❌ No configurations worked")
        print("\nThis suggests a fundamental issue:")
        print("1. Google Wallet API might not be enabled")
        print("2. Service account lacks proper permissions")
        print("3. Issuer ID format is incorrect")
        print("4. Google Pay Console setup might be required")
    
    print(f"\n🎯 NEXT STEPS:")
    if working_configs:
        print("1. Test the URLs above in your browser")
        print("2. Use the working configuration in your main code")
        print("3. If URLs still fail, the issue is with Google's review process")
    else:
        print("1. Check Google Cloud Console - APIs & Services")
        print("2. Ensure 'Google Wallet API' is enabled")
        print("3. Verify service account has 'Wallet Objects Admin' role")
        print("4. Consider setting up Google Pay Console account")

if __name__ == "__main__":
    main()