from typing import Union
from fastapi import FastAPI
from fastapi.responses import Response
import kendra_chat_open_ai as openai
import json


app = FastAPI()

llm_chain = openai.build_chain()
chain = openai

@app.post("/generate-response")
def generate_response(input: str):
    print("demo")
    result = chain.run_chain(llm_chain, input, [])
    print("result: ", result)
    answer = result['answer']

    print("answer: ", answer)

    document_list = []
    if 'source_documents' in result:
        for d in result['source_documents']:
            if not (d.metadata['source'] in document_list):
                document_list.append((d.metadata['source']))

    return Response(status_code=200, content=json.dumps({"answer": answer, "sources": document_list}))