import streamlit as st

def inject_custom_css():
    st.markdown("""
        <style>
        /* Import Inter Font and Material Symbols */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0');

        /* Global Typography and Base Styling */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Color Palette Overrides */
        :root {
            --primary-color: #374151; /* Gray 700 (Buttons) */
            --primary-hover: #4b5563; /* Gray 600 */
            --primary-light: #1f2937; /* Gray 800 (Active sidebar) */
            --bg-color: #000000;      /* Pure black */
            --card-bg: #111827;       /* Very dark gray */
            --text-main: #f9fafb;     /* White/Light gray */
            --text-muted: #9ca3af;    /* Gray 400 */
            --success: #10b981;       
            --warning: #f59e0b;       
            --danger: #f43f5e;        
            --info: #0ea5e9;          
            --border-color: #374151;  /* Gray 700 */
        }
        
        /* Main Application Background */
        .stApp {
            background-color: var(--bg-color);
        }

        /* Top Header Adjustment */
        header[data-testid="stHeader"] {
            background-color: transparent !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: var(--card-bg) !important;
            border-right: 1px solid var(--border-color);
        }
        
        .st-emotion-cache-16txtl3 {
            padding: 2rem 1rem;
        }

        /* Sidebar Radio Navigation Hack */
        /* Make the radio buttons look like a clean, full-width SaaS navigation */
        div[role="radiogroup"] {
            gap: 0.5rem !important; /* Generous spacing */
        }
        
        /* Ensure the label covers the full width and acts as a flex container */
        div[role="radiogroup"] label {
            padding: 0.75rem 1rem !important;
            margin: 0 !important;
            border-radius: 0.5rem;
            cursor: pointer;
            transition: all 0.2s ease;
            background-color: transparent;
            display: flex !important;
            align-items: center !important;
            width: 100% !important;
        }
        
        div[role="radiogroup"] label:hover {
            background-color: var(--bg-color) !important;
        }
        
        /* Hide the actual radio circle completely - use aggressive selectors */
        div[role="radiogroup"] label > *:not(:has(p)),
        div[role="radiogroup"] label[data-baseweb="radio"] > div:first-of-type,
        div[role="radiogroup"] label[data-baseweb="radio"] > input + div {
            display: none !important;
            width: 0 !important;
            height: 0 !important;
            opacity: 0 !important;
            visibility: hidden !important;
        }
        
        /* The text container */
        div[role="radiogroup"] label p {
            font-size: 0.95rem;
            color: var(--text-muted);
            font-weight: 500;
            display: flex;
            align-items: center;
            margin: 0;
            width: 100%;
        }
        
        /* Inject Icons using Material Symbols ligatures */
        div[role="radiogroup"] label p::before {
            font-family: 'Material Symbols Outlined';
            font-size: 1.25rem;
            margin-right: 0.75rem;
            color: var(--text-muted);
            transition: color 0.2s ease;
        }
        
        /* Target by nth-of-type if wrapped in divs, otherwise nth-child */
        div[role="radiogroup"] > div:nth-child(1) label p::before, div[role="radiogroup"] > label:nth-child(1) p::before { content: 'dashboard'; }
        div[role="radiogroup"] > div:nth-child(2) label p::before, div[role="radiogroup"] > label:nth-child(2) p::before { content: 'dns'; }
        div[role="radiogroup"] > div:nth-child(3) label p::before, div[role="radiogroup"] > label:nth-child(3) p::before { content: 'hub'; }
        div[role="radiogroup"] > div:nth-child(4) label p::before, div[role="radiogroup"] > label:nth-child(4) p::before { content: 'warning'; }
        div[role="radiogroup"] > div:nth-child(5) label p::before, div[role="radiogroup"] > label:nth-child(5) p::before { content: 'play_circle'; }
        div[role="radiogroup"] > div:nth-child(6) label p::before, div[role="radiogroup"] > label:nth-child(6) p::before { content: 'build'; }
        div[role="radiogroup"] > div:nth-child(7) label p::before, div[role="radiogroup"] > label:nth-child(7) p::before { content: 'balance'; }
        div[role="radiogroup"] > div:nth-child(8) label p::before, div[role="radiogroup"] > label:nth-child(8) p::before { content: 'security'; }
        div[role="radiogroup"] > div:nth-child(9) label p::before, div[role="radiogroup"] > label:nth-child(9) p::before { content: 'analytics'; }
        div[role="radiogroup"] > div:nth-child(10) label p::before, div[role="radiogroup"] > label:nth-child(10) p::before { content: 'history'; }
        
        /* Style the active selected state */
        div[role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"],
        div[role="radiogroup"] label:has(input:checked) {
            background-color: var(--primary-light) !important;
        }
        
        /* Bright Blue (#3b82f6) for the active text and icon */
        div[role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"] p,
        div[role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"] p::before,
        div[role="radiogroup"] label:has(input:checked) p,
        div[role="radiogroup"] label:has(input:checked) p::before {
            color: #3b82f6 !important;
            font-weight: 600;
        }

        /* Streamlit Primary Button Styling */
        button[kind="primary"] {
            background-color: var(--primary-color) !important;
            color: white !important;
            border: none !important;
            border-radius: 0.5rem !important;
            padding: 0.5rem 1rem !important;
            font-weight: 500 !important;
            box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.1), 0 2px 4px -1px rgba(79, 70, 229, 0.06) !important;
            transition: all 0.2s ease !important;
        }
        button[kind="primary"]:hover {
            background-color: var(--primary-hover) !important;
            box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.1), 0 4px 6px -2px rgba(79, 70, 229, 0.05) !important;
            transform: translateY(-1px);
        }

        /* Metrics Styling */
        div[data-testid="stMetricValue"] {
            font-weight: 600 !important;
            color: var(--text-main) !important;
        }
        div[data-testid="stMetricLabel"] {
            color: var(--text-muted) !important;
            font-size: 0.875rem !important;
            font-weight: 500 !important;
        }

        /* Container Border Overrides to look like tailwind cards */
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            border-radius: 1.25rem !important; /* Large rounded corners */
            border: 1px solid var(--border-color) !important; /* Add subtle border for dark mode */
            background-color: var(--card-bg) !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5) !important; /* Darker shadow */
            padding: 1.5rem !important;
        }

        /* Expander Styling */
        div[data-testid="stExpander"] {
            border: 1px solid var(--border-color) !important;
            border-radius: 0.5rem !important;
            background-color: var(--card-bg) !important;
        }
        
        /* DataFrame Styling overrides */
        .stDataFrame {
            border-radius: 0.5rem;
            border: 1px solid var(--border-color);
            overflow: hidden;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: var(--text-main);
            font-weight: 600 !important;
            letter-spacing: -0.025em;
        }
        
        </style>
    """, unsafe_allow_html=True)
