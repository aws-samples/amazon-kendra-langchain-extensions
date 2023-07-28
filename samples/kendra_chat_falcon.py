# from aws_langchain.kendra import AmazonKendraRetriever #custom library
from langchain.retrievers import AmazonKendraRetriever
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain import SagemakerEndpoint
from langchain.llms.sagemaker_endpoint import LLMContentHandler
import sys
import json
import os

class bcolors:
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
  region = os.environ["AWS_REGION"]
  kendra_index_id = os.environ["KENDRA_INDEX_ID"]
  endpoint_name = os.environ["FALCON_ENDPOINT"]

  class ContentHandler(LLMContentHandler):
      content_type = "application/json"
      accepts = "application/json"

      def transform_input(self, prompt: str, model_kwargs: dict) -> bytes:
          # input_str = json.dumps({"text_inputs": prompt, **model_kwargs})
          # return input_str.encode('utf-8')
          input_str = json.dumps({"inputs": prompt, "parameters": model_kwargs})
          print("input")
          print(input_str)
          return input_str.encode('utf-8')
      
      def transform_output(self, output: bytes) -> str:
          # response_json = json.loads(output.read().decode("utf-8"))
          # return response_json["generated_texts"][0]
          response_json = json.loads(output.read().decode("utf-8"))
          prompt_length = response_json[0]["generated_text"].find("Solution:") + 9
          print("output")
          print(response_json[0]["generated_text"][prompt_length:])
          return response_json[0]["generated_text"][prompt_length:]

  content_handler = ContentHandler()

  # llm=SagemakerEndpoint(
  #         endpoint_name=endpoint_name, 
  #         region_name=region, 
  #         model_kwargs={"temperature":1e-10, "max_length": 500},
  #         content_handler=content_handler
  #     )

  llm=SagemakerEndpoint(
          endpoint_name=endpoint_name, 
          region_name=region, 
          # model_kwargs={"temperature":1e-10, "max_length": 500},
            model_kwargs={
            "do_sample": True,
            "top_p": 0.9,
            "temperature": 0.01,
            "max_new_tokens": 400,
            "repetition_penalty": 1.03,
            "stop": ["\nInstruction:","<|endoftext|>","</s>"]
          },
          content_handler=content_handler
      )
      
  retriever = AmazonKendraRetriever(index_id=kendra_index_id)

  prompt_template = """
  The following is a friendly conversation between a human and an AI. 
  The AI is talkative and provides lots of specific details from its context.
  If the AI does not know the answer to a question, it truthfully says it 
  does not know.
  {context}
  Instruction: Based on the above documents, provide a detailed answer for, {question} Answer "don't know" 
  if not present in the document. 
  Solution:"""
  PROMPT = PromptTemplate(
      template=prompt_template, input_variables=["context", "question"]
  )

  condense_qa_template = """
  Given the following conversation and a follow up question, rephrase the follow up question 
  to be a standalone question.

  Chat History:
  {chat_history}
  Follow Up Input: {question}
  Standalone question:"""
  standalone_question_prompt = PromptTemplate.from_template(condense_qa_template)

  qa = ConversationalRetrievalChain.from_llm(
        llm=llm, 
        retriever=retriever, 
        condense_question_prompt=standalone_question_prompt, 
        return_source_documents=True, 
        combine_docs_chain_kwargs={"prompt":PROMPT})
  return qa

def run_chain(chain, prompt: str, history=[]):
   return chain({"question": prompt, "chat_history": history})

if __name__ == "__main__":
  chat_history = []
  qa = build_chain()
  print(bcolors.OKBLUE + "Hello! How can I help you?" + bcolors.ENDC)
  print(bcolors.OKCYAN + "Ask a question, start a New search: or CTRL-D to exit." + bcolors.ENDC)
  print(">", end=" ", flush=True)
  for query in sys.stdin:
    if (query.strip().lower().startswith("new search:")):
      query = query.strip().lower().replace("new search:","")
      chat_history = []
    elif (len(chat_history) == MAX_HISTORY_LENGTH):
      chat_history.pop(0)
    result = run_chain(qa, query, chat_history)
    chat_history.append((query, result["answer"]))
    print(bcolors.OKGREEN + result['answer'] + bcolors.ENDC)
    if 'source_documents' in result:
      print(bcolors.OKGREEN + 'Sources:')
      for d in result['source_documents']:
        print(d.metadata['source'])
    print(bcolors.ENDC)
    print(bcolors.OKCYAN + "Ask a question, start a New search: or CTRL-D to exit." + bcolors.ENDC)
    print(">", end=" ", flush=True)
  print(bcolors.OKBLUE + "Bye" + bcolors.ENDC)