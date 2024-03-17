from flask import Blueprint, g, request
from app.partner.model import Partner
from app.route_guard import platform_auth_required

from app.call.model import *
from app.call.schema import *
from app.user.model import User
from helpers.langchain import qa_chain
from helpers.openai import qa
#from helpers.vectara.query import query

bp = Blueprint('call', __name__, template_folder='templates')

@bp.post('/call/initialize')
@platform_auth_required
def make_intial_call_response():
    if g.platform.name.lower() == 'jambonz':
        session_id = request.json.get('call_id')
        from_ = request.json.get('from', '')
        to_ = request.json.get('to', '')
        user = User.get_by_phone(from_)
        if not user:
            return [
                {
                    "verb": "say",
                    "text": "Please call from a registered phone number!"
                 },
                ]
        partner = Partner.get_by_assigned_phone(to_)
        answer = f"Hello {user.name.split()[0]}, welcome to {partner.name} Customer Support! How may I assist you today?"
        Call.create(user.id, partner.id, session_id, "Hello", answer)
        return [
                {
                    "verb": "gather",
                    "say": {
                    "text": answer
                    },
                    "input": [
                    "speech"
                    ],
                    "actionHook": "/call/inprogress",
                    "timeout": 15
                }
                ]
    else:
        # do radysis logic here
        session_id = request.json.get('sessionId')
        partner_id = int(request.json.get('info', '').split('_')[1])
        user_id = int(request.json.get('info', '').split('_')[0])
        user = User.get_by_id(user_id)
        partner = Partner.get_by_id(partner_id)
        if user and partner:
            answer = f"Hello {user.name.split()[0]}, welcome to {partner.name} Customer Support! How may I assist you today?"
            Call.create(user.id, partner_id, session_id, "Hello", answer)
            return answer
        return "You are not registered!"

@bp.post('/call/inprogress')
@platform_auth_required
def respond_to_call_in_progress():
    answer = "Sorry, could you repeat that please?"
    if g.platform.name.lower() == 'jambonz':
        session_id = request.json.get('call_id')
        from_ = request.json.get('from', '')
        to_ = request.json.get('to', '')
        user = User.get_by_phone(from_)
        partner = Partner.get_by_assigned_phone(to_)
        speech = request.json.get('speech', {})
        alternatives = speech.get('alternatives', [])

        for alternative in alternatives:
            confidence = alternative.get('confidence')
            if confidence >= 0.7:
                # Store Call Before Responding
                history = Call.get_by_user_id_and_session_id(user.id, session_id)
                answer = qa_chain(alternative.get('transcript'), history, partner)
                # res, success = query(partner.corpus_id, alternative.get('transcript'))
                # if success and (not 'returned results did not contain sufficient information to be summarized into a useful answer for your query' in res.json().get('responseSet')[0].get('summary')[0].get('text')):
                #     answer = qa(alternative.get('transcript'), res.json().get('responseSet')[0].get('summary')[0].get('text'))
                # else:
                #     answer = "Sorry, I don't have answer for that at the moment."
                Call.create(user.id, partner.id, session_id, alternative.get('transcript'), answer)
                break
        if 'take care' in answer.lower() or 'bye' in answer.lower():
            return [
                    {
                    "verb": "say",
                    "text": answer,
                    },
                    {
                    "verb": "hangup"
                    }
                    ]
        return [
                {
                    "verb": "gather",
                    "say": {
                    "text": answer
                    },
                    "input": [
                    "speech"
                    ],
                    "actionHook": "/call/inprogress",
                    "timeout": 15
                }
                ]
    else:
        # do radysis logic here
        session_id = request.json.get('sessionId')
        question = request.json.get('text')
        user_id = int(request.json.get('info', '').split('_')[0])
        partner_id = int(request.json.get('info', '').split('_')[1])
        partner = Partner.get_by_id(partner_id)
        user = User.get_by_id(user_id)
        history = Call.get_by_user_id_and_session_id(user.id, session_id)
        answer = qa_chain(question, history, partner)
        # res, success = query(partner.corpus_id, question)
        # if success and (not 'returned results did not contain sufficient information to be summarized into a useful answer for your query' in res.json().get('responseSet')[0].get('summary')[0].get('text')):
        #     answer = qa(question, res.json().get('responseSet')[0].get('summary')[0].get('text'))
        # else:
        #     answer = "Sorry, I don't have answer for that at the moment."
        Call.create(user.id, partner.id, session_id, question, answer)
        return answer

@bp.post('/call/status')
@platform_auth_required
def get_call_status():
    return ""

