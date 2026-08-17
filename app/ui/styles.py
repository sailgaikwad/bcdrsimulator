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

        /* Semantic Color Palette */
        :root {
            --success: #10b981;       
            --warning: #f59e0b;       
            --danger: #f43f5e;        
            --info: #0ea5e9;          
        }
        
        /* Top Header Adjustment */
        header[data-testid="stHeader"] {
            background-color: transparent !important;
        }

        /* Sidebar Styling Adjustment */
        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.2);
        }
        
        .st-emotion-cache-16txtl3 {
            padding: 2rem 1rem;
        }

        /* Sidebar Radio Navigation Hack */
        div[role="radiogroup"] {
            gap: 0.5rem !important;
        }
        
        /* Ensure the label covers the full width and acts as a flex container */
        label[data-testid="stRadioOption"] {
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
        
        label[data-testid="stRadioOption"]:hover {
            background-color: rgba(128, 128, 128, 0.1) !important; /* Subtle hover */
        }
        
        /* Hide the radio circle! It is the sibling immediately preceding the text container. */
        label[data-testid="stRadioOption"] div:not([data-testid="stMarkdownContainer"]):has(+ div[data-testid="stMarkdownContainer"]) {
            display: none !important;
            width: 0 !important;
            height: 0 !important;
            opacity: 0 !important;
            visibility: hidden !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* The text container */
        label[data-testid="stRadioOption"] p {
            font-size: 0.95rem;
            color: var(--text-color);
            opacity: 0.8;
            font-weight: 500;
            display: flex;
            align-items: center;
            margin: 0;
            width: 100%;
        }
        
        /* Inject Icons using Material Symbols ligatures */
        label[data-testid="stRadioOption"] p::before {
            font-family: 'Material Symbols Outlined';
            font-size: 1.25rem;
            margin-right: 0.75rem;
            color: var(--text-color);
            opacity: 0.7;
            transition: color 0.2s ease;
        }
        
        /* Target by nth-of-type if wrapped in divs, otherwise nth-child */
        div[role="radiogroup"] > div:nth-child(1) label[data-testid="stRadioOption"] p::before, label[data-testid="stRadioOption"]:nth-child(1) p::before { content: 'dashboard'; }
        div[role="radiogroup"] > div:nth-child(2) label[data-testid="stRadioOption"] p::before, label[data-testid="stRadioOption"]:nth-child(2) p::before { content: 'dns'; }
        div[role="radiogroup"] > div:nth-child(3) label[data-testid="stRadioOption"] p::before, label[data-testid="stRadioOption"]:nth-child(3) p::before { content: 'hub'; }
        div[role="radiogroup"] > div:nth-child(4) label[data-testid="stRadioOption"] p::before, label[data-testid="stRadioOption"]:nth-child(4) p::before { content: 'warning'; }
        div[role="radiogroup"] > div:nth-child(5) label[data-testid="stRadioOption"] p::before, label[data-testid="stRadioOption"]:nth-child(5) p::before { content: 'play_circle'; }
        div[role="radiogroup"] > div:nth-child(6) label[data-testid="stRadioOption"] p::before, label[data-testid="stRadioOption"]:nth-child(6) p::before { content: 'build'; }
        div[role="radiogroup"] > div:nth-child(7) label[data-testid="stRadioOption"] p::before, label[data-testid="stRadioOption"]:nth-child(7) p::before { content: 'balance'; }
        div[role="radiogroup"] > div:nth-child(8) label[data-testid="stRadioOption"] p::before, label[data-testid="stRadioOption"]:nth-child(8) p::before { content: 'security'; }
        div[role="radiogroup"] > div:nth-child(9) label[data-testid="stRadioOption"] p::before, label[data-testid="stRadioOption"]:nth-child(9) p::before { content: 'analytics'; }
        div[role="radiogroup"] > div:nth-child(10) label[data-testid="stRadioOption"] p::before, label[data-testid="stRadioOption"]:nth-child(10) p::before { content: 'history'; }
        
        /* Style the active selected state */
        label[data-testid="stRadioOption"][data-selected="true"],
        label[data-testid="stRadioOption"]:has(input:checked) {
            background-color: rgba(128, 128, 128, 0.15) !important;
        }
        
        /* Bright Blue (#3b82f6) for the active text and icon */
        label[data-testid="stRadioOption"][data-selected="true"] p,
        label[data-testid="stRadioOption"][data-selected="true"] p::before,
        label[data-testid="stRadioOption"]:has(input:checked) p,
        label[data-testid="stRadioOption"]:has(input:checked) p::before {
            color: #3b82f6 !important;
            opacity: 1;
            font-weight: 600;
            text-shadow: none !important;
            box-shadow: none !important;
        }
        
        /* Black shadow ONLY behind the active icon for contrast if needed */
        label[data-testid="stRadioOption"][data-selected="true"] p::before,
        label[data-testid="stRadioOption"]:has(input:checked) p::before {
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2) !important;
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
            color: var(--text-color) !important;
        }
        div[data-testid="stMetricLabel"] {
            color: var(--text-color) !important;
            opacity: 0.7;
            font-size: 0.875rem !important;
            font-weight: 500 !important;
        }

        /* Container Border Overrides to look like tailwind cards */
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            border-radius: 1.25rem !important; /* Large rounded corners */
            border: 1px solid rgba(128, 128, 128, 0.2) !important; /* Subtle border */
            background-color: var(--secondary-background-color) !important;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06) !important; /* Lighter shadow */
            padding: 1.5rem !important;
        }

        /* Expander Styling */
        div[data-testid="stExpander"] {
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
            border-radius: 0.5rem !important;
            background-color: var(--secondary-background-color) !important;
        }
        
        /* DataFrame Styling overrides */
        .stDataFrame {
            border-radius: 0.5rem;
            border: 1px solid rgba(128, 128, 128, 0.2);
            overflow: hidden;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: var(--text-color);
            font-weight: 600 !important;
            letter-spacing: -0.025em;
        }
        
        </style>
    """, unsafe_allow_html=True)
