import io
import os

class ImageFiles:
    """
    ファイルのバイナリのデータを格納するクラス

    param:
    byte:bytes
    ファイルのバイトデータ

    filename:str
    ファイル名、拡張子は付けても付けなくてもいい

    付かなかった場合マジックナンバーから推測する
    """
    def __init__(
        self,
        byte:bytes,
        filename:str = None
    ) -> None:
        """
        Discordのファイルの送信を行う際のクラス

        param:
        byte:bytes
        ファイルのバイナリデータ

        filename:str
        ファイル名、拡張子も付ける

        ついていない場合はマジックナンバーから推測する
        """
        self.byte = byte
        if len(os.path.splitext(filename)[1]) == 0:
            extension = self.detect_image_file()
            self.filename = filename + extension.capitalize()
        else:
            self.filename = filename

    def detect_image_file(self) -> str:
        """
        バイナリデータのマジックナンバーから画像ファイルの拡張子を識別する。

        param:
        file_byte:io.BytesIO
        ファイルのバイナリデータ

        return
        拡張子の文字列:str
        """
        header = io.BytesIO(self.byte).read(12)
        if header[:2] == b'\xFF\xD8':
            return '.jpg'
        if header[:4] == b'\x89\x50\x4E\x47':
            return '.png'
        if header[:4] == b'\x47\x49\x46\x38':
            return '.gif'

class AudioFiles:
    """
    ファイルのバイナリのデータを格納するクラス

    param:
    byte:bytes
    ファイルのバイトデータ

    filename:str
    ファイル名、拡張子は付けても付けなくてもいい

    付かなかった場合マジックナンバーから推測する
    """
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

        iobyte:io.BytesIO
        ファイルのバイナリデータ

        filename:str
        ファイル名、拡張子も付ける

        ついていない場合はマジックナンバーから推測する
        """
        self.byte = byte
        self.iobyte = io.BytesIO(byte)
        if len(os.path.splitext(filename)[1]) == 0:
            extension = self.detect_audio_file()
            self.filename = filename + extension.capitalize()
        else:
            self.filename = filename

    def detect_audio_file(self) -> str:
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
