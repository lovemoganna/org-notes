from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json, random, hashlib
data=json.loads(Path('tools/staging-e2e-assets.json').read_text())
base=Path('.')
navy='#183244'; cream='#FCF7EC'
fonts=list(Path('/usr/share/fonts').rglob('*NotoSansCJK*Regular*'))+list(Path('/usr/share/fonts').rglob('*NotoSansCJK*Bold*'))
assert fonts, 'Install Noto CJK font before rendering'
reg=next((str(f) for f in fonts if 'Regular' in f.name),str(fonts[0]))
bold=next((str(f) for f in fonts if 'Bold' in f.name),reg)
F=lambda n,b=False:ImageFont.truetype(bold if b else reg,n)
for item in data:
  im=Image.new('RGB',(1500,750),cream); d=ImageDraw.Draw(im)
  for y in range(40,750,31): d.line((25,y,1495,y),fill='#ECE7DF',width=2)
  for y in range(22,700,83): d.ellipse((-8,y,34,y+30),fill='#C9D3D3',outline='#788A90',width=2)
  d.rounded_rectangle((75,35,1410,165),radius=20,fill='#FFFFFF',outline='#DADBD5',width=3)
  d.text((110,47),item['title'],font=F(67,True),fill=navy)
  d.text((108,133),'从原文中提炼结构，保留事实与边界',font=F(23),fill=item['accent'])
  for i,pair in enumerate(item['modules']):
    title,body=pair.split('|')
    x=90+(i%2)*677;y=202+(i//2)*211
    d.rounded_rectangle((x,y,x+640,y+190),radius=21,fill='white',outline='#DFDFD8',width=3)
    d.rounded_rectangle((x+15,y+18,x+65,y+72),radius=14,fill=item['accent'])
    d.text((x+31,y+22),str(i+1),font=F(33,True),fill='white')
    d.text((x+87,y+21),title,font=F(36,True),fill=navy)
    d.line((x+22,y+96,x+609,y+96),fill='#E5E8E5',width=2)
    d.text((x+27,y+115),body,font=F(28),fill='#41545B')
  d.rounded_rectangle((88,640,1430,716),radius=18,fill='#F7E7D4',outline='#F0DBC5',width=2)
  d.text((111,661),'边界：'+item['caveat'],font=F(25),fill=navy)
  dst=base/item['assetPath'];dst.parent.mkdir(parents=True,exist_ok=True)
  im.save(dst,'WEBP',quality=80,method=6)
  print('IMAGE_CREATED',item['id'],len(dst.read_bytes()),hashlib.sha256(dst.read_bytes()).hexdigest())
