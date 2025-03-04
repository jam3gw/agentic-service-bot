# Unit Tests

This directory contains unit tests for the Agentic Service Bot project. Unit tests focus on testing individual components and functions in isolation.

## Test Files

- `test_request_analyzer.py`: Tests for the request analyzer component
- `test_customer.py`: Tests for the customer model

## Running Unit Tests

To run all unit tests:

```bash
python -m unittest discover -s tests/unit
```

Or using pytest:

```bash
pytest tests/unit/
```

To run a specific test file:

```bash
python -m unittest tests/unit/test_request_analyzer.py
```

Or using pytest:

```bash
pytest tests/unit/test_request_analyzer.py
```

## Writing Unit Tests

When writing unit tests, follow these guidelines:

1. Test one function or method at a time
2. Mock external dependencies
3. Use descriptive test method names that explain what is being tested
4. Include docstrings explaining the purpose of the test
5. Follow the Arrange-Act-Assert pattern
6. Use appropriate assertions for the expected outcomes

Example:

```python
def test_identify_request_type_device_relocation(self):
    """Test that device relocation requests are correctly identified.
    
    This test ensures the request analyzer can properly categorize
    requests related to moving devices to different locations.
    """
    # Arrange
    request_text = "Move my smart speaker to the bedroom"
    
    # Act
    request_type = RequestAnalyzer.identify_request_type(request_text)
    
    # Assert
    self.assertEqual(request_type, "device_relocation")
```

## Dependencies

Unit tests should have minimal dependencies and should not require external services or resources. Any external dependencies should be mocked. 