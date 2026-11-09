"""Analyze raw observations; produce figures without invented or selected results."""
from pathlib import Path
from collections import defaultdict, Counter
import csv, json, math, statistics, re, hashlib, xml.etree.ElementTree as ET
import sys

root=Path(__file__).resolve().parent
workspace=root.parent.parent
sys.path.insert(0,str(workspace/'tmp/ef10-plot-packages'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

result=root/'results'; figures=root/'figures';figures.mkdir(exist_ok=True)
raw=list(csv.DictReader((result/'samples.csv').open(encoding='utf8')))
assert len(raw)==1350
assert sum(r['phase']=='steady' for r in raw)==1080
groups=defaultdict(list)
for r in raw:
    groups[(r['phase'],r['band'],int(r['size']),r['mode'])].append(r)

def percentile(values,p):
    return sorted(values)[math.ceil(p*len(values))-1]
def key_from_sql(sql):
    m=re.search(r'_(steady|churn)_(hot|cold)_(5|50|500)_(MultipleParameters|Parameter|Constant)\b',sql)
    assert m,sql[:180]
    return m[1],m[2],int(m[3]),m[4]

dmv=defaultdict(lambda:defaultdict(float))
for round in range(1,4):
    before={key_from_sql(r['text']):r for r in json.loads((result/f'dmv-warmup-round-{round}.json').read_text())}
    after={key_from_sql(r['text']):r for r in json.loads((result/f'dmv-steady-round-{round}.json').read_text())}
    assert len(before)==len(after)==18
    for k,a in after.items():
        b=before[k];assert a['execution_count']-b['execution_count']==20
        for name in ('execution_count','total_worker_time','total_logical_reads','total_elapsed_time'):
            delta=a[name]-b[name]; assert delta>=0
            dmv[k][name]+=delta

summary=[]
for k,rows in sorted(groups.items()):
    phase,band,size,mode=k
    times=[float(r['client_ms']) for r in rows]
    assert len(times)==(60 if phase=='steady' else 15)
    s={'phase':phase,'band':band,'size':size,'mode':mode,'n':len(times),'median_ms':statistics.median(times),
       'p95_ms':percentile(times,.95),'min_ms':min(times),'max_ms':max(times),
       'unique_sql_shapes':len({r['sql_shape_sha256'] for r in rows}),
       'parameter_counts':sorted({int(r['command_parameters']) for r in rows}),
       'round_medians_ms':{str(i):statistics.median(float(r['client_ms']) for r in rows if int(r['round'])==i) for i in sorted({int(r['round']) for r in rows})}}
    if phase=='steady':
        assert len({r['result_sha256'] for r in rows})==1
        assert dmv[k]['execution_count']==60
        s.update(sql_cpu_mean_ms=dmv[k]['total_worker_time']/60000,sql_elapsed_mean_ms=dmv[k]['total_elapsed_time']/60000,logical_reads_mean=dmv[k]['total_logical_reads']/60)
    summary.append(s)

# Equal input variants across modes must return identical fingerprints and exact totals.
checks=defaultdict(list)
for r in raw:
    checks[(r['phase'],r['round'],r['sample'],r['band'],r['size'])].append(r)
for rows in checks.values():
    assert len(rows)==3
    for field in ['result_sha256','result_groups','matching_transactions','total_amount_minor']:
        assert len({r[field] for r in rows})==1,(field,rows)

ns={'s':'http://schemas.microsoft.com/sqlserver/2004/07/showplan'}
plans=[]
for p in sorted((result/'plans').glob('*.sqlplan')):
    tree=ET.parse(p);ops=tree.findall('.//s:RelOp',ns)
    plans.append({'case':p.stem,'relop_count':len(ops),'physical_ops':dict(Counter(o.get('PhysicalOp') for o in ops)),
                  'boundary':'Actual diagnostic execution after timed observations; no diagnostic timing used in charts.'})
(result/'plan-summary.json').write_text(json.dumps(plans,indent=2)+'\n',encoding='utf8')
fix=json.loads((result/'scoped-fix.json').read_text())
fixsummary={}
for label in ('default-scalar','scoped-EF.Parameter'):
    times=[r['ClientMs'] for r in fix['Raw'] if r['Variant']==label]
    assert len(times)==30
    fixsummary[label]={'n':len(times),'median_ms':statistics.median(times),'p95_ms':percentile(times,.95)}
assert fix['ParameterCounts']==[500,1] and fix['AllResultsMatch']
payload={'schema':1,'primary_run':json.loads((result/'environment.json').read_text())['RunId'],
         'percentile_method':'nearest rank; p95 = sorted[ceil(.95*n)-1]',
         'sql_metric_method':'Sum per-round DMV deltas AFTER subtracting warmups; /60 executions; CPU reported in ms with SQL DMV precision limits',
         'matched_cross_mode_triplets':len(checks),'summary':summary,'scoped_fix':fixsummary,'all_checks_passed':True}
(result/'summary.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf8')
with (result/'summary.csv').open('w',newline='',encoding='utf8') as f:
    fields=['phase','band','size','mode','n','median_ms','p95_ms','unique_sql_shapes','sql_cpu_mean_ms','logical_reads_mean']
    w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(summary)

colors={'MultipleParameters':'#4778ea','Parameter':'#008b7d','Constant':'#c78720'}
labels={'MultipleParameters':'Scalar params (EF10 default)','Parameter':'JSON / OPENJSON','Constant':'Inline constants'}
modes=list(colors)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.titleweight':'bold','figure.facecolor':'#f5f7fb','axes.facecolor':'#f5f7fb','text.color':'#16283d','axes.labelcolor':'#16283d','xtick.color':'#41536b','ytick.color':'#16283d','savefig.facecolor':'#f5f7fb'})
lookup={(s['phase'],s['band'],s['size'],s['mode']):s for s in summary}
fig,axes=plt.subplots(2,3,figsize=(15.5,9.5),sharex='row')
for row,band in enumerate(('hot','cold')):
    for col,size in enumerate((5,50,500)):
        ax=axes[row,col]
        rows=[lookup[('steady',band,size,m)] for m in modes]
        maxrow=max(lookup[('steady',band,z,m)]['p95_ms'] for z in (5,50,500) for m in modes)
        ax.barh(range(3),[r['median_ms'] for r in rows],height=.52,color=[colors[m] for m in modes])
        ax.scatter([r['p95_ms'] for r in rows],range(3),color='#172538',marker='D',s=24,zorder=5)
        for y,r in enumerate(rows):
            ax.text(max(r['median_ms'],r['p95_ms'])+maxrow*.025,y,f"{r['median_ms']:.2f}",va='center',fontsize=12,fontweight='bold')
        ax.set_xlim(0,maxrow*1.2);ax.invert_yaxis();ax.set_yticks(range(3),[labels[m] for m in modes] if col==0 else [])
        ax.tick_params(axis='y',length=0);ax.grid(axis='x',alpha=.17);ax.set_axisbelow(True)
        ax.set_title(f"{size} {'high-volume' if band=='hot' else 'low-volume'} merchants",loc='left',fontsize=13,pad=15)
        ax.set_xlabel('Client elapsed, milliseconds')
fig.suptitle('The EF10 default did not win this report',x=.04,y=.98,ha='left',fontsize=23,fontweight='bold')
fig.text(.04,.925,'Real SQL Server measurements · 1,000,000 synthetic transactions · 60 warmed samples per bar',fontsize=13)
fig.legend(handles=[Line2D([0],[0],color='#172538',marker='D',linestyle='',label='p95 (nearest rank)')],loc='upper right',bbox_to_anchor=(.98,.947),frameon=False)
fig.text(.04,.035,'Bars and labels = median. Axis range differs between rows. Release / EF Core 10.0.14 / SQL Server 2019 LocalDB / MAXDOP 1 / one client.',fontsize=10)
fig.subplots_adjust(left=.205,right=.96,top=.86,bottom=.12,wspace=.13,hspace=.44)
fig.savefig(figures/'latency-comparison.png',dpi=150);fig.savefig(figures/'latency-comparison.svg');plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(13.8,6.2))
churn_limit=max(lookup[(p,'cold',500,m)]['median_ms'] for p in ('steady','churn') for m in modes)*1.4
for ax,phase,title in zip(axes,('steady','churn'),('Repeated identical selection','15 fresh selections')):
    rows=[lookup[(phase,'cold',500,m)] for m in modes]
    ax.barh(range(3),[r['median_ms'] for r in rows],color=[colors[m] for m in modes],height=.54)
    for i,r in enumerate(rows):ax.text(r['median_ms']+.22,i,f"{r['median_ms']:.2f} ms",va='center',fontweight='bold',fontsize=13)
    ax.set_xlim(0,churn_limit);ax.invert_yaxis()
    ax.set_yticks(range(3),[labels[m] for m in modes] if phase=='steady' else [])
    ax.tick_params(axis='y',length=0);ax.set_title(title,loc='left',fontsize=15,pad=15)
    ax.set_xlabel('Median client elapsed, milliseconds');ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
fig.suptitle('Constants were slower with fresh merchant selections',x=.035,y=.97,ha='left',fontsize=22,fontweight='bold')
fig.text(.035,.86,'500 low-volume merchants · same dataset and query · warmed execution and compile-inclusive churn are separate phases',fontsize=11)
fig.text(.035,.055,'Steady: 60 samples per mode. Churn: 15 per mode. One JSON SQL shape vs 15 constant SQL shapes in this churn case. LocalDB; not production.',fontsize=10)
fig.subplots_adjust(left=.25,right=.96,top=.76,bottom=.18,wspace=.2)
fig.savefig(figures/'selection-churn.png',dpi=150);fig.savefig(figures/'selection-churn.svg');plt.close(fig)

# Portrait article figure with identical scales and explicit per-phase sample sizes.
fig,axes=plt.subplots(2,1,figsize=(9,10.5),sharex=True)
for ax,phase,title in zip(axes,('steady','churn'),('Same list · 60 warmed samples','Fresh lists · 15 samples\nCompile-inclusive client time')):
    rows=[lookup[(phase,'cold',500,m)] for m in modes]
    ax.barh(range(3),[r['median_ms'] for r in rows],color=[colors[m] for m in modes],height=.54)
    for i,r in enumerate(rows):ax.text(r['median_ms']+.3,i,f"{r['median_ms']:.2f} ms",va='center',fontweight='bold',fontsize=18)
    ax.set_xlim(0,churn_limit);ax.invert_yaxis()
    ax.set_yticks(range(3),['EF10 default','JSON / OPENJSON','Constants'],fontsize=15)
    ax.tick_params(axis='y',length=0);ax.tick_params(axis='x',labelsize=13,labelbottom=True)
    ax.set_title(title,loc='left',fontsize=17,pad=15)
    ax.set_xlabel('Median client elapsed (ms)',fontsize=14)
    ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
fig.suptitle('Constants were slower\nwith fresh merchant selections',x=.055,y=.975,ha='left',fontsize=24,fontweight='bold')
fig.text(.055,.873,'500 low-volume merchants · 1 million synthetic transactions',fontsize=13)
fig.text(.055,.041,'EF Core 10.0.14 · SQL Server 2019 LocalDB · MAXDOP 1\nSame scale in both panels. One client; local experiment, not production.',fontsize=11)
fig.subplots_adjust(left=.28,right=.94,top=.80,bottom=.13,hspace=.52)
fig.savefig(figures/'article-comparison.png',dpi=150);fig.savefig(figures/'article-comparison.svg');plt.close(fig)

# Matplotlib emits insignificant trailing spaces in SVG path lines.
for p in figures.glob('*.svg'):
    p.write_text('\n'.join(line.rstrip() for line in p.read_text(encoding='utf8').splitlines())+'\n',encoding='utf8',newline='\n')

print(json.dumps({'samples':len(raw),'cross_mode_triplets':len(checks),'actual_plans':len(plans),'scoped_fix':fixsummary,'cold_500':{m:lookup[('steady','cold',500,m)]['median_ms'] for m in modes}},indent=2))
