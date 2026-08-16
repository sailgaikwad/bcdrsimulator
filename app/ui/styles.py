import streamlit as st

def inject_custom_css():
    st.markdown("""
        <style>
        /* Import Inter Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Global Typography and Base Styling */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Color Palette Overrides */
        :root {
            --primary-color: #3b82f6; /* Blue 500 */
            --primary-hover: #2563eb; /* Blue 600 */
            --primary-light: #eff6ff; /* Blue 50 */
            --bg-color: #f3f4f6;      /* Gray 100 */
            --card-bg: #ffffff;
            --text-main: #111827;     /* Gray 900 */
            --text-muted: #6b7280;    /* Gray 500 */
            --success: #10b981;       /* Emerald 500 */
            --warning: #f59e0b;       /* Amber 500 */
            --danger: #f43f5e;        /* Rose 500 */
            --info: #0ea5e9;          /* Sky 500 */
            --border-color: #e5e7eb;  /* Gray 200 */
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
        /* Make the radio buttons look like clean navigation links */
        div[role="radiogroup"] {
            gap: 0.25rem !important;
        }
        div[role="radiogroup"] > label {
            padding: 0.75rem 1rem !important;
            margin: 0 !important;
            border-radius: 0.5rem;
            cursor: pointer;
            transition: all 0.2s ease;
            background-color: transparent;
        }
        div[role="radiogroup"] > label:hover {
            background-color: var(--bg-color) !important;
        }
        /* Hide the actual radio circle */
        div[role="radiogroup"] > label > div:first-child {
            display: none !important;
        }
        /* Style the active selected state */
        div[role="radiogroup"] > label[data-baseweb="radio"][aria-checked="true"] {
            background-color: var(--primary-light) !important;
            color: var(--primary-color) !important;
        }
        div[role="radiogroup"] > label[data-baseweb="radio"][aria-checked="true"] p {
            color: var(--primary-color) !important;
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
            border: none !important;           /* Remove border, rely on shadow */
            background-color: var(--card-bg) !important;
            box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05), 0 0 3px rgba(0,0,0,0.02) !important; /* Soft, diffused shadow */
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
