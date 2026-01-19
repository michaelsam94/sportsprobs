#!/usr/bin/env python3
"""Quick test script to verify ADMIN_TOKEN is configured correctly."""

import os
from app.core.config import settings

print("=" * 50)
print("ADMIN_TOKEN Configuration Test")
print("=" * 50)
print(f"ADMIN_TOKEN from settings: {settings.ADMIN_TOKEN}")
print(f"ADMIN_TOKEN from env: {os.getenv('ADMIN_TOKEN', 'NOT SET')}")
print(f"Expected token: dx0d3ukqoM0LlUuxaAVsz2DSYv70bhAwuy048P9WCmbpOcEgrHblie14j8K1gwKl")
print("=" * 50)

if settings.ADMIN_TOKEN:
    print("✓ ADMIN_TOKEN is configured")
    if settings.ADMIN_TOKEN == "dx0d3ukqoM0LlUuxaAVsz2DSYv70bhAwuy048P9WCmbpOcEgrHblie14j8K1gwKl":
        print("✓ ADMIN_TOKEN matches expected value")
    else:
        print("✗ ADMIN_TOKEN does NOT match expected value")
else:
    print("✗ ADMIN_TOKEN is NOT configured")

