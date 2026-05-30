#!/usr/bin/env python3
"""
Smoke test to verify the test runner and test infrastructure works.
This test doesn't require a database and can run anywhere.
"""

import sys
import os

def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")
    
    try:
        import pytest
        print("✓ pytest imported successfully")
    except ImportError as e:
        print(f"✗ pytest import failed: {e}")
        return False
    
    try:
        import asyncio
        print("✓ asyncio imported successfully")
    except ImportError as e:
        print(f"✗ asyncio import failed: {e}")
        return False
    
    try:
        import argparse
        print("✓ argparse imported successfully")
    except ImportError as e:
        print(f"✗ argparse import failed: {e}")
        return False
    
    try:
        import logging
        print("✓ logging imported successfully")
    except ImportError as e:
        print(f"✗ logging import failed: {e}")
        return False
    
    return True

def test_test_runner_import():
    """Test that the test runner can be imported."""
    print("\nTesting test runner import...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import test_runner
        print("✓ test_runner imported successfully")
        
        # Test basic classes
        from test_runner import TestGroup, TestRunner
        print("✓ TestGroup and TestRunner classes imported")
        
        # Test enum values
        auth_group = TestGroup.AUTH
        print(f"✓ TestGroup.AUTH = {auth_group.value}")
        
        return True
    except Exception as e:
        print(f"✗ test_runner import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_makefile_exists():
    """Test that Makefile exists and has test commands."""
    print("\nTesting Makefile...")
    
    makefile_path = os.path.join(os.path.dirname(__file__), "Makefile")
    
    if not os.path.exists(makefile_path):
        print(f"✗ Makefile not found at {makefile_path}")
        return False
    
    print("✓ Makefile exists")
    
    # Read and check for test commands
    with open(makefile_path, 'r') as f:
        content = f.read()
    
    test_commands = [
        "make test",
        "make test-auth",
        "make test-accounts",
        "make test-comprehensive",
        "make test-all",
    ]
    
    found_commands = []
    for cmd in test_commands:
        if cmd in content:
            found_commands.append(cmd)
            print(f"✓ Found command: {cmd}")
    
    if len(found_commands) >= 3:
        print(f"✓ Found {len(found_commands)} test commands")
        return True
    else:
        print(f"✗ Only found {len(found_commands)} test commands (expected at least 3)")
        return False

def test_test_files_exist():
    """Test that test files exist."""
    print("\nTesting test files...")
    
    test_dir = os.path.join(os.path.dirname(__file__), "tests")
    
    if not os.path.exists(test_dir):
        print(f"✗ tests directory not found at {test_dir}")
        return False
    
    print("✓ tests directory exists")
    
    required_files = [
        "test_auth.py",
        "test_auth_comprehensive.py",
        "test_accounts.py",
        "conftest.py",
    ]
    
    found_files = []
    for filename in required_files:
        filepath = os.path.join(test_dir, filename)
        if os.path.exists(filepath):
            found_files.append(filename)
            print(f"✓ Found test file: {filename}")
        else:
            print(f"✗ Missing test file: {filename}")
    
    if len(found_files) >= 3:
        print(f"✓ Found {len(found_files)} test files")
        return True
    else:
        print(f"✗ Only found {len(found_files)} test files (expected at least 3)")
        return False

def test_documentation_exists():
    """Test that documentation exists."""
    print("\nTesting documentation...")
    
    docs_file = os.path.join(os.path.dirname(__file__), "TESTING.md")
    
    if not os.path.exists(docs_file):
        print(f"✗ TESTING.md not found at {docs_file}")
        return False
    
    print("✓ TESTING.md exists")
    
    # Check file size
    file_size = os.path.getsize(docs_file)
    if file_size > 1000:  # At least 1KB
        print(f"✓ TESTING.md has sufficient content ({file_size} bytes)")
        return True
    else:
        print(f"✗ TESTING.md seems too small ({file_size} bytes)")
        return False

def main():
    """Run all smoke tests."""
    print("=" * 80)
    print("FinDoctor Backend Smoke Test")
    print("=" * 80)
    
    tests = [
        ("Imports", test_imports),
        ("Test Runner Import", test_test_runner_import),
        ("Makefile", test_makefile_exists),
        ("Test Files", test_test_files_exist),
        ("Documentation", test_documentation_exists),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*40}")
        print(f"Running: {test_name}")
        print(f"{'='*40}")
        
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"✗ Test {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ All smoke tests passed! The test infrastructure is ready.")
        print("\nNext steps:")
        print("1. Install dependencies: uv sync --dev")
        print("2. Start database: make db-up")
        print("3. Run tests: make test")
    else:
        print("❌ Some smoke tests failed. Check the output above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())