import json
import os
import time
from pathlib import Path
from typing import List
import streamlit as st
from PIL import Image

from src.models import PropertyInput, SceneScript, VideoScript
from src.pipeline import generate_property_video
from src.script_generator import create_script
from src.tts import AVAILABLE_VOICES

# Configure Studio Page
st.set_page_config(
    page_title="Realty Assistant | Property Video Generator",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# High-End Modern Light Enterprise Theme (Linear / Stripe / Vercel grade)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #F8FAFC !important;
        color: #0F172A !important;
    }
    
    /* Clean up default Streamlit clutter */
    header, #MainMenu, footer {
        visibility: hidden !important;
        height: 0px !important;
    }
    
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1080px !important;
    }
    
    /* Clean Container Styling (Eliminates empty boxes, ensures crisp borders) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 24px 28px !important;
        box-shadow: 0 2px 8px -2px rgba(15, 23, 42, 0.05) !important;
        margin-bottom: 18px !important;
    }
    
    /* Executive Header Bar */
    .company-nav {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 24px;
        margin-bottom: 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    
    .company-brand-row {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .company-logo-badge {
        background: #0A1931;
        border: 2px solid #D97706;
        border-radius: 8px;
        width: 42px;
        height: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        color: #F59E0B;
        font-size: 1.05rem;
        letter-spacing: -0.02em;
    }
    
    .company-title {
        font-size: 1.3rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.02em;
        margin: 0;
    }
    .company-sub {
        font-size: 0.82rem;
        color: #64748B;
        margin: 1px 0 0 0;
    }
    .company-badge-box {
        font-size: 0.74rem;
        color: #1E40AF;
        background-color: #EFF6FF;
        border: 1px solid #DBEAFE;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        text-align: right;
    }
    
    /* Stepper Navigation Bar */
    .stepper-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
        margin-bottom: 18px;
    }
    
    .step-box {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 10px;
        text-align: center;
        font-size: 0.8rem;
        font-weight: 600;
        color: #64748B;
        transition: all 0.15s ease;
    }
    .step-box.active {
        background-color: #1D4ED8;
        border-color: #1D4ED8;
        color: #FFFFFF;
        font-weight: 700;
        box-shadow: 0 4px 10px -2px rgba(29, 78, 216, 0.35);
    }
    .step-box.done {
        background-color: #F0FDF4;
        border-color: #BBF7D0;
        color: #15803D;
    }
    
    /* Section Headings */
    .section-title-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #F1F5F9;
        padding-bottom: 12px;
        margin-bottom: 18px;
    }
    .section-main-heading {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.01em;
        margin: 0;
    }
    .section-stage-badge {
        font-size: 0.72rem;
        font-weight: 700;
        color: #1E40AF;
        background-color: #EFF6FF;
        border: 1px solid #DBEAFE;
        padding: 3px 10px;
        border-radius: 4px;
        text-transform: uppercase;
    }
    
    /* Rich Inventory Showcase Card */
    .inventory-card {
        background: linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 100%);
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 18px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    .inv-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.02em;
    }
    .inv-chips-row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 8px;
        margin-bottom: 12px;
    }
    .inv-pill {
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .pill-price {
        background-color: #FEF3C7;
        color: #92400E;
        border: 1px solid #FDE68A;
    }
    .pill-loc {
        background-color: #EFF6FF;
        color: #1E40AF;
        border: 1px solid #DBEAFE;
    }
    .pill-type {
        background-color: #F1F5F9;
        color: #334155;
        border: 1px solid #CBD5E1;
    }
    .inv-features-list {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
    }
    .feature-tag {
        font-size: 0.76rem;
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        color: #475569;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 500;
    }
    
    /* Media Cards */
    .photo-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 6px;
        text-align: center;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }
    .photo-tag {
        font-size: 0.68rem;
        font-weight: 700;
        color: #1E40AF;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 10px 22px !important;
        transition: all 0.15s ease !important;
    }
    
    /* Form Inputs */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        font-size: 0.88rem !important;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #1D4ED8 !important;
        box-shadow: 0 0 0 1px #1D4ED8 !important;
    }
    .stSelectbox>div>div {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
    }
    
    /* Centered Glowing Viraaj Ventures / Realty Assistant Logo Loader */
    @keyframes pulse-halo {
        0% {
            transform: scale(0.96);
            filter: drop-shadow(0 0 14px rgba(217, 119, 6, 0.4)) drop-shadow(0 0 30px rgba(29, 78, 216, 0.25));
        }
        50% {
            transform: scale(1.05);
            filter: drop-shadow(0 0 36px rgba(217, 119, 6, 0.85)) drop-shadow(0 0 55px rgba(29, 78, 216, 0.6));
        }
        100% {
            transform: scale(0.96);
            filter: drop-shadow(0 0 14px rgba(217, 119, 6, 0.4)) drop-shadow(0 0 30px rgba(29, 78, 216, 0.25));
        }
    }
    
    @keyframes text-blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.65; }
    }
    
    .glowing-loader-box {
        background: radial-gradient(circle at center, #FFFFFF 0%, #F8FAFC 100%);
        border: 2px solid #D97706;
        border-radius: 12px;
        padding: 44px 28px;
        text-align: center;
        box-shadow: 0 14px 40px -10px rgba(217, 119, 6, 0.3);
        margin: 20px auto;
        max-width: 680px;
    }
    
    .glowing-symbol {
        display: inline-block;
        animation: pulse-halo 2.2s infinite ease-in-out;
        margin-bottom: 18px;
    }
    
    .glowing-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    
    .glowing-subtitle {
        font-size: 0.85rem;
        color: #D97706;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-top: 4px;
        animation: text-blink 1.8s infinite ease-in-out;
    }
    
    .glowing-status {
        font-size: 0.95rem;
        color: #1E293B;
        font-weight: 600;
        margin-top: 14px;
    }
    
    /* Specs KPI Grid */
    .specs-kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin-top: 14px;
        margin-bottom: 16px;
    }
    .kpi-cell {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 8px;
        text-align: center;
    }
    .kpi-label {
        font-size: 0.68rem;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .kpi-val {
        font-size: 1.05rem;
        font-weight: 800;
        color: #0F172A;
        margin-top: 3px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Preset Listings Library
presets_data = {
    "Emerald Heights (Sector 150, Noida - 3 & 4 BHK Luxury Apartments)": {
        "name": "Emerald Heights Luxury Residences",
        "location": "Sector 150, Noida Expressway",
        "price": "1.85 Cr Onwards",
        "property_type": "3 & 4 BHK Luxury Apartments",
        "features": [
            "Expansive 2,450 sq.ft. open layout with Italian marble",
            "Smart European modular kitchen with branded fittings",
            "Private master suite with designer walk-in wardrobe",
            "Infinity swimming pool and world-class sports clubhouse",
            "Panoramic golf-course and expressway facing balconies",
        ],
        "contact_cta": "Book your exclusive site tour today. Call +91 98765 43210 or visit realtyassistant.in",
        "images": [
            "sample_data/images/01_exterior.jpg",
            "sample_data/images/02_living_room.jpg",
            "sample_data/images/04_modular_kitchen.jpg",
            "sample_data/images/03_master_bedroom.jpg",
            "sample_data/images/05_swimming_pool.jpg",
            "sample_data/images/06_balcony_view.jpg",
            "sample_data/images/09_twilight_exterior.jpg",
        ],
    },
    "The Royal Palms Grand Villa (Jaypee Greens - 5 BHK Independent Villa)": {
        "name": "The Royal Palms Grand Villa",
        "location": "Jaypee Greens, Greater Noida",
        "price": "4.50 Cr",
        "property_type": "5 BHK Independent Luxury Villa",
        "features": [
            "5,200 sq.ft. private plot with manicured front lawn",
            "Double-height living room with floor-to-ceiling glass",
            "Chef's kitchen with premium German appliances",
            "Private temperature-controlled rooftop pool",
            "Spa-inspired master bathroom with Italian marble soaking tub",
        ],
        "contact_cta": "Limited units available. Call Realty Assistant: +91 91234 56789 to schedule a private viewing",
        "images": [
            "sample_data/images/01_exterior.jpg",
            "sample_data/images/02_living_room.jpg",
            "sample_data/images/04_modular_kitchen.jpg",
            "sample_data/images/05_swimming_pool.jpg",
            "sample_data/images/07_luxury_bathroom.jpg",
            "sample_data/images/09_twilight_exterior.jpg",
        ],
    },
    "Custom Property Listing (Blank Form)": {
        "name": "",
        "location": "",
        "price": "",
        "property_type": "",
        "features": [],
        "contact_cta": "",
        "images": [],
    },
}

# Top Navigation Bar with Viraaj Ventures & Realty Assistant Branding
st.markdown(
    """
    <div class="company-nav">
        <div class="company-brand-row">
            <div class="company-logo-badge">RA</div>
            <div>
                <h1 class="company-title">Realty Assistant | Property Video Generator</h1>
                <p class="company-sub">Viraaj Ventures Ecosystem &bull; AI & Automation (Product) &bull; Noida HQ</p>
            </div>
        </div>
        <div class="company-badge-box">
            Enterprise Pipeline Online<br>
            <span style="color: #16A34A; font-weight: 700;">Status: Ready for Production</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "wizard_step" not in st.session_state:
    st.session_state.wizard_step = 1

if "preset_choice" not in st.session_state:
    st.session_state.preset_choice = list(presets_data.keys())[0]

if "form_data" not in st.session_state or st.session_state.get("last_preset") != st.session_state.preset_choice:
    p_data = presets_data[st.session_state.preset_choice]
    st.session_state.form_data = {
        "name": p_data["name"],
        "location": p_data["location"],
        "price": p_data["price"],
        "property_type": p_data["property_type"],
        "features": "\n".join(p_data["features"]),
        "contact_cta": p_data["contact_cta"],
        "images": p_data["images"].copy(),
        "orientation": "16:9",
        "voice_key": list(AVAILABLE_VOICES.keys())[0],
        "speech_rate": "+10%",
        "duration_mode": "dynamic",
        "custom_scene_duration": 4.5,
        "motion_style": "dynamic_mix",
        "bgm_volume": 0.12,
        "watermark_text": "REALTY ASSISTANT EXCLUSIVE",
    }
    st.session_state.last_preset = st.session_state.preset_choice
    st.session_state.storyboard_scenes = []

cur_step = st.session_state.wizard_step

# Interactive Stepper Navigation Bar
step_labels = [
    "1. Property Specs",
    "2. Visual Media",
    "3. Voice & Settings",
    "4. Storyboard & Copy",
    "5. Video Production",
]

step_html = '<div class="stepper-grid">'
for idx, lbl in enumerate(step_labels, 1):
    if idx == cur_step:
        step_html += f'<div class="step-box active">{lbl}</div>'
    elif idx < cur_step:
        step_html += f'<div class="step-box done">{lbl} [Done]</div>'
    else:
        step_html += f'<div class="step-box">{lbl}</div>'
step_html += '</div>'
st.markdown(step_html, unsafe_allow_html=True)

# Placeholder for Glowing Loader during video generation
loader_spot = st.empty()

# ==================== STEP 1: PROPERTY SPECS ====================
if cur_step == 1:
    with st.container(border=True):
        st.markdown(
            """
            <div class="section-title-row">
                <div class="section-main-heading">1. Listing Specifications & Inventory Setup</div>
                <div class="section-stage-badge">Stage 1 of 5</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        selected_p = st.selectbox(
            "Choose Inventory Listing Preset (Auto-fills verified specifications from Realty Assistant):",
            options=list(presets_data.keys()),
            index=list(presets_data.keys()).index(st.session_state.preset_choice),
        )
        if selected_p != st.session_state.preset_choice:
            st.session_state.preset_choice = selected_p
            st.rerun()

        fd = st.session_state.form_data

        # Render Rich Inventory Showcase Card if preset selected
        if fd["name"]:
            feat_list = [f.strip() for f in fd["features"].split("\n") if f.strip()]
            chips_html = "".join([f'<span class="feature-tag">{feat}</span>' for feat in feat_list])
            st.markdown(
                f"""
                <div class="inventory-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <div class="inv-title">{fd['name']}</div>
                            <div class="inv-chips-row">
                                <span class="inv-pill pill-price">Price: {fd['price']}</span>
                                <span class="inv-pill pill-loc">Location: {fd['location']}</span>
                                <span class="inv-pill pill-type">Config: {fd['property_type']}</span>
                            </div>
                        </div>
                        <div style="font-size: 0.75rem; color: #166534; background: #DCFCE7; border: 1px solid #BBF7D0; padding: 4px 10px; border-radius: 4px; font-weight: 700;">
                            VERIFIED INVENTORY
                        </div>
                    </div>
                    <div style="font-size: 0.74rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 6px;">Architectural Highlights:</div>
                    <div class="inv-features-list">{chips_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            fd["name"] = st.text_input("Property / Project Name *", value=fd["name"], placeholder="Project Title")
            fd["location"] = st.text_input("Location / Sector", value=fd["location"], placeholder="Sector, City")
            fd["price"] = st.text_input("Listing Price / Starting From", value=fd["price"], placeholder="e.g. 1.85 Cr Onwards")
        with col_s2:
            fd["property_type"] = st.text_input("Configuration / Type", value=fd["property_type"], placeholder="e.g. 3 & 4 BHK Luxury Apartments")
            fd["contact_cta"] = st.text_input("Call to Action / Inquiries", value=fd["contact_cta"], placeholder="Phone, email, or website")
            fd["features"] = st.text_area("Key Features (one per line)", value=fd["features"], height=105, placeholder="Expansive living hall\nModern modular kitchen\nInfinity pool")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        nav_c1, nav_c2 = st.columns([0.72, 0.28])
        with nav_c2:
            if st.button("Save & Continue to Media ->", width="stretch", type="primary"):
                if not fd["name"].strip():
                    st.error("Please enter a property name before continuing.")
                else:
                    st.session_state.wizard_step = 2
                    st.rerun()

# ==================== STEP 2: VISUAL MEDIA ====================
elif cur_step == 2:
    with st.container(border=True):
        st.markdown(
            """
            <div class="section-title-row">
                <div class="section-main-heading">2. Architectural Photography Sequence</div>
                <div class="section-stage-badge">Stage 2 of 5</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        fd = st.session_state.form_data

        st.caption("Active Visual Asset Sequence (Correlated semantically with voiceover narration):")
        if fd["images"]:
            p_cols = st.columns(min(7, len(fd["images"])))
            category_labels = ["1. Exterior", "2. Living Hall", "3. Kitchen", "4. Master Suite", "5. Swimming Pool", "6. Balcony View", "7. Twilight Facade"]
            for i, img_path in enumerate(fd["images"][:7]):
                p = Path(img_path)
                if p.exists():
                    try:
                        thumb = Image.open(p)
                        tag = category_labels[i] if i < len(category_labels) else f"Photo {i+1}"
                        with p_cols[i]:
                            st.image(thumb, width="stretch")
                            st.markdown(f'<div class="photo-tag">{tag}</div>', unsafe_allow_html=True)
                    except Exception:
                        pass

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        new_uploads = st.file_uploader(
            "Upload Custom Photos to Replace Preset Sequence (JPEG, PNG, WEBP)",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
        )
        if new_uploads:
            custom_dir = Path("output/custom_uploads")
            custom_dir.mkdir(parents=True, exist_ok=True)
            saved_imgs = []
            for idx, f in enumerate(new_uploads):
                sp = custom_dir / f"user_{idx}_{f.name}"
                with open(sp, "wb") as uf:
                    uf.write(f.getbuffer())
                saved_imgs.append(str(sp))
            fd["images"] = saved_imgs
            st.success(f"{len(saved_imgs)} custom images loaded successfully.")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        nav_c1, nav_c2, nav_c3 = st.columns([0.28, 0.44, 0.28])
        with nav_c1:
            if st.button("<- Back to Specs", width="stretch"):
                st.session_state.wizard_step = 1
                st.rerun()
        with nav_c3:
            if st.button("Save & Continue to Voice ->", width="stretch", type="primary"):
                st.session_state.wizard_step = 3
                st.rerun()

# ==================== STEP 3: VOICE & SETTINGS ====================
elif cur_step == 3:
    with st.container(border=True):
        st.markdown(
            """
            <div class="section-title-row">
                <div class="section-main-heading">3. Narration Voice, Aspect Ratio & Director Controls</div>
                <div class="section-stage-badge">Stage 3 of 5</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        fd = st.session_state.form_data

        v_c1, v_c2 = st.columns(2)
        with v_c1:
            voice_keys = list(AVAILABLE_VOICES.keys())
            voice_labels = [f"{AVAILABLE_VOICES[k]['name']}" for k in voice_keys]
            v_idx = voice_keys.index(fd["voice_key"]) if fd["voice_key"] in voice_keys else 0
            selected_v = st.selectbox(
                "Select Narrator Voice",
                range(len(voice_keys)),
                format_func=lambda i: voice_labels[i],
                index=v_idx,
            )
            fd["voice_key"] = voice_keys[selected_v]

            pace_options = ["Slow (-10%)", "Standard (+0%)", "Commercial (+10%)", "Fast (+20%)"]
            cur_pace = "Commercial (+10%)" if fd["speech_rate"] == "+10%" else ("Fast (+20%)" if fd["speech_rate"] == "+20%" else "Standard (+0%)")
            chosen_pace = st.select_slider("Speech Cadence / Tempo", options=pace_options, value=cur_pace)
            pace_map = {"Slow (-10%)": "-10%", "Standard (+0%)": "+0%", "Commercial (+10%)": "+10%", "Fast (+20%)": "+20%"}
            fd["speech_rate"] = pace_map[chosen_pace]

            fd["bgm_volume"] = st.slider("Studio Background Music Volume (Auto-Ducked during Voice)", 0.0, 0.30, float(fd["bgm_volume"]), 0.02)

        with v_c2:
            aspect_opts = [
                "16:9 Landscape (Website, YouTube, Email Portals)",
                "9:16 Vertical (WhatsApp Status, Instagram Reels)",
                "1:1 Square (Social Feed, LinkedIn)",
            ]
            cur_asp_idx = 1 if fd["orientation"] == "9:16" else (2 if fd["orientation"] == "1:1" else 0)
            chosen_asp = st.radio("Video Orientation & Target Channel", options=aspect_opts, index=cur_asp_idx)
            fd["orientation"] = "9:16" if "9:16" in chosen_asp else ("1:1" if "1:1" in chosen_asp else "16:9")

            dur_opts = ["Dynamic Speech-Paced (Auto-timed)", "Snappy Promo (3.2s cuts)", "Detailed Walkthrough (5.0s cuts)", "Custom Manual Duration"]
            cur_dur_idx = 1 if fd["duration_mode"] == "fast" else (2 if fd["duration_mode"] == "relaxed" else (3 if fd["duration_mode"] == "custom" else 0))
            chosen_dur = st.selectbox("Pacing Profile", options=dur_opts, index=cur_dur_idx)
            if "Custom" in chosen_dur:
                fd["duration_mode"] = "custom"
                fd["custom_scene_duration"] = st.slider("Manual Seconds Per Scene", 3.0, 8.0, float(fd["custom_scene_duration"] or 4.5), 0.5)
            elif "Snappy" in chosen_dur:
                fd["duration_mode"] = "fast"
            elif "Detailed" in chosen_dur:
                fd["duration_mode"] = "relaxed"
            else:
                fd["duration_mode"] = "dynamic"

            fd["watermark_text"] = st.text_input("Brand Watermark Tag", value=fd["watermark_text"])

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        nav_c1, nav_c2, nav_c3 = st.columns([0.28, 0.44, 0.28])
        with nav_c1:
            if st.button("<- Back to Media", width="stretch"):
                st.session_state.wizard_step = 2
                st.rerun()
        with nav_c3:
            if st.button("Save & Continue to Storyboard ->", width="stretch", type="primary"):
                st.session_state.wizard_step = 4
                st.rerun()

# ==================== STEP 4: STORYBOARD & REGENERATE ====================
elif cur_step == 4:
    with st.container(border=True):
        st.markdown(
            """
            <div class="section-title-row">
                <div class="section-main-heading">4. Scene Storyboard & Narration Copy</div>
                <div class="section-stage-badge">Stage 4 of 5</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        fd = st.session_state.form_data
        voice_meta = AVAILABLE_VOICES[fd["voice_key"]]
        cleaned_feat = [f.strip() for f in fd["features"].split("\n") if f.strip()]
        if not cleaned_feat:
            cleaned_feat = ["Spacious contemporary layout", "Prime connected location", "Luxury lifestyle amenities"]

        prop_obj = PropertyInput(
            name=fd["name"] or "Exclusive Property Showcase",
            location=fd["location"] or "Prime Location",
            price=fd["price"] or "Price On Request",
            property_type=fd["property_type"] or "Luxury Residence",
            features=cleaned_feat,
            contact_cta=fd["contact_cta"] or "Contact Realty Assistant for private viewings.",
            images=fd["images"],
            orientation=fd["orientation"],
            language=voice_meta["language"],
            voice_id=voice_meta["id"],
            speech_rate=fd["speech_rate"],
            duration_mode=fd["duration_mode"],
            custom_scene_duration=fd["custom_scene_duration"],
            motion_style=fd["motion_style"],
            watermark_text=fd["watermark_text"],
            bgm_volume=fd["bgm_volume"],
            enable_ai_script=True,
        )

        top_c1, top_c2 = st.columns([0.72, 0.28])
        with top_c1:
            st.caption("Review and edit the exact headlines and spoken sentences. Click 'AI Regenerate Script' to rewrite fresh copy.")
        with top_c2:
            if st.button("AI Regenerate Script", width="stretch"):
                with st.spinner("Regenerating copy..."):
                    valid_imgs = prop_obj.get_valid_images(base_dir=Path.cwd())
                    gen_s = create_script(prop_obj, valid_imgs, api_key=os.getenv("GEMINI_API_KEY"))
                    st.session_state.storyboard_scenes = [s.model_dump() for s in gen_s.scenes]
                    st.success("Script regenerated successfully.")

        # Generate initial script if not present
        if not st.session_state.storyboard_scenes:
            with st.spinner("Assembling storyboard copy..."):
                valid_imgs = prop_obj.get_valid_images(base_dir=Path.cwd())
                gen_s = create_script(prop_obj, valid_imgs, api_key=os.getenv("GEMINI_API_KEY"))
                st.session_state.storyboard_scenes = [s.model_dump() for s in gen_s.scenes]

        # Display rich scene cards with live word count
        for idx, s in enumerate(st.session_state.storyboard_scenes):
            with st.expander(f"Scene {idx+1}: [{s['scene_type'].upper()}] {s['headline']}", expanded=(idx == 0)):
                sc1, sc2 = st.columns([1.15, 0.85])
                with sc1:
                    s["headline"] = st.text_input(f"Headline (Scene {idx+1})", value=s["headline"], key=f"sb_head_{idx}")
                    s["subtext"] = st.text_input(f"Subtitle (Scene {idx+1})", value=s["subtext"], key=f"sb_sub_{idx}")
                    s["voiceover_text"] = st.text_area(f"Spoken Voiceover Script (Scene {idx+1})", value=s["voiceover_text"], height=65, key=f"sb_vo_{idx}")
                    w_count = len(s["voiceover_text"].split())
                    st.caption(f"Word Count: {w_count} words | Estimated Speech Time: ~{round(w_count / 3.0, 1)}s")
                with sc2:
                    if s.get("image_path") and Path(s["image_path"]).exists():
                        st.caption(f"Matched Photo: {Path(s['image_path']).name}")
                        try:
                            th = Image.open(s["image_path"])
                            st.image(th, width="stretch")
                        except Exception:
                            pass

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        nav_c1, nav_c2, nav_c3 = st.columns([0.28, 0.44, 0.28])
        with nav_c1:
            if st.button("<- Back to Settings", width="stretch"):
                st.session_state.wizard_step = 3
                st.rerun()
        with nav_c3:
            generate_action = st.button("PRODUCE 1080P VIDEO NOW", width="stretch", type="primary")

        # Execution upon clicking Produce Video
        if generate_action:
            start_t = time.time()

            # Center Glowing Viraaj Ventures / Realty Assistant Logo Loader Callback
            def studio_loader_callback(stage_text: str, pct: float):
                elapsed_s = round(time.time() - start_t, 1)
                loader_spot.markdown(
                    f"""
                    <div class="glowing-loader-box">
                        <div class="glowing-symbol">
                            <svg width="92" height="92" viewBox="0 0 100 100">
                                <polygon points="50,4 94,27 94,73 50,96 6,73 6,27" stroke="#D97706" stroke-width="4" fill="#0A1931"/>
                                <path d="M50 16 L82 33 L82 67 L50 84 L18 67 L18 33 Z" stroke="#3B82F6" stroke-width="3" fill="none"/>
                                <path d="M35 66 L35 34 L49 34 C56 34 60 38 60 44 C60 50 56 54 49 54 L35 54 M47 54 L60 66" stroke="#FFFFFF" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                        <div class="glowing-title">VIRAAJ VENTURES &bull; REALTY ASSISTANT</div>
                        <div class="glowing-subtitle">AI & AUTOMATION VIDEO PIPELINE</div>
                        <div class="glowing-status">{stage_text}</div>
                        <div style="margin: 20px auto; max-width: 480px; background: #E2E8F0; border-radius: 9999px; height: 8px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #1D4ED8, #D97706); height: 100%; width: {int(pct*100)}%;"></div>
                        </div>
                        <div style="font-size: 0.82rem; color: #64748B;">Target: 1080p Full HD &bull; H.264 &bull; Elapsed: {elapsed_s}s</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Assemble custom script
            assembled = []
            for i, sd in enumerate(st.session_state.storyboard_scenes):
                assembled.append(
                    SceneScript(
                        scene_index=i,
                        scene_type=sd.get("scene_type", "feature"),
                        headline=sd["headline"],
                        subtext=sd["subtext"],
                        voiceover_text=sd["voiceover_text"],
                        image_path=sd.get("image_path"),
                        duration=4.5,
                    )
                )
            custom_script = VideoScript(
                property_name=fd["name"],
                language=voice_meta["language"],
                source="custom_storyboard",
                scenes=assembled,
            )

            try:
                studio_loader_callback("Validating inventory specs and anti-hallucination constraints...", 0.10)
                res = generate_property_video(
                    prop=prop_obj,
                    api_key=os.getenv("GEMINI_API_KEY"),
                    custom_script=custom_script,
                    status_callback=studio_loader_callback,
                )
                total_t = round(time.time() - start_t, 1)
                loader_spot.empty()
                st.session_state.last_result = res
                st.session_state.last_time = total_t
                st.session_state.wizard_step = 5
                st.rerun()

            except Exception as err:
                loader_spot.empty()
                st.error(f"Render failed: {err}")

# ==================== STEP 5: PRODUCTION EXPORT & INTEGRATION ====================
elif cur_step == 5:
    with st.container(border=True):
        st.markdown(
            """
            <div class="section-title-row">
                <div class="section-main-heading">5. Production Output & Enterprise Distribution</div>
                <div class="section-stage-badge">Stage 5 of 5</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        fd = st.session_state.form_data

        if "last_result" in st.session_state:
            res = st.session_state.last_result
            v_path = res.get("output_path")

            if v_path and Path(v_path).exists():
                with open(v_path, "rb") as vf:
                    v_bytes = vf.read()

                st.markdown(
                    f"""
                    <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 12px 16px; color: #166534; font-size: 0.9rem; font-weight: 700; text-align: center; margin-bottom: 14px;">
                        Promotional video produced successfully in {st.session_state.get('last_time', 45)} seconds. Ready for distribution.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Video Player
                st.video(v_bytes)

                st.download_button(
                    label="Download High-Definition Video (MP4)",
                    data=v_bytes,
                    file_name=Path(v_path).name,
                    mime="video/mp4",
                    width="stretch",
                    type="primary",
                )

                # Specs KPI Grid
                st.markdown(
                    f"""
                    <div class="specs-kpi-grid">
                        <div class="kpi-cell"><div class="kpi-label">Duration</div><div class="kpi-val">{res['duration']}s</div></div>
                        <div class="kpi-cell"><div class="kpi-label">Resolution</div><div class="kpi-val">{res['resolution']}</div></div>
                        <div class="kpi-cell"><div class="kpi-label">Orientation</div><div class="kpi-val">{res['orientation']}</div></div>
                        <div class="kpi-cell"><div class="kpi-label">File Size</div><div class="kpi-val">{res['filesize_mb']} MB</div></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Enterprise Integration Tabs
                e_tab1, e_tab2, e_tab3 = st.tabs([
                    "Production Specifications",
                    "WhatsApp Client Share Pitch",
                    "CRM Webhook Integration (LeadSquared / Salesforce)",
                ])

                with e_tab1:
                    t_col1, t_col2 = st.columns(2)
                    with t_col1:
                        st.caption(f"• Project Name: **{fd['name']}**")
                        st.caption(f"• Location: **{fd['location']}**")
                        st.caption(f"• Audio Narration: **{AVAILABLE_VOICES[fd['voice_key']]['name']}**")
                    with t_col2:
                        st.caption(f"• Total Scene Count: **{res['scenes_count']} scenes**")
                        st.caption(f"• Video Codec: **H.264 / AAC 24fps**")
                        st.caption(f"• BGM Track: **Acoustic Studio Ambient (Auto-Ducked)**")

                with e_tab2:
                    st.caption("Sales executives can copy and send this pitch directly to buyers on WhatsApp:")
                    feat_sample = [f.strip() for f in fd["features"].split("\n") if f.strip()][:3]
                    wa_pitch = (
                        f"Hi! Here is an exclusive video tour of *{fd['name']}* at {fd['location']}.\n\n"
                        f"• Configuration: {fd['property_type']}\n"
                        f"• Starting Price: {fd['price']}\n"
                        f"• Highlights: {', '.join(feat_sample)}\n\n"
                        f"Watch the full video walkthrough and contact us to schedule a site tour: {fd['contact_cta']}"
                    )
                    st.text_area("WhatsApp Pitch Message", value=wa_pitch, height=105)

                with e_tab3:
                    st.caption("JSON Webhook payload for Realty Assistant's CRM (Salesforce / LeadSquared) automation:")
                    crm_hook = {
                        "event": "listing_video.produced",
                        "timestamp": int(time.time()),
                        "company": "Viraaj Ventures / Realty Assistant",
                        "listing_id": f"RA-{abs(hash(fd['name'])) % 100000}",
                        "property_name": fd["name"],
                        "location": fd["location"],
                        "price": fd["price"],
                        "video_url": f"https://media.realtyassistant.in/videos/{Path(v_path).name}",
                        "duration_seconds": res["duration"],
                        "resolution": res["resolution"],
                        "aspect_ratio": res["orientation"],
                        "scenes_count": res["scenes_count"],
                        "status": "ready_to_distribute",
                    }
                    st.code(json.dumps(crm_hook, indent=2), language="json")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        nav_back1, nav_back2 = st.columns([0.3, 0.7])
        with nav_back1:
            if st.button("<- Create / Edit Another Video", width="stretch"):
                st.session_state.wizard_step = 1
                st.rerun()
