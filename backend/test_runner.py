#!/usr/bin/env python3
"""
Enhanced test runner for FinDoctor API with comprehensive endpoint testing.

Features:
- Test specific endpoint groups via command-line flags
- Detailed logging with different verbosity levels
- Database verification for auth tests
- Comprehensive test coverage for all API endpoints
- Colorized output for better readability
"""

import asyncio
import argparse
import logging
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Set
from enum import Enum

import pytest

# Try to import colorama for colored output, fall back to no colors
try:
    from colorama import init, Fore, Style
    COLORAMA_AVAILABLE = True
    init(autoreset=True)
except ImportError:
    COLORAMA_AVAILABLE = False
    # Create dummy color classes
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = DummyColor()
    Style = DummyColor()


class TestGroup(Enum):
    """Enum for test groups matching API tags."""
    AUTH = "auth"
    USER = "current-user"
    REFERENCE = "reference-data"
    INSTITUTIONS = "financial-institutions"
    ACCOUNTS = "accounts"
    TRANSACTIONS = "transactions"
    TRANSFERS = "transfers"
    RECURRING = "recurring-transactions"
    ASSETS = "assets"
    LIABILITIES = "liabilities"
    LIABILITY_PAYMENTS = "liability-payments"
    GOALS = "goals"
    TAGS = "tags"
    ANALYTICS = "analytics"
    AI_CHAT = "ai-chat"
    IMPORTS = "imports"
    ALL = "all"


class TestRunner:
    """Main test runner class."""
    
    def __init__(self, verbosity: int = 1, groups: Optional[List[TestGroup]] = None):
        self.verbosity = verbosity
        self.groups = groups or [TestGroup.ALL]
        self.logger = self._setup_logger()
        self.start_time = None
        self.end_time = None
        self.results = {}
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with appropriate verbosity."""
        logger = logging.getLogger("test_runner")
        logger.setLevel(logging.DEBUG if self.verbosity >= 3 else logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        if self.verbosity >= 3:
            ch.setLevel(logging.DEBUG)
        elif self.verbosity >= 2:
            ch.setLevel(logging.INFO)
        else:
            ch.setLevel(logging.WARNING)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        return logger
    
    def _get_test_paths_for_groups(self) -> List[str]:
        """Get test file paths for selected test groups."""
        test_paths = []
        
        # Map test groups to test files
        group_to_file = {
            TestGroup.AUTH: ["tests/test_auth.py"],
            TestGroup.ACCOUNTS: ["tests/test_accounts.py"],
            # Add more mappings as test files are created
        }
        
        if TestGroup.ALL in self.groups:
            # Run all tests
            test_paths = ["tests/"]
        else:
            # Run specific groups
            for group in self.groups:
                if group in group_to_file:
                    test_paths.extend(group_to_file[group])
                else:
                    self.logger.warning(f"No test file mapped for group: {group.value}")
        
        return test_paths
    
    def _build_pytest_args(self, test_paths: List[str]) -> List[str]:
        """Build pytest arguments based on configuration."""
        args = []
        
        # Add test paths
        args.extend(test_paths)
        
        # Verbosity
        if self.verbosity >= 3:
            args.extend(["-v", "-s"])
        elif self.verbosity >= 2:
            args.append("-v")
        else:
            args.append("-q")
        
        # Color output
        args.append("--color=yes")
        
        # Detailed reporting
        if self.verbosity >= 2:
            args.append("--tb=short")
        else:
            args.append("--tb=no")
        
        # Log capture
        if self.verbosity >= 3:
            args.append("--capture=no")
        else:
            args.append("--capture=sys")
        
        return args
    
    def print_banner(self):
        """Print test runner banner."""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}FinDoctor API Test Runner")
        print(f"{Fore.CYAN}{'='*80}")
        print(f"{Fore.YELLOW}Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.YELLOW}Test Groups: {', '.join([g.value for g in self.groups])}")
        print(f"{Fore.YELLOW}Verbosity: {self.verbosity}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    def print_summary(self, exit_code: int):
        """Print test summary."""
        duration = self.end_time - self.start_time if self.start_time and self.end_time else 0
        
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}Test Summary")
        print(f"{Fore.CYAN}{'='*80}")
        print(f"{Fore.YELLOW}Duration: {duration:.2f} seconds")
        print(f"{Fore.YELLOW}Exit Code: {exit_code}")
        
        if exit_code == 0:
            print(f"{Fore.GREEN}✓ All tests passed!")
        else:
            print(f"{Fore.RED}✗ Some tests failed")
        
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    async def run_tests(self) -> int:
        """Run tests and return exit code."""
        self.start_time = time.time()
        self.print_banner()
        
        # Get test paths
        test_paths = self._get_test_paths_for_groups()
        if not test_paths:
            self.logger.error("No test paths found for selected groups")
            return 1
        
        self.logger.info(f"Running tests for: {', '.join(test_paths)}")
        
        # Build pytest arguments
        pytest_args = self._build_pytest_args(test_paths)
        
        # Run pytest
        self.logger.debug(f"Pytest args: {' '.join(pytest_args)}")
        exit_code = pytest.main(pytest_args)
        
        self.end_time = time.time()
        self.print_summary(exit_code)
        
        return exit_code


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="FinDoctor API Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all                     # Run all tests
  %(prog)s --auth --accounts         # Run auth and accounts tests
  %(prog)s --groups auth accounts    # Run auth and accounts tests
  %(prog)s --verbose                 # Run with verbose output
  %(prog)s --debug                   # Run with debug output
        """
    )
    
    # Test group arguments
    group = parser.add_argument_group("Test Groups")
    group.add_argument("--all", action="store_true", help="Run all tests (default)")
    group.add_argument("--auth", action="store_true", help="Test authentication endpoints")
    group.add_argument("--accounts", action="store_true", help="Test accounts endpoints")
    group.add_argument("--transactions", action="store_true", help="Test transactions endpoints")
    group.add_argument("--transfers", action="store_true", help="Test transfers endpoints")
    group.add_argument("--reference", action="store_true", help="Test reference data endpoints")
    group.add_argument("--analytics", action="store_true", help="Test analytics endpoints")
    group.add_argument("--ai-chat", action="store_true", help="Test AI chat endpoints")
    
    # Alternative group specification
    group.add_argument(
        "--groups",
        nargs="+",
        choices=[g.value for g in TestGroup],
        help="Specify test groups by name"
    )
    
    # Output control
    output = parser.add_argument_group("Output Control")
    output.add_argument("-v", "--verbose", action="count", default=0, 
                       help="Increase verbosity (use -v, -vv, -vvv)")
    output.add_argument("-q", "--quiet", action="store_true", 
                       help="Suppress non-essential output")
    output.add_argument("--debug", action="store_true", 
                       help="Enable debug output (same as -vvv)")
    
    return parser.parse_args()


def args_to_test_groups(args: argparse.Namespace) -> List[TestGroup]:
    """Convert command line arguments to test groups."""
    groups = []
    
    # If specific groups are requested via --groups
    if args.groups:
        for group_name in args.groups:
            try:
                groups.append(TestGroup(group_name))
            except ValueError:
                print(f"{Fore.RED}Warning: Unknown test group: {group_name}{Style.RESET_ALL}")
    
    # If individual flags are used
    else:
        if args.all or not any([args.auth, args.accounts, args.transactions, 
                               args.transfers, args.reference, args.analytics, args.ai_chat]):
            groups.append(TestGroup.ALL)
        else:
            if args.auth:
                groups.append(TestGroup.AUTH)
            if args.accounts:
                groups.append(TestGroup.ACCOUNTS)
            if args.transactions:
                groups.append(TestGroup.TRANSACTIONS)
            if args.transfers:
                groups.append(TestGroup.TRANSFERS)
            if args.reference:
                groups.append(TestGroup.REFERENCE)
            if args.analytics:
                groups.append(TestGroup.ANALYTICS)
            if args.ai_chat:
                groups.append(TestGroup.AI_CHAT)
    
    return groups


def calculate_verbosity(args: argparse.Namespace) -> int:
    """Calculate verbosity level from arguments."""
    if args.debug:
        return 3
    if args.quiet:
        return 0
    return min(args.verbose, 3)


async def main():
    """Main entry point."""
    args = parse_args()
    verbosity = calculate_verbosity(args)
    groups = args_to_test_groups(args)
    
    runner = TestRunner(verbosity=verbosity, groups=groups)
    exit_code = await runner.run_tests()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())