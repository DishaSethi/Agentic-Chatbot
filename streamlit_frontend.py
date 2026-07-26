import streamlit as st
import uuid
from langgraph_backend import chatbot,retrieve_all_threads
from langchain_core.messages import HumanMessage



def get_text(chunk):
     if isinstance(chunk.content,str):
          return chunk.content
     elif isinstance(chunk.content,list):
          return "".join(part.get("text","") for part in chunk.content if isinstance(part,dict))
     return ""
if 'thread_id' not in st.session_state:
     st.session_state['thread_id']=str(uuid.uuid4())

def generate_thread_id():
     return str(uuid.uuid4())

def reset_chat():
     thread_id=generate_thread_id()
     st.session_state['thread_id']=thread_id
     add_thread(st.session_state['thread_id'])
     st.session_state['message_history']=[]

def add_thread(thread_id):
     if thread_id not in st.session_state['chat_threads']:
          st.session_state['chat_threads'].append(thread_id)


def load_conversation(thread_id):
    state=chatbot.get_state(config={'configurable':{"thread_id":thread_id}})
    if state.values:
         return state.values.get('messages',[])

    return []

CONFIG={'configurable':{'thread_id':st.session_state['thread_id']}}
#





if 'chat_threads' not in st.session_state:
     st.session_state['chat_threads']=retrieve_all_threads()

if 'thread_id' not in st.session_state:
     st.session_state['thread_id']=generate_thread_id()
     add_thread(st.session_state['thread_id'])


if 'message_history' not in st.session_state:
     st.session_state['message_history']=[]


#
st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
     reset_chat()
     st.rerun()

st.sidebar.header('My Conversations')

for thread_id in st.session_state['chat_threads'][::-1]:
 if st.sidebar.button(str(thread_id)[:8]+"..."):
   st.session_state['thread_id']=thread_id
   messages=load_conversation(thread_id)

   temp_messages=[]

   for message in messages:
        if isinstance(message,HumanMessage):
             role='user'
        else:
             role='assistant'
        clean_content=get_text(message)
        temp_messages.append({'role':role,'content':clean_content})

   st.session_state['message_history']=temp_messages
   st.rerun()
#
for message in st.session_state['message_history']:
     with st.chat_message(message['role']):
          st.text(message['content'])


user_input=st.chat_input('Type here')

if user_input:

     st.session_state['message_history'].append({'role':'user','content':user_input})
     with st.chat_message('user'):
         st.write(user_input)

     # response=chatbot.invoke({'messages':[HumanMessage(content=user_input)]},config=CONFIG )
     # ai_message=  response['messages'][-1].content

     with st.chat_message('assistant'):

         dynamic_config={'configurable':{'thread_id':st.session_state['thread_id']}}


         ai_message = st.write_stream(
              get_text(message_chunk) for message_chunk, metadata in chatbot.stream(
                   {'messages': [HumanMessage(content=user_input)]},
                   config=dynamic_config,
                   stream_mode='messages'
              )
         )
     st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})