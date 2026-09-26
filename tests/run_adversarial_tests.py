#!/usr/bin/env python3
"""
Adversarial test runner script using unittest.
"""

import sys
import os
import unittest

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    os.chdir(project_root)
    
    print("=" * 60)
    print("Running Vera Adversarial & Robustness Test Suite...")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=os.path.join(project_root, "tests"), pattern="test_adversarial.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\nAll adversarial & robustness tests passed! [100%]")
        sys.exit(0)
    else:
        print(f"\nAdversarial tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        sys.exit(1)
