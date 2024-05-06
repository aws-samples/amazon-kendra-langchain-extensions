from langchain.retrievers import AmazonKendraRetriever
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.llms import SagemakerEndpoint
from langchain.llms.sagemaker_endpoint import LLMContentHandler
import sys
import json
import os
from typing import Dict, List


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
  endpoint_name = os.environ["LLAMA_2_ENDPOINT"]

  class ContentHandler(LLMContentHandler):
      content_type = "application/json"
      accepts = "application/json"

      def transform_input(self, prompt: str, model_kwargs: dict) -> bytes:
          # input_str = json.dumps({"inputs": [[{"role": "user", "content": prompt},]],
          #                         "parameters" : model_kwargs
          #                         })
          input_str = json.dumps({"inputs": prompt,
                                  "parameters" : model_kwargs
                                  })
          return input_str.encode('utf-8')
      
      def transform_output(self, output: bytes) -> str:
          response_json = json.loads(output.read().decode("utf-8")) 
          print(response_json)
          return response_json['generated_text']
    

  content_handler = ContentHandler()

  llm=SagemakerEndpoint(
          endpoint_name=endpoint_name, 
          region_name=region, 
          model_kwargs={"max_new_tokens": 500, "top_p": 0.9,"temperature":0.0},
          endpoint_kwargs={"CustomAttributes":"accept_eula=true"},
          content_handler=content_handler)
      
  retriever = AmazonKendraRetriever(index_id=kendra_index_id,region_name=region)

  prompt_template = """
  <s>[INST] <<SYS>>
  The following is a friendly conversation between a human and an AI. 
  The AI is talkative and provides lots of specific details from its context.
  If the AI does not know the answer to a question, it truthfully says it 
  does not know.
  {context}
  <</SYS>>
  Instruction: Based on the above documents, provide a detailed answer for, {question} Answer "don't know" 
  if not present in the document. 
  Solution:
  [/INST]"""
  
  PROMPT = PromptTemplate(
      template=prompt_template, input_variables=["context", "question"],
  )
  condense_qa_template = """
  <s>[INST] <<SYS>>
  Given the following conversation and a follow up question, rephrase the follow up question 
  to be a standalone question.

  Chat History:
  {chat_history}
  Follow Up Input: {question}
    <</SYS>>
  Standalone question:  [/INST]"""
  standalone_question_prompt = PromptTemplate.from_template(condense_qa_template)
 

  qa = ConversationalRetrievalChain.from_llm(
        llm=llm, 
        retriever=retriever, 
        condense_question_prompt=standalone_question_prompt, 
        return_source_documents=True, 
        combine_docs_chain_kwargs={"prompt":PROMPT},
        verbose=True
        )
  return qa

def run_chain(chain, prompt: str, history=[]):

   return chain({"question": prompt, "chat_history": history})


def format_messages(messages: List[Dict[str, str]]) -> List[str]:
    """Format messages for Llama-2 chat models.
    
    The model only supports 'system', 'user' and 'assistant' roles, starting with 'system', then 'user' and 
    alternating (u/a/u/a/u...). The last message must be from 'user'.
    """
    prompt: List[str] = []

    if messages[0]["role"] == "system":
        content = "".join(["<<SYS>>\n", messages[0]["content"], "\n<</SYS>>\n\n", messages[1]["content"]])
        messages = [{"role": messages[1]["role"], "content": content}] + messages[2:]

    for user, answer in zip(messages[::2], messages[1::2]):
        prompt.extend(["<s>", "[INST] ", (user["content"]).strip(), " [/INST] ", (answer["content"]).strip(), "</s>"])

    prompt.extend(["<s>", "[INST] ", (messages[-1]["content"]).strip(), " [/INST] "])

    return "".join(prompt)


def print_messages(prompt: str, response: str) -> None:
    bold, unbold = '\033[1m', '\033[0m'
    print(f"{bold}> Input{unbold}\n{prompt}\n\n{bold}> Output{unbold}\n{response[0]['generated_text']}\n")

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