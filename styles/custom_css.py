"""Custom CSS styles for NeuroNote UI."""

from __future__ import annotations

import streamlit as st

from styles.theme import is_dark_mode


def inject_custom_css() -> None:
    """Inject custom CSS into the Streamlit app."""
    dark = is_dark_mode()

    if dark:
        bg = "#0F0F13"
        card_bg = "#1A1A23"
        text = "#E8E8ED"
        muted = "#6B7280"
        border = "#2A2A3A"
        hover = "#252535"
        input_bg = "#1E1E2E"
    else:
        bg = "#F8F9FA"
        card_bg = "#FFFFFF"
        text = "#1A1A2E"
        muted = "#6B7280"
        border = "#E5E7EB"
        hover = "#F3F4F6"
        input_bg = "#FFFFFF"

    css = f"""
    <style>
        /* Global */
        .stApp {{
            background-color: {bg};
            color: {text};
        }}

        /* Headers */
        h1, h2, h3 {{
            color: {text} !important;
            font-weight: 600 !important;
        }}

        /* Cards */
        .neuro-card {{
            background: {card_bg};
            border: 1px solid {border};
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.2s ease;
        }}
        .neuro-card:hover {{
            border-color: #7C3AED;
            box-shadow: 0 4px 20px rgba(124, 58, 237, 0.15);
            transform: translateY(-2px);
        }}

        .neuro-card-dashboard {{
            background: {card_bg};
            border: 1px solid {border};
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
            transition: all 0.2s ease;
        }}
        .neuro-card-dashboard:hover {{
            border-color: #7C3AED;
            box-shadow: 0 4px 20px rgba(124, 58, 237, 0.15);
            transform: translateY(-2px);
        }}

        .neuro-stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: #7C3AED;
            line-height: 1.2;
            margin-bottom: 0.25rem;
        }}
        .neuro-stat-label {{
            font-size: 0.8rem;
            color: {muted};
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        /* Buttons */
        .stButton > button {{
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s ease;
        }}
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, #7C3AED, #6D28D9);
            border: none;
            color: white;
        }}
        .stButton > button[kind="primary"]:hover {{
            background: linear-gradient(135deg, #8B5CF6, #7C3AED);
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
            transform: translateY(-1px);
        }}

        /* Quick action buttons */
        .neuro-action-btn {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
            background: {card_bg};
            border: 1px solid {border};
            border-radius: 12px;
            padding: 2rem;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
            font-size: 1.1rem;
            font-weight: 500;
            color: {text};
        }}
        .neuro-action-btn:hover {{
            background: {hover};
            border-color: #7C3AED;
            box-shadow: 0 4px 20px rgba(124, 58, 237, 0.15);
            transform: translateY(-2px);
        }}
        .neuro-action-icon {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}

        /* Input fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {{
            background-color: {input_bg} !important;
            border: 1px solid {border} !important;
            border-radius: 10px !important;
            color: {text} !important;
            padding: 0.75rem 1rem !important;
        }}
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: #7C3AED !important;
            box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1) !important;
        }}

        /* Select boxes */
        .stSelectbox > div > div {{
            background-color: {input_bg} !important;
            border: 1px solid {border} !important;
            border-radius: 10px !important;
            color: {text} !important;
        }}

        /* Chat messages */
        .neuro-user-msg {{
            background: linear-gradient(135deg, #7C3AED22, #6D28D922);
            border: 1px solid #7C3AED44;
            border-radius: 16px;
            padding: 1rem 1.25rem;
            margin: 0.5rem 0;
            margin-left: 2rem;
        }}
        .neuro-assistant-msg {{
            background: {card_bg};
            border: 1px solid {border};
            border-radius: 16px;
            padding: 1rem 1.25rem;
            margin: 0.5rem 0;
            margin-right: 2rem;
        }}
        .neuro-msg-time {{
            font-size: 0.75rem;
            color: {muted};
            margin-top: 0.5rem;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 2px;
            background: {card_bg};
            border-radius: 10px;
            padding: 4px;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            padding: 0.5rem 1rem;
            transition: all 0.2s ease;
        }}
        .stTabs [aria-selected="true"] {{
            background: #7C3AED !important;
            color: white !important;
        }}

        /* Expanders */
        .streamlit-expanderHeader {{
            background: {card_bg};
            border: 1px solid {border};
            border-radius: 10px;
            transition: all 0.2s ease;
        }}
        .streamlit-expanderHeader:hover {{
            background: {hover};
        }}

        /* Dividers */
        hr {{
            border-color: {border};
            margin: 1.5rem 0;
        }}

        /* Spinner */
        .stSpinner > div {{
            border-color: #7C3AED !important;
        }}

        /* Progress bar */
        .stProgress > div > div {{
            background: linear-gradient(90deg, #7C3AED, #8B5CF6);
        }}

        /* Metrics */
        .stMetric {{
            background: {card_bg};
            border: 1px solid {border};
            border-radius: 12px;
            padding: 1rem;
        }}
        .stMetric label {{
            color: {muted} !important;
        }}
        .stMetric [data-testid="stMetricValue"] {{
            color: #7C3AED !important;
            font-weight: 700 !important;
        }}

        /* Source citation */
        .neuro-source {{
            background: {card_bg};
            border: 1px solid {border};
            border-left: 3px solid #7C3AED;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            margin: 0.5rem 0;
            font-size: 0.9rem;
        }}
        .neuro-source:hover {{
            background: {hover};
        }}

        /* Follow-up buttons */
        .neuro-followup {{
            display: inline-block;
            background: {card_bg};
            border: 1px solid {border};
            border-radius: 20px;
            padding: 0.4rem 1rem;
            margin: 0.25rem;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .neuro-followup:hover {{
            background: #7C3AED22;
            border-color: #7C3AED;
        }}

        /* Flash card */
        .neuro-flash-card {{
            background: {card_bg};
            border: 1px solid {border};
            border-radius: 16px;
            padding: 2.5rem;
            text-align: center;
            min-height: 250px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            perspective: 1000px;
        }}
        .neuro-flash-card:hover {{
            border-color: #7C3AED;
            box-shadow: 0 8px 30px rgba(124, 58, 237, 0.2);
        }}
        .neuro-flash-card-front {{
            font-size: 1.3rem;
            font-weight: 500;
        }}
        .neuro-flash-card-back {{
            font-size: 1.1rem;
            color: {muted};
        }}

        /* Processing stages */
        .neuro-stage {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem;
            border-radius: 8px;
            transition: all 0.3s ease;
        }}
        .neuro-stage-active {{
            background: #7C3AED22;
            border-left: 3px solid #7C3AED;
        }}
        .neuro-stage-complete {{
            color: #10B981;
        }}
        .neuro-stage-pending {{
            color: {muted};
        }}

        /* Empty state */
        .neuro-empty {{
            text-align: center;
            padding: 3rem 1rem;
            color: {muted};
        }}
        .neuro-empty-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }}
        .neuro-empty-title {{
            font-size: 1.25rem;
            font-weight: 500;
            color: {text};
            margin-bottom: 0.5rem;
        }}

        /* Status card */
        .neuro-status {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
        }}
        .neuro-status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }}
        .neuro-status-dot.online {{
            background: #10B981;
        }}
        .neuro-status-dot.offline {{
            background: #EF4444;
        }}
        .neuro-status-dot.warning {{
            background: #F59E0B;
        }}

        /* Sidebar */
        .css-1d391kg, .css-1lcbmhc {{
            background: {card_bg};
        }}

        /* Chat input area */
        .neuro-chat-input {{
            position: relative;
        }}

        /* Toast notifications */
        .neuro-toast {{
            position: fixed;
            top: 1rem;
            right: 1rem;
            z-index: 9999;
        }}

        /* Tags/badges */
        .neuro-badge {{
            display: inline-block;
            background: #7C3AED22;
            color: #7C3AED;
            border: 1px solid #7C3AED44;
            border-radius: 6px;
            padding: 0.15rem 0.5rem;
            font-size: 0.75rem;
            font-weight: 500;
        }}

        /* Toggle switch */
        .neuro-toggle {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        /* Layout helpers */
        .neuro-flex-center {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .neuro-gap {{
            gap: 1rem;
        }}

        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        ::-webkit-scrollbar-thumb {{
            background: {border};
            border-radius: 3px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: {muted};
        }}

        /* Selection */
        ::selection {{
            background: #7C3AED44;
            color: white;
        }}

        /* Animation */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .neuro-fade-in {{
            animation: fadeIn 0.3s ease;
        }}

        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateX(-10px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}
        .neuro-slide-in {{
            animation: slideIn 0.3s ease;
        }}

        /* Loading skeleton */
        .neuro-skeleton {{
            background: linear-gradient(90deg, {card_bg} 25%, {hover} 50%, {card_bg} 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            border-radius: 8px;
            height: 1rem;
            margin-bottom: 0.5rem;
        }}
        @keyframes shimmer {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}

        /* PDF viewer */
        .neuro-pdf-container {{
            border: 1px solid {border};
            border-radius: 12px;
            overflow: hidden;
            background: {card_bg};
        }}

        /* Study notes */
        .neuro-topic-section {{
            background: {card_bg};
            border: 1px solid {border};
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.2s ease;
        }}
        .neuro-topic-section:hover {{
            border-color: #7C3AED44;
        }}
        .neuro-topic-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
            color: {text};
        }}

        /* Formula card */
        .neuro-formula-card {{
            background: {card_bg};
            border: 1px solid {border};
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.2s ease;
        }}
        .neuro-formula-card:hover {{
            border-color: #7C3AED;
        }}
        .neuro-formula {{
            font-family: 'Courier New', monospace;
            font-size: 1.2rem;
            text-align: center;
            padding: 1rem;
            background: {bg};
            border-radius: 8px;
            margin-bottom: 1rem;
        }}

        /* Sidebar nav items */
        .neuro-nav-item {{
            padding: 0.6rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            font-weight: 500;
        }}
        .neuro-nav-item:hover {{
            background: #7C3AED15;
        }}
        .neuro-nav-item.active {{
            background: #7C3AED22;
            color: #7C3AED;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
