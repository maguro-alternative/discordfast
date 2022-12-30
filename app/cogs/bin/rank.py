import gc
import discord

import librosa
import numpy as np
import wave
from pydub import AudioSegment
import youtube_dl

class Wav_Karaoke:
    def __init__(self,user_id:int) -> None:
        self.filename = f".\wave\{user_id}_music"
        self.music_file_path = f'.\wave\{user_id}_music.wav'
        self.voice_file_path = f'.\wave\{user_id}_voice.wav'
        self.ratio_music_file_path = f'.\wave\{user_id}_ratio_music.wav'
        self.ratio_voice_file_path = f'.\wave\{user_id}_ratio_voice.wav'

    async def music_wav_open(self):   #wavファイルを開く
        base_sound = AudioSegment.from_file(self.music_file_path, format="wav")
        return base_sound

    async def music_wav_second(self) -> float:   #wavファイルを開く
        base_sound = AudioSegment.from_file(self.music_file_path, format="wav")
        return base_sound.duration_seconds

    async def voice_wav_open(self):   #wavファイルを開く
        base_sound = AudioSegment.from_file(self.voice_file_path, format="wav")
        return base_sound

    async def voice_wav_second(self) -> float:   #wavファイルを開く
        base_sound = AudioSegment.from_file(self.voice_file_path, format="wav")
        return base_sound.duration_seconds

    # サンプリング周波数を計算
    async def get_sampling_frequency(self,file_path:str) -> int:
        wr = wave.open(file_path, "r")
        fs = wr.getframerate()
        wr.close()
        return fs

    async def limit_wav_duration(self):   #wavファイルの秒数を60秒以内に収める
        before_values=[self.music_file_path,self.voice_file_path]
        after_values=[self.ratio_music_file_path,self.ratio_voice_file_path]
        for before_value,after_value in zip(before_values,after_values):
            before_sound = AudioSegment.from_file(before_value, format="wav")
            time = before_sound.duration_seconds

            if time>=60:
                speed = time/60
                base_sound = before_sound.speedup(playback_speed=speed, crossfade=0)
            else :
                base_sound = before_sound

            base_sound.export(after_value, format="wav")

    # 採点(類似度計算)
    async def calculate_wav_similarity(self):

        path_list=[self.ratio_music_file_path,self.ratio_voice_file_path]
    
        # 各wavファイルの振幅データ列とサンプリング周波数を取得し、リストに格納
        x_and_fs_list = []
        for path in path_list:
            x, fs = librosa.load(path,await self.get_sampling_frequency(path))
            x_and_fs_list.append((x, fs))
            #print(path+" サンプリング周波数 "+str(getSamplingFrequency(path))+"Hz")

        # 使用する特徴量を抽出し、リストに格納
        feature_list = []
        for x_and_fs in x_and_fs_list:
            feature = librosa.feature.spectral_centroid(x_and_fs[0], x_and_fs[1])
            feature_list.append(feature)

        del x_and_fs_list
        del path_list
        gc.collect()

        # 類似度を計算
        ac, wp = librosa.sequence.dtw(feature_list[0], feature_list[1])
        # -1で一番最後の要素を取得
        eval = 1 - (ac[-1][-1] / np.array(ac).max())
        #print("Score : {}".format(round(eval,4)))

        return eval*100

    # youtube-dlでダウンロード
    async def song_dl(self,video_url:str):
        filename = self.filename
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl':  filename + '.%(ext)s',
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192'
                },
                {
                    'key': 'FFmpegMetadata'
                },
            ],
        }
        ydl = youtube_dl.YoutubeDL(ydl_opts)
        ydl.extract_info(video_url, download=True)

def wavbase(wav):   #wavファイルを開く
    base_sound = AudioSegment.from_file(wav, format="wav")
    return base_sound

# サンプリング周波数を計算
def getSamplingFrequency(path):
    wr = wave.open(path, "r")
    fs = wr.getframerate()
    wr.close()
    return fs

def wavsecond(wav): #wavファイルの秒数を計算
    base_sound = AudioSegment.from_file(wav, format="wav")
    return base_sound.duration_seconds

def onewav(ctx:discord.ApplicationContext):   #wavファイルの秒数を60秒以内に収める
    before_values=[f"./wave/{ctx.author.id}_music.wav","./wave/sample_voice.wav"]
    after_values=["./wave/ratio_music.wav","./wave/ratio_voice.wav"]
    for before_value,after_value in zip(before_values,after_values):
        time=wavbase(before_value).duration_seconds

        if time>=60:
            speed = time/60
            base_sound = wavbase(before_value).speedup(playback_speed=speed, crossfade=0)
        else :
            base_sound=wavbase(before_value)

        base_sound.export(after_value, format="wav")

# 採点(類似度計算)
def wavcomp():

    path_list=["./wave/ratio_music.wav","./wave/ratio_voice.wav"]
    
    # 各wavファイルの振幅データ列とサンプリング周波数を取得し、リストに格納
    x_and_fs_list = []
    for path in path_list:
        x, fs = librosa.load(path, getSamplingFrequency(path))
        x_and_fs_list.append((x, fs))
        print(path+" サンプリング周波数 "+str(getSamplingFrequency(path))+"Hz")

    # 使用する特徴量を抽出し、リストに格納
    feature_list = []
    for x_and_fs in x_and_fs_list:
        feature = librosa.feature.spectral_centroid(x_and_fs[0], x_and_fs[1])
        feature_list.append(feature)

    del x_and_fs_list
    gc.collect()

    del path_list
    gc.collect()

    # 類似度を計算
    ac, wp = librosa.sequence.dtw(feature_list[0], feature_list[1])
    # -1で一番最後の要素を取得
    eval = 1 - (ac[-1][-1] / np.array(ac).max())
    print("Score : {}".format(round(eval,4)))

    return eval*100

def wavmain(ctx:discord.ApplicationContext):
    onewav(ctx)
    eval=wavcomp()
    return round(eval, 4)

if __name__ == "__main__":
    wavmain()

