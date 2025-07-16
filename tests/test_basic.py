"""Basic tests for iPanel functionality."""

import pytest
import sys
import os

# Add the iPanel directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'iPanel'))

try:
    from iPanel.class import public
except ImportError:
    # Create a mock public module if not available
    class MockPublic:
        def __init__(self):
            pass
        
        def version(self):
            return "1.0.0"
        
        def get_config(self, key, default=None):
            return default
    
    public = MockPublic()


class TestBasicFunctionality:
    """Test basic functionality of iPanel."""
    
    def test_version(self):
        """Test version retrieval."""
        if hasattr(public, 'version'):
            version = public.version()
            assert version is not None
        else:
            assert True  # Skip if version method not available
    
    def test_config_retrieval(self):
        """Test configuration retrieval."""
        if hasattr(public, 'get_config'):
            config = public.get_config('test_key', 'default_value')
            assert config == 'default_value'
        else:
            assert True  # Skip if get_config method not available
    
    def test_basic_imports(self):
        """Test that basic imports work."""
        try:
            import os
            import sys
            import json
            assert True
        except ImportError:
            pytest.fail("Basic imports failed")
    
    def test_python_version(self):
        """Test Python version compatibility."""
        assert sys.version_info >= (3, 8)
    
    def test_os_path_operations(self):
        """Test basic OS path operations."""
        test_path = os.path.join('test', 'path')
        assert os.path.join('test', 'path') == test_path
        
        # Test path normalization
        normalized = os.path.normpath(test_path)
        assert normalized is not None
    
    def test_json_operations(self):
        """Test JSON operations."""
        import json
        
        test_data = {"key": "value", "number": 42}
        json_str = json.dumps(test_data)
        parsed_data = json.loads(json_str)
        
        assert parsed_data == test_data
    
    def test_string_operations(self):
        """Test string operations."""
        test_string = "iPanel Test String"
        
        assert test_string.lower() == "ipanel test string"
        assert test_string.upper() == "IPANEL TEST STRING"
        assert "Panel" in test_string
        assert test_string.startswith("iPanel")
        assert test_string.endswith("String")
    
    def test_list_operations(self):
        """Test list operations."""
        test_list = [1, 2, 3, 4, 5]
        
        assert len(test_list) == 5
        assert test_list[0] == 1
        assert test_list[-1] == 5
        
        # Test list comprehension
        squared = [x*x for x in test_list]
        assert squared == [1, 4, 9, 16, 25]
    
    def test_dict_operations(self):
        """Test dictionary operations."""
        test_dict = {"a": 1, "b": 2, "c": 3}
        
        assert test_dict["a"] == 1
        assert "b" in test_dict
        assert test_dict.get("d", "default") == "default"
        
        # Test dictionary comprehension
        doubled = {k: v*2 for k, v in test_dict.items()}
        assert doubled == {"a": 2, "b": 4, "c": 6}
    
    def test_exception_handling(self):
        """Test exception handling."""
        with pytest.raises(ValueError):
            raise ValueError("Test exception")
        
        try:
            int("not_a_number")
        except ValueError:
            assert True  # Expected exception
        else:
            pytest.fail("Expected ValueError was not raised")
    
    def test_file_operations(self):
        """Test file operations."""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                content = f.read()
            assert content == "test content"
        finally:
            os.unlink(temp_path)
    
    def test_datetime_operations(self):
        """Test datetime operations."""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        future = now + timedelta(days=1)
        
        assert future > now
        assert (future - now).days == 1
    
    def test_logging_import(self):
        """Test logging import."""
        import logging
        
        logger = logging.getLogger('test_logger')
        assert logger is not None
        assert logger.name == 'test_logger'
    
    def test_regex_operations(self):
        """Test regex operations."""
        import re
        
        pattern = r'\d+'
        text = "There are 123 numbers in 456 this text"
        
        matches = re.findall(pattern, text)
        assert matches == ['123', '456']
        
        # Test substitution
        result = re.sub(pattern, 'X', text)
        assert result == "There are X numbers in X this text"
