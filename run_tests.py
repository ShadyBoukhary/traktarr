#!/usr/bin/env python3
"""
Test Runner for Traktarr

This script provides a convenient way to run tests with different configurations.
"""

import sys
import subprocess
import argparse
import os


def run_command(cmd, description):
    """Run a command and handle the output."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
        else:
            print(f"❌ {description} failed with exit code {result.returncode}")
        
        return result.returncode == 0
        
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def install_test_dependencies():
    """Install test dependencies."""
    print("Installing test dependencies...")
    return run_command([
        sys.executable, '-m', 'pip', 'install', '-r', 'test-requirements.txt'
    ], "Installing test dependencies")


def run_unit_tests():
    """Run unit tests."""
    return run_command([
        sys.executable, '-m', 'pytest', 'tests/', '-m', 'unit or not integration', '-v'
    ], "Unit tests")


def run_integration_tests():
    """Run integration tests."""
    return run_command([
        sys.executable, '-m', 'pytest', 'tests/', '-m', 'integration', '-v'
    ], "Integration tests")


def run_cli_tests():
    """Run CLI tests."""
    return run_command([
        sys.executable, '-m', 'pytest', 'tests/test_cli_commands.py', '-v'
    ], "CLI command tests")


def run_business_logic_tests():
    """Run business logic tests."""
    return run_command([
        sys.executable, '-m', 'pytest', 'tests/test_business_logic.py', '-v'
    ], "Business logic tests")


def run_helper_tests():
    """Run helper tests."""
    return run_command([
        sys.executable, '-m', 'pytest', 'tests/test_helpers.py', '-v'
    ], "Helper module tests")


def run_all_tests():
    """Run all tests."""
    return run_command([
        sys.executable, '-m', 'pytest', 'tests/', '-v'
    ], "All tests")


def run_coverage_tests():
    """Run tests with coverage reporting."""
    return run_command([
        sys.executable, '-m', 'pytest', 'tests/', 
        '--cov=cli', '--cov=core', '--cov=helpers', '--cov=media', '--cov=misc', '--cov=notifications',
        '--cov-report=html', '--cov-report=term-missing', '-v'
    ], "Tests with coverage")


def run_fast_tests():
    """Run only fast tests (exclude slow marker)."""
    return run_command([
        sys.executable, '-m', 'pytest', 'tests/', '-m', 'not slow', '-v'
    ], "Fast tests")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Traktarr Test Runner')
    parser.add_argument(
        'test_type',
        choices=[
            'all', 'unit', 'integration', 'cli', 'business', 'helpers', 
            'coverage', 'fast', 'install-deps'
        ],
        help='Type of tests to run'
    )
    parser.add_argument(
        '--install-first',
        action='store_true',
        help='Install test dependencies before running tests'
    )
    
    args = parser.parse_args()
    
    # Change to the traktarr directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    success = True
    
    # Install dependencies if requested
    if args.install_first or args.test_type == 'install-deps':
        success = install_test_dependencies()
        if args.test_type == 'install-deps':
            return 0 if success else 1
    
    # Run the requested tests
    if args.test_type == 'all':
        success = run_all_tests()
    elif args.test_type == 'unit':
        success = run_unit_tests()
    elif args.test_type == 'integration':
        success = run_integration_tests()
    elif args.test_type == 'cli':
        success = run_cli_tests()
    elif args.test_type == 'business':
        success = run_business_logic_tests()
    elif args.test_type == 'helpers':
        success = run_helper_tests()
    elif args.test_type == 'coverage':
        success = run_coverage_tests()
    elif args.test_type == 'fast':
        success = run_fast_tests()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
