import youtube_dl
from flask import Flask, request, Response
import os
import time

app = Flask(__name__)

def format_speed(speed):
  
  speed = speed / 1024
  
  if speed < 1024:
    unit = 'KB/s'
  else:
    speed = speed / 1024
    if speed < 1024:
      unit = 'MB/s'
    else:
      speed = speed / 1024
      unit = 'GB/s'
 
  return f"{speed:.2f} {unit}"

def format_size(size):
  
  size = size / 1024
  
  if size < 1024:
    unit = 'KB'
  else:
    size = size / 1024
    if size < 1024:
      unit = 'MB'
    else:
      size = size / 1024
      unit = 'GB'
 
  return f"{size:.2f} {unit}"

def convert_video(video_id, format, folder):

  import subprocess
  
  source = f"{folder}/{video_id}.mp4"
  target = f"{folder}/{video_id}.{format}"

  command = f"ffmpeg -i {source} {target}" # ou "avconv -i {source} {target}"
  
  try:
    # exécuter la commande et attendre qu'elle se termine
    subprocess.run(command, shell=True, check=True)
    yield f"Conversion terminée, vidéo sauvegardée dans {folder}\n\n"
  except subprocess.CalledProcessError as e:
    yield f"Erreur lors de la conversion: {e}\n\n"


def download_video(url, format, folder):
 
  video = youtube_dl.YoutubeDL({'outtmpl': f'{folder}/%(id)s.%(ext)s', 'continuedl': True})
  
  info = video.extract_info(url, download=False)
 
  video_id = info['id']
  video_title = info['title']
  
  total_size = info['filesize'] or info['filesize_approx']
  
  yield f"Téléchargement de {video_title} ({video_id})\n\n"
  
  def progress_hook(d):
    if d['status'] == 'downloading':
      
      downloaded = d['downloaded_bytes']
      total = d['total_bytes'] or d['total_bytes_estimate']
      speed = d['speed']
      eta = d['eta']
      
      percentage = downloaded / total * 100
      speed = format_speed(speed)
      downloaded = format_size(downloaded)
      total = format_size(total)
      
      yield f"{percentage:.1f}% de {downloaded}/{total} à {speed}, temps estimé: {eta} secondes\n\n"
    elif d['status'] == 'finished':
    
      yield f"Téléchargement terminé, conversion en {format}\n\n"
    elif d['status'] == 'error':
    
      yield f"Erreur lors du téléchargement: {d['error']}\n\n"
  
  try:
    video.download([url], progress_hooks=[progress_hook])
 
    yield from convert_video(video_id, format, folder)
    
    yield f"Téléchargement et conversion réussis\n\n"
    
  except youtube_dl.utils.DownloadError as e:
    yield f"Erreur lors du téléchargement: {e}\n\n"


@app.route('/download', methods=['POST'])
def download():
 
 # modifier cette partie pour accepter les informations JSON
 data = request.get_json()
 url = data['url']
 format = data['format']
 folder = data['folder']

 
 if not url or not format or not folder:
   return jsonify({'error': 'Paramètres manquants'})

 
 if not os.path.exists(folder):
   os.makedirs(folder)

 
 generator = download_video(url, format, folder)

 
 return Response(generator, mimetype='text/plain')



if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
