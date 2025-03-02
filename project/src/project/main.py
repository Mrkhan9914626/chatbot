import streamlit as st
from project.crews.assistant_crew.assistant_crew import AssistantCrew
import sys
import os
import json
import re

def initialize_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'assistant_crew' not in st.session_state:
        st.session_state.assistant_crew = AssistantCrew()

def extract_raw_response(response):
    try:
        # Handle CrewOutput object
        if hasattr(response, 'raw'):
            return response.raw
            
        # Handle string response
        if isinstance(response, str):
            # First try to extract content between "raw":" and the next quote
            match = re.search(r'"raw":"(.*?)(?:","|\})', response)
            if match:
                return match.group(1).strip()
            
            # If that fails, try to remove all metadata sections
            response = re.sub(r'"pydantic":.*?(?=,"|}})', '', response)
            response = re.sub(r'"json_dict":.*?(?=,"|}})', '', response)
            response = re.sub(r'"tasks_output":.*?(?=,"|}})', '', response)
            response = re.sub(r'"token_usage":.*?(?=}|$)', '', response)
            
            # Try to extract just the raw message
            match = re.search(r'"raw":"(.*?)"', response)
            if match:
                return match.group(1).strip()
            
            # If still no match, try JSON parsing as last resort
            try:
                data = json.loads(response)
                if isinstance(data, dict):
                    return data.get('raw', response)
            except:
                pass
                
        return str(response)
    except Exception:
        return str(response)

def main():
    st.set_page_config(
        page_title="AI Personal Assistant",
        page_icon="🤖",
        layout="wide"
    )
    
    # Add sidebar with clear chat button
    with st.sidebar:
        st.title("Options")
        if st.button("🗑️ Clear Chat History", type="primary"):
            st.session_state.messages = []
            st.rerun()
    
    initialize_session_state()
    
    st.title("🤖 AI Personal Assistant")
    st.markdown("""
    Welcome! I'm your AI assistant. I can help you with various tasks and remember our conversations.
    """)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("You:"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.assistant_crew.crew().kickoff(
                        inputs={
                            "question": prompt
                        }
                    )
                    # Extract only the raw response and clean it
                    clean_response = extract_raw_response(response)
                    if isinstance(clean_response, str):
                        clean_response = clean_response.replace('\\n', '\n').replace('\\"', '"')
                    st.write(clean_response)
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": clean_response})
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()

