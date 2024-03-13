from flask import Blueprint, request, jsonify

from app.route_guard import auth_required

from app.upload.model import *
from app.upload.schema import *
from app.agent.model import Agent
from app.partner.model import Partner

import jwt
import json

from app import app
from app.user.model import User

from helpers.upload import (do_upload, remove_upload,
                            pinecone_upload_file, 
                            create_corpus, 
                            vectara_upload, 
                            _prep_upload_file_json,
                            create_corpus_api_key)

import requests

bp = Blueprint('upload', __name__, url_prefix='/upload')


@bp.post('/add')
@auth_required()
def add():
    file = request.files.get('file')
    if file:
        url = do_upload(file)
        if url:
            return {'url': url, 'message': 'File uploaded successfully'}
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


@bp.post('/vectara-corpus-create')
@auth_required('agentadmin')
def vectara_corpus_create():
    #when creating corpus, we just need to pass partner corpus id and partner name
    user = get_user_from_access_token(request.headers.get('Authorization'))
    partner = Partner.get_by_id(Agent.get_by_user_id(user.id).partner_id)   

    if partner.corpus_id is None:
        msg, status = create_corpus(partner_name=partner.name)
        print(f'\nMESSAGE: {msg}\n')
        if status is True:
            partner.corpus_id = msg.get('corpusId')
            partner.save()
            
            #after creating the corpus, we need to create an api key for the corpus
            msg2, status = create_corpus_api_key(partner.corpus_id)
            if status is True:
                partner.corpus_api_key = msg2['keyId']
                partner.save()
            else:
                return {'msg':'error creating corpus api key', 'data':msg2}
            return {'msg':'corpus created successfully','data':msg}
        else:
            return {'msg':'error creating corpus', 'data':msg}
    else:
        return jsonify({'msg':'partner already have a corpus id'}), 400
    

@bp.post('/vectara-add')
@auth_required('agentadmin')
def vectara_add():
    user = get_user_from_access_token(request.headers.get('Authorization'))
    partner = Partner.get_by_id(Agent.get_by_user_id(user.id).partner_id)
    files = request.files.get('file')
    file = _prep_upload_file_json(files, partner)
    res, status = vectara_upload(file, int(partner.corpus_id), partner.corpus_api_key)
    if status is True:
        return {'msg':'file uploaded to corpus successfully', 'data':res}
    else:
        return {'msg':'error uploading data'}
    
@bp.post('/pinecone-add')
@auth_required('agentadmin')
def pinecone_add():
    filepath = request.json.get('filepath')
    user = get_user_from_access_token(request.headers.get('Authorization'))
    partner_name = Partner.get_by_id(Agent.get_by_user_id(user.id).partner_id).name.replace(' ', '-').lower()

    if filepath:
        stat = pinecone_upload_file(filepath, partner_name)
        if stat:
            return {'status': stat, 'message': 'File uploaded successfully'}
        return {'error': 'Error uploading file'}
    return {'error': 'No file to upload'}



def get_user_from_access_token(auth):
    try:
        token = auth.split(' ')[1]
        payload = jwt.decode(token, app.config.get('JWT_SECRET_KEY'), algorithms=["HS256"])
        auth_id = payload['sub']
    except Exception as e:
        return {"message": "Unauthorized to perform action"}
    user = User.get_by_id(auth_id)
    return user
