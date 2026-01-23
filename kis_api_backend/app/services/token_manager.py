import json
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Manages KIS API access tokens with caching and automatic renewal.

    Tokens are stored in a JSON file to persist across server restarts.
    The manager automatically renews tokens when they expire.
    """

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        base_url: str,
        token_file: str = "token.json"
    ):
        """
        Initialize the TokenManager.

        Args:
            app_key: KIS API application key
            app_secret: KIS API application secret
            base_url: KIS API base URL
            token_file: Path to the token storage file
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url
        self.token_file = Path(token_file)
        self._token_data: Optional[Dict[str, Any]] = None

    def get_valid_token(self) -> str:
        """
        Get a valid access token, automatically renewing if expired.

        Returns:
            str: A valid access token

        Raises:
            Exception: If token retrieval fails
        """
        # Try to load existing token from file
        if self._token_data is None:
            self._load_token()

        # Check if token is valid
        if self._is_token_valid():
            logger.info("Using cached token (still valid)")
            return self._token_data["access_token"]

        # Token expired or doesn't exist, request new one
        logger.info("Token expired or not found, requesting new token")
        self._request_new_token()
        return self._token_data["access_token"]

    def _is_token_valid(self) -> bool:
        """
        Check if the current token is still valid.

        Returns:
            bool: True if token exists and hasn't expired
        """
        if self._token_data is None:
            return False

        if "expires_at" not in self._token_data:
            return False

        expires_at = datetime.fromisoformat(self._token_data["expires_at"])
        # Add 60 second buffer to avoid using token at the edge of expiration
        return datetime.now() < (expires_at - timedelta(seconds=60))

    def _request_new_token(self) -> None:
        """
        Request a new access token from KIS API.

        Raises:
            Exception: If token request fails
        """
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }
        url = f"{self.base_url}/oauth2/tokenP"

        try:
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=body)
                response.raise_for_status()
                data = response.json()

                # Calculate expiration time (KIS tokens are valid for 24 hours)
                expires_in = data.get("expires_in", 86400)  # Default 24 hours in seconds
                expires_at = datetime.now() + timedelta(seconds=expires_in)

                self._token_data = {
                    "access_token": data["access_token"],
                    "token_type": data.get("token_type", "Bearer"),
                    "expires_in": expires_in,
                    "expires_at": expires_at.isoformat(),
                }

                self._save_token()
                logger.info(f"New token obtained, expires at {expires_at}")

        except httpx.HTTPError as e:
            logger.error(f"Failed to get access token: {e}")
            raise Exception(f"Failed to get access token: {e}")

    def _save_token(self) -> None:
        """Save token data to file."""
        try:
            with open(self.token_file, "w") as f:
                json.dump(self._token_data, f, indent=2)
            logger.debug(f"Token saved to {self.token_file}")
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
            # Don't raise - we can still use the token in memory

    def _load_token(self) -> None:
        """Load token data from file if it exists."""
        if not self.token_file.exists():
            logger.debug("Token file does not exist")
            return

        try:
            with open(self.token_file, "r") as f:
                self._token_data = json.load(f)
            logger.debug(f"Token loaded from {self.token_file}")
        except Exception as e:
            logger.warning(f"Failed to load token from file: {e}")
            self._token_data = None

    def clear_token(self) -> None:
        """Clear cached token data and delete token file."""
        self._token_data = None
        if self.token_file.exists():
            self.token_file.unlink()
            logger.info("Token file deleted")
