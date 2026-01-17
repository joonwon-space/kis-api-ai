# Update KIS API Client

## Scope of work
- Update the KIS API client to correctly fetch the balance.
- Improve the login process to use environment variables.
- Clarify the balance response by renaming a field.

## Logic changes
- **`kis_api_backend/app/schemas/__init__.py`**:
    - Made the fields in `LoginRequest` optional to allow them to be sourced from environment variables.
- **`kis_api_backend/app/api/v1/auth.py`**:
    - Updated the `login` function to fetch KIS API credentials from environment variables if they are not provided in the request body.
- **`kis_api_backend/kis_client.py`**:
    - Dynamically set the `tr_id` header in the `get_balance` function based on the `is_simulation` flag.

## Expected impact
- The API will be more secure and convenient to use as credentials can be managed through environment variables.
- The balance inquiry will work correctly for both simulation and real trading.
