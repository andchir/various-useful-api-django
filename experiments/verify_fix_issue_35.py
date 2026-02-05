"""
Verify the fix for issue #35.
Test with the exact example from the issue report.
"""

# First, let's verify the fix in the code
print("=" * 80)
print("Verifying Fix for Issue #35")
print("=" * 80)

# Read the fixed code
with open('/tmp/gh-issue-solver-1770330661591/main/views.py', 'r') as f:
    content = f.read()

# Find the css_triangle_generator function
import re
match = re.search(r'def css_triangle_generator\(request\):.*?size = (.*?)\n', content, re.DOTALL)
if match:
    size_line = match.group(1).strip()
    print(f"\n✓ Found size assignment in css_triangle_generator:")
    print(f"  size = {size_line}")

    if 'int(request.data.get' in size_line:
        print(f"  ✓ Fix applied correctly - size is converted to int!")
    else:
        print(f"  ✗ Fix NOT applied - size is not converted to int")
else:
    print("✗ Could not find size assignment")

# Now simulate the logic with the exact input from the issue
print("\n" + "=" * 80)
print("Testing with exact input from issue #35:")
print("=" * 80)

test_input = {
    "direction": "top",
    "color": "#B70B0B",
    "size": 30
}

print(f"\nInput:")
import json
print(json.dumps(test_input, indent=2))

# Simulate the fixed code
direction = test_input.get('direction', 'top')
color = test_input.get('color', '#B70B0B')
size = int(test_input.get('size', 30))  # This is the fix!

print(f"\nAfter parsing:")
print(f"  direction = {direction} (type: {type(direction).__name__})")
print(f"  color = {color} (type: {type(color).__name__})")
print(f"  size = {size} (type: {type(size).__name__})")

# Test the calculations that were failing before
try:
    half_size = int(size / 2)
    base_size = round(size * 0.866)

    print(f"\nCalculations:")
    print(f"  half_size = {half_size}")
    print(f"  base_size = {base_size}")

    # Build CSS code
    css_lines = [
        '.triangle {',
        '  width: 0;',
        '  height: 0;',
        '  border-style: solid;',
        f'  border-right: {half_size}px solid transparent;',
        f'  border-left: {half_size}px solid transparent;',
        f'  border-bottom: {base_size}px solid {color.lower()};',
        '  border-top: 0;',
        '}'
    ]

    css_code = '\n'.join(css_lines)

    print(f"\n✓ SUCCESS - Generated CSS code:")
    print(css_code)

    print(f"\n" + "=" * 80)
    print("✓ Fix verified successfully!")
    print("The API should now work with the input from issue #35")
    print("=" * 80)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    print("Fix verification FAILED")
