"""Tests for project structure and setup."""

import sys
from pathlib import Path

import pytest


def test_lse_package_exists():
    """Test that the lse package directory exists."""
    package_dir = Path(__file__).parent.parent / "lse"
    assert package_dir.exists(), "lse package directory should exist"
    assert package_dir.is_dir(), "lse should be a directory"


def test_lse_package_importable():
    """Test that the lse package can be imported."""
    try:
        import lse
    except ImportError:
        pytest.fail("lse package should be importable")


def test_required_subdirectories_exist():
    """Test that required subdirectories exist in the lse package."""
    package_dir = Path(__file__).parent.parent / "lse"
    
    required_dirs = ["commands"]
    for dir_name in required_dirs:
        dir_path = package_dir / dir_name
        assert dir_path.exists(), f"{dir_name} directory should exist"
        assert dir_path.is_dir(), f"{dir_name} should be a directory"


def test_init_files_exist():
    """Test that __init__.py files exist in required locations."""
    package_dir = Path(__file__).parent.parent / "lse"
    
    init_locations = [
        package_dir / "__init__.py",
        package_dir / "commands" / "__init__.py",
    ]
    
    for init_file in init_locations:
        assert init_file.exists(), f"{init_file} should exist"
        assert init_file.is_file(), f"{init_file} should be a file"


def test_console_script_entry_point():
    """Test that the console script entry point is properly configured."""
    # This test verifies that the entry point would work after installation
    # The actual entry point is configured in pyproject.toml
    try:
        from lse.cli import app
        assert app is not None, "CLI app should be defined"
    except ImportError:
        pytest.fail("CLI app should be importable from lse.cli")


def test_required_dependencies_available():
    """Test that required dependencies can be imported."""
    required_packages = [
        ("typer", "typer"),
        ("dotenv", "python-dotenv"),
        ("pydantic", "pydantic"),
        ("rich", "rich"),
    ]
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            pytest.fail(f"Required package {package_name} should be installed")