import moviepy.editor as mp
import streamlit as st
import numpy as np

import cv2
import tempfile

from moviepy.video.compositing.concatenate import concatenate_videoclips
from skimage.filters import gaussian


def blur(image):
    return gaussian(image.astype(float), sigma=st.session_state.blur_sigma)


def sharpen(image):
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]])

    # Image processing using filters
    sharpened = cv2.filter2D(image, -1, kernel)

    # Make sure the pixel value is between 0-255
    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)

    return sharpened


def get_subclip(start, stop):
    global clip
    
    # https://zulko.github.io/moviepy/ref/Clip.html?highlight=subclip#moviepy.Clip.Clip.subclip
    return clip.subclip(start, stop)


def apply_effects():
    global clip, duration
    
    # init final_clip as clip if no effects are set
    final_clip = clip
    
    # check if blur is set
    start = st.session_state.blur_start
    stop = st.session_state.blur_stop
    if stop > start:
        subclip = get_subclip(start, stop)
        
        # https://zulko.github.io/moviepy/ref/VideoClip/VideoClip.html?highlight=fl_image#moviepy.video.io.VideoFileClip.VideoFileClip.fl_image
        subclip = subclip.fl_image(blur)
        final_clip = concatenate_videoclips([final_clip.subclip(0, start), subclip, final_clip.subclip(stop)])
    
    # check if sharp is set
    start = st.session_state.sharp_start
    stop = st.session_state.sharp_stop
    if stop > start:
        subclip = get_subclip(start, stop)
        subclip = subclip.fl_image(sharpen)
        final_clip = concatenate_videoclips([final_clip.subclip(0, start), subclip, final_clip.subclip(stop)])

    # check if text is set
    if st.session_state.overlay_text:
        txt_clip = ( mp.TextClip(txt=st.session_state.overlay_text, fontsize=70, color='white')
            .set_position('center')
            .set_duration(duration) )
    
        # https://zulko.github.io/moviepy/ref/VideoClip/VideoClip.html?highlight=compositevideoclip#moviepy.video.compositing.CompositeVideoClip.CompositeVideoClip
        final_clip = mp.CompositeVideoClip([final_clip, txt_clip])
    
    # write edited clip to temp file
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    temp_filename = temp_file.name
    final_clip.write_videofile(temp_filename)
    
    render(temp_filename, 'Edited video')
        

def render(filename, title):
    # Open the temporary file and read its contents as bytes
    with open(filename, "rb") as file:
        video_bytes = file.read()

    # Display the video in Streamlit
    st.header(title)
    st.subheader("")
    st.video(video_bytes)


# Initialize streamlit
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
st.sidebar.markdown("<h2>Upload file</h2>", unsafe_allow_html=True)

clip = st.sidebar.file_uploader(" ", type=["mp4", "avi", "flv", "mov"])
 
if clip:
    # write & render original video
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    temp_filename = temp_file.name
    temp_file.write(clip.read())

    clip = mp.VideoFileClip(temp_filename)
    duration = clip.duration
    render(temp_filename, 'Original video')
    
    # init form
    with st.sidebar.form(key='form_effects'):
        st.write("Gaussian blur")
        st.number_input("Start Time (seconds)", key='blur_start')
        st.number_input("End Time (seconds)", key='blur_stop')
        st.number_input("Amount", key='blur_sigma', value=2)
        st.write("Sharpening")
        st.number_input("Start Time (seconds)", key='sharp_start')
        st.number_input("End Time (seconds)", key='sharp_stop')
        st.text_input("Text overlay", key='overlay_text')
        st.form_submit_button(label='Apply changes', on_click=apply_effects)
    