#!/usr/bin/env python3
from pathlib import Path
from urllib.request import Request, urlopen
import subprocess, shutil

ROOT=Path.cwd(); SRC=ROOT/'reel_sources'; TMP=ROOT/'reel_tmp'; SRC.mkdir(exist_ok=True); TMP.mkdir(exist_ok=True)
OUT=ROOT/'Damodar_Month_Reel_Final.mp4'
W,H,FPS=1080,1920,30
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; FONT_BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
SOURCES={
 'aarti.webm':'https://commons.wikimedia.org/wiki/Special:Redirect/file/Mangal_Aarti_at_ISKCON_Ujjain.webm',
 'bhajan.webm':'https://commons.wikimedia.org/wiki/Special:Redirect/file/A_Bhajan_at_ISKCON_Ujjain.webm'
}
def run(cmd):
    print('+',' '.join(str(c) for c in cmd),flush=True)
    subprocess.run([str(c) for c in cmd],check=True)
def dl(url,path):
    req=Request(url,headers={'User-Agent':'Mozilla/5.0'})
    print('Downloading',path.name,flush=True)
    with urlopen(req,timeout=120) as r, open(path,'wb') as f: shutil.copyfileobj(r,f)
    if path.stat().st_size<1000: raise RuntimeError('download too small')
for n,u in SOURCES.items(): dl(u,SRC/n)

# Extract a real deity/darshan frame from the real ISKCON video for intro/outro.
img=SRC/'real_darshan.jpg'
run(['ffmpeg','-y','-ss','6','-i',SRC/'aarti.webm','-frames:v','1','-q:v','2',img])

def esc(s): return s.replace('\\','\\\\').replace(':','\\:').replace("'","\\'")
def seg(src,start,dur,out,headline=None,kicker=None):
    f="[0:v]split=2[bg][fg];"+f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=22:8,eq=brightness=-0.20:saturation=1.08[bg2];"+"[fg]scale=1020:-2,eq=contrast=1.04:saturation=1.07[fg2];[bg2][fg2]overlay=(W-w)/2:(H-h)/2,format=yuv420p"
    if kicker: f+=f",drawtext=fontfile={FONT}:text='{esc(kicker)}':fontcolor=white@0.9:fontsize=34:x=(w-text_w)/2:y=150:shadowcolor=black@0.8:shadowx=2:shadowy=2"
    if headline: f+=f",drawtext=fontfile={FONT_BOLD}:text='{esc(headline)}':fontcolor=white:fontsize=52:x=(w-text_w)/2:y=h-270:box=1:boxcolor=black@0.28:boxborderw=20:shadowcolor=black@0.7:shadowx=2:shadowy=2"
    f+=f",fade=t=in:st=0:d=.2,fade=t=out:st={dur-.3:.2f}:d=.3[v]"
    run(['ffmpeg','-y','-ss',str(start),'-i',src,'-t',str(dur),'-filter_complex',f,'-map','[v]','-an','-r',str(FPS),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',out])
def still(src,dur,out,title,sub):
    f=f"[0:v]split=2[bg][fg];[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=26:10,eq=brightness=-0.22:saturation=1.08[bg2];[fg]scale=1020:-2[fg2];[bg2][fg2]overlay=(W-w)/2:(H-h)/2,format=yuv420p,drawtext=fontfile={FONT_BOLD}:text='{esc(title)}':fontcolor=white:fontsize=58:x=(w-text_w)/2:y=155:box=1:boxcolor=black@0.24:boxborderw=22:shadowcolor=black@0.8:shadowx=2:shadowy=2,drawtext=fontfile={FONT}:text='{esc(sub)}':fontcolor=white@0.95:fontsize=34:x=(w-text_w)/2:y=245:shadowcolor=black@0.8:shadowx=2:shadowy=2,fade=t=in:st=0:d=.45,fade=t=out:st={dur-.5:.2f}:d=.5[v]"
    run(['ffmpeg','-y','-loop','1','-i',src,'-t',str(dur),'-filter_complex',f,'-map','[v]','-an','-r',str(FPS),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',out])

parts=[]
p=TMP/'00.mp4'; still(img,3.2,p,'KARTIK - DAMODAR MONTH','The month most dear to Sri Krishna'); parts.append(p)
for i,(st,d,hd,k) in enumerate([
    (4,3.7,None,'Begin with darshan'),
    (19,3.8,'Offer a lamp',None),
    (37,3.8,None,None),
    (57,3.8,'Remember Sri Damodara',None),
    (78,3.8,None,None),
    (98,3.8,'Let devotion become your light',None)
],1):
    p=TMP/f'{i:02d}.mp4'; seg(SRC/'aarti.webm',st,d,p,hd,k); parts.append(p)
p=TMP/'07.mp4'; seg(SRC/'bhajan.webm',2,2.8,p,None,'Hare Krishna'); parts.append(p)
p=TMP/'08.mp4'; still(img,4.0,p,'OFFER A LAMP. OFFER YOUR HEART.','Hare Krishna'); parts.append(p)
concat=TMP/'concat.txt'; concat.write_text('\n'.join("file '{}'".format(x.resolve().as_posix()) for x in parts)); silent=TMP/'silent.mp4'
run(['ffmpeg','-y','-f','concat','-safe','0','-i',concat,'-c','copy',silent])
probe=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',silent],text=True).strip())
fade=max(0,probe-1.8)
# Use real devotional audio embedded in the real ISKCON aarti source.
run(['ffmpeg','-y','-ss','12','-i',SRC/'aarti.webm','-i',silent,'-filter_complex',f"[0:a]volume=0.86,afade=t=in:st=0:d=1.0,afade=t=out:st={fade:.2f}:d=1.8[a]",'-map','1:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart','-metadata','title=Damodar Month Reel','-metadata','comment=Real ISKCON devotional footage; no AI-generated media',OUT])
print('FINAL',OUT,OUT.stat().st_size,flush=True)
