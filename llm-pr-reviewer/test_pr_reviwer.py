import unittest

# Assuming the function is in a module named pr_reviewer
from pr_reviewer import calculate_positions


class TestCalculatePositions(unittest.TestCase):
    def test_simple_one_line_change(self):
        # Test for a simple one-line change in a GitHub workflow file
        patch_content = """@@ -43,7 +43,7 @@ jobs:
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
-      - uses: nakamasato/github-actions/llm-pr-reviewer@nakamasato-patch-1
+      - uses: nakamasato/github-actions/llm-pr-reviewer@only-comment
         with:
           github_token: ${{ secrets.GITHUB_TOKEN }}
           openai_api_key: ${{ secrets.OPENAI_API_KEY_PR_AGENT }}"""

        # Expected result -
        expected = [{"line_number": 46, "position": 6}]

        # Call the function
        result = calculate_positions(patch_content)

        # Assert the result matches expected values
        self.assertEqual(result, expected)

    def test_multi_line_change(self):
        # Test for a multi-line change
        patch_content = """@@ -10,8 +10,9 @@ def analyze_code(changed_content: str, filename: str):
     # Initialize analysis
     results = []

-    # Process code
-    for line in changed_content.split("\\n"):
+    # Process code with improved handling
+    lines = changed_content.split("\\n")
+    for line in lines:
         # Analysis logic here
         pass
         """

        # Expected result - line_start: 12, line_end: 14
        expected = [
            {"line_number": 13, "position": 7},
            {"line_number": 14, "position": 8},
            {"line_number": 15, "position": 9},
        ]

        # Call the function
        result = calculate_positions(patch_content)

        # Assert the result matches expected values
        self.assertEqual(result, expected)

    def test_multiple_hunks(self):
        # Test with multiple hunks in the patch
        patch_content = """@@ -5,6 +5,7 @@ def foo():
     # First change
     print("hello")
+    print("world")

@@ -20,7 +21,7 @@ def bar():
     # Second change
-    return False
+    return True
     """

        # Expected result should include both hunks
        expected_hunks = [
            {"line_number": 7, "position": 4},  # First hunk, added line
            {"line_number": 22, "position": 9},  # Second hunk, changed line
        ]

        # Call the function
        results = calculate_positions(patch_content)

        # Assert the results match expected values
        self.assertEqual(results, expected_hunks)

    def test_empty_patch(self):
        # Test with an empty patch
        patch_content = ""

        # Expected result - empty or None
        result = calculate_positions(patch_content)

        # Assert the result is empty or None
        self.assertFalse(result)  # Should be empty dict, None, or False

    def test_no_change_patch(self):
        # Test with a patch that has context but no actual changes
        patch_content = """@@ -10,5 +10,5 @@ def analyze_code():
     # This is just context
     # More context
     # Even more context
     # No actual changes
     """

        # Expected result - empty or appropriate indication of no changes
        result = calculate_positions(patch_content)

        # Assert the result indicates no changes
        self.assertFalse(result)  # Should be empty dict, None, or False


if __name__ == "__main__":
    unittest.main()
