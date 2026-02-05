"""
Simple test to demonstrate the type error in css_triangle_generator.

The problem: request.data.get('size', 30) can return different types
depending on how the data is parsed.
"""

print("=" * 80)
print("Testing the Type Error in css_triangle_generator")
print("=" * 80)

# Simulate the problematic scenario
print("\n1. Testing with integer value (should work):")
size = 30  # This is what we expect
try:
    half_size = int(size / 2)
    base_size = round(size * 0.866)
    print(f"   size = {size} (type: {type(size).__name__})")
    print(f"   half_size = {half_size}")
    print(f"   base_size = {base_size}")
    print("   ✓ SUCCESS")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

print("\n2. Testing with string value (will fail):")
size = "30"  # This is what causes the error
try:
    half_size = int(size / 2)  # This line will fail!
    base_size = round(size * 0.866)
    print(f"   size = {size} (type: {type(size).__name__})")
    print(f"   half_size = {half_size}")
    print(f"   base_size = {base_size}")
    print("   ✓ SUCCESS")
except Exception as e:
    print(f"   size = {size} (type: {type(size).__name__})")
    print(f"   ✗ ERROR: {e}")
    print(f"   This is the exact error from issue #35!")

print("\n3. Testing the fix - convert to int first:")
size = "30"  # Even if it's a string
try:
    size = int(size)  # Convert to int first
    half_size = int(size / 2)
    base_size = round(size * 0.866)
    print(f"   size = {size} (type: {type(size).__name__})")
    print(f"   half_size = {half_size}")
    print(f"   base_size = {base_size}")
    print("   ✓ SUCCESS - Fix works!")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

print("\n4. Testing with invalid value (should handle gracefully):")
size = "abc"
try:
    size = int(size)
    half_size = int(size / 2)
    base_size = round(size * 0.866)
    print(f"   ✓ SUCCESS")
except ValueError as e:
    print(f"   ✗ ValueError: {e}")
    print(f"   This should be caught and return proper error message")

print("\n" + "=" * 80)
print("Conclusion:")
print("- The error occurs when 'size' is a string")
print("- Fix: Convert size to int explicitly before using it")
print("- Also need to validate and handle ValueError for non-numeric inputs")
print("=" * 80)
