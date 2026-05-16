import streamlit as st
from skryba.app.modules import generate_story_text, generate_story_voice, show_sidebar
from skryba.utils.data_handler import load_json
from pathlib import Path

languages = [Path("skryba/app/lang_pl.json"), Path("skryba/app/lang_en.json")]

lang_list = ["Polski", "English"]
lang = st.sidebar.selectbox(
    "Language", lang_list, index=0, label_visibility="collapsed"
)
text = load_json(languages[lang_list.index(lang)])


def generate(link: str, lang: str, hr_mode: bool) -> bool:
    try:
        story = generate_story_text(link, lang, hr_mode)
    except Exception as e:
        if str(e) == "Not a github link":
            st.warning(text["link_error"])
        else:
            st.warning(text["text_error"])
        return False
    else:
        st.text(story)
        if "🔮🖤" in story:
            return False

    try:
        path = generate_story_voice(story, link, lang)
    except Exception:
        st.warning(text["token_error"])
    else:
        st.audio(path, "audio/mp3")

    return True


st.title(text["title"])

link = st.text_input(
    text["link_label"],
    placeholder="https://github.com/knsiczarnamagia/wave4-skryba",
    value="https://github.com/knsiczarnamagia/wave4-skryba",
)

if st.sidebar.button(text["cache"]):
    st.cache_data.clear()

hr_mode = st.sidebar.toggle("**HR MODE**", False)

if st.button(text["button"]):
    if generate(link, ["pl", "en"][lang_list.index(lang)], hr_mode):
        show_sidebar(text)
