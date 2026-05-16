from skryba.tts_services.tts_pipeline import TTSPipeline
from skryba.utils.data_handler import load_json
from typing import Dict, Any
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path
from run_pipeline import run

load_dotenv()


@st.cache_data
def generate_story_text(link: str, lang: str, hr_mode: bool):
    return run(link, Path("working_data"), lang, hr_mode)


@st.cache_data
def generate_story_voice(story: str, link: str, lang: str):
    (_, _, path) = link.partition("github.com/")
    path = "audio/" + path.replace("/", ".") + ".mp3"
    tts = TTSPipeline(story, lang, path)
    tts.run()
    return path


def show_sidebar(text: Dict[str, Any]):
    data: Dict[str, Any] = load_json(Path("working_data/processed_data.json"))
    with st.sidebar.expander(f"**{text['repo_name']}**"):
        st.write(data["repo_name"].split("/")[1])

    s = ""
    for el in data["contributors"]:
        s += "- " + el + "\n"
    with st.sidebar.expander(f"**{text['contributors']}**"):
        st.markdown(s)

    with st.sidebar.expander(f"**{text['most_active']}**"):
        st.write(data["most_active_contributor"])
    with st.sidebar.expander(f"**{text['least_active']}**"):
        st.write(data["least_active_contributor"])

    s = ""
    for el in data["programming_languages"]:
        s += "- " + el + "\n"
    with st.sidebar.expander(f"**{text['plang_list']}**"):
        st.markdown(s)

    if data["tags"]:
        s = ""
        for el in data["tags"]:
            s += "- " + el + "\n"
        with st.sidebar.expander(f"**{text['tags']}**"):
            st.markdown(s)
