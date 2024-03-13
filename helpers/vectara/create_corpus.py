"""Simple example of using the Vectara REST API for creating a corpus.
"""

import json
import logging
import os
import requests

from helpers.vectara.auth import get_jwt_token

def _get_create_corpus_json(name, description):
    """ Returns a create corpus json. """
    corpus = {}
    corpus["name"] = name
    corpus["description"] = description

    return json.dumps({"corpus":corpus})

def create_corpus(name, description):
    """Create a corpus.
    Args:
        customer_id: Unique customer ID in vectara platform.
        admin_address: Address of the admin server. e.g., api.vectara.io
        jwt_token: A valid Auth token.

    Returns:
        (response, True) in case of success and returns (error, False) in case of failure.
    """

    post_headers = {
        "customer-id": os.getenv("VECTARA_CUSTOMER_ID"),
        "Authorization": f"Bearer {get_jwt_token()}"
    }
    response = requests.post(
        f"https://{os.getenv('VECTARA_BASE')}/v1/create-corpus",
        data=_get_create_corpus_json(name, description),
        verify=True,
        headers=post_headers)

    if response.status_code != 200:
        logging.error("Create Corpus failed with code %d, reason %s, text %s",
                       response.status_code,
                       response.reason,
                       response.text)
        return response, False
    return response, True