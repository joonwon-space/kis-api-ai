# Create Test Code

## Scope of work
- Create test code for the KIS API client.
- The test code will cover the `login` and `get_balance` functions.

## Logic changes
- **`kis_api_backend/tests/test_kis_client.py`**:
    - Create a new test file.
    - Add a test case for successful login.
    - Add a test case for successful balance inquiry.
    - Add a test case for balance inquiry without login.
    - Add a test case for login with invalid credentials.

## Expected impact
- The test code will ensure the KIS API client is working as expected.
- It will help to prevent regressions in the future.
