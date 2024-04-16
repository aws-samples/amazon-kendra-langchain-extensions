# from aws_langchain.kendra import AmazonKendraRetriever #custom library
import os
import sys

import boto3
import botocore
from botocore.client import Config
from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.chains.llm import LLMChain
from langchain.llms.bedrock import Bedrock
from langchain.prompts import PromptTemplate
from langchain.retrievers import AmazonKendraRetriever
from langchain_community.chat_models.bedrock import BedrockChat


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


MAX_HISTORY_LENGTH = 5
MODEL_ID_70B = "meta.llama2-70b-chat-v1"
MODEL_ID_13B = "meta.llama2-13b-chat-v1"


def build_chain_llama2_70B():
    return build_chain(MODEL_ID_70B)


def build_chain_llama2_13B():
    return build_chain(MODEL_ID_13B)


def build_chain(model_id):
    region = os.environ["AWS_REGION"]
    kendra_index_id = os.environ["KENDRA_INDEX_ID"]

    bedrock_config = Config(connect_timeout=120, read_timeout=120, retries={'max_attempts': 0})
    bedrock_client = boto3.client('bedrock-runtime', config=bedrock_config)

    credentials_profile_name = os.environ.get("AWS_PROFILE", "")
    llm = BedrockChat(
        credentials_profile_name=credentials_profile_name,
        model_id=model_id, 
        client=bedrock_client, 
        model_kwargs={ 
            "max_gen_len": 2048,
            "temperature": 1,
            "top_p": 0.999,
        }
    )
    retriever = AmazonKendraRetriever(
        index_id=kendra_index_id, top_k=5, region_name=region
    )

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
        combine_docs_chain_kwargs={"prompt": PROMPT},
        verbose=True,
    )

    # qa = ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever, qa_prompt=PROMPT, return_source_documents=True)
    return qa


def run_chain(chain, prompt: str, history=[]):
    return chain({"question": prompt, "chat_history": history})


if __name__ == "__main__":
    chat_history = []
    qa = build_chain()
    print(bcolors.OKBLUE + "Hello! How can I help you?" + bcolors.ENDC)
    print(
        bcolors.OKCYAN
        + "Ask a question, start a New search: or CTRL-D to exit."
        + bcolors.ENDC
    )
    print(">", end=" ", flush=True)
    for query in sys.stdin:
        if query.strip().lower().startswith("new search:"):
            query = query.strip().lower().replace("new search:", "")
            chat_history = []
        elif len(chat_history) == MAX_HISTORY_LENGTH:
            chat_history.pop(0)
        result = run_chain(qa, query, chat_history)
        chat_history.append((query, result["answer"]))
        print(bcolors.OKGREEN + result["answer"] + bcolors.ENDC)
        if "source_documents" in result:
            print(bcolors.OKGREEN + "Sources:")
            for d in result["source_documents"]:
                print(d.metadata["source"])
        print(bcolors.ENDC)
        print(
            bcolors.OKCYAN
            + "Ask a question, start a New search: or CTRL-D to exit."
            + bcolors.ENDC
        )
        print(">", end=" ", flush=True)
    print(bcolors.OKBLUE + "Bye" + bcolors.ENDC)
