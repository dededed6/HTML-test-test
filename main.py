import os
import yt_dlp
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from google.cloud import speech
import deepl
import pysrt

def download_youtube_video(url, output_path):
    ydl_opts = {
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.download([url])
    return result

def extract_audio_segment(video_path, start_time, end_time, output_path):
    audio_path = os.path.join(output_path, "audio_segment.wav")
    ffmpeg_extract_subclip(video_path, start_time, end_time, targetname=audio_path)
    return audio_path

def speech_to_text(audio_path):
    client = speech.SpeechClient()
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()
    
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ko-KR",
        enable_word_time_offsets=True,
    )
    
    response = client.recognize(config=config, audio=audio)
    return response.results

def translate_text(text, target_lang="KO"):
    auth_key = "YOUR_DEEPL_API_KEY"
    translator = deepl.Translator(auth_key)
    result = translator.translate_text(
        text, 
        target_lang=target_lang,
        source_lang="auto",
        split_sentences="1",
        preserve_formatting="1",
        formality="default"
    )
    return result.text

def write_subtitle_file(results, output_path):
    subs = pysrt.SubRipFile()
    index = 1
    for result in results:
        for alternative in result.alternatives:
            start_time = result.alternatives[0].words[0].start_time.total_seconds()
            end_time = result.alternatives[0].words[-1].end_time.total_seconds()
            text = translate_text(alternative.transcript)
            subs.append(pysrt.SubRipItem(index=index, start=pysrt.SubRipTime(seconds=start_time), end=pysrt.SubRipTime(seconds=end_time), text=text))
            index += 1

    subtitle_path = os.path.join(output_path, "translated_subtitle.srt")
    subs.save(subtitle_path, encoding='utf-8')
    return subtitle_path

# 사용자 입력
youtube_url = input("유튜브 링크를 입력하세요: ")
start_time = int(input("번역 시작 시간을 초 단위로 입력하세요: "))
end_time = int(input("번역 종료 시간을 초 단위로 입력하세요: "))
output_path = "downloads"

# 유튜브 비디오 다운로드
video_filename = download_youtube_video(youtube_url, output_path)
video_path = os.path.join(output_path, video_filename)

# 오디오 세그먼트 추출
audio_segment_path = extract_audio_segment(video_path, start_time, end_time, output_path)

# 음성을 텍스트로 변환
recognition_results = speech_to_text(audio_segment_path)

# 자막 파일 작성
subtitle_path = write_subtitle_file(recognition_results, output_path)

print(f"자막 파일이 '{subtitle_path}'에 저장되었습니다.")
