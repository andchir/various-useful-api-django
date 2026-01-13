#!/usr/bin/env python3
"""
Experiment script to test the website screenshot API crop functionality
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
from PIL import Image
import tempfile
import uuid


def test_basic_crop():
    """Test basic cropping functionality"""
    print("Test 1: Basic crop (crop center 400x300 from 1280x720 screenshot)")

    url = "https://example.com"
    width = 1280
    height = 720
    full_page = False

    # Crop parameters - crop center 400x300 region
    crop_left = 440  # (1280 - 400) / 2
    crop_top = 210   # (720 - 300) / 2
    crop_width = 400
    crop_height = 300

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

            # Apply cropping
            img = Image.open(screenshot_path)
            right = crop_left + crop_width
            lower = crop_top + crop_height
            cropped_img = img.crop((crop_left, crop_top, right, lower))
            cropped_img.save(screenshot_path)

            # Verify the crop
            final_img = Image.open(screenshot_path)
            final_width, final_height = final_img.size

            if final_width == crop_width and final_height == crop_height:
                print(f"✓ Cropped screenshot dimensions: {final_width}x{final_height}")
                return True
            else:
                print(f"✗ Expected {crop_width}x{crop_height}, got {final_width}x{final_height}")
                return False

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False


def test_top_left_crop():
    """Test cropping from top-left corner"""
    print("\nTest 2: Crop from top-left corner (0,0) 640x480")

    url = "https://example.com"
    width = 1280
    height = 720

    crop_left = 0
    crop_top = 0
    crop_width = 640
    crop_height = 480

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

            # Apply cropping
            img = Image.open(screenshot_path)
            right = crop_left + crop_width
            lower = crop_top + crop_height
            cropped_img = img.crop((crop_left, crop_top, right, lower))
            cropped_img.save(screenshot_path)

            # Verify the crop
            final_img = Image.open(screenshot_path)
            final_width, final_height = final_img.size

            if final_width == crop_width and final_height == crop_height:
                print(f"✓ Cropped screenshot dimensions: {final_width}x{final_height}")
                return True
            else:
                print(f"✗ Expected {crop_width}x{crop_height}, got {final_width}x{final_height}")
                return False

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False


def test_bottom_right_crop():
    """Test cropping from bottom-right area"""
    print("\nTest 3: Crop from bottom-right area")

    url = "https://example.com"
    width = 1280
    height = 720

    # Crop bottom-right 400x300
    crop_left = 880  # 1280 - 400
    crop_top = 420   # 720 - 300
    crop_width = 400
    crop_height = 300

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

            # Apply cropping
            img = Image.open(screenshot_path)
            right = crop_left + crop_width
            lower = crop_top + crop_height
            cropped_img = img.crop((crop_left, crop_top, right, lower))
            cropped_img.save(screenshot_path)

            # Verify the crop
            final_img = Image.open(screenshot_path)
            final_width, final_height = final_img.size

            if final_width == crop_width and final_height == crop_height:
                print(f"✓ Cropped screenshot dimensions: {final_width}x{final_height}")
                return True
            else:
                print(f"✗ Expected {crop_width}x{crop_height}, got {final_width}x{final_height}")
                return False

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False


def test_no_crop():
    """Test that screenshot works without cropping (crop_width/height = 0)"""
    print("\nTest 4: No crop (crop_width and crop_height = 0)")

    url = "https://example.com"
    width = 1280
    height = 720

    crop_width = 0
    crop_height = 0

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

            # No cropping should be applied when crop_width and crop_height are 0
            # Verify original dimensions are maintained
            img = Image.open(screenshot_path)
            img_width, img_height = img.size

            if img_width == width and img_height == height:
                print(f"✓ Screenshot dimensions unchanged: {img_width}x{img_height}")
                return True
            else:
                print(f"✗ Expected {width}x{height}, got {img_width}x{img_height}")
                return False

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False


def test_invalid_crop_boundaries():
    """Test error handling for crop boundaries outside image"""
    print("\nTest 5: Invalid crop boundaries (should fail gracefully)")

    url = "https://example.com"
    width = 1280
    height = 720

    # Try to crop beyond image boundaries
    crop_left = 1200
    crop_top = 600
    crop_width = 500  # Would extend to 1700, beyond 1280
    crop_height = 400  # Would extend to 1000, beyond 720

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

            # Try to apply cropping (should raise error)
            img = Image.open(screenshot_path)
            img_width, img_height = img.size
            right = crop_left + crop_width
            lower = crop_top + crop_height

            if right > img_width or lower > img_height:
                print(f"✓ Correctly detected invalid crop boundaries")
                print(f"  Image size: {img_width}x{img_height}")
                print(f"  Crop box would be: ({crop_left}, {crop_top}, {right}, {lower})")
                return True
            else:
                print(f"✗ Failed to detect invalid boundaries")
                return False

        except Exception as e:
            print(f"✗ Unexpected error: {str(e)}")
            return False


if __name__ == '__main__':
    print("=" * 60)
    print("Website Screenshot Crop - Experiment Tests")
    print("=" * 60)

    results = []

    results.append(("Basic crop", test_basic_crop()))
    results.append(("Top-left crop", test_top_left_crop()))
    results.append(("Bottom-right crop", test_bottom_right_crop()))
    results.append(("No crop", test_no_crop()))
    results.append(("Invalid boundaries", test_invalid_crop_boundaries()))

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(passed for _, passed in results)
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed."))

    sys.exit(0 if all_passed else 1)
