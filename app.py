"""
Streamlit UI for Yakr Executive Summary Generator.
Professional branded interface.
"""

import asyncio
import base64
import logging
import os
import tempfile
from pathlib import Path

import streamlit as st

from filters import filter_all_candidates
from generator import generate_all, generate_summary
from parser import group_by_client, parse_workbooks

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Page Config & Brand Assets
# ---------------------------------------------------------------------------

ASSETS_DIR = Path(__file__).parent / "assets"

st.set_page_config(
    page_title="Yakr. Executive Summaries",
    page_icon=str(ASSETS_DIR / "yakr-icon-black.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_base64_image(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


LOGO_B64 = get_base64_image(ASSETS_DIR / "yakr-logo-red-transparent.png")

# ---------------------------------------------------------------------------
# Password Gate
# ---------------------------------------------------------------------------

def check_password() -> bool:
    """Show a branded login page and return True if the password is correct."""
    if st.session_state.get("authenticated"):
        return True

    # Minimal CSS for login page
    st.markdown(f"""
    <style>
        @import url('https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700,900&display=swap');
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        section[data-testid="stSidebar"] {{display: none;}}
    </style>
    <div style="text-align: center; padding-top: 4rem;">
        <img src="data:image/png;base64,{LOGO_B64}" width="160" alt="Yakr.">
        <h2 style="font-family: Satoshi, Arial, sans-serif; margin-top: 1.5rem;">Executive Summary Generator</h2>
        <p style="color: #888; margin-bottom: 2rem;">Enter your password to continue</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        password = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Password")
        if st.button("Log in", type="primary", use_container_width=True):
            try:
                correct_password = st.secrets["APP_PASSWORD"]
            except Exception:
                correct_password = os.environ.get("APP_PASSWORD", "yakr2026")
            if password == correct_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password")

    return False


if not check_password():
    st.stop()

# ---------------------------------------------------------------------------
# Custom CSS — Yakr Brand Styling
# ---------------------------------------------------------------------------

st.markdown(f"""
<style>
    /* Import Satoshi font */
    @import url('https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700,900&display=swap');

    /* Brand colors */
    :root {{
        --yakr-red: #ff004f;
        --yakr-green: #0ae57d;
        --yakr-blue: #034dff;
        --yakr-black: #000000;
        --yakr-dark: #111111;
        --yakr-gray: #f7f7f8;
        --yakr-border: #e5e5e5;
    }}

    /* Global typography */
    html, body, [class*="css"] {{
        font-family: 'Satoshi', Arial, sans-serif;
    }}

    /* Hide default Streamlit header/footer but keep sidebar toggle */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header[data-testid="stHeader"] {{
        background: transparent !important;
        backdrop-filter: none !important;
    }}
    header[data-testid="stHeader"] .stDeployButton {{
        visibility: hidden;
    }}

    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background-color: var(--yakr-black);
        color: white;
    }}
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] span {{
        color: white !important;
    }}
    section[data-testid="stSidebar"] .stRadio label span p {{
        color: white !important;
    }}
    section[data-testid="stSidebar"] hr {{
        border-color: #333 !important;
    }}

    /* Sidebar file uploader */
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] {{
        background-color: #1a1a1a;
        border-radius: 8px;
        padding: 8px;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] label {{
        color: #ccc !important;
        font-size: 0.85rem;
    }}
    /* File uploader drop zone — dark background to match sidebar */
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
        background-color: #1a1a1a !important;
        border-color: #444 !important;
        color: white !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] span,
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small,
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] p,
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {{
        color: #ccc !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {{
        background-color: #333 !important;
        border-color: #555 !important;
    }}

    /* Generate button */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
        background-color: var(--yakr-red) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
        font-family: 'Satoshi', Arial, sans-serif;
        font-weight: 700;
        font-size: 1rem;
        padding: 0.6rem 1rem;
        transition: all 0.2s ease;
    }}
    section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {{
        background-color: #e0004a !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(255, 0, 79, 0.3);
    }}

    /* Main area */
    .main .block-container {{
        padding-top: 2rem;
        max-width: 1100px;
    }}

    /* Metric cards */
    div[data-testid="stMetric"] {{
        background: white;
        border: 1px solid var(--yakr-border);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}
    div[data-testid="stMetric"] label {{
        color: #888 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: var(--yakr-black) !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
    }}

    /* Email preview container */
    .email-preview {{
        background: white;
        border: 1px solid var(--yakr-border);
        border-radius: 12px;
        padding: 2rem 2.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        font-family: Arial, sans-serif;
        font-size: 0.95rem;
        line-height: 1.65;
        color: #222;
        white-space: pre-wrap;
        max-height: 600px;
        overflow-y: auto;
    }}
    .email-preview-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid var(--yakr-red);
    }}
    .email-preview-header h3 {{
        margin: 0;
        font-family: 'Satoshi', Arial, sans-serif;
        font-weight: 700;
        color: var(--yakr-black);
    }}
    .email-preview-badge {{
        background: #f0fff5;
        color: #059040;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        border: 1px solid #b7f5d0;
    }}

    /* Client table */
    .client-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
    }}
    .client-table th {{
        text-align: left;
        padding: 0.6rem 1rem;
        border-bottom: 2px solid var(--yakr-black);
        font-weight: 700;
        color: var(--yakr-black);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .client-table td {{
        padding: 0.55rem 1rem;
        border-bottom: 1px solid #f0f0f0;
        color: #333;
    }}
    .client-table tr:hover td {{
        background: #fafafa;
    }}
    .client-table .branch-tag {{
        background: #f0f0f0;
        color: #666;
        font-size: 0.7rem;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        margin-left: 0.5rem;
    }}
    .count-pill {{
        display: inline-block;
        min-width: 28px;
        text-align: center;
        padding: 0.15rem 0.5rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
    }}
    .count-active {{
        background: #f0fff5;
        color: #059040;
    }}
    .count-nomove {{
        background: #f5f5f5;
        color: #888;
    }}

    /* Page header */
    .page-header {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.25rem;
    }}
    .page-header h1 {{
        font-family: 'Satoshi', Arial, sans-serif;
        font-weight: 700;
        font-size: 1.6rem;
        color: var(--yakr-black);
        margin: 0;
    }}
    .page-subtitle {{
        color: #888;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }}

    /* Welcome card */
    .welcome-card {{
        background: linear-gradient(135deg, #fff 0%, #fafafa 100%);
        border: 1px solid var(--yakr-border);
        border-radius: 16px;
        padding: 3rem;
        text-align: center;
        max-width: 600px;
        margin: 3rem auto;
    }}
    .welcome-card h2 {{
        font-family: 'Satoshi', Arial, sans-serif;
        font-weight: 700;
        margin-bottom: 1rem;
    }}
    .welcome-card .steps {{
        text-align: left;
        margin: 1.5rem auto;
        max-width: 400px;
    }}
    .welcome-card .step {{
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
        font-size: 0.9rem;
        color: #444;
    }}
    .welcome-card .step-num {{
        background: var(--yakr-red);
        color: white;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 700;
        flex-shrink: 0;
    }}

    /* Download button */
    .stDownloadButton > button {{
        background-color: var(--yakr-black) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
        font-weight: 600;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
    }}
    .stTabs [data-baseweb="tab"] {{
        font-family: 'Satoshi', Arial, sans-serif;
        font-weight: 500;
        font-size: 0.85rem;
        padding: 0.5rem 1rem;
    }}
    .stTabs [aria-selected="true"] {{
        border-bottom-color: var(--yakr-red) !important;
        color: var(--yakr-red) !important;
    }}

    /* Progress bar */
    .stProgress > div > div {{
        background-color: var(--yakr-red) !important;
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    # Logo
    st.markdown(f"""
        <div style="padding: 1rem 0 1.5rem 0; text-align: center;">
            <img src="data:image/png;base64,{LOGO_B64}" width="120" alt="Yakr.">
        </div>
    """, unsafe_allow_html=True)

    st.markdown("##### Data Files")

    vm_file = st.file_uploader(
        "Active Visa Matters",
        type=["xlsx"],
        key="vm_file",
        label_visibility="collapsed",
        help="Upload the Active Visa Matters xlsx file",
    )
    if vm_file:
        st.markdown(f"<small style='color:#0ae57d;'>Active Visa Matters loaded</small>", unsafe_allow_html=True)
    else:
        st.markdown(f"<small style='color:#666;'>Upload Active Visa Matters (.xlsx)</small>", unsafe_allow_html=True)

    cp_file = st.file_uploader(
        "Capacity Planning",
        type=["xlsx"],
        key="cp_file",
        label_visibility="collapsed",
        help="Upload the Capacity Planning xlsx file",
    )
    if cp_file:
        st.markdown(f"<small style='color:#0ae57d;'>Capacity Planning loaded</small>", unsafe_allow_html=True)
    else:
        st.markdown(f"<small style='color:#666;'>Upload Capacity Planning (.xlsx)</small>", unsafe_allow_html=True)

    st.divider()
    st.markdown("##### Options")

    greeting = st.radio("Greeting", ["Morning", "Afternoon"], horizontal=True, label_visibility="collapsed")
    st.markdown(f"<small style='color:#888;'>Greeting: {greeting}</small>", unsafe_allow_html=True)

    include_finalised = st.checkbox("Include finalised cases", value=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def save_uploaded_file(uploaded_file) -> Path:
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        return Path(tmp.name)


def render_client_table(clients, sorted_names):
    """Render a styled HTML table of clients."""
    rows = ""
    for name in sorted_names:
        c = clients[name]
        active = len(c.active_candidates)
        no_move = len(c.no_movement_candidates)
        branch_tag = ""
        if c.parent_company:
            branch_tag = f'<span class="branch-tag">{c.parent_company}</span>'

        rows += f"""
        <tr>
            <td><strong>{c.company_name}</strong>{branch_tag}</td>
            <td>{c.candidate_count}</td>
            <td><span class="count-pill count-active">{active}</span></td>
            <td><span class="count-pill count-nomove">{no_move}</span></td>
        </tr>"""

    return f"""
    <table class="client-table">
        <thead>
            <tr>
                <th>Client</th>
                <th>Total</th>
                <th>Active</th>
                <th>No Movement</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """


def render_email_preview(text: str, client_name: str):
    """Render email text in a styled preview container."""
    # Escape HTML but preserve line breaks
    import html
    escaped = html.escape(text)
    st.markdown(f"""
        <div class="email-preview-header">
            <h3>Draft for {html.escape(client_name)}</h3>
            <span class="email-preview-badge">Ready for review</span>
        </div>
        <div class="email-preview">{escaped}</div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main Content
# ---------------------------------------------------------------------------

if vm_file and cp_file:
    @st.cache_data(show_spinner="Parsing spreadsheets...")
    def load_data(_vm_bytes: bytes, _cp_bytes: bytes, vm_name: str, cp_name: str):
        vm_path = save_uploaded_file(vm_file)
        cp_path = save_uploaded_file(cp_file)
        candidates = parse_workbooks(vm_path, cp_path)
        candidates = filter_all_candidates(candidates)
        clients = group_by_client(candidates)
        return clients

    clients = load_data(vm_file.getvalue(), cp_file.getvalue(), vm_file.name, cp_file.name)

    if not include_finalised:
        clients = {
            name: c for name, c in clients.items()
            if any(cand.sheet_source != "finalised" for cand in c.candidates)
        }

    sorted_names = sorted(clients.keys(), key=lambda n: (
        clients[n].parent_company or n,
        n,
    ))

    # --- Sidebar: Client Selection ---
    with st.sidebar:
        st.divider()
        st.markdown("##### Client")

        display_options = ["All Clients"] + [
            clients[n].display_name for n in sorted_names
        ]
        selected_display = st.selectbox(
            "Select client",
            display_options,
            label_visibility="collapsed",
        )

        generate_btn = st.button(
            "Generate Summary",
            type="primary",
            use_container_width=True,
        )

        # Sidebar footer
        st.markdown("""
            <div style="position: fixed; bottom: 1rem; left: 1rem; right: 1rem; max-width: 280px;">
                <hr style="border-color: #333;">
                <small style="color: #555;">Powered by Claude AI</small>
            </div>
        """, unsafe_allow_html=True)

    # --- Page Header ---
    st.markdown("""
        <div class="page-header">
            <h1>Executive Summaries</h1>
        </div>
    """, unsafe_allow_html=True)

    # --- All Clients View ---
    if selected_display == "All Clients":
        total_candidates = sum(c.candidate_count for c in clients.values())
        total_active = sum(len(c.active_candidates) for c in clients.values())
        total_no_move = sum(len(c.no_movement_candidates) for c in clients.values())

        st.markdown(f'<p class="page-subtitle">{len(clients)} companies &middot; {total_candidates} candidates</p>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Companies", len(clients))
        with col2:
            st.metric("Active", total_active)
        with col3:
            st.metric("No Movement", total_no_move)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(render_client_table(clients, sorted_names), unsafe_allow_html=True)

    # --- Single Client View ---
    else:
        selected_client = None
        for name in sorted_names:
            if clients[name].display_name == selected_display:
                selected_client = clients[name]
                break

        if selected_client:
            st.markdown(f'<p class="page-subtitle">{selected_client.candidate_count} candidates</p>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("With Updates", len(selected_client.active_candidates))
            with col2:
                st.metric("No Movement", len(selected_client.no_movement_candidates))

            if selected_client.active_candidates:
                with st.expander(f"Candidates with updates ({len(selected_client.active_candidates)})"):
                    for c in selected_client.active_candidates:
                        visa_label = c.visa_type.replace("Nom-Visa", "").replace("_", " ")
                        st.markdown(f"- **{c.full_name}** — {visa_label}")

            if selected_client.no_movement_candidates:
                with st.expander(f"No movement ({len(selected_client.no_movement_candidates)})"):
                    for c in selected_client.no_movement_candidates:
                        visa_label = c.visa_type.replace("Nom-Visa", "").replace("_", " ")
                        st.markdown(f"- {c.full_name} — {visa_label}")

    # --- Generate ---
    if generate_btn:
        if selected_display == "All Clients":
            st.markdown("<br>", unsafe_allow_html=True)
            progress_bar = st.progress(0, text="Generating summaries...")
            completed = {"count": 0}
            total = len(clients)

            def on_progress(company_name: str):
                completed["count"] += 1
                progress_bar.progress(
                    completed["count"] / total,
                    text=f"{completed['count']}/{total} — {company_name}",
                )

            client_list = [clients[n] for n in sorted_names]
            results = asyncio.run(generate_all(client_list, greeting, on_progress))
            progress_bar.progress(1.0, text="All summaries generated")

            if results:
                tabs = st.tabs(list(results.keys()))
                all_text_parts = []
                for tab, (name, text) in zip(tabs, results.items()):
                    with tab:
                        render_email_preview(text, name)
                        st.text_area(
                            "Edit draft",
                            value=text,
                            height=400,
                            key=f"edit_{name}",
                            label_visibility="collapsed",
                        )
                    all_text_parts.append(f"=== {name} ===\n\n{text}")

                st.markdown("<br>", unsafe_allow_html=True)
                all_text = "\n\n---\n\n".join(all_text_parts)
                st.download_button(
                    "Download All Summaries",
                    data=all_text,
                    file_name="yakr_executive_summaries.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

        else:
            if selected_client:
                with st.spinner(""):
                    try:
                        result = generate_summary(selected_client, greeting)

                        st.markdown("<br>", unsafe_allow_html=True)
                        render_email_preview(result, selected_client.display_name)

                        st.markdown("<br>", unsafe_allow_html=True)
                        with st.expander("Edit draft", expanded=False):
                            st.text_area(
                                "Edit",
                                value=result,
                                height=500,
                                key="single_edit",
                                label_visibility="collapsed",
                            )

                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Error generating summary: {e}")

# ---------------------------------------------------------------------------
# Welcome State — No files uploaded
# ---------------------------------------------------------------------------
else:
    st.markdown(f"""
        <div class="welcome-card">
            <img src="data:image/png;base64,{LOGO_B64}" width="140" alt="Yakr." style="margin-bottom: 1.5rem;">
            <h2>Executive Summary Generator</h2>
            <p style="color: #666; margin-bottom: 0.5rem;">
                Generate weekly client update emails from your visa matters and capacity planning spreadsheets.
            </p>
            <div class="steps">
                <div class="step">
                    <div class="step-num">1</div>
                    <div>Upload <strong>Active Visa Matters</strong> xlsx</div>
                </div>
                <div class="step">
                    <div class="step-num">2</div>
                    <div>Upload <strong>Capacity Planning</strong> xlsx</div>
                </div>
                <div class="step">
                    <div class="step-num">3</div>
                    <div>Select a client and click <strong>Generate</strong></div>
                </div>
                <div class="step">
                    <div class="step-num">4</div>
                    <div>Review, edit, and copy to Outlook</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
