"""Tests for main.py"""

import os
import sys
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.main import add_to_summary, debug, error, get_input, info, main, process_input, set_output


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_get_input_with_value(self):
        """Test get_input returns value when set."""
        with patch.dict(os.environ, {"INPUT_EXAMPLE_INPUT": "test-value"}):
            assert get_input("example-input") == "test-value"
    
    def test_get_input_without_value(self):
        """Test get_input returns None when not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_input("example-input") is None
    
    def test_get_input_required_missing(self):
        """Test get_input exits when required input is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.exit") as mock_exit:
                get_input("example-input", required=True)
                mock_exit.assert_called_once_with(1)
    
    def test_set_output_with_github_output(self):
        """Test set_output writes to GITHUB_OUTPUT file."""
        with patch.dict(os.environ, {"GITHUB_OUTPUT": "/tmp/output.txt"}):
            with patch("builtins.open", mock_open()) as mock_file:
                set_output("result", "test-value")
                mock_file.assert_called_once_with("/tmp/output.txt", "a")
                mock_file().write.assert_called_once_with("result=test-value\n")
    
    def test_set_output_fallback(self, capsys):
        """Test set_output falls back to console output."""
        with patch.dict(os.environ, {}, clear=True):
            set_output("result", "test-value")
            captured = capsys.readouterr()
            assert "::set-output name=result::test-value" in captured.out
    
    def test_info(self, capsys):
        """Test info message output."""
        info("Test message")
        captured = capsys.readouterr()
        assert "::notice::Test message" in captured.out
    
    def test_error(self, capsys):
        """Test error message output."""
        error("Error message")
        captured = capsys.readouterr()
        assert "::error::Error message" in captured.out
    
    def test_debug_enabled(self, capsys):
        """Test debug message when debug is enabled."""
        with patch.dict(os.environ, {"ACTIONS_STEP_DEBUG": "true"}):
            debug("Debug message")
            captured = capsys.readouterr()
            assert "::debug::Debug message" in captured.out
    
    def test_debug_disabled(self, capsys):
        """Test debug message when debug is disabled."""
        with patch.dict(os.environ, {}, clear=True):
            debug("Debug message")
            captured = capsys.readouterr()
            assert captured.out == ""
    
    def test_add_to_summary(self):
        """Test adding content to job summary."""
        with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": "/tmp/summary.md"}):
            with patch("builtins.open", mock_open()) as mock_file:
                add_to_summary("Test content")
                mock_file.assert_called_once_with("/tmp/summary.md", "a")
                mock_file().write.assert_called_once_with("Test content\n")


class TestProcessInput:
    """Test the main processing function."""
    
    def test_process_input(self):
        """Test process_input returns expected result."""
        result = process_input("test-input")
        assert result == "Processed: test-input"


class TestMain:
    """Test the main function."""
    
    @patch("src.main.get_input")
    @patch("src.main.set_output")
    @patch("src.main.add_to_summary")
    def test_main_success(self, mock_summary, mock_output, mock_input):
        """Test successful execution of main."""
        # Setup mocks
        mock_input.side_effect = lambda name, **kwargs: {
            "example-input": "test-value",
            "github-token": "fake-token"
        }.get(name)
        
        with patch.dict(os.environ, {"GITHUB_CONTEXT": "{}"}):
            # Run main
            main()
        
        # Verify outputs were set
        assert mock_output.call_count == 2
        mock_output.assert_any_call("result", "Processed: test-value")
        mock_output.assert_any_call("status", "success")
        
        # Verify summary was added
        mock_summary.assert_called_once()
    
    @patch("src.main.get_input")
    @patch("sys.exit")
    def test_main_failure(self, mock_exit, mock_input):
        """Test main handles exceptions properly."""
        # Setup mock to raise exception
        mock_input.side_effect = Exception("Test error")
        
        # Run main
        main()
        
        # Verify exit was called
        mock_exit.assert_called_once_with(1)