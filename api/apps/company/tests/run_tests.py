
"""
Test runner script for company app tests.

This script provides a convenient way to run all company app tests
with proper configuration and reporting.

Usage:
    python run_tests.py
    python run_tests.py --models
    python run_tests.py --serializers
    python run_tests.py --views
    python run_tests.py --permissions
    python run_tests.py --verbose
    python run_tests.py --coverage
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.pytest_settings')

import django
django.setup()


def run_tests(test_type=None, verbose=False, coverage=False):
    """Run tests with the specified options."""
    

    cmd = ['python', '-m', 'pytest']
    

    test_dir = Path(__file__).parent
    
    if test_type:
        if test_type == 'models':
            cmd.append(str(test_dir / 'test_models.py'))
        elif test_type == 'serializers':
            cmd.append(str(test_dir / 'test_serializers.py'))
        elif test_type == 'views':
            cmd.append(str(test_dir / 'test_views.py'))
        elif test_type == 'permissions':
            cmd.append(str(test_dir / 'test_permissions.py'))
    else:
        cmd.append(str(test_dir))
    

    if verbose:
        cmd.append('-v')
    
    if coverage:
        cmd.extend(['--cov=apps.company', '--cov-report=html', '--cov-report=term'])
    

    cmd.extend([
        '--tb=short',
        '--strict-markers',
        '--disable-warnings'
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 50)
    

    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode


def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(description='Run company app tests')
    parser.add_argument(
        '--models', 
        action='store_true', 
        help='Run only model tests'
    )
    parser.add_argument(
        '--serializers', 
        action='store_true', 
        help='Run only serializer tests'
    )
    parser.add_argument(
        '--views', 
        action='store_true', 
        help='Run only view tests'
    )
    parser.add_argument(
        '--permissions', 
        action='store_true', 
        help='Run only permission tests'
    )
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true', 
        help='Run with verbose output'
    )
    parser.add_argument(
        '--coverage', '-c', 
        action='store_true', 
        help='Run with coverage report'
    )
    
    args = parser.parse_args()
    

    test_type = None
    if args.models:
        test_type = 'models'
    elif args.serializers:
        test_type = 'serializers'
    elif args.views:
        test_type = 'views'
    elif args.permissions:
        test_type = 'permissions'
    

    exit_code = run_tests(
        test_type=test_type,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

