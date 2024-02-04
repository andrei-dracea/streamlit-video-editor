import moviepy.editor as mp
import streamlit as st
import numpy as np

import cv2
import tempfile

from moviepy.video.compositing.concatenate import concatenate_videoclips
from skimage.filters import gaussian


def blur(image):
    return gaussian(image.astype(float), sigma=2)

def sharpen(image):
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]])

    # Image processing using filters
    sharpened = cv2.filter2D(image, -1, kernel)

    # Make sure the pixel value is between 0-255
    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)

    return sharpened

st.set_page_config(
    page_title="Video Editor",
    page_icon="🎞️",
    layout="wide",
    initial_sidebar_state="auto",
)

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            # header {visibility: hidden;}
            </style>
            """

st.markdown(hide_streamlit_style, unsafe_allow_html=True)
st.sidebar.markdown("<h2>Upload file</h2>",unsafe_allow_html=True)

clip = st.sidebar.file_uploader(" ", type=["mp4", "avi", "flv", "mov"])

if clip:
    temp_file = tempfile.NamedTemporaryFile(suffix=".temp", delete=False)
    temp_filename = temp_file.name
    temp_file.write(clip.read())

    clip = mp.VideoFileClip(temp_filename)
    w, h = clip.size
    duration = clip.duration

    def get_subclip():
        global clip
        return clip.subclip(st.session_state.input_start, st.session_state.input_stop)
    
    def callback_blur():
        subclip = get_subclip()
        subclip = subclip.fl_image(blur)
        render(subclip)
    
    def callback_sharp():
        subclip = get_subclip()
        subclip = subclip.fl_image(sharpen)
        render(subclip)

    def callback_text():
        txt_clip = ( mp.TextClip(txt=st.session_state.input_text,fontsize=70,color='white')
             .set_position('center')
             .set_duration(10) )
        render(subclip = txt_clip, type = 'text')
        
    with st.sidebar.form(key='form_vfx'):
        start = st.number_input("Start Time (seconds)", key='input_start')
        end = st.number_input("End Time (seconds)", key='input_stop')
        button1 = st.form_submit_button(label='Apply gaussian blur', on_click=callback_blur)
        button2 = st.form_submit_button(label='Apply sharpening', on_click=callback_sharp)

    with st.sidebar.form(key='form_text'):
        end = st.text_input("Enter text", key='input_text')
        submit_button = st.form_submit_button(label='Add text overlay', on_click=callback_text)

    def render(subclip, type='vfx'):
        global clip

        if type == 'text':
            final_clip = mp.CompositeVideoClip([clip, subclip])
        else:
            final_clip = concatenate_videoclips([clip.subclip(0, st.session_state.input_start), subclip, clip.subclip(st.session_state.input_stop)])

        # Save video to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_filename = temp_file.name
            final_clip.write_videofile(temp_filename)

        # Open the temporary file and read its contents as bytes
        with open(temp_filename, "rb") as file:
            video_bytes = file.read()
        
        # st.session_state.filename = temp_filename

        # Display the video in Streamlit
        st.header("Edited Video")
        st.subheader("")
        st.video(video_bytes)
    