from langchain.retrievers import AmazonKendraRetriever
from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.prompts import PromptTemplate
from langchain import SagemakerEndpoint
from langchain.llms.sagemaker_endpoint import LLMContentHandler
import sys
import json
import os


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


def build_chain():
    region = os.environ["AWS_REGION"]
    kendra_index_id = os.environ["KENDRA_INDEX_ID"]
    endpoint_name = os.environ["LLAMA_2_ENDPOINT"]
    language_code = os.environ["LANGUAGE_CODE"]

    class ContentHandler(LLMContentHandler):
        content_type = "application/json"
        accepts = "application/json"

        def transform_input(self, prompt: str, model_kwargs: dict) -> bytes:
            input_str = json.dumps(
                {
                    "inputs": [
                        [
                            {"role": "user", "content": prompt, "instruction": ""},
                        ]
                    ],
                    "parameters": model_kwargs,
                }
            )
            return input_str.encode("utf-8")

        def transform_output(self, output: bytes) -> str:
            response_json = json.loads(output.read().decode("utf-8"))
            return response_json[0]["generation"]["content"]

    content_handler = ContentHandler()

    llm = SagemakerEndpoint(
        endpoint_name=endpoint_name,
        region_name="us-east-1",
        model_kwargs={
            "max_new_tokens": 1000,
            "temperature": 0.4,
            "do_sample": True,
            "pad_token_id": 0,
            "bos_token_id": 2,
            "eos_token_id": 3,  # 265,  # 「。」の ID に相当。
            "stop_ids": [50278, 50279, 50277, 1, 0],
        },
        endpoint_kwargs={"CustomAttributes": "accept_eula=true"},
        content_handler=content_handler,
    )

    retriever = AmazonKendraRetriever(
        index_id=kendra_index_id,
        top_k=2,
        region_name=region,
        attribute_filter={
            "EqualsTo": {
                "Key": "_language_code",
                "Value": {"StringValue": language_code},
            }
        },
    )

    prompt_template = """
  <s>[INST] <<SYS>>
  あなたは誠実で優秀な日本人のアシスタントです。
  以下の資料から抜粋して質問に答えます。資料にない内容は答えず「わかりません」と答えます。
  {context}
  上記の資料に基づき以下の質問について資料から抜粋して日本語で回答してください。資料にない内容は答えず「わかりません」と答えてください。
  <</SYS>>
  {question}
  [/INST]

  """

    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"],
    )

    condense_qa_template = """
  次の会話とフォローアップの質問があったら、フォローアップの質問を日本語で言い換えてください 
  独立した質問になります。

  チャット履歴:
  {chat_history}
  フォローアップ入力: {question}
  スタンドアロンの質問:
  """

    standalone_question_prompt = PromptTemplate.from_template(condense_qa_template)

    qa = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        condense_question_prompt=standalone_question_prompt,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": PROMPT},
        verbose=True,
    )
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
