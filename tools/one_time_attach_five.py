#!/usr/bin/env python3
import hashlib,json,re,urllib.parse,urllib.request
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
CASES=json.loads(r'''[["T01","提示词基础","notes/knowledge/prompt-foundations/bd495eff-e3a8-5279-b195-09c80df649e0.org","Major/1.什么是提示词.md","1c9ed5231580eb25d96e75da70ed5981dc5a877c","指令|上下文|输入数据|输出要求"],["T02","提示词实践","notes/knowledge/prompt-practice/ac1d030f-b7fe-5823-a313-f48d4de5d81c.org","Major/3.提示实践.md","abdb5480bacec8a42cea0cbdbdef6c636e484ae9","清晰性|上下文|精确性|角色设定"],["T03","提示词工具","notes/knowledge/prompt-tool-selection/01ac0ca1-ed8e-5573-a04d-2f2fdfa012b8.org","Major/4.提示工具.md","d9a479eb1f97ea7f195a515067971a496ca8496a","模板管理|实验评估|团队权限|接口集成"],["T04","相关方冲突预判","notes/knowledge/stakeholder-conflict-detection/74089b46-d15b-50df-8843-cbb05d586394.org","Original/Work/Project/5-冲突预判.md","01f58b5d93f03387979a257792b068fb018ce17a","目标差异|职责边界|资源争夺|沟通信号"],["T05","提示词质量检查","notes/knowledge/prompt-quality-audit/0e17a6e1-c423-5c02-8183-b797c8603034.org","Original/Meta/Prompt_Word_Quality_Inspection_Tools.md","81aad0de95a86ab0c9983dbd9ae97dc10c30fd36","目标定位|结构检查|效果验证|安全边界"]]''')
SHA='0fdfdde53854523a9bd8704a1ac2c2c785702072'
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
if not Path(FONT).exists():raise RuntimeError('CJK font missing')
def f(n):return ImageFont.truetype(FONT,n)
def paint(path,title,labels):
    im=Image.new('RGB',(1440,720),'#faf6eb'); d=ImageDraw.Draw(im)
    for y in range(40,710,34):d.line((20,y,1425,y),fill='#e5dcd0',width=2)
    d.line((65,0,65,720),fill='#d6a6a0',width=3)
    for y in range(25,710,46):d.ellipse((12,y,38,y+23),fill='#f3eee2',outline='#1e3847',width=3)
    d.text((102,44),title,font=f(63),fill='#173249')
    d.text((103,141),'四个关键判断 · 具体模板与案例见原始正文',font=f(24),fill='#46626d')
    bg=['#DFEFF8','#DEF4EB','#FFF0DC','#F0E6F8'];cl=['#2E80AE','#0E9878','#C77644','#8B6DA6']
    for i,label in enumerate(labels):
        x=96+i*337
        d.rounded_rectangle((x,231,x+317,505),radius=20,fill=bg[i],outline=cl[i],width=5)
        d.ellipse((x+22,253,x+73,305),fill=cl[i])
        d.text((x+39,260),str(i+1),font=f(27),fill='white')
        d.text((x+22,356),label,font=f(33),fill='#1E384A')
        d.line((x+20,427,x+287,427),fill=cl[i],width=3)
        d.text((x+25,456),'核对 • 判断',font=f(22),fill='#4C6771')
    d.rounded_rectangle((102,554,1401,679),radius=18,fill='#FCEBDB',outline='#CC9F7D',width=3)
    d.text((143,594),'事实归事实，建议归建议；未经验证不得写成已取得的效果。',font=f(28),fill='#4D514F')
    path.parent.mkdir(parents=True,exist_ok=True)
    im.save(path,'WEBP',quality=75,method=6)
result=[]
for case,title,rel,src,blob,labels in CASES:
    url='https://raw.githubusercontent.com/lovemoganna/Prompts/'+SHA+'/'+urllib.parse.quote(src,safe='/')
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'note-reforge-five-e2e'}),timeout=40) as r:b=r.read()
    sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    if sha!=blob:raise RuntimeError(case+' wrong source blob')
    raw=b.decode('utf-8').rstrip('\n')
    if re.search(r'(?mi)^#\+end_example\s*$',raw):raise RuntimeError(case+' Org example terminator in source')
    note=ROOT/rel
    if not note.is_file():raise RuntimeError(case+' missing prewritten article')
    s=note.read_text(encoding='utf-8')
    uid=re.search(r'(?m)^#\+WIKI_ID:\s*(\S+)',s).group(1)
    if uid!=note.stem:raise RuntimeError(case+' note identity mismatch')
    asset=ROOT/'note-assets'/uid/'sketchnote-header.webp'
    if asset.exists():raise RuntimeError(case+' asset already exists')
    paint(asset,title,labels.split('|'))
    pic='\\n#+CAPTION: '+title+'知识结构图（固定输入、审阅后使用）\\n#+ATTR_HTML: :width 860px\\n[[file:../../../note-assets/'+uid+'/sketchnote-header.webp]]\\n'
    marker='#+WIKI_STATUS: draft'
    if s.count(marker)!=1:raise RuntimeError(case+' missing draft state')
    s=s.replace(marker,marker+pic,1)
    s=s.replace('本次为未发布预览稿，图像资源仍处于独立 HTML 评审包，尚未进入 GitHub 仓库。','本次仍为未发布预览稿；配图已随同当前候选提交，未经人工审阅不得公开。')
    s+='\\n* 来源全文（固定 Git 版本）\\n以下保留原始材料的全部文字、模板、代码和已记录的评价；示例块内容不执行。\\n#+begin_example\\n'+raw+'\\n#+end_example\\n'
    note.write_text(s,encoding='utf-8')
    assert raw in note.read_text(encoding='utf-8')
    result.append({'case':case,'path':rel,'uid':uid,'sourceBlob':sha,'sourceBytes':len(b),'image':str(asset.relative_to(ROOT)),'imageBytes':asset.stat().st_size})
print('FIVE_COMPLETE_CANDIDATES '+json.dumps(result,ensure_ascii=False))
