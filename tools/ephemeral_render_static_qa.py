#!/usr/bin/env python3
"""Quality repair: parallel concept cards, five cards when claiming five dimensions."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess,random
out=Path('.')
regular=subprocess.check_output(['fc-match','-f','%{file}','Noto Sans CJK SC'],text=True).strip()
bold=subprocess.check_output(['fc-match','-f','%{file}','Noto Sans CJK SC:style=Bold'],text=True).strip()
font=lambda n,b=False:ImageFont.truetype(bold if b else regular,n)
case=[
('825cb8d4-d667-4b1f-b24a-39af2d781001','提示词四要素','任务 · 上下文 · 输入 · 验收',['指令明确','背景充分','输入可核','验收可测'],['说明要做什么','告诉模型工作条件','给出数据与限制','描述可验证结果']),
('825cb8d4-d667-4b1f-b24a-39af2d781002','提示词试验与复核','从提示到真实试运行',['清晰性','上下文','精确性','视角与角色'],['先改写含糊指令','补齐关键信息','比较示例与格式','保留同条件测试']),
('825cb8d4-d667-4b1f-b24a-39af2d781003','提示词工具选择','按需求选择，不凭旧清单认定可用',['生成建议','结构调整','版本迭代','人工核验'],['识别目标任务','检查能力边界','保留改动版本','验证当前工具状态']),
('825cb8d4-d667-4b1f-b24a-39af2d781004','相关方冲突预判','先识别利益，再确认决策权',['利益映射','冲突预警','决策分层','冲突登记'],['记录真实诉求','标明资源与风险','明确谁作决定','复盘争议与行动']),
('825cb8d4-d667-4b1f-b24a-39af2d781005','提示词质量检查','提示词原文保真与五维审查',['相关性','深度','创新性','实用性','完整性'],['符合真实目标','覆盖关键条件','标注新颖点依据','让步骤可以复用','不丢事实和约束']),
]
for uid,title,subtitle,heads,items in case:
 W,H=1200,620
 im=Image.new('RGB',(W,H),(249,245,231));d=ImageDraw.Draw(im)
 for y in range(20,H,31):d.line((0,y,W,y),fill=(221,227,222),width=1)
 for x in (38,59):d.line((x,0,x,H),fill=(220,137,120) if x==59 else (219,218,204),width=2)
 for y in range(34,H,54):d.ellipse((16,y-8,30,y+6),outline=(44,64,73),width=3)
 d.text((87,30),title,font=font(52,True),fill=(16,49,68))
 d.line((88,102,515,102),fill=(25,161,147),width=7)
 d.text((89,123),subtitle,font=font(23),fill=(39,90,93))
 colors=((226,246,242),(253,241,212),(238,240,252),(255,235,229),(235,243,233))
 total=len(heads);step=276 if total==4 else 220
 for i,(head,desc) in enumerate(zip(heads,items)):
  x=86+i*step;y=205;w=253 if total==4 else 198;h=245
  d.rounded_rectangle((x+3,y+5,x+w+3,y+h+5),radius=22,fill=(220,220,213))
  d.rounded_rectangle((x,y,x+w,y+h),radius=20,fill=colors[i],outline=(36,86,97),width=3)
  d.ellipse((x+16,y+20,x+60,y+64),fill=(24,159,145))
  d.text((x+30,y+22),str(i+1),font=font(25,True),fill='white')
  d.text((x+17,y+82),head,font=font(30 if total==4 else 25,True),fill=(21,58,74))
  for j in range(0,len(desc),8):d.text((x+18,y+139+(j//8)*35),desc[j:j+8],font=font(22),fill=(40,65,72))
  if i<total-1:
   cx=x+w+9;cy=y+120
   d.ellipse((cx,cy-5,cx+9,cy+5),fill=(241,132,92))
 d.rounded_rectangle((86,505,1120,573),radius=15,fill=(249,221,194),outline=(216,140,110),width=2)
 d.text((107,523),'原始材料：lovemoganna/Prompts · 本图概括并列要点 · 完整证据和示例以正文为准',font=font(19),fill=(63,54,54))
 path=out/'note-assets'/uid/'sketchnote-header.png'
 path.parent.mkdir(parents=True,exist_ok=True)
 im.save(path,optimize=True)
 print('RENDERED',str(path),len(heads),'parallel cards')
