# pylint: disable=invalid-name,line-too-long
"""
Adapted from
https://github.com/aws-samples/amazon-kendra-langchain-extensions/blob/main/samples/kendra_chat_flan_xl.py
"""

import json
import os

from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain import SagemakerEndpoint
from langchain.llms.sagemaker_endpoint import ContentHandlerBase

from aws_langchain.kendra_index_retriever import KendraIndexRetriever

class bcolors:  #pylint: disable=too-few-public-methods
    """
    ANSI escape sequences
    https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

MAX_HISTORY_LENGTH = 5

def build_chain():
    """
    Builds the LangChain chain
    """
    region = os.environ["AWS_REGION"]
    kendra_index_id = os.environ["KENDRA_INDEX_ID"]
    endpoint_name = os.environ["FLAN_XL_ENDPOINT"]

    class ContentHandler(ContentHandlerBase):
        """
        Handler class to transform input and ouput
        into a format that the SageMaker Endpoint can understand
        """
        content_type = "application/json"
        accepts = "application/json"

        def transform_input(self, prompt: str, model_kwargs: dict) -> bytes:
            input_str = json.dumps({"text_inputs": prompt, **model_kwargs})
            return input_str.encode('utf-8')

        def transform_output(self, output: bytes) -> str:
            response_json = json.loads(output.read().decode("utf-8"))
            return response_json["generated_texts"][0]

    content_handler = ContentHandler()

    # Initialize LLM hosted on a SageMaker endpoint
    # https://python.langchain.com/en/latest/modules/models/llms/integrations/sagemaker.html
    llm=SagemakerEndpoint(
        endpoint_name=endpoint_name,
        region_name="us-east-1",
        model_kwargs={"temperature":1e-10, "max_length": 500},
        content_handler=content_handler
    )

    # Initialize Kendra index retriever
    retriever = KendraIndexRetriever(
       kendraindex=kendra_index_id,
       awsregion=region,
       return_source_documents=True
    )

    # Define prompt template
    # https://python.langchain.com/en/latest/modules/prompts/prompt_templates.html
    prompt_template = """
The following is a friendly conversation between a human and an AI. 
The AI is talkative and provides lots of specific details from its context.
If the AI does not know the answer to a question, it truthfully says it 
does not know.
{context}
Instruction: Based on the above documents, provide a detailed answer for,
{question} Answer "don't know" if not present in the document. Solution:
"""
    qa_prompt = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    # Initialize QA chain with chat history
    # https://python.langchain.com/en/latest/modules/chains/index_examples/chat_vector_db.html
    qa = ConversationalRetrievalChain.from_llm(  #
        llm=llm,
        retriever=retriever,
        qa_prompt=qa_prompt,
        return_source_documents=True
    )

    return qa

def run_chain(chain, prompt: str, history=None):
    """
    Runs the Q&A chain given a user prompt and chat history
    """
    if history is None:
        history = []
    return chain({"question": prompt, "chat_history": history})

def prompt_user():
    """
    Helper function to get user input
    """
    print(f"{bcolors.OKBLUE}Hello! How can I help you?{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}Ask a question, start a New search: or Stop cell execution to exit.{bcolors.ENDC}")
    return input(">")

if __name__ == "__main__":
    # Initialize chat history
    chat_history = []

    # Initialize Q&A chain
    qa_chain = build_chain()

    try:
        while query := prompt_user():
            # Process user input in case of a new search
            if query.strip().lower().startswith("new search:"):
                query = query.strip().lower().replace("new search:", "")
                chat_history = []
            if len(chat_history) == MAX_HISTORY_LENGTH:
                chat_history.pop(0)

            # Show answer and keep a record
            result = run_chain(qa_chain, query, chat_history)
            chat_history.append((query, result["answer"]))
            print(f"{bcolors.OKGREEN}{result['answer']}{bcolors.ENDC}")

            # Show sources
            if 'source_documents' in result:
                print(bcolors.OKGREEN + 'Sources:')
                for doc in result['source_documents']:
                    print(f"+ {doc.metadata['source']}")
    except KeyboardInterrupt:
        pass
