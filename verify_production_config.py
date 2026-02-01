import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

def test_production_validation():
    print("Testing production validation...")
    
    # Set production environment
    os.environ['ENVIRONMENT'] = 'production'
    os.environ['DATABASE_URL'] = '' # Missing
    
    from app.config import Settings
    from pydantic import ValidationError
    
    try:
        s = Settings()
        print("FAIL: Should have raised error for missing DATABASE_URL")
        return False
    except (ValueError, ValidationError) as e:
        print(f"PASS: Correctly caught missing DATABASE_URL: {e}")
        
    print("All production validation tests passed.")
    return True

if __name__ == "__main__":
    if test_production_validation():
        sys.exit(0)
    else:
        sys.exit(1)
