#!/usr/bin/env python3
"""
Example demonstrating persistent mode for external scripts processing individual files.

This example shows how to use SVK-XMP's persistent mode when your external script
loops through files and processes them individually. This is much faster than
creating a new ExifTool process for each file.

Performance improvement: typically 2-3x faster for processing many files.
"""

import os
import time
from pathlib import Path
from svk_xmp.core.metadata_processor import MetadataProcessor


def find_image_files(directory, max_files=15):
    """Find image files in directory for testing."""
    image_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.tiff', '.tif', '.png')):
                image_files.append(os.path.join(root, file))
                if len(image_files) >= max_files:
                    return image_files
    return image_files


def traditional_approach(image_files):
    """Traditional approach - new processor for each file (slow)."""
    print("🐌 Traditional approach (creates new process each time):")
    start_time = time.time()
    
    results = []
    for i, image_file in enumerate(image_files, 1):
        processor = MetadataProcessor()  # New ExifTool process each time!
        try:
            xmp_xml = processor.extract_xmp_xml(image_file)
            fields = processor.parse_xmp_fields(xmp_xml)
            
            # Your processing logic here
            if fields.get('title'):
                results.append(f"File {i}: {fields['title']}")
            elif fields.get('description'):
                results.append(f"File {i}: {fields['description'][:50]}...")
            else:
                results.append(f"File {i}: No title/description")
                
        except Exception as e:
            results.append(f"File {i}: Error - {e}")
    
    elapsed = time.time() - start_time
    print(f"   Time: {elapsed:.2f} seconds")
    print(f"   Files processed: {len(results)}")
    return elapsed, results


def persistent_approach_context_manager(image_files):
    """Persistent approach using context manager (recommended)."""
    print("🚀 Persistent approach with context manager:")
    start_time = time.time()
    
    results = []
    # Single ExifTool process for all files - much faster!
    with MetadataProcessor(persistent=True) as processor:
        for i, image_file in enumerate(image_files, 1):
            try:
                xmp_xml = processor.extract_xmp_xml(image_file)  # Fast!
                fields = processor.parse_xmp_fields(xmp_xml)
                
                # Your processing logic here
                if fields.get('title'):
                    results.append(f"File {i}: {fields['title']}")
                elif fields.get('description'):
                    results.append(f"File {i}: {fields['description'][:50]}...")
                else:
                    results.append(f"File {i}: No title/description")
                    
            except Exception as e:
                results.append(f"File {i}: Error - {e}")
    # Automatic cleanup when exiting context manager
    
    elapsed = time.time() - start_time
    print(f"   Time: {elapsed:.2f} seconds")
    print(f"   Files processed: {len(results)}")
    return elapsed, results


def persistent_approach_manual_control(image_files):
    """Persistent approach using manual control."""
    print("⚙️  Persistent approach with manual control:")
    start_time = time.time()
    
    results = []
    processor = MetadataProcessor()
    processor.start_persistent_mode()  # Start persistent ExifTool process
    
    try:
        for i, image_file in enumerate(image_files, 1):
            try:
                xmp_xml = processor.extract_xmp_xml(image_file)  # Fast!
                fields = processor.parse_xmp_fields(xmp_xml)
                
                # Your processing logic here
                if fields.get('title'):
                    results.append(f"File {i}: {fields['title']}")
                elif fields.get('description'):
                    results.append(f"File {i}: {fields['description'][:50]}...")
                else:
                    results.append(f"File {i}: No title/description")
                    
            except Exception as e:
                results.append(f"File {i}: Error - {e}")
    finally:
        processor.stop_persistent_mode()  # Important: cleanup
    
    elapsed = time.time() - start_time
    print(f"   Time: {elapsed:.2f} seconds")
    print(f"   Files processed: {len(results)}")
    return elapsed, results


def main():
    """Demonstrate the performance difference between approaches."""
    print("SVK-XMP Persistent Mode Example")
    print("=" * 40)
    print()
    
    # Find test images (adjust path as needed)
    test_dir = "bildexempel"
    if not os.path.exists(test_dir):
        print(f"❌ Test directory '{test_dir}' not found!")
        print("   Please run this script from the project root directory.")
        print("   Or adjust the test_dir variable to point to your images.")
        return
    
    image_files = find_image_files(test_dir)
    if not image_files:
        print(f"❌ No image files found in '{test_dir}'!")
        return
    
    print(f"📁 Processing {len(image_files)} image files")
    print()
    
    # Compare all approaches
    time1, _ = traditional_approach(image_files)
    print()
    time2, _ = persistent_approach_context_manager(image_files)
    print()
    time3, _ = persistent_approach_manual_control(image_files)
    print()
    
    # Show performance improvement
    speedup_context = time1 / time2 if time2 > 0 else 0
    speedup_manual = time1 / time3 if time3 > 0 else 0
    
    print("📊 Performance Results:")
    print(f"   Context manager: {speedup_context:.1f}x faster ({time1-time2:.2f}s saved)")
    print(f"   Manual control:  {speedup_manual:.1f}x faster ({time1-time3:.2f}s saved)")
    print()
    print("💡 Recommendation:")
    print("   Use persistent mode when processing multiple files individually.")
    print("   The context manager approach is recommended for automatic cleanup.")


# Example of how you might use this in your own script
def your_external_script_example():
    """Example showing how to integrate persistent mode in your own script."""
    
    # Your file discovery logic
    my_image_files = find_image_files("bildexempel", max_files=5)
    
    print("Example: Your external script with persistent mode")
    print("-" * 50)
    
    # Process files with persistent mode
    with MetadataProcessor(persistent=True) as processor:
        for image_file in my_image_files:
            # Extract XMP data
            xmp_xml = processor.extract_xmp_xml(image_file)
            fields = processor.parse_xmp_fields(xmp_xml)
            
            # Your custom processing logic here
            print(f"Processing: {Path(image_file).name}")
            if fields.get('title'):
                print(f"  Title: {fields['title']}")
            if fields.get('creator'):
                print(f"  Creator: {fields['creator']}")
            if fields.get('keywords'):
                print(f"  Keywords: {fields['keywords']}")
            print()
            
            # You could save to database, modify files, generate reports, etc.


if __name__ == "__main__":
    main()
    print()
    your_external_script_example()