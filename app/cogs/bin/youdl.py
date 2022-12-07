import youtube_dl

# youtube-dlでダウンロード
def you(test_video:str,id:int):
  # test_video = 'https://www.youtube.com/watch?v=smhoJzDiiwE'
  filename = f"./wave/{id}_music"

  ydl_opts = {
      'format': 'bestaudio/best',
      'outtmpl':  filename + '.%(ext)s',
      'postprocessors': [
          {'key': 'FFmpegExtractAudio',
          'preferredcodec': 'wav',
          'preferredquality': '192'},
          {'key': 'FFmpegMetadata'},
      ],
  }

  ydl = youtube_dl.YoutubeDL(ydl_opts)
  info_dict = ydl.extract_info(test_video, download=True)