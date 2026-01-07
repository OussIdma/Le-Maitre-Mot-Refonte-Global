"""
Test minimal pour vérifier que backend.server s'importe sans crash
"""
import sys
import os

def test_backend_server_import():
    """Test that backend.server can be imported without crashing"""
    try:
        # Add the project root to Python path to resolve 'backend' module
        # The project root is one level up from backend
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        # Set minimal environment variables to bypass startup validation
        if not os.environ.get('MONGO_URL'):
            os.environ['MONGO_URL'] = 'mongodb://test'
        if not os.environ.get('DB_NAME'):
            os.environ['DB_NAME'] = 'test'

        from backend.server import app
        print("✅ backend.server imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import backend.server: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_backend_server_import()
    if success:
        print("🎉 Import test passed!")
        exit(0)
    else:
        print("💥 Import test failed!")
        exit(1)