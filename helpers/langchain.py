from pyconvex.pyconvex_main import query_doc

from app.partner.model import Partner

def qa_chain(question, history=[], partner: Partner = Partner(), doc_store='convex'):
    res = query_doc(query=question, company_name=partner.name, history=history)
    return res