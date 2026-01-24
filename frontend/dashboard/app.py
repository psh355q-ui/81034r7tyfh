import streamlit as st
import asyncio
import sys
import os
import pandas as pd
import plotly.express as px

# Check if running from root
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.append(current_dir)

from backend.ai.video.video_analyzer import get_video_analyzer
from backend.ai.thinking.signal_mapper import get_signal_mapper

st.set_page_config(page_title="Wall Street Intelligence", page_icon="📈", layout="wide")

st.title("🦅 Wall Street Intelligence Agent")
st.markdown("### Real-time Video Analysis & Signal Extraction")

# Sidebar
with st.sidebar:
    st.header("Settings")
    api_status = st.success("API Key Loaded") if os.getenv("OPENAI_API_KEY") else st.error("Missing OpenAI Key")
    
    st.info("Powered by Claude 3.5 Haiku & Whisper")
    st.markdown("---")
    st.markdown("**Nemotron Cache Status**")
    st.caption("System Prompt: Cached (Ephemeral)")

# Main Input
url = st.text_input("YouTube URL", placeholder="https://youtube.com/watch?v=...")

if st.button("Analyze Video", type="primary"):
    if not url:
        st.warning("Please enter a URL")
    else:
        with st.status("Processing Video...", expanded=True) as status:
            st.write("📥 Downloading Audio...")
            analyzer = get_video_analyzer()
            
            # Run Async Analysis
            async def run_analysis():
                # Download 3 mins for demo speed
                return await analyzer.analyze_youtube(url, download_sections=[(0, 180)])
            
            try:
                result = asyncio.run(run_analysis())
                st.write("🧠 Extracting Intelligence (Thinking Layer)...")
                
                # Signal Mapping (if not done inside analyzer, but it is now)
                # Ensure mapping happens
                mapper = get_signal_mapper()
                if not result.intelligence_data or 'related_tickers' not in result.intelligence_data[0]:
                     result.intelligence_data = mapper.map_signals(result.intelligence_data)
                
                status.update(label="Analysis Complete!", state="complete", expanded=False)
                
                # --- Display Results ---
                
                # 1. Summary Section
                st.subheader("📝 Executive Summary")
                st.info(result.summary)
                
                # 2. Intelligence Cards (The Core)
                st.subheader("💡 Market Intelligence Signals")
                
                if result.intelligence_data:
                    cols = st.columns(3)
                    for idx, item in enumerate(result.intelligence_data):
                        with cols[idx % 3]:
                            category = item.get('category', 'General')
                            color = "red" if category == "Policy" else "blue" if category == "Economy" else "green"
                            
                            with st.container(border=True):
                                st.markdown(f"**{category}**")
                                st.write(item.get('fact'))
                                st.markdown(f"**Impact:** {item.get('impact_score')}")
                                
                                tickers = item.get('related_tickers', [])
                                if tickers:
                                    st.markdown(f"**🎯 Tickers:** `{' '.join(tickers)}`")
                                else:
                                    st.caption("No direct ticker mapped")
                else:
                    st.warning("No specific market intelligence extracted.")

                # 3. Multimodal Metrics
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Sentiment Timeline")
                    if result.sentiment_timeline:
                        df = pd.DataFrame(result.sentiment_timeline)
                        fig = px.bar(df, x=df.index, y="sentiment_score", color="status",
                                     title="Text Sentiment Flow",
                                     color_discrete_map={"POSITIVE": "green", "NEGATIVE": "red"})
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("🔊 Audio Tone Analysis")
                    tone = result.tone_metrics
                    st.metric("Tone / Energy", tone.get('interpretation', 'N/A'))
                    st.progress(tone.get('high_energy_ratio', 0), text="Energy Level")
                    
            except Exception as e:
                st.error(f"Analysis Failed: {e}")
                st.exception(e)

if st.checkbox("Show Raw JSON"):
    st.json({"status": "Waiting for analysis"})
