import streamlit as st
import uuid
import sys
# import globals
# globals.initialize()

import kendra_chat_anthropic as anthropic
import kendra_chat_flan_xl as flanxl
import kendra_chat_flan_xxl as flanxxl
import kendra_chat_open_ai as openai
import kendra_chat_ai21 as ai21
import kendra_chat_falcon as falcon
import kendra_chat_bedrock as bedrock


USER_ICON = "images/user-icon.png"
AI_ICON = "images/logo.png"#"images/ai-icon.png"
MAX_HISTORY_LENGTH = 3
PROVIDER_MAP = {
    'openai': 'Open AI',
    'anthropic': 'Anthropic',
    'flanxl': 'Flan XL',
    'flanxxl': 'Flan XXL',
    'ai21': 'AI21',
    'falcon': 'Falcon',
    'bedrock': 'Bedrock',
}

# Check if the user ID is already stored in the session state
if 'user_id' in st.session_state:
    user_id = st.session_state['user_id']

# If the user ID is not yet stored in the session state, generate a random UUID
else:
    user_id = str(uuid.uuid4())
    st.session_state['user_id'] = user_id


if 'llm_chain' not in st.session_state:
    if (len(sys.argv) > 1):
        if (sys.argv[1] == 'anthropic'):
            st.session_state['llm_app'] = anthropic
            st.session_state['llm_chain'] = anthropic.build_chain()
        elif (sys.argv[1] == 'flanxl'):
            st.session_state['llm_app'] = flanxl
            st.session_state['llm_chain'] = flanxl.build_chain()
        elif (sys.argv[1] == 'falcon'):
            st.session_state['llm_app'] = falcon
            st.session_state['llm_chain'] = falcon.build_chain()
        elif (sys.argv[1] == 'flanxxl'):
            st.session_state['llm_app'] = flanxxl
            st.session_state['llm_chain'] = flanxxl.build_chain()
        elif (sys.argv[1] == 'openai'):
            st.session_state['llm_app'] = openai
            st.session_state['llm_chain'] = openai.build_chain()
        elif (sys.argv[1] == 'ai21'):
            st.session_state['llm_app'] = ai21
            st.session_state['llm_chain'] = ai21.build_chain()
        elif (sys.argv[1] == 'bedrock'):
            st.session_state['llm_app'] = bedrock
            st.session_state['llm_chain'] = bedrock.build_chain()
        else:
            raise Exception("Unsupported LLM: ", sys.argv[1])
    else:
        raise Exception("Usage: streamlit run app.py <anthropic|flanxl|flanxxl|openai|ai21|bedrock|falcon>")

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
    
if "chats" not in st.session_state:
    st.session_state.chats = [
        {
            'id': 0,
            'question': '',
            'answer': ''
        }
    ]

if "questions" not in st.session_state:
    st.session_state.questions = []

if "answers" not in st.session_state:
    st.session_state.answers = []

if "input" not in st.session_state:
    st.session_state.input = ""


st.markdown("""
        <style>
               .block-container {
                    padding-top: 32px;
                    padding-bottom: 32px;
                    padding-left: 0;
                    padding-right: 0;
                }
                .element-container img {
                    background-color: #000000;
                }

                .main-header {
                    font-size: 24px;
                }
        </style>
        """, unsafe_allow_html=True)


# Add a selectbox to the sidebar:
# add_selectbox = st.sidebar.selectbox(
#     'How would you like to be contacted?',
#     ('Email', 'Home phone', 'Mobile phone')
# )

# # Add a slider to the sidebar:
# add_slider = st.sidebar.slider(
#     'Kendra: Number of documents',
#     1, 10, (3)
# )


# max_new_tokens = st.sidebar.slider(
#     'LLM: Max number of tokens',
#     100, 1000, (400)
# )#400


def write_logo():
    col1, col2, col3 = st.columns([5, 1, 5])
    with col2:
        st.image(AI_ICON, use_column_width='always') 


def write_top_bar():
    col1, col2, col3 = st.columns([1,5,2])
    with col1:
        st.image(AI_ICON, use_column_width='always')
    with col2:
        selected_provider = sys.argv[1]
        if selected_provider in PROVIDER_MAP:
            provider = PROVIDER_MAP[selected_provider]
        else:
            provider = selected_provider.capitalize()
        header = f"An AI App powered by Amazon Kendra and Generative AI!"
        st.write(f"<h3 class='main-header'>{header}</h3>", unsafe_allow_html=True)
    with col3:
        clear = st.button("Clear Chat")
    return clear

clear = write_top_bar()

if clear:
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.input = ""
    st.session_state["chat_history"] = []

def handle_input():
    input = st.session_state.input
    question_with_id = {
        'question': input,
        'id': len(st.session_state.questions)
    }
    st.session_state.questions.append(question_with_id)

    chat_history = st.session_state["chat_history"]
    if len(chat_history) == MAX_HISTORY_LENGTH:
        chat_history = chat_history[:-1]

    llm_chain = st.session_state['llm_chain']
    chain = st.session_state['llm_app']
    result = chain.run_chain(llm_chain, input, chat_history)
    answer = result['answer']
    chat_history.append((input, answer))
    
    document_list = []
    if 'source_documents' in result:
        for d in result['source_documents']:
            if not (d.metadata['source'] in document_list):
                document_list.append((d.metadata['source']))

    st.session_state.answers.append({
        'answer': result,
        'sources': document_list,
        'id': len(st.session_state.questions)
    })
    st.session_state.input = ""

def write_user_message(md):
    col1, col2 = st.columns([1,12])
    
    with col1:
        st.image(USER_ICON, use_column_width='always')
    with col2:
        st.warning(md['question'])


def render_result(result):
    answer, sources = st.tabs(['Answer', 'Sources'])
    with answer:
        render_answer(result['answer'])
    with sources:
        if 'source_documents' in result:
            render_sources(result['source_documents'])
        else:
            render_sources([])

def render_answer(answer):
    col1, col2 = st.columns([1,12])
    with col1:
        st.image(AI_ICON, use_column_width='always')
    with col2:
        st.info(answer['answer'])

def render_sources(sources):
    col1, col2 = st.columns([1,12])
    with col2:
        with st.expander("Sources"):
            for s in sources:
                print(s.metadata)
                title = s.metadata["title"]
                title = s.metadata["source"]
                excerpt = s.metadata["excerpt"]
                st.write(title)
                st.caption(excerpt)

    
#Each answer will have context of the question asked in order to associate the provided feedback with the respective question
def write_chat_message(md, q):
    chat = st.container()

    print(md)

    with chat:
        if not md['sources']:
            st.info('The documents do not contain any information about the question.')
        else:
            render_answer(md['answer'])
        print("Rendering Sources..")
        # text = md['answer']['source_documents'][0].metadata
        # print(text)
        render_sources(md['answer']['source_documents'])#render_sources(md['sources'])
    
        
with st.container():
  for (q, a) in zip(st.session_state.questions, st.session_state.answers):
    write_user_message(q)
    write_chat_message(a, q)

st.markdown('---')
input = st.text_input("You are talking to an AI, ask any question.", key="input", on_change=handle_input)
