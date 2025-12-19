#!/usr/bin/env python3

import sys
import os
sys.path.append('/app')

from backend_test import LeMaitreMotAPITester

def main():
    print("Testing Dynamic Factory v1...")
    tester = LeMaitreMotAPITester()
    
    # Check if method exists
    if hasattr(tester, 'test_dynamic_factory_v1_complete'):
        print("✅ Method found!")
        success, results = tester.test_dynamic_factory_v1_complete()
        print(f"Test result: {'PASSED' if success else 'FAILED'}")
        return success
    else:
        print("❌ Method not found!")
        print("Available methods:")
        for attr in dir(tester):
            if attr.startswith('test_') and 'dynamic' in attr.lower():
                print(f"  - {attr}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)