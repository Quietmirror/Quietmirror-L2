"""Actual numerical curves from validation JSON; no synthetic acceptance data."""
import json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];RP=ROOT/'reports/l2_r4';OUT=ROOT/'views/l2_r4'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for file,title,stem in [('side_motion_raw.json','Side lever full BODY contact-inclusive samples','SIDE_EXACT_MOTION_CURVES'),('main_and_wheel_motion_raw.json','Main keys and wheel group exact sampled motion','MAIN_WHEEL_EXACT_MOTION_CURVES')]:
        p=RP/file
        if not p.exists():continue
        groups=json.loads(p.read_text());fig,axes=plt.subplots(len(groups),2,figsize=(12,3.2*len(groups)),squeeze=False,layout='constrained')
        for index,g in enumerate(groups):
            a=[s['angle_deg'] for s in g['samples']];gaps=[];ovs=[]
            for sample in g['samples']:
                pairs=sample.get('pairs',[sample]);gaps.append(min(s['gap_mm'] for s in pairs));ovs.append(max(s['overlap_mm3'] for s in pairs))
            for col,ys,label in [(0,gaps,'Exact minimum gap / mm'),(1,ovs,'Maximum pair intersection / mm^3')]:
                ax=axes[index,col];ax.plot(a,ys,'.-',linewidth=1);ax.set(xlabel='Rigid rotation / degrees',ylabel=label,title=g.get('part',g.get('group')));ax.grid(alpha=.25)
                if col==1:ax.axhline(.001,color='red',linestyle='--',label='0.001 mm^3');ax.legend(fontsize=8)
        fig.suptitle(title+'\nContacts, hard stops and compressed plungers require the explicit local classification report.',fontsize=11)
        fig.savefig(OUT/(stem+'.png'),dpi=160);plt.close(fig)
    p=RP/'side_functional_motion.json'
    if p.exists():
        fig,axs=plt.subplots(1,2,figsize=(12,4),layout='constrained')
        for ax,g in zip(axs,json.loads(p.read_text())):
            ss=sorted(g['samples'],key=lambda q:q['angle_deg'])
            for index,label in enumerate(['Remaining key / complete BODY','Ear / BODY without outward stop','Rib / BODY without inward stop']):
                ax.plot([s['angle_deg'] for s in ss],[s['nonfunctional'][index]['gap_mm'] for s in ss],'.-',label=label)
            ax.axhline(.3,color='red',linestyle='--');ax.set(title=g['part'],xlabel='Rotation / degrees',ylabel='Exact nonfunctional clearance / mm');ax.grid(alpha=.25);ax.legend(fontsize=7)
        fig.savefig(OUT/'SIDE_LOCAL_CONTACT_DECOMPOSITION.png',dpi=160);plt.close(fig)
    names=['SIDE_EXACT_MOTION_CURVES','MAIN_WHEEL_EXACT_MOTION_CURVES','SIDE_LOCAL_CONTACT_DECOMPOSITION']
    (RP/'motion_plot_manifest.json').write_text(json.dumps(dict(files={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/(n+'.png') for n in names] if p.exists()}),indent=2))

if __name__=='__main__':main()
