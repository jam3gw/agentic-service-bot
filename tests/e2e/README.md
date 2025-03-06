# End-to-End API Tests

This directory contains end-to-end tests for the Agentic Service Bot API.

### Available Tests

The following test files are available:

- `test_capabilities_api.py`: Tests the capabilities endpoint
- `test_customer_api.py`: Tests the customer endpoints
- `test_devices_api.py`: Tests the device endpoints
- `test_chat_api.py`: Tests the chat endpoints

### Test Data Setup

The tests use automated test data setup via pytest fixtures. The fixtures are defined in `conftest.py` and handle:

1. Creating a unique test customer with devices before tests run
2. Providing test data (customer ID, device IDs) to test functions
3. Cleaning up test data after tests complete

This approach ensures that:
- Each test run uses fresh, isolated test data
- Tests don't rely on hardcoded IDs that might become invalid
- Test data is properly cleaned up after tests finish

#### How to Use the Test Data Fixture

To use the test data in your tests, simply add the `test_data` parameter to your test function:

```python
def test_example(test_data):
    # Access test data
    customer_id = test_data['customer_id']
    device_id = test_data['device_id']
    
    # Use the IDs in your test
    response = requests.get(f"{REST_API_URL}/customers/{customer_id}/devices")
    # ...
```

### Running Tests

You can run the tests using pytest:

```bash
# Run all tests
python -m pytest tests/e2e/

# Run a specific test file
python -m pytest tests/e2e/test_devices_api.py

# Run a specific test
python -m pytest tests/e2e/test_devices_api.py::test_get_devices

# Run with verbose output
python -m pytest tests/e2e/ -v
```

### Current Status

- ✅ Capabilities API: Working
- ✅ Customer API: Working
- ✅ Devices API: Working
- ❌ Chat API: Returning 502 Bad Gateway

### Troubleshooting

If the tests are failing, check the following:

1. Make sure the API is deployed and accessible
2. Check that the API URL in the test files is correct
3. Verify that your AWS credentials are set up correctly
4. Check the CloudWatch logs for the API

### Manual Test Data Setup

If you need to manually set up test data, you can use the `setup_test_data.py` script:

```bash
python tests/e2e/setup_test_data.py
```

This will create a test customer with devices in the DynamoDB table and print the customer ID and device IDs.

To clean up test data, you can use the `cleanup_test_data.py` script:

```bash
python tests/e2e/cleanup_test_data.py
```

### Checking Existing Data

To check what test data already exists in the database, you can use the `check_existing_data.py` script:

```bash
python tests/e2e/check_existing_data.py
```

This will print all customers in the database with their devices.

## API Configuration

The tests are configured to use the following API endpoint:

- REST API URL: `https://k4w64ym45e.execute-api.us-west-2.amazonaws.com/dev/api`

If you need to test against a different endpoint, update the `REST_API_URL` variable in the `test_devices_api.py` file or use the `--url` parameter when running the tests.

## Cleaning Up Test Data

The test fixture automatically cleans up test data after tests are complete. If you need to manually clean up test data, you can use the provided script:

```bash
# Delete a test customer
python tests/e2e/cleanup_test_data.py --customer-id=test-customer-id

# Delete a test customer and all their messages
python tests/e2e/cleanup_test_data.py --customer-id=test-customer-id --delete-messages

# Skip confirmation prompts
python tests/e2e/cleanup_test_data.py --customer-id=test-customer-id --force
```

## Troubleshooting

If the tests are failing, check the following:

1. Ensure the API is running and accessible
2. Verify that the test data exists in the database
3. Check that the API URL is correct
4. Examine the error messages for specific issues

### Common Issues

- **502 Bad Gateway errors**: Currently, the chat history and chat endpoints are returning 502 errors. This is a known issue with the current API deployment.
- **"Customer not found" error**: This could indicate an issue with the test data setup. Check the output of the test run to see if the test customer was created successfully.
- **"Device not found" error**: Ensure the device ID being used matches one of the devices created by the test fixture.
- **Connection errors**: Verify that the API URL is correct and the API is running.

## Adding New Tests

To add new tests:

1. Create a new test file or add test methods to an existing file
2. Use the `test_data` fixture to access test customer and device IDs
3. Follow the existing pattern of making API requests and asserting on the responses

## Checking Existing Data

If you want to check what data already exists in the database without creating new test data, use:

```bash
python tests/e2e/check_existing_data.py
```

This script will attempt to discover existing customers by trying common customer IDs.

## API Troubleshooting Best Practices

When encountering 502 Bad Gateway errors or other API issues during testing:

1. **Don't immediately change API endpoints**: 
   - 502 errors are typically caused by server-side issues, not by using the wrong endpoint
   - Changing the API endpoint won't fix underlying implementation issues

2. **Check CloudWatch logs**:
   - Use `aws logs describe-log-groups` and `aws logs get-log-events` to check Lambda function logs
   - Look for error messages, exceptions, or timeouts in the logs

3. **Verify Lambda function configuration**:
   - Check environment variables required by the Lambda function
   - Ensure IAM roles and permissions are correctly set up
   - Verify timeout settings are appropriate for the function's workload

4. **Examine DynamoDB access patterns**:
   - Confirm that the Lambda function is using the correct table names
   - Verify that the query patterns match the table's key structure
   - Check for missing GSIs (Global Secondary Indexes) that might be required

5. **Test API Gateway directly**:
   - Use the API Gateway console to test the endpoint directly
   - This can help isolate whether the issue is in the Lambda function or API Gateway configuration

6. **Incrementally fix issues**:
   - Address one issue at a time and test after each change
   - Document each fix and its impact on the API behavior

Remember that 502 errors indicate that the server received an invalid response from an upstream server, which often points to issues in the Lambda function implementation or configuration. 