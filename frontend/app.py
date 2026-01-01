import streamlit as st
import sys
import os
import signal
import threading

# Hack: Patch signal.signal to avoid "ValueError: signal only works in main thread"
# This happens because Streamlit runs the script in a separate thread, but CrewAI/Telemetry 
# tries to register signal handlers which is only allowed in the main thread.
_original_signal = signal.signal
def _patched_signal(sig, handler):
    if threading.current_thread() is not threading.main_thread():
        return None
    return _original_signal(sig, handler)
signal.signal = _patched_signal

# Disable CrewAI Telemetry to avoid signal handler issues in Streamlit threads
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from chatops.crew import ChatOpsCrew
from aiops_workflow.graph import create_aiops_graph
from knowledge_base.ingest import add_document, get_uploaded_documents, remove_document

st.set_page_config(page_title="Enterprise ChatOps & AIOps", layout="wide")

# Hide Streamlit's default menu and footer
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Sidebar Navigation ---
with st.sidebar:
    st.title("🤖 ChatOps & AIOps")
    page = st.radio("Navigate", ["💬 ChatOps", "🚨 AIOps Dashboard", "📚 Knowledge Management"])
    st.divider()

# --- ChatOps Page ---
if page == "💬 ChatOps":
    st.header("Chat with your System")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("How can I help you?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("CrewAI Agents working..."):
                try:
                    # Format history
                    history_str = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[:-1]])
                    
                    crew = ChatOpsCrew()
                    response = crew.run(prompt, chat_history=history_str)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Error: {e}")

# --- AIOps Page ---
elif page == "🚨 AIOps Dashboard":
    st.title("AIOps Alert Management")
    st.markdown("Simulate system alerts and view the automated RCA workflow.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        alert_type = st.selectbox("Simulate Alert Type", ["High CPU Usage", "API Latency Spike", "Pod Crash"])
        if st.button("Trigger Alert"):
            st.session_state.alert_triggered = True
            st.session_state.alert_type = alert_type
            st.session_state.graph_state = {
                "alert_id": "ALERT-001",
                "alert_type": alert_type,
                "alert_details": {"severity": "High", "source": "Production"},
                "human_approval": None
            }
            
    with col2:
        if st.session_state.get("alert_triggered"):
            st.subheader("Workflow Execution")
            
            app = create_aiops_graph()
            
            # Run the graph
            current_state = st.session_state.graph_state
            
            with st.spinner("Running Diagnostic Agents..."):
                final_state = app.invoke(current_state)
                st.session_state.graph_state = final_state
            
            st.success("Diagnostics Complete")
            
            st.json(final_state)
            
            if final_state.get("suggested_action"):
                st.info(f"Suggested Action: {final_state['suggested_action']}")
                
                if st.button("Approve Action"):
                    # Re-run with approval
                    final_state["human_approval"] = True
                    with st.spinner("Executing Remediation..."):
                        post_approval_state = app.invoke(final_state)
                        st.success(post_approval_state.get("final_report"))

# --- Knowledge Management Page ---
elif page == "📚 Knowledge Management":
    st.title("Knowledge Base Management")
    st.markdown("Manage the documents available to the RAG agents.")
    
    st.subheader("Upload New Document")
    uploaded_file = st.file_uploader("Upload a file", type=["txt", "pdf", "docx"])
    if uploaded_file is not None:
        if st.button("Ingest Document"):
            with st.spinner("Ingesting..."):
                try:
                    file_content = uploaded_file.read()
                    file_type = uploaded_file.name.split(".")[-1].lower()
                    result = add_document(file_content, file_type, filename=uploaded_file.name)
                    st.success(result)
                    st.rerun() # Refresh list
                except Exception as e:
                    st.error(f"Error ingesting document: {e}")

    st.divider()
    
    st.subheader("Existing Documents")
    docs = get_uploaded_documents()
    
    if not docs:
        st.info("No custom documents uploaded yet. (System is using default mock data)")
    else:
        for doc in docs:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text(f"📄 {doc}")
            with col2:
                if st.button("Remove", key=f"del_{doc}"):
                    with st.spinner("Removing..."):
                        if remove_document(doc):
                            st.success(f"Removed {doc}")
                            st.rerun()
                        else:
                            st.error("Failed to remove document")
