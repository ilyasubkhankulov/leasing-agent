#!/usr/bin/env python3

import sys
import subprocess
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle the output"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr and result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully!")
        else:
            print(f"❌ {description} failed with exit code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to run {description}: {e}")
        return False
    
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking test dependencies...")
    
    try:
        import pytest
        import pytest_asyncio
        import pytest_mock
        import httpx
        print("✅ All test dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: poetry install --with test")
        return False

def main():
    """Main test runner function"""
    print("🧪 Leasing Agent Test Suite")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("pyproject.toml"):
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Test commands to run
    test_commands = [
        {
            "cmd": "python -m pytest tests/ -v --tb=short",
            "desc": "Running all tests with verbose output"
        },
        {
            "cmd": "python -m pytest tests/test_llm_service.py -v",
            "desc": "Running LLM service tests"
        },
        {
            "cmd": "python -m pytest tests/test_chat_api.py -v", 
            "desc": "Running Chat API tests"
        },
        {
            "cmd": "python -m pytest tests/test_tools_service.py -v",
            "desc": "Running Tools service tests"
        },
        {
            "cmd": "python -m pytest tests/ --tb=short --durations=10",
            "desc": "Running tests with performance timing"
        }
    ]
    
    # Optional: Run coverage if available
    try:
        import coverage
        test_commands.insert(0, {
            "cmd": "python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html",
            "desc": "Running tests with coverage report"
        })
    except ImportError:
        print("💡 Install coverage for test coverage reports: poetry add --group test coverage pytest-cov")
    
    # Run tests
    failed_tests = []
    
    for test_config in test_commands:
        if not run_command(test_config["cmd"], test_config["desc"]):
            failed_tests.append(test_config["desc"])
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    if failed_tests:
        print(f"❌ {len(failed_tests)} test suite(s) failed:")
        for failed in failed_tests:
            print(f"   • {failed}")
        sys.exit(1)
    else:
        print("✅ All test suites passed successfully!")
        print("\n🎉 Ready for deployment!")

if __name__ == "__main__":
    main()