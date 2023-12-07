# from aws_langchain.kendra import AmazonKendraRetriever #custom library
from langchain.retrievers import AmazonKendraRetriever
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.llms.bedrock import Bedrock
from langchain.chains.llm import LLMChain
import sys
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
  bedrock_region = os.environ["AWS_BEDROCK_REGION"]
  kendra_index_id = os.environ["KENDRA_INDEX_ID"]
  credentials_profile_name = os.environ['AWS_PROFILE']

  print(credentials_profile_name)

  llm = Bedrock(
      credentials_profile_name=credentials_profile_name,
      region_name = bedrock_region,
      model_kwargs={"maxTokens":200,"temperature":0.1,"topP":0.9, "countPenalty":{"scale":0},"presencePenalty":{"scale":0},"frequencyPenalty":{"scale":0}},
      model_id="ai21.j2-ultra-v1"
  )
      
  attribute_filter = {
            "EqualsTo": {      
                "Key": "_language_code",
                "Value": {
                    "StringValue": "nl"
                    }
                }
            }
  retriever = AmazonKendraRetriever(index_id=kendra_index_id,top_k=5,region_name=region, attribute_filter=attribute_filter)

  prompt_template = """Mens: Dit is een vriendschappelijk gesprek tussen een mens en een AI. 
  De AI is spraakzaam en geeft specifieke details uit zijn context, maar beperkt dit tot 240 tokens.
  Als de AI het antwoord op een vraag niet weet, zegt hij eerlijk dat hij het niet weet. 
  het niet weet.

  Assistent: OK, begrepen, ik zal een spraakzame waarheidsgetrouwe AI-assistent zijn.

  Mens: Hier zijn een paar documenten in <documenten> tags:
  <documenten>
  {context}
  </documenten>
  Geef op basis van de bovenstaande documenten een gedetailleerd antwoord op {question}. 
  Antwoord "weet niet" indien niet aanwezig in het document. 

  Assistent:
  """

  
  PROMPT = PromptTemplate(
      template=prompt_template, input_variables=["context", "question"]
  )

  condense_qa_template = """{chat_history}
  Mens:
  Gegeven het vorige gesprek en een vervolgvraag hieronder, herformuleer de vervolgvraag
  zodat het een op zichzelf staande vraag wordt.

  Vervolgvraag: {question}
  Op zichzelf staande vraag:

  Assistent:"""


  standalone_question_prompt = PromptTemplate.from_template(condense_qa_template)


  
  qa = ConversationalRetrievalChain.from_llm(
        llm=llm, 
        retriever=retriever, 
        condense_question_prompt=standalone_question_prompt, 
        return_source_documents=True, 
        combine_docs_chain_kwargs={"prompt":PROMPT},
        verbose=True)

  # qa = ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever, qa_prompt=PROMPT, return_source_documents=True)
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
