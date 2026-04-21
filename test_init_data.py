#!/usr/bin/env python3
"""Test script to verify initialization data."""

from backend.generators.event_init_data import EVENT_CATEGORIES, EVENT_SUBCATEGORIES, get_total_subcategories


def main():
    print("=" * 60)
    print("Event Attribute System - Initialization Data Verification")
    print("=" * 60)

    total_cats = len(EVENT_CATEGORIES)
    total_subcats = get_total_subcategories()

    print(f"\nTotal Categories: {total_cats}")
    print(f"Total Subcategories: {total_subcats}")

    print("\n" + "=" * 60)
    print("Category Breakdown:")
    print("=" * 60)

    for i, cat in enumerate(EVENT_CATEGORIES, 1):
        code = cat["code"]
        name = cat["name"]
        subcats = EVENT_SUBCATEGORIES.get(code, [])
        print(f"{i:2d}. {name} ({code}): {len(subcats)} subcategories")

    print("\n" + "=" * 60)
    print("Verification:")
    print("=" * 60)

    expected_cats = 40
    expected_min_subcats = 400
    expected_max_subcats = 550

    if total_cats == expected_cats:
        print(f"✓ Categories: {total_cats} (expected: {expected_cats})")
    else:
        print(f"✗ Categories: {total_cats} (expected: {expected_cats})")

    if expected_min_subcats <= total_subcats <= expected_max_subcats:
        print(f"✓ Subcategories: {total_subcats} (expected: {expected_min_subcats}-{expected_max_subcats})")
    else:
        print(f"✗ Subcategories: {total_subcats} (expected: {expected_min_subcats}-{expected_max_subcats})")

    print("\n" + "=" * 60)
    print("Sample Categories and Subcategories:")
    print("=" * 60)

    for cat in EVENT_CATEGORIES[:5]:
        code = cat["code"]
        name = cat["name"]
        subcats = EVENT_SUBCATEGORIES.get(code, [])
        print(f"\n{name}:")
        for sub in subcats[:3]:
            print(f"  - {sub['name']} ({sub['code']})")
        if len(subcats) > 3:
            print(f"  ... and {len(subcats) - 3} more")


if __name__ == "__main__":
    main()
