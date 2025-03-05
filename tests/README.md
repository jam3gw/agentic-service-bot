# Testing Guidelines

## Directory Structure

All tests for the agentic-service-bot project must be placed in this `tests` directory, following this simplified structure:

```
tests/
└── e2e/                  # End-to-end tests for complete workflows
```

## Testing Rules

1. **All test files must be placed in the `tests` directory**
   - No test files should be created in the main application directories
   - This ensures consistent test discovery and organization

2. **Test file naming**
   - All test files must be named with the prefix `test_`
   - Example: `test_user_workflow.py`

3. **Test organization**
   - End-to-end tests go in the `e2e/` directory
   - Additional test categories can be added as the project evolves

4. **Testing approach**
   - Tests should use real dependencies whenever possible
   - End-to-end tests should never use mocks
   - Each test file should be self-contained and not rely on external fixtures

## Running Tests

To run all tests:
```bash
pytest tests/
```

To run end-to-end tests:
```bash
pytest tests/e2e/
```

To run a specific test file:
```bash
pytest tests/e2e/test_user_workflow.py
``` 