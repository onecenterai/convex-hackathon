"""Simple example of using the Vectara REST API for searching a corpus.
"""

import json
import logging
import os
import requests

from helpers.vectara.auth import get_jwt_token

def _get_query_json(customer_id: int, corpus_id: int, query_value: str):
    """ Returns a query json. """
    query = {}
    query_obj = {}

    query_obj["query"] = query_value
    query_obj["num_results"] = 10

    corpus_key = {}
    corpus_key["customer_id"] = customer_id
    corpus_key["corpus_id"] = corpus_id

    query_obj["corpus_key"] = [ corpus_key ]
    query_obj["summary"] = [
        {
          "maxSummarizedResults": 5,
          "responseLang": "auto"
        }
      ]
    query["query"] = [ query_obj ]
    return json.dumps(query)


def query(corpus_id: int, query: str):
    """This method queries the data.
    Args:
        customer_id: Unique customer ID in vectara platform.
        corpus_id: ID of the corpus to which data needs to be indexed.
        query_address: Address of the querying server. e.g., api.vectara.io
        jwt_token: A valid Auth token.

    Returns:
        (response, True) in case of success and returns (error, False) in case of failure.

    """
    post_headers = {
        "customer-id": os.getenv("VECTARA_CUSTOMER_ID"),
        "Authorization": f"Bearer {get_jwt_token()}"
    }


    response = requests.post(
        f"https://{os.getenv('VECTARA_BASE')}/v1/query",
        data=_get_query_json(os.getenv('VECTARA_CUSTOMER_ID'), corpus_id, query),
        verify=True,
        headers=post_headers)

    if response.status_code != 200:
        logging.error("Query failed with code %d, reason %s, text %s",
                       response.status_code,
                       response.reason,
                       response.text)
        return response, False
    return response, True