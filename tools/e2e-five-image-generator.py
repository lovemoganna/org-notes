#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import subprocess,json,hashlib
items=json.loads(Path(__file__).with_name("e2e-five-image-spec.json").read_text())
file=subprocess.check_output(["fc-match","-f","%{file}","Noto Sans CJK SC"]).decode().strip()
def font(n):
 return ImageFont.truetype(file,n)
for item in items:
 im=Image.new("RGB",(1600,800),"#faf6ed")
 d=ImageDraw.Draw(im)
 for y in range(95,800,36):d.line((65,y,1590,y),fill="#e9e3d8",width=2)
 d.line((58,0,58,800),fill="#d4bbb6",width=4)
 for y in range(40,780,68):d.ellipse((12,y-11,84,y+10),outline="#334f5c",width=5)
 d.rounded_rectangle((110,30,1510,166),radius=28,fill="#fffdf8",outline="#dac9ae",width=3)
 d.text((140,48),item["title"],font=font(66),fill="#18364c")
 d.line((140,130,770,130),fill="#d28f40",width=7)
 d.text((145,177),item["subtitle"],font=font(28),fill="#4c6173")
 pastel=[("#e8f3f5","#28a5aa"),("#fff1d9","#dba448"),("#ebe9ff","#8175bd"),("#fee9e6","#d6796d")]
 pos=[(110,249),(840,249),(110,451),(840,451)]
 for i,content in enumerate(item["cards"]):
  title,desc=content.split("|",1)
  x,y=pos[i]
  bg,accent=pastel[i]
  d.rounded_rectangle((x,y,x+655,y+174),radius=24,fill=bg,outline=accent,width=4)
  d.rounded_rectangle((x+22,y+16,x+95,y+76),radius=17,fill=accent)
  d.text((x+39,y+26),str(i+1).zfill(2),font=font(29),fill="#fff")
  d.text((x+115,y+15),title,font=font(37),fill="#193c53")
  d.text((x+116,y+88),desc,font=font(27),fill="#354f61")
 d.rounded_rectangle((111,651,1496,718),radius=15,fill="#dfefeb")
 d.text((142,662),item["footer"],font=font(27),fill="#254956")
 d.rounded_rectangle((112,731,1495,781),radius=11,fill="#fff0e2")
 d.text((144,740),item["boundary"],font=font(23),fill="#80533d")
 out=Path("note-assets")/item["wikiId"]/"sketchnote-header.webp"
 out.parent.mkdir(parents=True,exist_ok=True)
 im.save(out,format="WEBP",quality=78,method=6)
 print("REAL_SKETCH",item["wikiId"],out.stat().st_size,hashlib.sha256(out.read_bytes()).hexdigest())
