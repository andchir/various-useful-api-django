# Playwright Installation Notes

## Python Version Compatibility

Playwright 1.49.1 requires greenlet as a dependency, which currently doesn't have precompiled wheels for Python 3.14.

### Recommended Python Versions
- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13

### Installation Steps

1. Install playwright package:
```bash
pip install playwright==1.49.1
```

2. Install browser binaries (required for headless mode):
```bash
python -m playwright install chromium
```

This downloads the Chromium browser binary that Playwright uses for taking screenshots.

### Production Deployment

For production systems, ensure:
1. Python version is 3.10-3.13 (not 3.14)
2. System has required dependencies for Chromium:
   - On Ubuntu/Debian: `apt-get install libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2`
3. Run `python -m playwright install chromium` after installing the package

### Testing Locally

If you're on Python 3.14, the experiment script won't run until greenlet adds support. The code will work correctly on supported Python versions.

### API Endpoint

Once installed, the API will be available at:
```
POST /api/v1/website_screenshot
```

With JSON body:
```json
{
  "url": "https://example.com",
  "width": 1280,
  "height": 720,
  "full": false
}
```

The response will include a `screenshot_url` field with the URL to the generated screenshot.
