# import streamlit as st
# from langgraph.graph import StateGraph
# from src.state.workflow import WorkflowBuilder
# from src.llm.model import LLMModel
# # from src.state.state import State

# st.set_page_config(page_title="InstaForce - AI Pipeline", layout="wide")

# # Title
# st.title("⚡ InstaForce: AI Deployment Pipeline")

# # Input box for Salesforce requirement
# requirement = st.text_area(
#     label="Enter Salesforce Requirement",
#     placeholder="Paste the user story / requirement here...",
#     height=200
# )

# # Button
# run_button = st.button("🚀 Go Live")

# # Run pipeline when button clicked
# if run_button:
#     if not requirement.strip():
#         st.warning("Please enter a valid requirement.")
#     else:
#         st.write("### 🔄 Processing...")

#         # Load LLM
#         groqllm = LLMModel()
#         llm=groqllm.get_llm()

#         # Build workflow
#         workflow = WorkflowBuilder(llm)
#         graph=workflow.setup_graph()


#         # Initial state
#         state = {"requirement": requirement}

#         # Stream results
#         output_container = st.container()

#         def stream_callback(update):
#             # Called on every node update
#             with output_container:
#                 st.write(update)

#         # Run the graph
#         final_state = graph.invoke(state, stream=stream_callback)

#         # Final output
#         st.success("🎉 Completed Successfully!")
#         st.write("### 🏁 Final Output")
#         st.json(final_state)


import json
import time
import traceback
import streamlit as st
from typing import Any, Dict

# Use your existing imports / classes
from src.state.workflow import WorkflowBuilder
from src.llm.model import LLMModel

# Local uploaded image (from developer note)
PROJECT_IMAGE_PATH = "/mnt/data/af72e198-500e-402d-b9d6-76fecee9bd55.png"

st.set_page_config(page_title="InstaForce - AI powered Salesforce deployment engine", layout="wide")

# Global luxury-styled header CSS
st.markdown(
    """
    <style>
    .instaforce-hero {
        font-family: 'Segoe UI', system-ui, -apple-system, Roboto, Ubuntu, 'Helvetica Neue', Arial, sans-serif;
        font-size: 54px;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin: 0 0 8px 0;
        line-height: 1.15;
        background: linear-gradient(90deg, #7C3AED 0%, #06B6D4 50%, #22C55E 100%);
        background-size: 200% 200%;
        animation: gradientShift 6s ease infinite;
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        text-shadow: 0 1px 0 rgba(255,255,255,0.25);
    }
    .hero-container { margin-top: -30px; }
    .instaforce-subtitle {
        font-size: 26px;
        color: #7C8BA1;
        margin-bottom: 18px;
        text-align: center;
    }
    .hero-wrap {
        display: flex; align-items: center; justify-content: center; gap: 16px;
        flex-wrap: wrap;
    }
    .hero-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(124, 58, 237, 0.1);
        color: #7C3AED;
        font-weight: 600;
        border: 1px solid rgba(124, 58, 237, 0.25);
        font-size: 12px;
        box-shadow: 0 2px 10px rgba(124,58,237,0.12);
        backdrop-filter: blur(4px);
        animation: chipPulse 3.5s ease-in-out infinite;
    }

    /* Animated underline accent */
    .hero-underline {
        width: 160px; height: 3px; border-radius: 2px; margin: 8px auto 0 auto;
        background: linear-gradient(90deg, rgba(124,58,237,0.9), rgba(6,182,212,0.9), rgba(34,197,94,0.9));
        background-size: 200% 200%;
        animation: gradientShift 6s ease infinite;
    }

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    @keyframes chipPulse {
        0%, 100% { transform: translateZ(0) scale(1); box-shadow: 0 2px 10px rgba(124,58,237,0.12); }
        50% { transform: translateZ(0) scale(1.03); box-shadow: 0 4px 16px rgba(124,58,237,0.18); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- helpers ----
def safe_serialize(obj: Any) -> str:
    try:
        return json.dumps(obj, default=lambda o: getattr(o, "__dict__", str(o)), indent=2)
    except Exception:
        return str(obj)

def append_log(agent_logs: Dict[str, list], agent_name: str, message: str, level: str = "info"):
    agent_logs.setdefault(agent_name, []).append({"t": time.time(), "level": level, "msg": message})

# ---- UI layout ----
st.markdown(
        """
        <div class="hero-container" style="display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center;">
            <div class="hero-wrap">
                <div class="instaforce-hero">⚡ InstaForce</div>
            </div>
            <div class="hero-wrap" style="margin-top:4px;">
                <div class="hero-chip">AI-powered • Salesforce Deployment Engine</div>
            </div>
            <div class="hero-underline"></div>
            <div class="instaforce-subtitle">Ship Salesforce changes faster with an agentic, auditable pipeline.</div>
        </div>
        """,
        unsafe_allow_html=True,
)

left_col, mid_col, right_col = st.columns([3, 4, 4])

with left_col:
    st.header("Input")
    requirement = st.text_area(
        label="Enter Salesforce Requirement (User Story / URS)",
        placeholder="e.g. As a salesforce admin, I want an approval process for high-value opportunities...",
        height=260,
    )
    st.checkbox("Verbose logs", key="verbose_logs", value=True)
    # Advanced options
    with st.expander("Advanced options", expanded=False):
        max_runtime = st.slider("Simulated step delay (s) — used for nicer UX", min_value=0.0, max_value=2.0, value=0.2, step=0.1)
        show_project_image = st.checkbox("Show project screenshot", value=True)
    
    go_live = st.button("🚀 Go Live", type="primary")

    # if show_project_image:
    #     try:
    #         st.markdown("**Project structure (uploaded screenshot)**")
    #         st.image(PROJECT_IMAGE_PATH, use_column_width=True)
    #     except Exception:
    #         st.write("Project image not found at path:", PROJECT_IMAGE_PATH)

with mid_col:
    st.header("Live Agent Logs")
    log_area = st.empty()
    # Per-agent expanders will be populated at runtime
    agents_expanders = st.container()

with right_col:
    st.header("Results")
    result_area = st.empty()
    download_col1, download_col2 = st.columns(2)
    with download_col1:
        download_json_btn = st.empty()
    with download_col2:
        download_txt_btn = st.empty()
    st.markdown("---")
    st.subheader("Graph")
    graph_preview = st.empty()
    st.markdown("---")
    st.subheader("Run Summary")
    summary_area = st.empty()

# Session storage for persistent logs between reruns
if "agent_logs" not in st.session_state:
    st.session_state.agent_logs = {}
if "node_order" not in st.session_state:
    st.session_state.node_order = []

# ---- Execution ----
if go_live:
    if not requirement or not requirement.strip():
        st.warning("Please enter a valid requirement before clicking Go Live.")
    else:
        # Reset logs/state
        st.session_state.agent_logs = {}
        st.session_state.node_order = []

        # Show processing
        with st.spinner("Booting LLM and building workflow..."):
            try:
                # Initialize LLM and workflow builder (your classes)
                groqllm = LLMModel()
                llm = groqllm.get_llm()

                workflow_builder = WorkflowBuilder(llm)
                graph = workflow_builder.setup_graph()

                # Try to extract node names for progress & preview
                node_names = []
                try:
                    # langgraph StateGraph compiled object may expose nodes; try common attributes
                    if hasattr(graph, "nodes"):
                        node_names = list(graph.nodes.keys()) if isinstance(graph.nodes, dict) else list(graph.nodes)
                    elif hasattr(graph, "_nodes"):
                        node_names = list(graph._nodes)
                except Exception:
                    node_names = []

                # fallback if none found (we expect req_agent, design_agent, codegen_agent)
                if not node_names:
                    node_names = ["req_agent", "design_agent", "codegen_agent","deploy_agent"]

                st.session_state.node_order = node_names

            except Exception as e:
                st.error("Failed building workflow or initializing LLM.")
                st.exception(e)
                raise

        # Show graph preview (simple)
        with graph_preview:
            st.write("**Nodes**:", ", ".join(st.session_state.node_order))
            st.write("**Start →** " + " → ".join(st.session_state.node_order) + " → **END**")
# -------------------------
# BEFORE run: create placeholders for each agent expander
# -------------------------
    agent_placeholders = {}
    for n in st.session_state.node_order:
        # create a placeholder for each agent; initially show the waiting message inside an expander
        ph = agents_expanders.empty()
        with ph:
            exp = st.expander(f"{n}", expanded=False)
            with exp:
                st.write("Waiting for output...")
        agent_placeholders[n] = ph  # store the container placeholder

    # Ensure a session counter is present (avoid nonlocal)
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0

    progress = st.progress(0)
    total_nodes = len(st.session_state.node_order)

    # -------------------------
    # Streaming callback (used if graph supports stream)
    initial_state = {"requirement": requirement}

    # -------------------------
    def stream_callback(update):
        """
        Called when the graph emits streaming updates.
        The update shape may vary; try to infer agent name and message.
        """
        # infer agent name and message
        agent_name = None
        message = update

        if isinstance(update, dict):
            agent_name = update.get("agent") or update.get("node") or update.get("node_name")
            message = update.get("msg") or update.get("output") or update.get("result") or update

        # fallback: guess current agent if not provided
        if not agent_name:
            # pick by current index if available
            idx = st.session_state.current_index
            agent_name = st.session_state.node_order[idx] if idx < total_nodes else st.session_state.node_order[-1]

        # record into session logs
        append_log(st.session_state.agent_logs, agent_name, safe_serialize(message))

        # update the specific agent placeholder (replace its contents)
        ph = agent_placeholders.get(agent_name)
        if ph:
            ph.empty()  # clear prior contents
            with ph:
                exp = st.expander(f"{agent_name}", expanded=True)
                with exp:
                    logs = st.session_state.agent_logs.get(agent_name, [])
                    # show last N logs
                    for entry in logs[-20:]:
                        t = time.strftime("%H:%M:%S", time.localtime(entry["t"]))
                        st.text(f"[{t}] {entry['msg']}")

        # increment progress smartly (first message from an agent increments)
        if len(st.session_state.agent_logs.get(agent_name, [])) == 1:
            st.session_state.current_index = min(total_nodes, st.session_state.current_index + 1)
            progress.progress(st.session_state.current_index / total_nodes)

    # -------------------------
    # Invoke the graph (try streaming; fallback to sync)
    # -------------------------
    final_state = None
    try:
        # Try native streaming via graph.stream if available
        if hasattr(graph, "stream"):
            try:
                for update in graph.stream(initial_state):
                    stream_callback(update)
                # After streaming completes, get final state if supported
                if hasattr(graph, "get_state"):
                    final_state = graph.get_state()
                else:
                    # Fallback: invoke once to fetch final snapshot
                    final_state = graph.invoke(initial_state)
            except Exception:
                # If stream fails, fallback to invoke
                final_state = graph.invoke(initial_state)
        else:
            # preferred streaming call if invoke supports stream kw
            try:
                final_state = graph.invoke(initial_state, stream=stream_callback)
            except TypeError:
                # graph.invoke doesn't accept stream parameter — do sync run
                final_state = graph.invoke(initial_state)

        # Populate placeholders from final_state when no streaming per-agent outputs
        if isinstance(final_state, dict):
            any_updates = any(len(st.session_state.agent_logs.get(n, [])) > 0 for n in st.session_state.node_order)
            if not any_updates:
                for node in st.session_state.node_order:
                    node_output = final_state.get(node) or final_state.get(node + "_output")
                    ph = agent_placeholders.get(node)
                    if ph:
                        ph.empty()
                        with ph:
                            exp = st.expander(f"{node}", expanded=True)
                            with exp:
                                if node_output is None:
                                    st.write("No node-specific output available. Run completed.")
                                else:
                                    try:
                                        st.json(node_output)
                                    except Exception:
                                        st.text(safe_serialize(node_output))
        progress.progress(1.0)

    except Exception as e:
        tb = traceback.format_exc()
        append_log(st.session_state.agent_logs, "system", str(e), level="error")
        append_log(st.session_state.agent_logs, "system", tb, level="error")
        st.exception(e)
        final_state = {"error": str(e), "traceback": tb}

    # -------------------------
    # Final: show final_state in UI (right column)
    # -------------------------
    with result_area.container():
        st.success("🎉 Pipeline completed")
        
        # Display deployment status prominently
        if final_state and isinstance(final_state, dict) and "deploy_status" in final_state:
            deploy_status = final_state["deploy_status"]
            
            st.subheader("Deployment Status")
            
            if deploy_status.get("success"):
                st.success(f" {deploy_status.get('message', 'Deployment successful')}")
            else:
                st.error(f" {deploy_status.get('message', 'Deployment failed')}")
            
            # Show files deployed
            if deploy_status.get("written_files"):
                with st.expander("📄 Files Deployed", expanded=True):
                    for file in deploy_status["written_files"]:
                        st.code(file, language="text")
            
            # Show deployment details
            with st.expander(" Deployment Details", expanded=False):
                st.write(f"**Return Code:** {deploy_status.get('returncode')}")
                st.write(f"**Command:** `{deploy_status.get('deploy_command', 'N/A')}`")
                
                if deploy_status.get("parsed_response"):
                    st.write("**Salesforce CLI Response:**")
                    st.json(deploy_status["parsed_response"])
                
                if deploy_status.get("stdout"):
                    with st.expander("📋 CLI Output (stdout)", expanded=False):
                        st.code(deploy_status["stdout"], language="json")
                
                if deploy_status.get("stderr"):
                    with st.expander("⚠️ CLI Errors (stderr)", expanded=False):
                        st.code(deploy_status["stderr"], language="text")
            
            st.markdown("---")
        
        st.subheader("Final State (preview)")
        try:
            st.json(final_state)
        except Exception:
            st.text(safe_serialize(final_state))

        # provide downloads
        serialized = safe_serialize(final_state)
        download_json_btn.download_button(
            label="Download JSON",
            data=serialized,
            file_name="pipeline_result.json",
            mime="application/json",
        )
        download_txt_btn.download_button(
            label="Download raw text",
            data=str(serialized),
            file_name="pipeline_result.txt",
            mime="text/plain",
        )


        st.balloons()
        # st.snow()
