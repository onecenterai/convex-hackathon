"""Utility functions for interacting with Vectara over REST.
"""

import os
from authlib.integrations.requests_client import OAuth2Session

def get_jwt_token():
    """Connect to the server and get a JWT token."""
    token_endpoint = os.getenv('VECTARA_AUTH_URL')
    session = OAuth2Session(
        os.getenv('VECTARA_APP_ID'), os.getenv('VECTARA_APP_SECRET'), scope="")
    token = session.fetch_token(token_endpoint, grant_type="client_credentials")
    return token["access_token"]