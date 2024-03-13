import os
from dotenv import load_dotenv
from convex import ConvexClient
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from convex_retriever import ConvexDocStore
from langchain.document_loaders import PyPDFLoader
from langchain.tools import Tool
from langchain.agents import initialize_agent
from langchain.agents.types import AgentType
from langchain.schema import HumanMessage, AIMessage
from langchain.docstore.document import Document
import multiprocessing
import copy



load_dotenv()
client = ConvexClient(os.getenv('CONVEX_URL'))
embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

def get_all_documents():
    res = client.query("docs:get")
    return res

def upload_document(file, name, company_name, description):
    #embed document
    #pass embeddings into function >:)
    
    loader = PyPDFLoader(file)
    w_pages = loader.load_and_split()
    pages = copy.deepcopy(w_pages)
    pages = parallel_vectorize(pages, embeddings)    
    
    
    for i in range(len(w_pages)):
        res = client.action("docs:insert", args={'name':f'{name}_{i}', 
                                                 'company_name':company_name, 
                                                 'description':description, 
                                                 'content':w_pages[i].page_content, 
                                                 'embeddings':pages[i].page_content})
    
    return True

def vectorize(embeddings, page_content, result_queue):
        vectors = embeddings.embed_query(page_content)
        result_queue.put(vectors)

def parallel_vectorize(pages, embeddings):
    vec_queue = multiprocessing.Queue()
    processes = []

    for page in pages:
        process = multiprocessing.Process(target=vectorize, args=(embeddings, page.page_content, vec_queue))
        processes.append(process)
        process.start()

    # Retrieve results from the queue
    for page in pages:
        page.page_content = vec_queue.get()      

    # Wait till all the processes run completely before going on
    for process in processes:
        process.join()
    
    return pages



def query_doc(query, company_name):
    # embeds = embeddings.embed_query(query)
    # as_output = client.action("docs:doc_search", args={'query_embedding':embeds, 'company_name':company_name})
    history = []
    docstore = ConvexDocStore(index=company_name, embeddings=embeddings, convex_url=os.getenv('CONVEX_URL'))
    retriever = docstore.as_retriever()
    llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"))

    qa = RetrievalQA.from_chain_type(llm=llm, chain_type='stuff', retriever=retriever)

    system_message = f"""
            "You are a helpful HR representative."
            "You provide assistant to  vectara employees about Vectara Inc."
            "information about Vectara Inc can be accessed using the `vectara employee guide book` tool"
            "You can ask questions to help you understand and diagnose the problem."
            "If you are unsure of how to help, you can suggest the client to go to the HR Admin office."
            "Try to sound as human as possible"
            "Make your responses as concise as possible"
            """
    tools = [
        Tool(
            name=f"vectara employee guide book",
            func=qa.run,
            description=f"Useful when you need to answer vectara employees questions",
        )
    ]

    executor = initialize_agent(
        agent = AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        tools=tools,
        llm=llm,
        handle_parsing_errors="Check your output and make sure it conforms!",
        agent_kwargs={"system_message": system_message},
        verbose=True,
    )

    q = {"question": query}

    chat_history = []
    
    for h in history:
        chat_history.append(HumanMessage(content=h.question))
        chat_history.append(AIMessage(content=h.answer))

    return executor.run(input=q, chat_history=chat_history)

def test():
    embeds = embeddings.embed_query('can you please tell me about the onsite mini zoo')
    as_output = client.action("docs:doc_search", args={'query_embedding':embeds, 'company_name':'ACME'})
    
        
    return [Document(page_content=d.get('content'), metadata={'id':d.get('_id'), 'score':d.get('_score')}) for d in as_output]

if __name__ == '__main__':
    # upload_document('/home/g1f7/Documents/data/vectara_employee_handbook.pdf', 'test1', 'ACME', 'this is a test doc')
    # print(len(get_all_documents()))
    a = query_doc(query='can you please tell me about the onsite mini zoo?', company_name='ACME')
    print(a)
    # print(test())
    

