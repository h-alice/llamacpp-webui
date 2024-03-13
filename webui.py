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
            st.markdown("### RAG Settings")
            st.markdown("Chunk Size: 文章分割的大小")
            st.markdown("Chunk Overlap: 文章分割的重疊大小")
            st.markdown("Top K: 保留機率最高的前 K 個文章")

        st.markdown("### LLM Generation Parameter")
        model_topk = st.slider("Top K", 0, 200, 10, key="model_topk")
        model_topp = st.slider("Top P", 0.0, 1.0, 0.9, key="model_topp")
        model_temperature = st.slider("Temperature", 0.0, 1.0, 0.01, key="model_temperature")
        model_repetition_penalty = st.slider("Repetition Penalty", 0.0, 2.0, 1.10, key="model_repetition_penalty")

        # TODO: Refactor, extract document processing logic.
        st.markdown("### RAG Settings")
        rag_chunk_size = st.slider("Chunk Size", 0, 500, 100, key="rag_chunk_size")
        rag_chunk_overlap = st.slider("Chunk Overlap", 0, 100, 25, key="rag_chunk_overlap")
        rag_topk = st.slider("Top K", 0, 100, 3, key="rag_topk")


    # File upload interface
    with st.expander("文件上傳"):
        uploaded_files = st.file_uploader("Choose a file", accept_multiple_files=True)

        if uploaded_files is not None:

            all_document_full_names = []
            for _file in uploaded_files:
                file_full_name = f"{st.session_state.session_id}-{_file.name}"  # Create file name.
                bytes_data = _file.getvalue() # Get raw data.
                doc_output = document_folder / file_full_name # Destination file.
                doc_output.write_bytes(bytes_data) # Write file to document folder.
                all_document_full_names.append(doc_output.absolute()) # Append current file to list.

            st.session_state.documents = all_document_full_names

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

        rag_param = RagParameters.new_rag_parameter(
            chunk_size=rag_chunk_size,
            chunk_overlap=rag_chunk_overlap,
            top_k=rag_topk,
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
        if st.session_state["documents"]:   # Document list is not null, invoke RAG.
            topk_doc_score = topk_documents(user_input, embedding_conf, rag_param, st.session_state["documents"])
            rag_docs = [x for x, _ in topk_doc_score]
            rag_reference = ""
            for d, score in topk_doc_score:
                rag_reference += "```\n"
                rag_reference += d.page_content
                rag_reference += "\n"
                rag_reference += "```\n"
            with st.expander("參考文件 Referenced Document"):
                st.markdown(rag_reference)

        # Prompt crafting.
        prompt = craft_prompt(user_input, rag_docs, keep_placeholder=False)
        # TODO: Append history to prompt.
        #prompt = "".join(st.session_state.history) + prompt
        # Simulating bot typing.
        for response in llm_stream_result(llm_instance, prompt, llm_model_conf, llm_param): # type: ignore
            if "undertale" in prompt.lower():  # type: ignore
                cursor = "❤️"
            else:
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