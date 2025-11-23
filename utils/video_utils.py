import os, tempfile, shutil
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_OK = True
except Exception:
    MOVIEPY_OK = False

from .ocr_utils import ocr_from_path
from .ai_utils import transcribe_audio_path

def process_video_file(fp):
    """
    Extract audio (mp3) and a few frames from the video file
    Returns dictionary: { audio_text: "...", frames_text: "..." }
    If moviepy not available, return empty dict.
    """
    if not MOVIEPY_OK:
        return {}
    tmpdir = tempfile.mkdtemp(prefix="satya_")
    try:
        clip = VideoFileClip(fp)
        audio_path = os.path.join(tmpdir, "audio.mp3")
        if clip.audio:
            clip.audio.write_audiofile(audio_path, logger=None)
            audio_text = transcribe_audio_path(audio_path) or ""
        else:
            audio_text = ""
        frames_text = ""
        duration = clip.duration or 1
        times = [duration * i / 4.0 for i in range(1, 4)]
        for i, t in enumerate(times):
            frame_path = os.path.join(tmpdir, f"frame_{i}.jpg")
            clip.save_frame(frame_path, t)
            frames_text += ocr_from_path(frame_path) + "\n"
        return { "audio_text": audio_text, "frames_text": frames_text }
    except Exception as e:
        print("Video processing error:", e)
        return {}
    finally:
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass
