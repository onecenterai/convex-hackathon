from flask import Blueprint, request, jsonify

from app.route_guard import auth_required

from app.upload.model import *
from app.upload.schema import *
from app.agent.model import Agent
from app.partner.model import Partner
from flask import g

import jwt
import json

from app import app
from app.user.model import User

from helpers.upload import (do_upload, remove_upload,
                            #pinecone_upload_file, 
                            #create_corpus, 
                            #vectara_upload, 
                            #_prep_upload_file_json,
                            #create_corpus_api_key
                            )

from pyconvex.pyconvex_main import upload_document

import requests

bp = Blueprint('upload', __name__, url_prefix='/upload')

@bp.post('/add')
@auth_required()
def add():
    file = request.files.get('file')
    p = Partner.get_by_id(g.user.agent.partner_id)
    d = f'Document for {p.name} uploaded by {g.user.name}'
    if file:
        res = upload_document(file=file, name=f'{p.name} document', description=d, company_name=p.name)
        if res:
             return {'message': 'File uploaded successfully'}
        return {'error': 'Error uploading file'}
    return {'error': 'No file to upload'}


@bp.delete('/remove/<file_to_remove>')
@auth_required()
def remove(file_to_remove):
    if remove_upload(file_to_remove):
        return {'success': 'File removed'}
    return {'error': 'Error removing file'}

@bp.put('/update/<file_to_update>')
@auth_required()
def update(file_to_update):
    file = request.files.get('file')
    if file:
        url = do_upload(file, file_to_update)
        if url:
            return {'url': url, 'message': 'File updated successfully'}
        return {'error': 'Error uploading file'}
    return {'error': 'No file to update'}

@bp.patch('/update/<file_to_update>')
@auth_required()
def update_file_content(file_to_update):
    content = request.form.get('content')
    if content:
        url = do_upload(content, file_to_update)
        if url:
            return {'url': url, 'message': 'File content updated successfully'}
        return {'error': 'Error updating file content'}
    return {'error': 'No file content to update'}

