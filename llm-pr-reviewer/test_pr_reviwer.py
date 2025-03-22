import unittest

# Assuming the function is in a module named pr_reviewer
from pr_reviewer import extract_patch_changes


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

        # Expected result based on the updated function
        expected = [
            {
                "old_start_line": 43,
                "old_end_line": 49,
                "new_start_line": 43,
                "new_end_line": 49
            }
        ]

        # Call the function
        result = extract_patch_changes(patch_content)

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

        # Expected result with updated format
        expected = [
            {
                "old_start_line": 10,
                "old_end_line": 17,
                "new_start_line": 10,
                "new_end_line": 18
            }
        ]

        # Call the function
        result = extract_patch_changes(patch_content)

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

        # Expected result should include both hunks with the updated format
        expected = [
            {
                "old_start_line": 5,
                "old_end_line": 10,
                "new_start_line": 5,
                "new_end_line": 11
            },
            {
                "old_start_line": 20,
                "old_end_line": 26,
                "new_start_line": 21,
                "new_end_line": 27
            }
        ]

        # Call the function
        results = extract_patch_changes(patch_content)

        # Assert the results match expected values
        self.assertEqual(results, expected)

    def test_empty_patch(self):
        # Test with an empty patch
        patch_content = ""

        # Expected result - empty list
        result = extract_patch_changes(patch_content)

        # Assert the result is an empty list
        self.assertEqual(result, [])

    def test_no_change_patch(self):
        # Test with a patch that has context but no actual changes
        patch_content = """@@ -10,5 +10,5 @@ def analyze_code():
     # This is just context
     # More context
     # Even more context
     # No actual changes
     """

        # Expected result - a list with one hunk info
        expected = [
            {
                "old_start_line": 10,
                "old_end_line": 14,
                "new_start_line": 10,
                "new_end_line": 14
            }
        ]

        # Call the function
        result = extract_patch_changes(patch_content)

        # Assert the result matches expected values
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
