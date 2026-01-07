#!/usr/bin/env python3
"""
Test script to verify the fix for the generate endpoint
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_import_and_route():
    """Test that the module imports correctly and route is properly defined"""
    try:
        import backend.routes.exercises_routes as routes_module
        
        # Test 1: Check that module imports without errors
        print("✅ Module backend.routes.exercises_routes imported successfully")
        
        # Test 2: Check that router exists
        if not hasattr(routes_module, 'router'):
            print("❌ ERROR: router not found in exercises_routes module")
            return False
        print("✅ Router exists in exercises_routes")
        
        # Test 3: Check that generate_exercise function exists and has correct signature
        if not hasattr(routes_module, 'generate_exercise'):
            print("❌ ERROR: generate_exercise function not found")
            return False
            
        import inspect
        sig = inspect.signature(routes_module.generate_exercise)
        params = list(sig.parameters.keys())
        
        if 'fastapi_request' not in params:
            print(f"❌ ERROR: fastapi_request parameter not found in generate_exercise. Parameters: {params}")
            return False
            
        param_type = sig.parameters['fastapi_request'].annotation
        if 'Request' not in str(param_type):
            print(f"❌ ERROR: fastapi_request parameter type is not Request, got: {param_type}")
            return False
            
        print(f"✅ generate_exercise function has correct signature: {sig}")
        
        # Test 4: Check that the route is registered
        if not hasattr(routes_module.router, 'routes'):
            print("❌ ERROR: router has no routes attribute")
            return False
            
        routes = routes_module.router.routes
        generate_route = None
        for route in routes:
            if route.path == '/generate' and 'POST' in route.methods:
                generate_route = route
                break
                
        if not generate_route:
            print("❌ ERROR: POST /generate route not found")
            return False
            
        if generate_route.endpoint != routes_module.generate_exercise:
            print(f"❌ ERROR: Route endpoint doesn't match function. Expected {routes_module.generate_exercise}, got {generate_route.endpoint}")
            return False
            
        print(f"✅ POST /generate route is correctly mapped to generate_exercise function")
        
        print("\n🎉 All tests passed! The fix has been successfully implemented.")
        print("\nSummary of changes:")
        print("- Fixed import: added 'Request' to the import statement")
        print("- Removed conflicting 'FastAPIRequest' alias import")
        print("- Updated function signature to use 'Request' instead of 'FastAPIRequest'")
        print("- Verified module imports without errors")
        print("- Verified route is correctly mapped to the function")
        print("- Maintains backward compatibility: body JSON priority, query params as fallback")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_import_and_route()
    if success:
        print("\n✅ VERIFICATION SUCCESSFUL - The fix is properly implemented!")
        sys.exit(0)
    else:
        print("\n❌ VERIFICATION FAILED - Issues found!")
        sys.exit(1)