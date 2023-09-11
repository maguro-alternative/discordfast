import gc
import asyncio

import librosa
import numpy as np
import wave
import os

import subprocess
from functools import partial
import re
import youtube_dl
from yt_dlp import YoutubeDL

class WavKaraoke:
    def __init__(self,user_id:int) -> None:
        """
        カラオケのクラス

        self.filename               :str
            ダウンロードする音楽ファイルの相対パス
        self.music_file_path        :str
            ダウンロードした音楽ファイルの相対パス
        self.voice_file_path        :str
            録音音声ファイルの相対パス
        self.ratio_music_file_path  :str
            60秒に収めた音楽ファイルの相対パス
        self.ratio_voice_file_path  :str
            60秒に収めた録音音声ファイルの相対パス
        """
        self.filename = f".\wave\{user_id}_music"
        self.music_file_path = f'.\wave\{user_id}_music.wav'
        self.voice_file_path = f'.\wave\{user_id}_voice.wav'
        self.ratio_music_file_path = f'.\wave\{user_id}_ratio_music.wav'
        self.ratio_voice_file_path = f'.\wave\{user_id}_ratio_voice.wav'
        self.loop = asyncio.get_event_loop()
        self.before_values = [
            f'.\wave\{user_id}_music.wav',
            f'.\wave\{user_id}_voice.wav'
        ]
        self.after_values = [
            f'.\wave\{user_id}_ratio_music.wav',
            f'.\wave\{user_id}_ratio_voice.wav'
        ]

    async def music_wav_second(self) -> float:   #音楽のwavファイルの秒数を返す
        with wave.open(self.music_file_path,mode='rb') as wf:
            return float(wf.getnframes()) / wf.getframerate()

    async def voice_wav_second(self) -> float:   #録音音声のwavファイルの秒数を返す
        with wave.open(self.voice_file_path,mode='rb') as wf:
            return float(wf.getnframes()) / wf.getframerate()

    # サンプリング周波数を計算
    async def get_sampling_frequency(self,file_path:str) -> int:
        wr = wave.open(file_path, "r")
        fs = wr.getframerate()
        wr.close()
        return fs

    async def limit_wav_duration(self):   #wavファイルの秒数を60秒以内に収める
        """
        wavファイルを60秒に収める理由
        採点で使用するDTW(動的タイムワープ方式)は2種類の時系列データの比較を行うもの。
        長さが異なるものも比較できるが、異なる分だけ対応付けをしなければならないので、メモリにデータを残さないといけない。
        約1GBを許容範囲とした結果、wavファイルを60秒に抑えることにした。
        """
        for before_value,after_value in zip(self.before_values,self.after_values):
            cmd = f"ffprobe -hide_banner {before_value} -show_entries format=duration"
            process = await self.loop.run_in_executor(
                None,
                partial(
                    subprocess.run,cmd.split(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
            )
            stdout_result = process.stdout.decode()
            match = re.search(r'(\d+\.\d+)', stdout_result)
            sound_second = float(match.group(1))

            if sound_second >= 60:
                cmd = f'ffmpeg -i {before_value} -filter:a "atempo={sound_second / 60}" -t 60 {after_value}'
                await self.loop.run_in_executor(
                    None,
                    partial(
                        subprocess.run,cmd.split(),
                        check=True
                    )
                )
            else:
                os.rename(before_value,after_value)

    # 採点(類似度計算)
    async def calculate_wav_similarity(self):
        # 各wavファイルの振幅データ列とサンプリング周波数を取得し、リストに格納
        x_and_fs_list = []
        for path in self.after_values:
            x, fs = await self.loop.run_in_executor(
                executor=None,
                func=librosa.load(
                    path,
                    await self.get_sampling_frequency(path)
                )
            )
            x_and_fs_list.append((x, fs))

        # 使用する特徴量を抽出し、リストに格納
        feature_list = []
        for x_and_fs in x_and_fs_list:
            feature = await self.loop.run_in_executor(
                executor=None,
                func=librosa.feature.spectral_centroid(
                    x_and_fs[0],
                    x_and_fs[1]
                )
            )
            feature_list.append(feature)

        # メモリ削減のため、特徴量を削除
        del x_and_fs_list
        gc.collect()

        # 類似度を計算
        ac, wp = await self.loop.run_in_executor(
            executor=None,
            func=librosa.sequence.dtw(
                feature_list[0],
                feature_list[1]
            )
        )
        # -1で一番最後の要素を取得
        eval = 1 - (ac[-1][-1] / np.array(ac).max())

        return round(eval*100,4)

    async def yt_song_dl(
        self,
        video_url:str,
    ) -> None:
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
        with YoutubeDL(ydl_opts) as ydl:
            await self.loop.run_in_executor(
                None,
                lambda: ydl.download(
                    [video_url]
                )
            )
