#!/usr/bin/env python3
"""
Test runner script for the FastAPI Todo App.
This script provides convenient ways to run different types of tests.
"""

import sys
import subprocess
import argparse
import os


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🚀 {description}")
    print(f"Command: {command}")
    print("-" * 50)

    try:
        result = subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed successfully")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return e.returncode


def main():
    parser = argparse.ArgumentParser(description="Test runner for FastAPI Todo App")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "api", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage report"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--file",
        help="Run specific test file"
    )

    args = parser.parse_args()

    # Base pytest command
    pytest_cmd = ["pytest"]

    # Add verbose flag
    if args.verbose:
        pytest_cmd.append("-v")

    # Add coverage
    if args.coverage:
        pytest_cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])

    # Add parallel execution
    if args.parallel:
        pytest_cmd.extend(["-n", "auto"])

    # Specific file
    if args.file:
        pytest_cmd.append(f"tests/{args.file}")
    elif args.type != "all":
        pytest_cmd.extend(["-m", args.type])

    # Join command
    command = " ".join(pytest_cmd)

    # Set up environment
    os.environ["PYTHONPATH"] = os.getcwd()

    # Run tests
    return run_command(command, f"Running {args.type} tests")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
