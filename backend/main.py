from typing import Union
from fastapi import FastAPI
from kendra_retriever_samples.kendra_chat_open_ai

app = FastAPI()

llm_chain = None
llm_app = None

@app.on_event("startup")
async def startup_event():


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/generate-response")
def read_item(query: str, chat_history: list[str]):
    llm_chain = st.session_state['llm_chain']
    chain = st.session_state['llm_app']
    result = chain.run_chain(llm_chain, input, chat_history)
    answer = result['answer']
    chat_history.append((input, answer))

    return {"item_id": item_id, "q": q}



