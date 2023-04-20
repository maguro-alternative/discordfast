import io
import asyncio
import os

class Audio_Files:
    def __init__(
        self,
        byte:bytes,
        filename:str = None
    )-> None:
        """
        Discordのファイルの送信を行う際のクラス

        param:
        byte:bytes
        ファイルのバイナリデータ

        filename:str
        ファイル名、拡張子も付ける

        content_type:str
        コンテンツタイプ(text/*等)
        """
        self.byte = byte
        self.iobyte = io.BytesIO(byte)
        self.loop = asyncio.new_event_loop()
        if len(os.path.splitext(filename)[1]) == 0:
            extension = self.loop.run_in_executor(
                executor=None,
                func=self.detect_audio_file
            )
            self.loop.run_until_complete(extension)
            self.filename = filename + extension.result()
        else:
            self.filename = filename
            
        # self.content_type = magic.from_file(byte, mime=True)
        
    async def detect_audio_file(self) -> str:
        """
        バイナリデータのマジックナンバーから音声ファイルの拡張子を識別する。

        param:
        file_byte:io.BytesIO
        ファイルのバイナリデータ

        return
        拡張子の文字列:str
        """
        header = self.iobyte.read(12)
            
        # AIFFファイルのマジックナンバー
        if header.startswith(b'FORM') and header[8:12] == b'AIFF':
            return '.aiff'
            
        # AIFF-Cファイルのマジックナンバー
        if header.startswith(b'FORM') and header[8:12] == b'AIFC':
            return '.aifc'
            
        # WAVEファイルのマジックナンバー
        if header.startswith(b'RIFF') and header[8:12] == b'WAVE':
            return '.wav'
            
        # MP3ファイルのマジックナンバー
        if header.startswith(b'\xFF\xFB') or header.startswith(b'\xFF\xF3') or \
        header.startswith(b'\xFF\xF2') or header.startswith(b'\xFF\xF4'):
            return '.mp3'

        # FLACファイルのマジックナンバー
        if header.startswith(b'fLaC'):
            return '.flac'

        # OGG Vorbisファイルのマジックナンバー
        if header.startswith(b'OggS') and header[28:31] == b'vorb':
            return '.ogg'

        # AACファイルのマジックナンバー
        if header.startswith(b'\xFF\xF1') or header.startswith(b'\xFF\xF9'):
            return '.aac'

        # AC-3ファイルのマジックナンバー
        if header.startswith(b'\x0B\x77') or header.startswith(b'\x77\x0B'):
            return '.ac3'

        # AMRファイルのマジックナンバー
        if header.startswith(b'#!AMR'):
            return '.amr'

        # GSMファイルのマジックナンバー
        if header.startswith(b'\x00\x01\x00\x01'):
            return '.gsm'
        
        # M4Aのマジックナンバー(LINEボイスメッセージの標準規格)
        if header.startswith(b'\x00\x00\x00\x1c') and header[8:12] == b'M4A ':
            return '.m4a'

        # マジックナンバーに該当するファイル形式が見つからなかった場合はNoneを返す
        return None
