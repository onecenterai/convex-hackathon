import os
from dotenv import load_dotenv
from convex import ConvexClient
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from pyconvex.convex_retriever import ConvexDocStore
from langchain.document_loaders import PyPDFLoader
from langchain.tools import Tool
from langchain.agents import initialize_agent
from langchain.agents.types import AgentType
from langchain.schema import HumanMessage, AIMessage
from langchain.docstore.document import Document
import multiprocessing
import copy



convex_url = os.getenv('CONVEX_URL')
open_ai_key = os.getenv('OPENAI_API_KEY')

client = ConvexClient(address=convex_url)
embeddings = OpenAIEmbeddings(openai_api_key=open_ai_key)

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



def query_doc(query, company_name, history = []):
    
    docstore = ConvexDocStore(index=company_name, embeddings=embeddings, convex_url=os.getenv('CONVEX_URL'))
    retriever = docstore.as_retriever()
    llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"))

    qa = RetrievalQA.from_chain_type(llm=llm, chain_type='stuff', retriever=retriever)

    system_message = f"""
            "You are a helpful HR representative."
            "You provide assistant to  {company_name} employees and/or customers about {company_name} Inc."
            "information about {company_name} Inc can be accessed using the `{company_name} guide book` tool"
            "You can ask questions to help you understand and diagnose the problem."
            "If you are unsure of how to help, you can suggest the client to go to the HR Admin office."
            "Try to sound as human as possible"
            "Make your responses as concise as possible"
            """
    tools = [
        Tool(
            name=f"{company_name} guide book",
            func=qa.run,
            description=f"Useful when you need to answer {company_name} employees and/or customers questions",
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

    

