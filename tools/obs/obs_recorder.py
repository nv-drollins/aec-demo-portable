"""
OBS Recorder — System Tray
Sends path + filename to OBS via WebSocket before every recording,
matching exactly what Claude does via MCP. No file moving required.
Filename: {NNN}_{phase}_{app}_{requestor}
"""
import pystray
from PIL import Image, ImageDraw
import json, threading, time, os, glob, websocket, hashlib, base64
from datetime import datetime

TOOLS_DIR    = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(TOOLS_DIR, "current_session.json")
CONFIG_FILE  = os.path.join(TOOLS_DIR, "obs_recorder_config.json")
AEC_BASE     = os.path.normpath(os.path.join(TOOLS_DIR, ".."))

def load_config():
    defaults = {"host":"localhost","port":4455,"password":"",
                "scene":"Claude-rhino_capture",
                "items":{"claude":1,"rhino":2,"blender":3,"display":0}}
    try:
        with open(CONFIG_FILE) as f: return {**defaults,**json.load(f)}
    except:
        with open(CONFIG_FILE,"w") as f: json.dump(defaults,f,indent=2)
        return defaults

CFG = load_config()

# ── PROJECT INFERENCE ──────────────────────────────────────────────────
def infer_project():
    """Use session file if fresh (<4h), else find most recent capture."""
    try:
        with open(SESSION_FILE) as f: s = json.load(f)
        age = (datetime.now() - datetime.fromisoformat(s["timestamp"])).total_seconds()
        if age < 14400: return s
    except: pass

    versions = os.path.join(AEC_BASE, "aa_demo_versions")
    files = glob.glob(os.path.join(versions,"*","demo_captures","*.*"))
    if files:
        latest = max(files, key=os.path.getmtime)
        parts  = latest.replace("\\","/").split("/")
        try:
            vi = parts.index("aa_demo_versions")
            proj = parts[vi+1]
            return {"project_name": proj,
                    "record_path":  os.path.join(versions, proj, "demo_captures"),
                    "phase": "user_input"}
        except: pass
    return {"project_name":"unknown",
            "record_path": os.path.join(AEC_BASE,"demo_captures"),
            "phase":"user_input"}

def next_number(record_path):
    os.makedirs(record_path, exist_ok=True)
    files = [f for f in os.listdir(record_path)
             if f.endswith((".mp4",".mkv",".mov"))]
    return len(files) + 1

def write_session(data):
    data["timestamp"] = datetime.now().isoformat(timespec="seconds")
    with open(SESSION_FILE,"w") as f: json.dump(data,f,indent=2)

# ── OBS CLIENT ─────────────────────────────────────────────────────────
class OBS:
    def __init__(self):
        self.ws=None; self._id=0; self.ok=False
        self.lock=threading.Lock()

    def connect(self):
        try:
            ws=websocket.WebSocket(); ws.settimeout(5)
            ws.connect(f"ws://{CFG['host']}:{CFG['port']}")
            hello=json.loads(ws.recv())
            payload={"op":1,"d":{"rpcVersion":1}}
            ai=hello.get("d",{}).get("authentication")
            pw=CFG.get("password","")
            if ai and pw:
                s=base64.b64encode(hashlib.sha256((pw+ai["salt"]).encode()).digest()).decode()
                a=base64.b64encode(hashlib.sha256((s+ai["challenge"]).encode()).digest()).decode()
                payload["d"]["authentication"]=a
            ws.send(json.dumps(payload)); ws.recv()
            self.ws=ws; self.ok=True
            print("OBS connected")
        except Exception as e:
            self.ok=False; print(f"OBS connect failed: {e}")

    def req(self, type_, data=None):
        with self.lock:
            if not self.ok: self.connect()
            if not self.ok: return None
            self._id+=1
            try:
                self.ws.send(json.dumps({"op":6,"d":{
                    "requestType":type_,"requestId":str(self._id),
                    "requestData":data or {}}}))
                return json.loads(self.ws.recv()).get("d",{}).get("responseData")
            except: self.ok=False; return None

    def show_only(self, item_id):
        for name,iid in CFG["items"].items():
            if iid==0: continue
            self.req("SetSceneItemEnabled",
                {"sceneName":CFG["scene"],"sceneItemId":iid,
                 "sceneItemEnabled":(iid==item_id)})

    def set_record_dir(self, path):
        """Set OBS recording output directory."""
        os.makedirs(path, exist_ok=True)
        self.req("SetRecordDirectory", {"recordDirectory": path})

    def set_filename(self, name):
        """Set OBS filename format — plain name, no date variables."""
        self.req("SetProfileParameter", {
            "parameterCategory": "Output",
            "parameterName":     "FilenameFormatting",
            "parameterValue":    name
        })

    def is_recording(self):
        r=self.req("GetRecordStatus")
        return r.get("outputActive",False) if r else False

    def start(self): self.req("StartRecord")
    def stop(self):  self.req("StopRecord")

obs = OBS()

# ── ACTIONS ────────────────────────────────────────────────────────────
def do_record(app_name, item_id):
    s      = infer_project()
    proj   = s.get("project_name","unknown")
    phase  = s.get("phase","user_input") if s.get("requestor")=="claude" else "user_input"
    dest   = s.get("record_path", os.path.join(AEC_BASE,"demo_captures"))
    n      = next_number(dest)
    fname  = f"{n:03d}_{phase}_{app_name}_sean"

    # Write session — keeps Claude informed
    write_session({"project_name":proj,"record_path":dest,
                   "phase":phase,"app":app_name,
                   "requestor":"sean","current_filename":fname})

    if obs.is_recording(): obs.stop(); time.sleep(0.6)

    # Switch source
    if item_id > 0: obs.show_only(item_id); time.sleep(0.25)

    # Tell OBS exactly where and what to name the file
    obs.set_record_dir(dest)
    obs.set_filename(fname)
    time.sleep(0.15)

    obs.start()
    set_icon("red")
    icon.title = f"● {fname}"

def do_stop():
    obs.stop()
    time.sleep(0.4)
    obs.show_only(CFG["items"]["claude"])
    set_icon("dark")
    icon.title = "OBS Recorder — Stopped"

def run(fn,*a): threading.Thread(target=fn,args=a,daemon=True).start()

# ── TRAY ICON ──────────────────────────────────────────────────────────
def make_icon(fill):
    img=Image.new("RGBA",(64,64),(0,0,0,0))
    d=ImageDraw.Draw(img)
    d.ellipse([2,2,62,62],fill=fill,outline="#ffffff",width=3)
    d.ellipse([22,22,42,42],fill="#ffffff")
    return img

ICONS={"dark":make_icon("#2c2c2c"),"red":make_icon("#c0392b")}
def set_icon(s): icon.icon=ICONS.get(s,ICONS["dark"])

menu=pystray.Menu(
    pystray.MenuItem("● Record Rhino",   lambda:run(do_record,"rhino",  CFG["items"]["rhino"])),
    pystray.MenuItem("● Record Claude",  lambda:run(do_record,"claude", CFG["items"]["claude"])),
    pystray.MenuItem("● Record Blender", lambda:run(do_record,"blender",CFG["items"]["blender"])),
    pystray.MenuItem("● Record Display", lambda:run(do_record,"display",0)),
    pystray.Menu.SEPARATOR,
    pystray.MenuItem("⏹  Stop Recording",lambda:run(do_stop)),
)

icon=pystray.Icon("OBS Recorder",ICONS["dark"],"OBS Recorder",menu)
threading.Thread(target=obs.connect,daemon=True).start()
icon.run()
