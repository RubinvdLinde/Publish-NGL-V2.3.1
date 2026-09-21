from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from email.parser import BytesParser
from email.policy import default
import json, hashlib, re, webbrowser, threading, time

ROOT=Path(__file__).resolve().parent
PORT=8772
PLATFORMS={'NS':'Nintendo Switch','NS2':'Nintendo Switch 2','GC':'Nintendo GameCube','WII':'Nintendo Wii','WiiU':'Nintendo Wii U','SNES':'Super Nintendo','GB':'Game Boy'}
STATUS_SOURCE={'unplayed':'Not Played','playing':'Have Played','played':'Finished','dropped':'Stopped'}

def parse_num(v):
    v=(v or '').strip()
    if not v:return None
    try:
        x=float(v);return int(x) if x.is_integer() else x
    except:return None

def safe_name(s):
    s=re.sub(r'[<>:"/\\|?*]+','',s)
    return re.sub(r'\s+',' ',s).strip()[:160]

def read_games():return json.loads((ROOT/'data/games.json').read_text(encoding='utf-8'))
def write_games(g): (ROOT/'data/games.json').write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf-8')
def read_tiers():return json.loads((ROOT/'data/tier-order.json').read_text(encoding='utf-8'))
def write_tiers(t): (ROOT/'data/tier-order.json').write_text(json.dumps(t,ensure_ascii=False,indent=2),encoding='utf-8')

def parse_multipart(handler):
    n=int(handler.headers.get('Content-Length','0')); body=handler.rfile.read(n)
    ct=handler.headers.get('Content-Type','')
    msg=BytesParser(policy=default).parsebytes((f'Content-Type: {ct}\r\nMIME-Version: 1.0\r\n\r\n').encode()+body)
    fields={}; files={}
    if msg.is_multipart():
        for part in msg.iter_parts():
            name=part.get_param('name',header='content-disposition'); filename=part.get_filename()
            if not name: continue
            data=part.get_payload(decode=True) or b''
            if filename: files[name]=(filename,data,part.get_content_type())
            else: fields[name]=data.decode(part.get_content_charset() or 'utf-8',errors='replace')
    return fields,files

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        from urllib.parse import unquote, urlparse
        rel=unquote(urlparse(path).path).lstrip('/')
        return str((ROOT/rel).resolve())
    def json(self,obj,status=200):
        data=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        if self.path.startswith('/api/games'):
            return self.json(read_games())
        return super().do_GET()
    def do_POST(self):
        try:
            fields,files=parse_multipart(self)
            if self.path=='/api/add-game': return self.add_game(fields,files)
            if self.path=='/api/replace-cover': return self.replace_cover(fields,files)
            return self.json({'ok':False,'message':'Unknown endpoint'},404)
        except Exception as e:
            return self.json({'ok':False,'message':f'Error: {e}'},500)
    def add_game(self,f,files):
        title=(f.get('title') or '').strip(); code=f.get('platformCode','NS')
        if not title or 'cover' not in files:return self.json({'ok':False,'message':'Title and cover are required.'},400)
        games=read_games(); ids=[int(g['id']) for g in games if str(g.get('id','')).isdigit()]; new_id=max(ids or [0])+1
        orig,data,mime=files['cover']; ext=Path(orig).suffix.lower(); ext=ext if ext in ['.jpg','.jpeg','.png','.webp'] else '.jpg'
        filename=f"{new_id:03d} - {safe_name(title)} [{code}]{ext}"
        (ROOT/'covers'/filename).write_bytes(data)
        version=hashlib.sha1(data).hexdigest()[:10]
        status=f.get('status','unplayed'); fmt=f.get('format','Physical')
        g={'id':str(new_id),'title':title,'platformCode':code,'platform':PLATFORMS.get(code,code),'metaScore':parse_num(f.get('metaScore')),'score':parse_num(f.get('score')),'format':fmt,'status':status,'sourceStatus':STATUS_SOURCE.get(status,status),'cover':filename,'coverVersion':version,'tier':'U','tierPosition':None,'mainExtra':parse_num(f.get('mainExtra')),'completionist':parse_num(f.get('completionist')),'timePlayed':parse_num(f.get('timePlayed')),'notes':''}
        games.append(g);write_games(games)
        tiers=read_tiers();tiers.setdefault('U',[]).append(str(new_id));write_tiers(tiers)
        return self.json({'ok':True,'message':f'Added #{new_id}: {title}. It will appear as Unranked after publishing.'})
    def replace_cover(self,f,files):
        if 'cover' not in files:return self.json({'ok':False,'message':'Choose a cover image.'},400)
        gid=str(f.get('id',''));games=read_games();g=next((x for x in games if str(x.get('id'))==gid),None)
        if not g:return self.json({'ok':False,'message':'Game not found.'},404)
        orig,data,mime=files['cover']; ext=Path(orig).suffix.lower();ext=ext if ext in ['.jpg','.jpeg','.png','.webp'] else Path(g.get('cover','x.jpg')).suffix
        old=ROOT/'covers'/g['cover']; filename=f"{int(gid):03d} - {safe_name(g['title'])} [{g['platformCode']}]{ext}"
        newp=ROOT/'covers'/filename;newp.write_bytes(data)
        if old.exists() and old.resolve()!=newp.resolve(): old.unlink()
        g['cover']=filename;g['coverVersion']=hashlib.sha1(data).hexdigest()[:10];write_games(games)
        return self.json({'ok':True,'message':f"Cover replaced for {g['title']}."})

if __name__=='__main__':
    print(f'NGL Admin: http://localhost:{PORT}/admin.html')
    print('Leave this window open while using NGL Admin. Press Ctrl+C to stop.')
    threading.Thread(target=lambda:(time.sleep(1),webbrowser.open(f'http://localhost:{PORT}/admin.html')),daemon=True).start()
    ThreadingHTTPServer(('127.0.0.1',PORT),Handler).serve_forever()
