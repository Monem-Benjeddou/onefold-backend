
"""
Simple test runner to check company app tests step by step.
"""

import os
import sys
import subprocess


project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.pytest_settings')

import django
django.setup()


def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    print(f"Command: {cmd}")
    print("-" * 60)
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ SUCCESS")
        if result.stdout:
            print(result.stdout)
    else:
        print("❌ FAILED")
        if result.stderr:
            print("STDERR:", result.stderr)
        if result.stdout:
            print("STDOUT:", result.stdout)
    
    return result.returncode == 0


def main():
    """Run tests step by step."""
    print("🚀 Starting Company App Test Suite")
    

    os.chdir(project_root)
    

    success = run_command(
        "python -c \"import ast; ast.parse(open('api/apps/company/tests/test_models.py').read()); print('✅ Models syntax OK')\"",
        "Checking test_models.py syntax"
    )
    if not success:
        print("❌ Syntax error in test_models.py")
        return
    
    success = run_command(
        "python -c \"import ast; ast.parse(open('api/apps/company/tests/test_serializers.py').read()); print('✅ Serializers syntax OK')\"",
        "Checking test_serializers.py syntax"
    )
    if not success:
        print("❌ Syntax error in test_serializers.py")
        return
    

    success = run_command(
        "python -m pytest api/apps/company/tests/ --collect-only -q",
        "Testing collection (no syntax errors)"
    )
    if not success:
        print("❌ Collection failed")
        return
    

    success = run_command(
        "python -m pytest api/apps/company/tests/test_basic.py -v",
        "Running basic setup tests"
    )
    if not success:
        print("❌ Basic tests failed")
        return
    

    success = run_command(
        "python -m pytest api/apps/company/tests/test_models.py -v --tb=short",
        "Running model tests"
    )
    if not success:
        print("❌ Model tests failed")
        return
    

    success = run_command(
        "python -m pytest api/apps/company/tests/test_serializers.py -v --tb=short",
        "Running serializer tests"
    )
    if not success:
        print("❌ Serializer tests failed")
        return
    
    print(f"\n{'='*60}")
    print("🎉 All tests completed!")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()

