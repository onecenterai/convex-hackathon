from app import celery, db

import os
from app.call.model import Call, Response
from app.partner.model import Partner
from app.resource.model import Resource


from app.review.model import Review
from helpers.langchain import qa_chain
from helpers.openai import transcribe, rewrite
from pyconvex.pyconvex_main import upload_document, delete_resource



@celery.task
def create_transcript(review_id, transient_audio_file=None):
    try:
        if transient_audio_file:
            print(transient_audio_file)
            review = Review.get_by_id(review_id)
            transcript = transcribe(transient_audio_file)
            review.content = rewrite(transcript).get('content')
            review.update()
            os.remove(transient_audio_file)
            return "Review Generated Successfully!"
    except Exception as e:
        print(e)
        if transient_audio_file:
            try:
                os.remove(transient_audio_file)
            except:
                pass
        db.session.rollback()
        return "Review Could Not Be Generated Successfully!"

@celery.task
def start_training(resource_id, name):
    file = Resource.get_by_id(resource_id)
    if file:
        res = upload_document(file=file.url, name=f'{name} document', description=file.description, company_name=name)
        if res:
              return {'message': 'File uploaded successfully'}
        return {'error': 'Error uploading file'}
    return {'error': 'No file to upload'}
    

@celery.task
def undo_training(resource_id):
    try:
        
        resource = Resource.get_by_id(resource_id)
        partner = Partner.get_by_id(resource.partner_id)
        resource.update(training_status = 'pending')
        
        delete_resource(partner.name)
        resource.delete()
        return "Resource Deleted Successfully!"
    except Exception as e:
        print(e)
        db.session.rollback()
        return "Resource could not be deleted!"

@celery.task
def do_long_call(user_id, session_id, question, partner_id):
    try:
        
        history = Call.get_by_user_id_and_session_id(user_id, session_id)
        partner = Partner.get_by_id(partner_id)
        answer = qa_chain(question, history, partner)
        Call.create(user_id, partner.id, session_id, question, answer)
        Response.create(user_id, partner_id, session_id, answer)
        return "Call Completed Successfully!"
    except Exception as e:
        print(e)
        db.session.rollback()
        return "Call failed!"
    
#TODO: Schedule tasks to optimize corpus api keys.
    # basically, we want less api keys,
    # so from time to time we create an api key that multiple corpa can share, and delete their existing api keys