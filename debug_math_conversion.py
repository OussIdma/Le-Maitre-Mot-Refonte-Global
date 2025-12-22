#!/usr/bin/env python3
"""
Debug script to test LaTeX to MathML conversion directly
"""

import sys
sys.path.append('/app/backend')

from curriculum_data import process_math_content_for_pdf

def test_conversion():
    print("🔍 DEBUGGING LaTeX to MathML Conversion")
    print("="*60)
    
    # Test cases that might be causing the issue
    test_cases = [
        "Étant données les fractions \\frac{3}{4} et \\frac{5}{6}. Calculez la somme de ces deux fractions.",
        "Simplifiez la fraction \\frac{28}{42}.",
        "Calculer \\frac{7}{8} + \\frac{3}{4}",
        "Résoudre \\frac{2x}{5} = \\frac{3}{10}",
        "Expression avec 7 de 8 plus 3 par 4",  # Broken format
        "Calculer 715 de 45 et 23 par 910"  # User's reported issue
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}:")
        print(f"Input:  {test_case}")
        
        try:
            result = process_math_content_for_pdf(test_case)
            print(f"Output: {result}")
            
            # Check if conversion happened
            if result != test_case:
                print("✅ Conversion occurred")
                if '<math' in result:
                    print("✅ MathML tags found")
                else:
                    print("⚠️  Conversion occurred but no MathML tags")
            else:
                print("❌ No conversion occurred")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("🔍 TESTING SPECIFIC PATTERNS")
    print("="*60)
    
    # Test the specific patterns that might be causing issues
    patterns_to_test = [
        "\\frac{7}{8}",
        "\\frac{715}{45}",
        "\\frac{23}{910}",
        "7 de 8",
        "715 de 45",
        "23 par 910"
    ]
    
    for pattern in patterns_to_test:
        print(f"\n🔍 Testing pattern: {pattern}")
        try:
            result = process_math_content_for_pdf(pattern)
            print(f"Result: {result}")
            if result != pattern:
                print("✅ Pattern was processed")
            else:
                print("❌ Pattern was not processed")
        except Exception as e:
            print(f"❌ Error processing pattern: {e}")

if __name__ == "__main__":
    test_conversion()