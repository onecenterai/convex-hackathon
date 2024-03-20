from flask import Blueprint, g, request
from app.agent.model import Agent
#from app.celery.tasks import start_training, undo_training
from app.route_guard import auth_required
from app.partner.model import Partner

from app.resource.model import *
from app.resource.schema import *

from pyconvex.pyconvex_main import upload_document
from pyconvex.pyconvex_main import delete_resource as convex_resource_delete

bp = Blueprint('resource', __name__)

@bp.post('/resource')
@auth_required('agentadmin')
def create_resource():
    title = request.json.get('title')
    description = request.json.get('description')
    url = request.json.get('url')
    if not url:
        return {'message': 'Resource URL can not be empty'}, 400
    agent = Agent.get_by_user_id(g.user.id)
    resource = Resource.create(title, description, url, agent.partner_id)
    return ResourceSchema().dump(resource), 201

@bp.get('/resource/<int:id>')
@auth_required('agentadmin')
def get_resource(id):
    resource = Resource.get_by_id(id)
    if resource is None:
        return {'message': 'Resource not found'}, 404
    return ResourceSchema().dump(resource), 200

@bp.patch('/resource/<int:id>')
@auth_required('agentadmin')
def update_resource(id):
    resource = Resource.get_by_id(id)
    if resource is None:
        return {'message': 'Resource not found'}, 404
    title = request.json.get('title')
    description = request.json.get('description')
    url = request.json.get('url')
    resource.update(title, description, url)
    return ResourceSchema().dump(resource), 200

@bp.delete('/resource/<int:id>')
@auth_required('agentadmin')
def delete_resource(id):
    resource = Resource.get_by_id(id)
    p = Partner.get_by_id(g.user.agent.partner_id)

    if resource is None:
        return {'message': 'Resource not found'}, 404
    # undo_training.delay(resource.id)
    
    res = convex_resource_delete(company_name=p.name, doc_name=resource.title)
    if res:
        resource.delete()
        return {'message': 'Resource Deleted'}, 200
    else:
        return {'message': 'Error Deleting Resource'}

@bp.get('/resources')
@auth_required('agentadmin')
def get_resources():
    # resources = Resource.get_all()
    agent = Agent.get_by_user_id(g.user.id)
    resources = Resource.get_by_partner_id(agent.partner_id)
    return ResourceSchema(many=True).dump(resources), 200

@bp.post('/resource/<int:id>/train')
@auth_required('agentadmin')
def train_model_with_resource(id):
    p = Partner.get_by_id(g.user.agent.partner_id)
    resource = Resource.get_by_id(id)
    if resource is None:
        return {'message': 'Resource not found'}, 404
    elif resource.training_status == 'complete':
        return {'message': 'Resource already used for training'}, 404
    elif resource.training_status == 'processing':
        return {'message': 'Resource training in progress'}, 404
    # start resource training here
    #start_training.delay(resource.id, p.name)
    res = upload_document(file=resource.url, name=p.title, description=resource.description, company_name=p.name)
    resource.training_status == 'complete'
    return {'message': 'Resource training completed Successfully successfully'}, 200