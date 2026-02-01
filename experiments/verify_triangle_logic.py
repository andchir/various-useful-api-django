"""
Simple verification of triangle generator logic
"""

def generate_triangle_css(direction, color, size):
    """
    Simulate the triangle generation logic
    """
    # Calculate dimensions for equilateral triangle
    half_size = int(size / 2)
    base_size = round(size * 0.866)

    # Build CSS code based on direction
    css_lines = [
        '.triangle {',
        '  width: 0;',
        '  height: 0;',
        '  border-style: solid;'
    ]

    if direction == 'top':
        css_lines.extend([
            f'  border-right: {half_size}px solid transparent;',
            f'  border-left: {half_size}px solid transparent;',
            f'  border-bottom: {base_size}px solid {color.lower()};',
            '  border-top: 0;'
        ])
    elif direction == 'right':
        css_lines.extend([
            f'  border-top: {half_size}px solid transparent;',
            f'  border-bottom: {half_size}px solid transparent;',
            f'  border-left: {base_size}px solid {color.lower()};',
            '  border-right: 0;'
        ])
    elif direction == 'bottom':
        css_lines.extend([
            f'  border-right: {half_size}px solid transparent;',
            f'  border-left: {half_size}px solid transparent;',
            f'  border-top: {base_size}px solid {color.lower()};',
            '  border-bottom: 0;'
        ])
    elif direction == 'left':
        css_lines.extend([
            f'  border-top: {half_size}px solid transparent;',
            f'  border-bottom: {half_size}px solid transparent;',
            f'  border-right: {base_size}px solid {color.lower()};',
            '  border-left: 0;'
        ])

    css_lines.append('}')
    return '\n'.join(css_lines)


# Test cases from the issue
test_cases = {
    'top': {
        'direction': 'top',
        'color': '#B70B0B',
        'size': 30,
        'expected': [
            'border-right: 15px solid transparent;',
            'border-left: 15px solid transparent;',
            'border-bottom: 26px solid #b70b0b;',
            'border-top: 0;'
        ]
    },
    'right': {
        'direction': 'right',
        'color': '#B70B0B',
        'size': 30,
        'expected': [
            'border-top: 15px solid transparent;',
            'border-bottom: 15px solid transparent;',
            'border-left: 26px solid #b70b0b;',
            'border-right: 0;'
        ]
    },
    'bottom': {
        'direction': 'bottom',
        'color': '#B70B0B',
        'size': 30,
        'expected': [
            'border-right: 15px solid transparent;',
            'border-left: 15px solid transparent;',
            'border-top: 26px solid #b70b0b;',
            'border-bottom: 0;'
        ]
    },
    'left': {
        'direction': 'left',
        'color': '#B70B0B',
        'size': 30,
        'expected': [
            'border-top: 15px solid transparent;',
            'border-bottom: 15px solid transparent;',
            'border-right: 26px solid #b70b0b;',
            'border-left: 0;'
        ]
    }
}

print("Verifying CSS Triangle Generator Logic\n")
print("=" * 80)

all_passed = True

for name, test in test_cases.items():
    print(f"\nTest: {name.upper()} triangle")
    print(f"Input: direction={test['direction']}, color={test['color']}, size={test['size']}")

    # Generate CSS
    css_code = generate_triangle_css(test['direction'], test['color'], test['size'])

    print(f"\nGenerated CSS:\n{css_code}")

    # Verify expected lines
    missing_lines = []
    for expected_line in test['expected']:
        if expected_line not in css_code:
            missing_lines.append(expected_line)

    if missing_lines:
        print(f"\n✗ FAILED: Missing expected lines:")
        for line in missing_lines:
            print(f"  - {line}")
        all_passed = False
    else:
        print("\n✓ PASSED: All expected lines present")

print("\n" + "=" * 80)
if all_passed:
    print("✓ All tests PASSED!")
    exit(0)
else:
    print("✗ Some tests FAILED")
    exit(1)
