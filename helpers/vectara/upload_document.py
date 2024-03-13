"""Simple example of using the Vectara REST API for uploading files.
"""

import json
import logging
import os
import requests

from helpers.vectara.auth import get_jwt_token

def _get_upload_file_json(id, title, text):
    """ Returns some example JSON file upload data. """
    document = {}
    document["document_id"] = f"{id}"
    # Note that the document ID must be unique for a given corpus
    document["title"] = title
    sections = []
    section = {}
    section["text"] = text
    sections.append(section)
    document["section"] = sections

    return json.dumps(document)

def upload_file(corpus_id: int, doc_id: int, title: str, text: str):
    """ Uploads a file to the corpus.
    Args:
        customer_id: Unique customer ID in vectara platform.
        corpus_id: ID of the corpus to which data needs to be indexed.
        idx_address: Address of the indexing server. e.g., api.vectara.io
        jwt_token: A valid Auth token.

    Returns:
        (response, True) in case of success and returns (error, False) in case of failure.

    """

    post_headers = {
        "Authorization": f"Bearer {get_jwt_token()}"
    }
    response = requests.post(
        f"https://{os.getenv('VECTARA_BASE')}/v1/upload?c={os.getenv('VECTARA_CUSTOMER_ID')}&o={corpus_id}",
        files={"file": ('file.json', _get_upload_file_json(doc_id, title, text), "application/json")},
        verify=True,
        headers=post_headers)

    if response.status_code != 200:
        logging.error("REST upload failed with code %d, reason %s, text %s",
                       response.status_code,
                       response.reason,
                       response.text)
        return response, False
    return response, True