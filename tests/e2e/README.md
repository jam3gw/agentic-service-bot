# End-to-End API Tests

This directory contains end-to-end tests for the Agentic Service Bot API endpoints.

## Available Tests

The tests verify the functionality of the following API endpoints:

- `GET /api/customers/{customerId}/devices` - Retrieves a customer's devices
- `PATCH /api/customers/{customerId}/devices/{deviceId}` - Updates a device's state
- `GET /api/capabilities` - Retrieves available service capabilities

## Setting Up Test Data

Before running the tests, you need to set up test data in the database. Use the provided script:

```bash
python tests/e2e/setup_test_data.py
```

This script will:
1. List all available DynamoDB tables
2. Create a test customer with devices in the `dev-customers` table
3. Output the customer and device IDs to use in your tests

After running the script, update the `TEST_CUSTOMER_ID` and `TEST_DEVICE_ID` variables in `test_api_endpoints.py` with the values provided by the script.

## Running the Tests

### Option 1: Using the run_api_tests.py script

The easiest way to run the tests is to use the provided script:

```bash
python tests/e2e/run_api_tests.py
```

This script will run all the tests and provide a summary of the results, showing which endpoints are working correctly and which are failing.

### Option 2: Using pytest

You can also run the tests using pytest:

```bash
pytest tests/e2e/test_api_endpoints.py -v
```

### Option 3: Running individual tests

You can run the test file directly to execute all tests:

```bash
python tests/e2e/test_api_endpoints.py
```

## API Configuration

The tests are configured to use the following API endpoints:

- REST API URL: `https://dehqrpqs4i.execute-api.us-west-2.amazonaws.com/dev`
- WebSocket URL: `wss://ig3bth930d.execute-api.us-west-2.amazonaws.com/dev`

If you need to test against different endpoints, update the `REST_API_URL` and `WEBSOCKET_URL` variables in the `test_api_endpoints.py` file.

## Troubleshooting

If the tests are failing, check the following:

1. Ensure the API is running and accessible
2. Verify that the test data exists in the database
3. Check that the API URLs are correct
4. Examine the error messages for specific issues

### Common Issues

- **"Customer not found" error**: Run the setup script again to create a new test customer and update the IDs in the test file.
- **"Device not found" error**: Ensure the device ID in the test file matches one of the devices created by the setup script.
- **Connection errors**: Verify that the API URLs are correct and the API is running.

## Adding New Tests

To add new tests:

1. Add new test functions to `test_api_endpoints.py`
2. Follow the existing pattern of making API requests and asserting on the responses
3. Update the `run_api_tests.py` script to include your new tests

## Checking Existing Data

If you want to check what data already exists in the database without creating new test data, use:

```bash
python tests/e2e/check_existing_data.py
```

This script will attempt to discover existing customers by trying common customer IDs. 