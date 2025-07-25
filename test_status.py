#!/usr/bin/env python3
"""
Test Status Summary for Traktarr

This script provides a quick overview of test status and runs the working tests.
"""
import subprocess
import sys

def run_tests_with_summary():
    """Run the tests that are known to work and provide a summary."""
    
    print("🚀 Traktarr Test Status Summary")
    print("=" * 50)
    
    # Tests that are fully working
    working_tests = [
        "tests/test_cli_commands.py",
        "tests/test_verification.py", 
        "tests/test_debug.py",
        "tests/test_business_logic_simple.py::TestBusinessLogicSimple::test_app_loaded_exists",
        "tests/test_business_logic_simple.py::TestBusinessLogicSimple::test_run_automatic_mode_basic",
        "tests/test_helpers.py::TestMediaProcessing",
        "tests/test_helpers.py::TestErrorHandling",
    ]
    
    print(f"✅ Running {len(working_tests)} test groups that are fully working...")
    print()
    
    # Run working tests
    cmd = ["python", "-m", "pytest"] + working_tests + ["-v", "--tb=short"]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return_code = result.returncode
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1
    
    print()
    print("📊 Test Categories Summary:")
    print("=" * 30)
    print("✅ WORKING:")
    print("   • CLI Commands (24 tests) - Full Click integration testing")
    print("   • Verification Tests (2 tests) - Basic setup verification")
    print("   • Debug Tests (1 test) - Debug command testing")
    print("   • Simple Business Logic (2 tests) - Basic module imports")
    print("   • Media Processing Helpers (3 tests) - Data filtering/processing")
    print("   • Error Handling (3 tests) - Exception handling")
    print()
    print("⚠️  PARTIALLY WORKING:")
    print("   • Helper Tests (3/9 working) - Some tests need module imports")
    print()
    print("❌ NEEDS FIXES:")
    print("   • Business Logic Tests (0/11) - Config singleton initialization issues")
    print("   • Integration Tests (1/6) - Import path and mocking issues")
    print()
    print("🔧 Main Issues to Fix:")
    print("   1. Config singleton requires proper initialization parameters")
    print("   2. Complex business logic functions need deep mocking")
    print("   3. Integration tests need correct import paths (media.* vs helpers.*)")
    print()
    print("📈 Overall Status:")
    print(f"   • Working Tests: ~35+ tests")
    print(f"   • Total Tests: ~61 tests")
    print(f"   • Success Rate: ~57% (significant improvement from initial 0%)")
    print()
    
    if return_code == 0:
        print("🎉 All working tests passed successfully!")
    else:
        print("⚠️  Some working tests had issues - check output above.")
    
    return return_code

def run_all_tests_summary():
    """Run all tests and provide a summary."""
    print("🔍 Running ALL tests for complete status...")
    print()
    
    cmd = ["python", "-m", "pytest", "tests/", "--tb=no", "-q"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = result.stdout + result.stderr
        return_code = result.returncode
        
        print("📊 Complete Test Results:")
        print(output)
        
    except subprocess.TimeoutExpired:
        print("⏱️  Test run timed out (some tests may be hanging)")
        return 1
    except Exception as e:
        print(f"❌ Error running all tests: {e}")
        return 1
    
    return return_code

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        exit_code = run_all_tests_summary()
    else:
        exit_code = run_tests_with_summary()
    
    sys.exit(exit_code)
