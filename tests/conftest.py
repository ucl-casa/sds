"""Pytest configuration and custom terminal report hooks for SDS test harness."""

import warnings

# ANSI terminal colors
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
NC = "\033[0m"

# Suppress known harmless upstream third-party warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*numpy.ndarray size changed.*", category=RuntimeWarning)
warnings.filterwarnings("ignore", message=".*Casting complex values to real.*")


def pytest_configure(config):
    """Register pytest warning filters for known harmless third-party notices."""
    config.addinivalue_line("filterwarnings", "ignore::DeprecationWarning")
    config.addinivalue_line("filterwarnings", "ignore:.*numpy.ndarray size changed.*:RuntimeWarning")
    config.addinivalue_line("filterwarnings", "ignore:.*Casting complex values to real.*:Warning")


def pytest_report_teststatus(report, config):
    """Custom formatting for test outcomes:
    - PASSED: green text with tick mark (✔ PASSED)
    - FAILED: red text with cross mark (❌ FAILED)
    - SKIPPED: yellow text with warning symbol (⚠️ SKIPPED)
    """
    if report.when == "call":
        if report.passed:
            return "passed", "P", (f"{GREEN}✔ PASSED{NC}", {"green": True, "bold": True})
        elif report.failed:
            return "failed", "F", (f"{RED}❌ FAILED{NC}", {"red": True, "bold": True})
        elif report.skipped:
            return "skipped", "S", (f"{YELLOW}⚠️ SKIPPED{NC}", {"yellow": True, "bold": True})
