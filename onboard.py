"""Developer Onboarding Check Script.

Verifies that a new developer's environment is correctly configured.
Supports --verbose and --fix flags for extended functionality.
"""

import sys
import os
import importlib
import subprocess
import shutil
import time
import argparse


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Developer Onboarding Environment Check"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show extra detail for each check",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to install missing packages automatically",
    )
    return parser.parse_args()


def check_python_version(verbose=False):
    """Check if Python version is 3.10 or higher.

    Args:
        verbose (bool): Print extra detail if True.

    Returns:
        tuple: (passed: bool, message: str, duration: float)
    """
    start = time.time()
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    passed = version_info.major == 3 and version_info.minor >= 10
    if passed:
        msg = f"Python version: {version_str} (>= 3.10 required)"
    else:
        msg = f"Python version: {version_str} — WARNING: 3.10+ required"
    if verbose:
        print(f"  Detail: Full version string — {sys.version}")
    duration = time.time() - start
    return passed, msg, duration


def check_virtual_environment(verbose=False):
    """Check if the script is running inside a virtual environment.

    Args:
        verbose (bool): Print extra detail if True.

    Returns:
        tuple: (passed: bool, message: str, duration: float)
    """
    start = time.time()
    in_venv = sys.prefix != sys.base_prefix
    env_name = os.path.basename(sys.prefix) if in_venv else "N/A"
    if in_venv:
        msg = f"Virtual environment: Active ({env_name})"
    else:
        msg = "Virtual environment: ERROR — Not running in a virtual environment"
    if verbose:
        print(f"  Detail: sys.prefix = {sys.prefix}")
    duration = time.time() - start
    return in_venv, msg, duration


def check_package_installed(package_name, verbose=False, fix=False):
    """Check if a specific package is installed and importable.

    Args:
        package_name (str): Name of the package to check.
        verbose (bool): Print extra detail if True.
        fix (bool): Attempt pip install if missing.

    Returns:
        tuple: (passed: bool, message: str, duration: float)
    """
    start = time.time()
    try:
        module = importlib.import_module(package_name)
        version = getattr(module, "__version__", "unknown")
        msg = f"{package_name} installed: version {version}"
        passed = True
    except ImportError:
        if fix:
            print(f"  Attempting to install {package_name}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package_name],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                module = importlib.import_module(package_name)
                version = getattr(module, "__version__", "unknown")
                msg = f"{package_name} installed (auto-fixed): version {version}"
                passed = True
            else:
                msg = f"{package_name}: FAILED to install automatically"
                passed = False
        else:
            msg = f"{package_name}: NOT installed"
            passed = False
        if verbose and not passed:
            print(f"  Detail: ImportError for {package_name}")
    duration = time.time() - start
    return passed, msg, duration


def check_internet_connectivity(verbose=False):
    """Check internet connectivity by making an HTTP request.

    Args:
        verbose (bool): Print extra detail if True.

    Returns:
        tuple: (passed: bool, message: str, duration: float)
    """
    start = time.time()
    try:
        import requests  # pylint: disable=import-outside-toplevel

        response = requests.get("https://httpbin.org/get", timeout=5)
        if response.status_code == 200:
            msg = "Internet connectivity: OK"
            passed = True
        else:
            msg = f"Internet connectivity: HTTP {response.status_code}"
            passed = False
        if verbose:
            print(f"  Detail: Response status = {response.status_code}")
    except ImportError:
        msg = "Internet connectivity: SKIPPED (requests not installed)"
        passed = False
    except Exception as exc:  # pylint: disable=broad-except
        msg = f"Internet connectivity: FAILED ({exc})"
        passed = False
    duration = time.time() - start
    return passed, msg, duration


def check_disk_space(verbose=False):
    """Check that at least 1 GB of disk space is available.

    Args:
        verbose (bool): Print extra detail if True.

    Returns:
        tuple: (passed: bool, message: str, duration: float)
    """
    start = time.time()
    usage = shutil.disk_usage(os.path.expanduser("~"))
    free_gb = usage.free / (1024 ** 3)
    passed = free_gb >= 1.0
    msg = f"Disk space: {free_gb:.2f} GB free"
    if not passed:
        msg += " — WARNING: Less than 1 GB available"
    if verbose:
        print(f"  Detail: Total={usage.total / (1024**3):.2f} GB, "
              f"Used={usage.used / (1024**3):.2f} GB")
    duration = time.time() - start
    return passed, msg, duration


def list_installed_packages():
    """Return a list of installed packages and their versions.

    Returns:
        list[str]: Lines describing each installed package.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--format=columns"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip().splitlines()


def run_all_checks(verbose=False, fix=False):
    """Run all onboarding checks and return results.

    Args:
        verbose (bool): Print extra detail.
        fix (bool): Auto-install missing packages.

    Returns:
        list[dict]: Each dict has keys: name, passed, message, duration.
    """
    checks = []

    for check_fn, label in [
        (lambda: check_python_version(verbose), "Python version"),
        (lambda: check_virtual_environment(verbose), "Virtual environment"),
        (lambda: check_package_installed("pylint", verbose, fix), "pylint installed"),
        (lambda: check_package_installed("black", verbose, fix), "black installed"),
        (lambda: check_internet_connectivity(verbose), "Internet connectivity"),
        (lambda: check_package_installed("numpy", verbose, fix), "numpy installed"),
        (lambda: check_disk_space(verbose), "Disk space"),
    ]:
        passed, message, duration = check_fn()
        checks.append(
            {"name": label, "passed": passed, "message": message, "duration": duration}
        )

    return checks


def print_report(checks, total_time):
    """Print a formatted report to stdout.

    Args:
        checks (list[dict]): Check results.
        total_time (float): Total execution time in seconds.
    """
    print("\n=== Developer Onboarding Check ===\n")
    for check in checks:
        status = "PASS" if check["passed"] else "FAIL"
        timing = f"  ({check['duration']*1000:.1f}ms)"
        print(f"[{status}] {check['message']}{timing}")
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    print("\n---")
    result_symbol = "✓" if passed_count == total else "✗"
    print(f"Result: {passed_count}/{total} checks passed {result_symbol}")
    print(f"Total execution time: {total_time*1000:.1f}ms")


def save_report(checks, total_time, filepath="setup_report.txt"):
    """Save the check report to a text file.

    Args:
        checks (list[dict]): Check results.
        total_time (float): Total execution time.
        filepath (str): Output file path.
    """
    lines = ["=== Developer Onboarding Check ===", ""]
    for check in checks:
        status = "PASS" if check["passed"] else "FAIL"
        lines.append(f"[{status}] {check['message']}  ({check['duration']*1000:.1f}ms)")
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    result_symbol = "✓" if passed_count == total else "✗"
    lines += [
        "",
        "---",
        f"Result: {passed_count}/{total} checks passed {result_symbol}",
        f"Total execution time: {total_time*1000:.1f}ms",
    ]

    # Installed packages section
    lines += ["", "=== Installed Packages ==="]
    for pkg_line in list_installed_packages():
        lines.append(pkg_line)

    with open(filepath, "w", encoding="utf-8") as report_file:
        report_file.write("\n".join(lines))
    print(f"\nReport saved to: {filepath}")


def main():
    """Entry point for the onboarding check script."""
    args = parse_arguments()
    overall_start = time.time()

    checks = run_all_checks(verbose=args.verbose, fix=args.fix)

    total_time = time.time() - overall_start
    print_report(checks, total_time)
    save_report(checks, total_time)


if __name__ == "__main__":
    main()
