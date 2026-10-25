#!/usr/bin/env python3
from pathlib import Path
from urllib.request import Request, urlopen
import subprocess, shutil, sys, os

ROOT = Path.cwd()
SRC = ROOT / 'reel_sources'
TMP = ROOT / 'reel_tmp'
SRC.mkdir(exist_ok=True)
TMP.mkdir(exist_ok=True)
OUT = ROOT / 'Damodar_Month_Reel_Final.mp4'

W, H, FPS = 1080, 1920, 30
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

sources = {
    'aarti.webm': 'https://commons.wikimedia.org/wiki/Special:Redirect/file/Mangal_Aarti_at_ISKCON_Ujjain.webm',
    'bhajan.webm': 'https://commons.wikimedia.org/wiki/Special:Redirect/file/A_Bhajan_at_ISKCON_Ujjain.webm',
    'damodar.ogg': 'https://commons.wikimedia.org/wiki/Special:Redirect/file/Sri_Damodarastaka_Swami_BA_Paramadvaiti.ogg',
    'ghaziabad.webp': 'https://iskconghaziabad.com/wp-content/uploads/2023/11/IMG-20230406-WA0029-1024x682.webp',
}

def run(cmd):
    print('+', ' '.join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True)

def download(url, path):
    print('Downloading', path.name, flush=True)
    req = Request(url, headers={'User-Agent':'Mozilla/5.0 Damodar-Reel/1.0'})
    with urlopen(req, timeout=90) as r, open(path, 'wb') as f:
        shutil.copyfileobj(r, f)
    if path.stat().st_size < 1000:
        raise RuntimeError(f'Download too small: {path}')

for name, url in sources.items():
    path = SRC / name
    try:
        download(url, path)
    except Exception as e:
        if name == 'ghaziabad.webp':
            print('Official Ghaziabad image download failed, using real CC fallback:', e)
            download('https://commons.wikimedia.org/wiki/Special:Redirect/file/Radha_Krishna_at_Iskcon_Vrindavan.jpg', SRC/'ghaziabad.jpg')
        else:
            raise

image_path = SRC/'ghaziabad.webp'
if not image_path.exists() or image_path.stat().st_size < 1000:
    image_path = SRC/'ghaziabad.jpg'

if not shutil.which('ffmpeg'):
    raise SystemExit('ffmpeg not found')

def esc(s):
    return s.replace('\\','\\\\').replace(':','\\:').replace("'", "\\'")

def video_segment(src, start, dur, out, headline=None, kicker=None):
    fg = "[0:v]split=2[bg][fg];" \
         f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=22:8,eq=brightness=-0.20:saturation=1.08[bg2];" \
         f"[fg]scale=1020:-2,eq=contrast=1.04:saturation=1.07[fg2];" \
         "[bg2][fg2]overlay=(W-w)/2:(H-h)/2,format=yuv420p"
    if kicker:
        fg += f",drawtext=fontfile={FONT}:text='{esc(kicker)}':fontcolor=white@0.88:fontsize=34:x=(w-text_w)/2:y=145:shadowcolor=black@0.8:shadowx=2:shadowy=2"
    if headline:
        fg += f",drawtext=fontfile={FONT_BOLD}:text='{esc(headline)}':fontcolor=white:fontsize=52:x=(w-text_w)/2:y=h-260:box=1:boxcolor=black@0.28:boxborderw=20:shadowcolor=black@0.7:shadowx=2:shadowy=2"
    fg += f",fade=t=in:st=0:d=0.22,fade=t=out:st={max(0,dur-0.28):.2f}:d=0.28[v]"
    run(['ffmpeg','-y','-ss',str(start),'-i',src,'-t',str(dur),'-filter_complex',fg,'-map','[v]','-an','-r',str(FPS),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',out])

def still_segment(src, dur, out, title, subtitle):
    filt = "[0:v]split=2[bg][fg];" \
           f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=26:10,eq=brightness=-0.24:saturation=1.08[bg2];" \
           "[fg]scale=1020:-2[fg2];" \
           "[bg2][fg2]overlay=(W-w)/2:(H-h)/2,format=yuv420p," \
           f"drawtext=fontfile={FONT_BOLD}:text='{esc(title)}':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=160:box=1:boxcolor=black@0.25:boxborderw=22:shadowcolor=black@0.8:shadowx=2:shadowy=2," \
           f"drawtext=fontfile={FONT}:text='{esc(subtitle)}':fontcolor=white@0.94:fontsize=36:x=(w-text_w)/2:y=245:shadowcolor=black@0.8:shadowx=2:shadowy=2," \
           f"fade=t=in:st=0:d=0.45,fade=t=out:st={max(0,dur-0.5):.2f}:d=0.5[v]"
    run(['ffmpeg','-y','-loop','1','-i',src,'-t',str(dur),'-filter_complex',filt,'-map','[v]','-an','-r',str(FPS),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',out])

segments=[]
p=TMP/'00_intro.mp4'; still_segment(image_path,3.4,p,'KARTIK - DAMODAR MONTH','Sri Sri Radha Madan Mohan | ISKCON Ghaziabad'); segments.append(p)

cuts = [
    (4.0, 3.7, None, 'The month most dear to Sri Krishna'),
    (19.0, 3.8, 'Offer a lamp', None),
    (37.0, 3.8, None, None),
    (57.0, 3.9, 'Sing Sri Damodarastakam', None),
    (78.0, 3.8, None, None),
    (98.0, 3.9, 'Let devotion become your light', None),
]
for i,(start,dur,headline,kicker) in enumerate(cuts,1):
    p=TMP/f'{i:02d}_aarti.mp4'
    video_segment(SRC/'aarti.webm',start,dur,p,headline=headline,kicker=kicker)
    segments.append(p)

p=TMP/'07_bhajan.mp4'; video_segment(SRC/'bhajan.webm',2.0,2.8,p,kicker='Hare Krishna'); segments.append(p)
p=TMP/'08_outro.mp4'; still_segment(image_path,4.0,p,'OFFER A LAMP. OFFER YOUR HEART.','Hare Krishna'); segments.append(p)

concat = TMP/'concat.txt'
concat.write_text('\n'.join("file '{}'".format(x.resolve().as_posix()) for x in segments))
silent=TMP/'silent.mp4'
run(['ffmpeg','-y','-f','concat','-safe','0','-i',concat,'-c','copy',silent])

# determine final duration for audio fade
probe = subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',silent], text=True).strip()
duration=float(probe)
fade_out=max(0,duration-1.8)
run(['ffmpeg','-y','-ss','4','-i',SRC/'damodar.ogg','-i',silent,
     '-filter_complex',f"[0:a]volume=0.95,afade=t=in:st=0:d=1.0,afade=t=out:st={fade_out:.2f}:d=1.8[a]",
     '-map','1:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',
     '-metadata','title=Damodar Month Reel','-metadata','comment=Real devotional footage; no AI-generated media',OUT])

print('FINAL:', OUT, 'size=', OUT.stat().st_size, flush=True)
