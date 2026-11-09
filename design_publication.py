"""Publication design preview; all numerical marks come from verified measurements."""
from pathlib import Path
import sys,json,hashlib
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parent.parent/'tmp/ef10-plot-packages'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,Rectangle,FancyArrowPatch,Circle
from matplotlib.font_manager import FontProperties
from PIL import Image

data=json.loads((root/'results/summary.json').read_text())
rows={(r['phase'],r['band'],r['size'],r['mode']):r for r in data['summary']}
fix=data['scoped_fix']
out=root/'figures';out.mkdir(exist_ok=True)
NAVY='#101e36';INK='#14273f';MUTED='#52647b';BLUE='#3d67d9';TEAL='#087b70';GRAY='#7a8799';PAPER='#f2f4f7';LINE='#d9e0e8'
FONT='C:/Windows/Fonts/segoeui.ttf';BOLD='C:/Windows/Fonts/seguisb.ttf';MONO='C:/Windows/Fonts/consola.ttf'
MODE=[('MultipleParameters','EF10 default','Scalar parameters',BLUE),('Parameter','JSON / OPENJSON','One JSON parameter',TEAL),('Constant','Inline constants','Values embedded in SQL',GRAY)]
qa=[]

class Canvas:
 def __init__(self,w,h,bg):
  self.w=w;self.h=h;self.fig=plt.figure(figsize=(w/100,h/100),dpi=100,facecolor=bg)
  self.ax=self.fig.add_axes([0,0,1,1]);self.ax.set(xlim=(0,w),ylim=(h,0));self.ax.axis('off');self.texts=[]
 def box(self,x,y,w,h,fill,edge=None,r=22,lw=1):
  p=FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0,rounding_size={r}',facecolor=fill,edgecolor=edge or fill,linewidth=lw)
  self.ax.add_patch(p);return p
 def text(self,x,y,s,size=28,color=INK,bold=False,mono=False,ha='left',region=None):
  f=FontProperties(fname=MONO if mono else BOLD if bold else FONT,size=size*72/100)
  t=self.ax.text(x,y,s,fontproperties=f,color=color,va='top',ha=ha,linespacing=1.2)
  self.texts.append((t,region));return t
 def line(self,x1,y1,x2,y2,color=LINE,lw=1,alpha=1):self.ax.plot([x1,x2],[y1,y2],color=color,lw=lw,alpha=alpha)
 def arrow(self,x1,y1,x2,y2,color=BLUE,lw=2):self.ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=18,linewidth=lw,color=color))
 def save(self,name):
  self.fig.canvas.draw();renderer=self.fig.canvas.get_renderer();bad=[]
  for t,region in self.texts:
   b=t.get_window_extent(renderer);left,top,right,bottom=b.x0,self.h-b.y1,b.x1,self.h-b.y0
   l,u,r,d=region or (0,0,self.w,self.h)
   if left<l-.5 or right>r+.5 or top<u-.5 or bottom>d+.5:bad.append({'text':t.get_text(),'bounds':[left,top,right,bottom],'allowed':[l,u,r,d]})
  assert not bad,json.dumps(bad,ensure_ascii=False)
  self.fig.savefig(out/(name+'.png'),dpi=100,facecolor=self.fig.get_facecolor())
  self.fig.savefig(out/(name+'.svg'),facecolor=self.fig.get_facecolor())
  p=out/(name+'.svg');p.write_text('\n'.join(x.rstrip() for x in p.read_text(encoding='utf8').splitlines())+'\n',encoding='utf8',newline='\n')
  qa.append({'file':name+'.png','size':[self.w,self.h],'text_boxes_checked':len(self.texts),'clipped_text':0})
  plt.close(self.fig)

def comparison_card(c,x,y,w,h,phase):
 warm=phase=='steady'
 c.box(x,y,w,h,'#ffffff',LINE,r=26)
 c.box(x+28,y+28,76,36,'#eaf0fc' if warm else '#e4f3ef',r=10)
 c.text(x+66,y+33,'01' if warm else '02',22,BLUE if warm else TEAL,True,ha='center')
 c.text(x+122,y+27,'Same merchant list' if warm else 'Fresh merchant lists',34,INK,True,region=(x,y,x+w,y+h))
 c.text(x+28,y+87,'60 warmed observations / mode' if warm else '15 lists / mode · compile-inclusive time',24,MUTED)
 c.line(x+28,y+132,x+w-28,y+132)
 bar_x=x+30;bar_w=w-210;max_ms=20
 step=(h-235)/3
 for i,(mode,label,desc,color) in enumerate(MODE):
  ry=y+156+i*step;value=rows[(phase,'cold',500,mode)]['median_ms']
  c.text(bar_x,ry,label,32,INK,True)
  c.text(x+w-30,ry,f'{value:.2f} ms',42,color,True,ha='right')
  by=ry+45
  c.box(bar_x,by,bar_w,18,'#edf0f5',r=9)
  c.box(bar_x,by,bar_w*value/max_ms,18,color,r=min(9,bar_w*value/max_ms/2))
 axis_y=y+h-56
 for tick in (0,5,10,15,20):
  px=bar_x+bar_w*tick/max_ms
  c.line(px,axis_y-9,px,axis_y-3,LINE)
  c.text(px,axis_y,str(tick),20,MUTED,ha='center')
 c.text(x+w-29,axis_y,'ms',21,MUTED,ha='right')

# Light editorial results page; the portrait is the primary in-article figure.
c=Canvas(1080,1500,PAPER)
c.text(54,43,'MEASURED RESULTS  /  EF CORE 10',23,BLUE,True)
c.text(54,91,'The cost of changing\nmerchant selections',48,INK,True)
c.text(54,220,'500 low-volume merchants · 1 million synthetic rows',26,MUTED)
comparison_card(c,48,282,984,480,'steady')
comparison_card(c,48,786,984,480,'churn')
c.box(48,1290,984,105,NAVY,r=24)
c.text(78,1312,'QUERY-SCOPED FIX',20,'#87aafa',True)
c.text(78,1343,'EF.Parameter(ids)',30,'#ffffff',True,mono=True)
c.text(1000,1348,'Global default unchanged',25,'#c5d4ee',ha='right')
c.text(54,1420,'Median client time · matching counts and exact amount totals',23,MUTED)
c.text(54,1455,'SQL Server 2019 LocalDB · MAXDOP 1 · one client',22,MUTED)
c.save('article-results-v2')

c=Canvas(1800,1000,PAPER)
c.text(62,43,'EF CORE 10  /  SYNTHETIC SQL SERVER EXPERIMENT',24,BLUE,True)
c.text(62,91,'Changing selections exposed a cost the fixed-list test missed.',47,INK,True)
c.text(62,159,'500 low-volume merchants · same report, same data and index · median client milliseconds',26,MUTED)
comparison_card(c,56,226,832,583,'steady')
comparison_card(c,912,226,832,583,'churn')
c.box(56,838,1688,95,NAVY,r=22)
c.text(86,858,'LOCAL CHANGE',20,'#87aafa',True)
c.text(86,888,'EF.Parameter(ids)',28,'#ffffff',True,mono=True)
c.text(1710,880,'The context retains MultipleParameters',28,'#d5e1f5',ha='right')
c.text(62,958,'SQL Server 2019 LocalDB · EF/.NET 10.0.14 · MAXDOP 1 · one client · synthetic data; not production capacity',22,MUTED)
c.save('comparison-wide-v2')

# Cover is conceptual only. All quantitative comparisons stay in the body figure.
c=Canvas(1920,1080,NAVY)
for gx in range(1080,1920,70):c.line(gx,70,gx,1010,'#213958',.7,alpha=.35)
for gy in range(70,1080,70):c.line(1050,gy,1890,gy,'#213958',.7,alpha=.35)
c.box(68,67,458,48,'#1c3151',r=12)
c.text(91,76,'EF CORE 10  ·  SQL SERVER',26,'#b3ceff',True)
c.text(72,174,'EF Core 10:\na query-level fix',80,'#ffffff',True,region=(68,160,1070,390))
c.text(77,418,'One report query uses JSON.\nThe context-wide policy stays in place.',37,'#c0cde1')
c.box(74,564,940,267,'#172b47','#294665',r=30)
c.text(108,591,'CONTEXT DEFAULT',40,'#a7c1ed',True)
c.text(108,658,'MultipleParameters',66,'#e3eaf5',True,mono=True)
c.text(108,770,'Retained for the context',34,'#c0cde1')
c.box(1120,166,684,165,'#192e4a','#31506e',r=25)
c.text(1154,191,'INPUT',31,'#9fb8d8',True)
c.text(1154,242,'500 merchant IDs',54,'#f5f8ff',True)
c.arrow(1462,338,1462,404,'#85a2c7',3)
c.box(1120,411,684,199,'#123b40','#397f7b',r=25,lw=1.5)
c.text(1154,438,'REPORT QUERY',31,'#91d7c9',True)
c.text(1154,493,'EF.Parameter(ids)',54,'#ffffff',True,mono=True)
c.text(1154,558,'Explicit, local override',31,'#b6d8d3')
c.arrow(1462,619,1462,686,'#6cc8ba',3)
c.box(1120,694,684,154,'#192e4a','#31506e',r=25)
c.text(1154,713,'ONE JSON PARAMETER',31,'#9fb8d8',True)
c.text(1154,771,'OPENJSON(@ids)',52,'#eaf2ff',True,mono=True)
c.line(74,918,1807,918,'#34506c',1)
c.text(78,948,'Conceptual query boundary · measured results in the article',34,'#bac9dd')
c.text(78,1001,'Local synthetic benchmark · EF/.NET 10.0.14 · SQL Server 2019 LocalDB',25,'#829ab8')
c.save('article-cover-v2')

# Minimal explanatory diagram: no timings mixed between the primary and follow-up phases.
c=Canvas(1600,760,PAPER)
c.text(60,44,'A small, inspectable boundary',45,INK,True)
c.text(60,112,'The global setting stays MultipleParameters. This report explicitly chooses JSON.',28,MUTED)
for x,title,body,fill in [(60,'Merchant IDs','ids: int[500]','#ffffff'),(565,'Report predicate','EF.Parameter(ids)','#e6f3ee'),(1070,'SQL parameter','OPENJSON(@ids)','#ffffff')]:
 c.box(x,230,470,235,fill,LINE,r=26)
 c.text(x+28,261,title,29,MUTED,True)
 c.text(x+28,334,body,36,TEAL if x==565 else INK,True,mono=True,region=(x,230,x+470,465))
c.arrow(536,348,557,348,BLUE,2);c.arrow(1041,348,1062,348,TEAL,2)
c.box(60,518,1480,150,NAVY,r=25)
c.text(91,545,'RESULT CHECK',23,'#9bb9e9',True)
c.text(91,586,'Same transaction counts and exact amount totals',38,'#ffffff',True)
c.text(63,702,'Conceptual diagram of the exercised query override · synthetic local experiment',24,MUTED)
c.save('query-fix-diagram-v2')

for name in ('article-results-v2','article-cover-v2'):
 im=Image.open(out/(name+'.png'));width=390;thumb=im.resize((width,round(im.height*width/im.width)),Image.Resampling.LANCZOS)
 thumb.save(out/(name+'-390-preview.png'))
metadata={'status':'DESIGN_PREVIEW_AWAITING_OWNER_APPROVAL','source_summary_sha256':hashlib.sha256((root/'results/summary.json').read_bytes()).hexdigest(),
 'charts':qa,'scales':'Both comparison cards start at zero and use the same 0..20ms range.',
 'phases':'Results figure is the primary steady/churn experiment. Cover is a conceptual query-boundary illustration and contains no latency/sample-count comparison.',
 'phone_preview':'390-pixel software-scaled readability preview, not native LinkedIn/mobile verification.',
 'benchmark_rerun':False,'publication':0}
(root/'design-qa.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'graphics':len(qa),'clipped_text':0,'source_data':'unchanged','publication':'none'}))
