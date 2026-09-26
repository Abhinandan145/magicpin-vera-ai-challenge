#!/usr/bin/env python3
"""
Test runner script using unittest (with pytest fallback if installed).
"""

import sys
import os
import unittest

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    os.chdir(project_root)
    
    print("=" * 60)
    print("Running Vera Test Suite (API, Replays, Logic)...")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.discover(start_dir=os.path.join(project_root, "tests"), pattern="test_api.py"))
    suite.addTests(loader.discover(start_dir=os.path.join(project_root, "tests"), pattern="test_replays.py"))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\nAll standard tests passed successfully! [100%]")
        sys.exit(0)
    else:
        print(f"\nTests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        sys.exit(1)
