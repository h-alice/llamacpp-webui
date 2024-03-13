##########################
# Chatbot User Interface #
##########################

# Python Standard Library Imports
import io  # Input/Output operations
import random  # Random number generation
import uuid  # Universally Unique Identifier generation
from pathlib import Path  # Handling file system paths
from typing import NamedTuple  # Type hinting for named tuples

# Third-Party Library Imports
import streamlit as st  # UI Framework for creating web applications
from langchain_core.language_models.llms import LLM
from langchain_community.llms import LlamaCpp

# Local Imports
from webui_config import UiConfig  # Configuration settings for the web UI
from llm_connector import llm_stream_result, LlmGenerationParameters, craft_prompt, craft_result_with_prompt
from document_rag_processor import topk_documents, RagParameters

def main_ui_logic(config: UiConfig, llm_instance: LLM) -> None:

    st.title("Chatbot Interface")

    ### Environment prepare.
    document_folder = Path(config.document_folder)
    # TODO: Logger: display warning.
    document_folder.mkdir(exist_ok=True)

    ### States
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "history" not in st.session_state:
        st.session_state.history = []

    if "documents" not in st.session_state:
        st.session_state.documents = []

    if "session_id" not in st.session_state:
        # Generate user session identifier.
        st.session_state.session_id = uuid.uuid4().hex

    ### Components


    with st.sidebar:
        st.markdown("# General Settings")
        with st.expander("參數說明"):
            st.markdown("### LLM Generation Parameter")
            st.markdown("Top K: 保留機率最高的前 K 個字")
            st.markdown("Top P: 從機率總和為 P 的字中選擇")
            st.markdown("Temperature: 生成時的亂度")
            st.markdown("Repetition Penalty: 重複字的懲罰")


        st.markdown("### LLM Generation Parameter")
        model_topk = st.slider("Top K", 0, 200, 10, key="model_topk")
        model_topp = st.slider("Top P", 0.0, 1.0, 0.9, key="model_topp")
        model_temperature = st.slider("Temperature", 0.0, 1.0, 0.75, key="model_temperature")
        model_repetition_penalty = st.slider("Repetition Penalty", 0.0, 2.0, 1.00, key="model_repetition_penalty")

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if user_input := st.chat_input("How can I help you today?"):

        # TODO: User model selection.
        llm_model_conf = config.llm_models
        embedding_conf = config.embedding_model

        llm_param = LlmGenerationParameters.new_generation_parameter(
            top_k=model_topk,
            top_p=model_topp,
            temperature=model_temperature,
            repetition_penalty=model_repetition_penalty,
            max_new_tokens=8192,
        )



        # Display user message in chat message container
        st.chat_message("user").markdown(user_input)

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

        ## RAG     
        rag_docs = []

        # Prompt crafting.
        prompt = craft_prompt(user_input, rag_docs, keep_placeholder=False)
        # TODO: Append history to prompt.
        #prompt = "".join(st.session_state.history) + prompt
        # Simulating bot typing.
        for response in llm_stream_result(llm_instance, prompt, llm_model_conf, llm_param): # type: ignore
            cursor = "❖"
            full_response += (response or "")
            message_placeholder.markdown(full_response + cursor)

        # While complete, display full bot response.
        message_placeholder.markdown(full_response)
        full_response_with_prompt = craft_result_with_prompt(user_input, full_response)

        # Add assistant response to chat history
        st.session_state.history.append(full_response_with_prompt)
        st.session_state.messages.append({"role": "assistant", "content": full_response})


if __name__ == "__main__":
    # Load config.
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = UiConfig.load_config_from_file(f)

    # Load LLM model.
    if config.llm_models.provider == "llama-cpp":
        llm_instance = LlamaCpp(
            model_path=config.llm_models.model_path,
            verbose=False,
        )
    else: raise NotImplementedError("Might implement sometime lol.")


    main_ui_logic(config=config, llm_instance=llm_instance)