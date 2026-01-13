#!/usr/bin/env python3
"""
Experiment script to test the website screenshot API functionality
"""
import os
import sys
import django

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from playwright.sync_api import sync_playwright
import tempfile
import uuid


def test_basic_screenshot():
    """Test basic screenshot functionality"""
    print("Test 1: Basic screenshot (not full page)")

    url = "https://example.com"
    width = 1280
    height = 720
    full_page = False

    with tempfile.TemporaryDirectory() as tmpdir:
        screenshot_path = os.path.join(tmpdir, f'{uuid.uuid1()}.png')

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': width, 'height': height}
                )
                page = context.new_page()
                page.set_default_timeout(20000)

                page.goto(url, wait_until='networkidle', timeout=20000)
                page.screenshot(path=screenshot_path, full_page=full_page)

                browser.close()

            if os.path.exists(screenshot_path):
                file_size = os.path.getsize(screenshot_path)
                print(f"✓ Screenshot created successfully: {file_size} bytes")
                return True
            else:
                print("✗ Screenshot file not created")
                return False

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False


def test_full_page_screenshot():
    """Test full page screenshot"""
    print("\nTest 2: Full page screenshot")

    url = "https://example.com"
    width = 1280
    height = 720
    full_page = True

    with tempfile.TemporaryDirectory() as tmpdir:
        screenshot_path = os.path.join(tmpdir, f'{uuid.uuid1()}.png')

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': width, 'height': height}
                )
                page = context.new_page()
                page.set_default_timeout(20000)

                page.goto(url, wait_until='networkidle', timeout=20000)
                page.screenshot(path=screenshot_path, full_page=full_page)

                browser.close()

            if os.path.exists(screenshot_path):
                file_size = os.path.getsize(screenshot_path)
                print(f"✓ Full page screenshot created successfully: {file_size} bytes")
                return True
            else:
                print("✗ Screenshot file not created")
                return False

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False


def test_timeout():
    """Test timeout handling"""
    print("\nTest 3: Timeout handling (testing with very short timeout)")

    url = "https://example.com"
    width = 1280
    height = 720

    with tempfile.TemporaryDirectory() as tmpdir:
        screenshot_path = os.path.join(tmpdir, f'{uuid.uuid1()}.png')

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': width, 'height': height}
                )
                page = context.new_page()
                # Set a very short timeout for testing
                page.set_default_timeout(1)

                try:
                    page.goto(url, wait_until='networkidle', timeout=1)
                    print("✗ Should have timed out but didn't")
                    browser.close()
                    return False
                except Exception:
                    print("✓ Timeout handling works correctly")
                    browser.close()
                    return True

        except Exception as e:
            print(f"✗ Unexpected error: {str(e)}")
            return False


def test_different_dimensions():
    """Test different viewport dimensions"""
    print("\nTest 4: Different viewport dimensions")

    url = "https://example.com"
    test_cases = [
        (800, 600),   # Small
        (1920, 1080), # Full HD
        (375, 667),   # Mobile
    ]

    all_passed = True

    for width, height in test_cases:
        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot_path = os.path.join(tmpdir, f'{uuid.uuid1()}.png')

            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        viewport={'width': width, 'height': height}
                    )
                    page = context.new_page()
                    page.set_default_timeout(20000)

                    page.goto(url, wait_until='networkidle', timeout=20000)
                    page.screenshot(path=screenshot_path, full_page=False)

                    browser.close()

                if os.path.exists(screenshot_path):
                    file_size = os.path.getsize(screenshot_path)
                    print(f"  ✓ {width}x{height}: {file_size} bytes")
                else:
                    print(f"  ✗ {width}x{height}: Screenshot not created")
                    all_passed = False

            except Exception as e:
                print(f"  ✗ {width}x{height}: Error - {str(e)}")
                all_passed = False

    return all_passed


if __name__ == '__main__':
    print("=" * 60)
    print("Website Screenshot API - Experiment Tests")
    print("=" * 60)

    results = []

    results.append(("Basic screenshot", test_basic_screenshot()))
    results.append(("Full page screenshot", test_full_page_screenshot()))
    results.append(("Timeout handling", test_timeout()))
    results.append(("Different dimensions", test_different_dimensions()))

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(passed for _, passed in results)
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed."))

    sys.exit(0 if all_passed else 1)
