import streamlit as st
import uuid
from chatbot_async import  build_graph,retrieve_all_threads
from langchain_core.messages import HumanMessage,AIMessage,ToolMessage
import asyncio


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
   async def fetch_state():
      chatbot=await build_graph()
      return await chatbot.aget_state(config={'configurable':{"thread_id":thread_id}})
   state=asyncio.run(fetch_state())
   if state.values:
         return state.values.get('messages',[])

   return []

# CONFIG={'configurable':{'thread_id':st.session_state['thread_id']}}

CONFIG={
     "configurable":{"thread_id":st.session_state["thread_id"],
          "metadata":{
               "thread_id":st.session_state["thread_id"]
          },
          "run_name":"chat_turn",
          }
}
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
    # 1. Handle the user input
    st.session_state['message_history'].append({'role':'user','content':user_input})
    with st.chat_message('user'):
        st.write(user_input)

    # 2. Handle the Assistant output (Notice how this is indented INSIDE the if block!)
    with st.chat_message('assistant'):
        # Create an empty box on the screen
        tool_container=st.container()
        message_placeholder = st.empty()

        async def process_stream():
         chatbot=await build_graph()
         full_response = ""

        # Iterate through the stream directly
         async for message_chunk, metadata in chatbot.astream(
             {"messages": [("user", user_input)]},
             config=CONFIG,
              stream_mode="messages"
         ):

             if hasattr(message_chunk,'tool_calls') and len(message_chunk.tool_calls)>0:
                  with tool_container:
                       for tool in message_chunk.tool_calls:
                            st.info(f"Agent is using tool:`{tool['name']}`...")

             elif isinstance(message_chunk,ToolMessage):
                  with tool_container:
                       with st.expander(f"Data received from {message_chunk.name}"):
                           st.write(message_chunk.content)

             elif isinstance(message_chunk,AIMessage):
                  content=message_chunk.content

                  if isinstance(content, list):
                       for item in content:
                            if isinstance(item, dict) and 'text' in item:
                                 if item['text']:
                                      full_response+=item['text']
                                      message_placeholder.markdown(full_response+"▌")
                  elif isinstance(content,str) and content:
                      full_response+=content
                      message_placeholder.markdown(full_response + "▌")

        # Stream is finished! Remove the cursor and show final text
         message_placeholder.markdown(full_response)
         return full_response

        final_response=asyncio.run(process_stream())

    # Save to history (Also indented inside the if block)
    st.session_state['message_history'].append({'role': 'assistant', 'content':final_response})
