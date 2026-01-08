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
from chatops.session_manager import SessionManager
from config.settings import settings

st.set_page_config(page_title="Enterprise ChatOps & AIOps", layout="wide")

# Initialize all session state variables
if "page" not in st.session_state:
    st.session_state.page = "ChatOps"
if "session_manager" not in st.session_state:
    st.session_state.session_manager = None
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "open_menu" not in st.session_state:
    st.session_state.open_menu = None

# ChatGPT-style CSS
st.markdown("""
<style>
/* Main container */
.main .block-container {
    max-width: 100% !important;
    padding-top: 2rem;
}

/* Sidebar styling - match ChatGPT background */
[data-testid="stSidebar"] {
    background-color: #f9f9f9 !important;
    padding: 0 !important;
}

/* Remove ALL padding and margins from sidebar containers */
[data-testid="stSidebar"] > div {
    padding: 0 !important;
    margin: 0 !important;
}

[data-testid="stSidebar"] > div > div {
    padding: 0 0.5rem !important;
    margin: 0 !important;
}

/* All text - dark on light background */
[data-testid="stSidebar"] {
    color: #1a1a1a !important;
}

/* Force left alignment for everything */
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] button {
    text-align: left !important;
    align-items: center !important;
    justify-content: flex-start !important;
}

/* Buttons - exact ChatGPT measurements: py-1.5 (0.375rem) px-2 (0.5rem) */
[data-testid="stSidebar"] button {
    width: 100%;
    margin: 0 !important;
    padding: 0.375rem 0.5rem !important;
    border-radius: 0.375rem;
    border: none;
    background-color: transparent !important;
    color: #1a1a1a !important;
    transition: background-color 0.15s;
    font-size: 0.875rem;
    font-weight: 400;
    display: flex !important;
    text-align: left !important;
    align-items: center !important;
    justify-content: flex-start !important;
    line-height: 1.2;
    gap: 0.375rem;
}

/* Hover - exact ChatGPT hover */
[data-testid="stSidebar"] button:hover {
    background-color: rgba(0,0,0,0.05) !important;
}

/* Delete X button - more subtle */
[data-testid="stSidebar"] button[title*="Delete"] {
    background-color: transparent !important;
    color: #9ca3af !important;
    padding: 0.25rem 0.4rem !important;
    width: auto;
    font-size: 0.875rem;
    opacity: 0.6;
}

[data-testid="stSidebar"] button[title*="Delete"]:hover {
    background-color: #fee2e2 !important;
    color: #dc2626 !important;
    opacity: 1;
}

/* Text input - match ChatGPT style */
[data-testid="stSidebar"] input {
    background-color: #f5f5f5 !important;
    border: 1px solid transparent !important;
    border-radius: 0.375rem;
    color: #1a1a1a !important;
    padding: 0.375rem 0.5rem !important;
    margin: 0 !important;
    font-size: 0.875rem;
}

[data-testid="stSidebar"] input::placeholder {
    color: #9ca3af !important;
}

[data-testid="stSidebar"] input:focus {
    background-color: #ffffff !important;
    border-color: #e5e5e5 !important;
    outline: none !important;
}

/* Divider - minimal spacing like ChatGPT */
[data-testid="stSidebar"] hr {
    border-color: #e5e5e5 !important;
    margin: 0.25rem 0 !important;
}

/* Markdown text */
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stMarkdown p {
    text-align: left !important;
    color: #1a1a1a !important;
    margin: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    # Page Navigation at TOP (not dropdown)
    if st.button("💬 ChatOps", key="nav_chatops", use_container_width=True):
        st.session_state.page = "ChatOps"
        st.rerun()

    if st.button("🚨 AIOps Dashboard", key="nav_aiops", use_container_width=True):
        st.session_state.page = "AIOps Dashboard"
        st.rerun()

    if st.button("📚 Knowledge Management", key="nav_knowledge", use_container_width=True):
        st.session_state.page = "Knowledge Management"
        st.rerun()

    st.markdown("---")

    # New Chat button (only show on ChatOps page)
    if st.session_state.page == "ChatOps":
        if st.button("➕ New chat", key="new_chat_btn"):
            if st.session_state.session_manager is None:
                st.session_state.session_manager = SessionManager(settings.SESSIONS_DIR)
            new_session_id = st.session_state.session_manager.create_session("New Chat")
            st.session_state.current_session_id = new_session_id
            st.rerun()

        # Search bar
        search = st.text_input("🔍", placeholder="Search chats...", label_visibility="collapsed")

        st.markdown("---")

        # Load sessions
        if st.session_state.session_manager is None:
            st.session_state.session_manager = SessionManager(settings.SESSIONS_DIR)

        session_manager = st.session_state.session_manager
        sessions = session_manager.list_sessions()

        # Filter by search
        if search:
            sessions = [s for s in sessions if search.lower() in s["title"].lower()]

        # Initialize current session if needed
        if st.session_state.current_session_id is None and sessions:
            st.session_state.current_session_id = sessions[0]["id"]
        elif st.session_state.current_session_id is None and not sessions:
            new_id = session_manager.create_session("New Chat")
            st.session_state.current_session_id = new_id
            sessions = session_manager.list_sessions()

        # Display chat sessions
        for session in sessions:
            session_id = session["id"]
            title = session["title"]
            is_current = (session_id == st.session_state.current_session_id)

            # Session row with delete button
            col1, col2 = st.columns([5, 1], gap="small")

            with col1:
                if is_current:
                    st.markdown(f"**▶ {title[:25]}...**" if len(title) > 25 else f"**▶ {title}**")
                else:
                    if st.button(
                        title[:25] + "..." if len(title) > 25 else title,
                        key=f"sess_{session_id}",
                        use_container_width=True
                    ):
                        st.session_state.current_session_id = session_id
                        st.rerun()

            with col2:
                # Direct X delete button (no menu)
                if st.button("✕", key=f"del_{session_id}", help="Delete chat"):
                    session_manager.delete_session(session_id)
                    remaining = session_manager.list_sessions()
                    st.session_state.current_session_id = remaining[0]["id"] if remaining else None
                    st.rerun()

    # Get current page
    page = st.session_state.get("page", "ChatOps")

# --- ChatOps Page ---
if "ChatOps" in page:
    # Get session manager (initialized in sidebar)
    session_manager = st.session_state.session_manager

    # Load current session
    current_session_id = st.session_state.current_session_id
    current_session = session_manager.get_session(current_session_id)

    if current_session:
        messages = current_session.get("messages", [])
        # Show session title as header
        st.title(f"💬 {current_session.get('title', 'New Chat')}")
    else:
        messages = []
        st.title("💬 New Chat")

    # Display chat messages
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("How can I help you?"):
        from datetime import datetime

        # Add user message
        user_msg = {"role": "user", "content": prompt, "timestamp": datetime.now().isoformat()}
        messages.append(user_msg)

        with st.chat_message("user"):
            st.markdown(prompt)

        # Get response
        with st.chat_message("assistant"):
            with st.spinner("🤖 CrewAI Agents working..."):
                try:
                    # Format history
                    history_str = "\n".join([f"{m['role']}: {m['content']}" for m in messages[:-1]])

                    crew = ChatOpsCrew()
                    response = crew.run(prompt, chat_history=history_str)

                    # Convert CrewOutput to string for display and storage
                    response_str = str(response)
                    st.markdown(response_str)

                    # Add assistant message
                    asst_msg = {"role": "assistant", "content": response_str, "timestamp": datetime.now().isoformat()}
                    messages.append(asst_msg)

                    # Save session
                    # Generate title from first message if this is a new session
                    if current_session:
                        title = current_session.get("title")
                        if len(messages) == 2 and title == "New Chat":
                            title = session_manager.generate_title(prompt)

                        session_manager.update_session(
                            current_session_id,
                            messages,
                            title=title
                        )

                    # Update UI to show new title
                    st.rerun()

                except Exception as e:
                    st.error(f"Error: {e}")
                    import traceback
                    st.error(traceback.format_exc())

# --- AIOps Page ---
elif "AIOps Dashboard" in page:
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
elif "Knowledge Management" in page:
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
