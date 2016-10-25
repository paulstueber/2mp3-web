############# SETUP ###############
# sudo apt-get install python3
# sudo apt-get install python3-pip
# sudo apt-get install libav-tools
# sudo python3 -m pip install youtube-dl
# ##################################

from http.server import BaseHTTPRequestHandler,HTTPServer
import sys
import os
import youtube_dl
from urllib.parse import urlparse, parse_qs

# very basic HTML template including css & javascript
s = """<html>
    <head>
        <title>M2MP3 - Musik to MP3</title>
        <link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">
        <style>
            body {
              padding-top: 50px;
            }
            .starter-template {
              padding: 40px 15px;
              text-align: center;
            }
            #video-overview img {
                width: 100%;
            }
        </style>
    </head> 
    <body>
        <div class="container">
            <div class="starter-template">
            <h1>MP3 generater from Web-Videos</h1>
            <p class="small">
                Very simple web frontend for <a href="https://rg3.github.io/youtube-dl/">youtube-dl</a>. It is meant to be simple as simple as possible. Anyone should be able to edit it to their needs. For reasons no multithreading is configured, so the server will only process one request at a time. <br />To start the server simply run: <strong>python3 2mp3.py &lt;PORT&gt; &lt;TARGET_FOLDER&gt;</strong>. The website is then (depending on your systen & configuration) available under: <strong>http://localhost:8000</strong>
            </p>
            <p class="lead">
                <div class="input-group">
                  <input type="text" class="form-control" placeholder="Video URL..." id="video-url">
                  <span class="input-group-btn">
                <button class="btn btn-default" type="button" id="download-mp3">Go!</button>
                  </span>
                </div><!-- /input-group -->
            </p>
            <div id="video-overview"></div>
        </div><!-- /.container -->

        <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js" integrity="sha384-0mSbJDEHialfmuBBQP6A4Qrprq5OVfW37PRR3j5ELqxss1yVqOtnepnHVP9aJ7xS" crossorigin="anonymous"></script>
<script>
$(document).ready(function(){
    var processed = {};
    $('#download-mp3').click(function() {
        var url = $('#video-url').val();
        url = url.startsWith('http') ? url : 'http://'+url; 
        if (processed[url] === undefined) {
          processed[url] = url;
          $.get('/info?url='+url, function(data) {
              var $preview = $('<div class="row"><div class="col-lg-4"><img src="'+data.thumbnail+'" width="200px" /></div><div class="col-lg-8"><h2>'+data.fulltitle+'</h2><div class="status">Datei wird verarbeitet...</div></div></div>');
              $('#video-overview').append($preview);
              $.get('/download?url='+url, function(data) {
                  $preview.find('.status').text("Fertig!");
                  console.log($preview.find('.status'));
              });
          });
        }
    });
});
</script>
    </body>
</html>
"""

# define where all mp3 should be stored
targetFolder = "./"

# c&p from youtube-dl tutorial
class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

# class to handle downloads
class AudioDownloader():
    def my_hook(self, d):
        if d['status'] == 'finished':
            print('Done downloading, now converting ...')

    def downloadAudio(self, url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'logger': MyLogger(),
            'progress_hooks': [self.my_hook],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            res = ydl.download([url])
            print("done with all")

    def downloadAudioInfo(self, url):
        filelist = [ f for f in os.listdir(".") if f.endswith(".json") ]
        for f in filelist:
            os.remove(f)
        ydl_opts = {
            'skip_download': True,
            'writeinfojson': True
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            res = ydl.download([url])
            filelist = [ f for f in os.listdir(".") if f.endswith(".json") ]
            with open(filelist[0], 'r') as myfile:
                data=myfile.read()
                print("done with all")
                return data

class MyHandler(BaseHTTPRequestHandler):
    ad=AudioDownloader()
    
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        
        params = parse_qs(urlparse(self.path).query)
        if self.path.startswith("/download") and 'url' in params:
            self.ad.downloadAudio(params['url'][0])
            filelist = [ f for f in os.listdir(".") if f.endswith(".mp3") ]
            for f in filelist:
              os.rename(f, targetFolder + f)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes("{\"status\": \"done\"}", 'UTF-8'))
            return
        if self.path.startswith("/info") and 'url' in params:
            json = self.ad.downloadAudioInfo(params['url'][0])
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(json, 'UTF-8'))
            return
            
        
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes(s, 'UTF-8'))
        
if __name__ == '__main__':
    HandlerClass = MyHandler
    ServerClass  = HTTPServer
    Protocol     = "HTTP/1.0"

    HOST_NAME = '0.0.0.0' 
    HOST_PORT = 8000 

    if sys.argv[1:]:
        HOST_PORT = int(sys.argv[1])
    if sys.argv[2:]:
        targetFolder = sys.argv[2] if sys.argv[2].endswith("/") else sys.argv[2] + "/"
        

    server_address = (HOST_NAME, HOST_PORT)

    HandlerClass.protocol_version = Protocol
    httpd = ServerClass(server_address, HandlerClass)

    sa = httpd.socket.getsockname()
    print("Serving HTTP on", sa[0], sa[1], "...")
    httpd.serve_forever()


