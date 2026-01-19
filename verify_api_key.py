#!/usr/bin/env python3
"""Script to verify API key exists and can be validated."""

import sys
import hashlib
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.infrastructure.security.api_key_service import api_key_service, APIKeyService

# The API key to verify
API_KEY = "sk_IlKzMWU-0G58anib7k4goRFU9lzKmsUoiGuS7x1o8Wo"

print("=" * 60)
print("API Key Verification")
print("=" * 60)
print(f"Storage file: {api_key_service.storage_file}")
print(f"Storage file exists: {api_key_service.storage_file.exists()}")
print(f"Number of keys loaded: {len(api_key_service._keys)}")
print()

# List all keys
print("Loaded API Keys:")
for key_id, key in api_key_service._keys.items():
    print(f"  - Key ID: {key_id}")
    print(f"    Name: {key.name}")
    print(f"    Client ID: {key.client_id}")
    print(f"    Active: {key.is_active}")
    print(f"    Hash: {key.key_hash[:20]}...")
    print()

# Try to validate the API key
print(f"Validating API key: {API_KEY[:20]}...")
key_info = api_key_service.validate_key(API_KEY)

if key_info:
    print("✅ API key is VALID!")
    print(f"   Key ID: {key_info.key_id}")
    print(f"   Name: {key_info.name}")
    print(f"   Client ID: {key_info.client_id}")
    print(f"   Active: {key_info.is_active}")
else:
    print("❌ API key is INVALID or NOT FOUND")
    print()
    print("Expected hash:", hashlib.sha256(API_KEY.encode()).hexdigest())
    print()
    print("Checking if hash matches any stored keys...")
    expected_hash = hashlib.sha256(API_KEY.encode()).hexdigest()
    for key_id, key in api_key_service._keys.items():
        if key.key_hash == expected_hash:
            print(f"  ✅ Hash matches key {key_id}!")
            print(f"     But validation failed - checking status...")
            print(f"     Active: {key.is_active}")
            if key.expires_at:
                from datetime import datetime
                print(f"     Expires: {key.expires_at}")
                print(f"     Now: {datetime.utcnow()}")
                if datetime.utcnow() > key.expires_at:
                    print(f"     ❌ Key is EXPIRED!")
        else:
            print(f"  ❌ Hash does not match key {key_id}")

print("=" * 60)

