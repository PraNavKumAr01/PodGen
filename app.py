import streamlit as st
import numpy as np
from make_pod import generate_podcast

def generate_podcast_wrapper(topic, male_speakers, female_speakers):
    num_speakers = int(male_speakers) + int(female_speakers)
    return generate_podcast(topic, num_speakers, int(male_speakers), int(female_speakers))

st.set_page_config(page_title="Podcast Generator")

st.markdown("# Podcast Generator")

col1, col2 = st.columns([1, 2])

with col1:
    male_speakers = st.selectbox("Male Speakers", options=["1", "2", "3"], index=0)
    female_speakers = st.selectbox("Female Speakers", options=["1", "2", "3"], index=0)
    generate_btn = st.button("Generate Podcast")

with col2:
    topic = st.text_area("Podcast Topic", height=177)

if generate_btn:
    if topic:
        with st.spinner("Generating podcast..."):
            audio = generate_podcast_wrapper(topic, male_speakers, female_speakers)
        st.audio(audio, format="audio/wav")
    else:
        st.warning("Please enter a podcast topic.")