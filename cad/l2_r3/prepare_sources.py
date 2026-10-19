"""Make a versioned source-level derivative of the archived R3.2 dependencies.

Original files stay untouched. Each replacement asserts the expected source
text, making the modified structural features explicit and auditable.
"""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
src=(ROOT/'cad/rebuild_r2/mechanics.py').read_text(encoding='utf8')
start=src.index('    # Both side buttons are captured sliding keys')
end=src.index('    from wheel_mechanism import build_wheel',start)
src=src[:start]+'    # L2-r3: obsolete slider seats, openings, pins and M2 paths omitted.\n\n'+src[end:]
old='''            ear=ear.cut(slot)
            arm=beam((xx,yy,9.5),(sign*(half_width(yy,p)-2.0),yy,9.5),1.3)
            additions.append(check(join(ear,arm),'PCB_LOCAL_M2_EAR'))'''
new='''            if sign < 0:  # construction -X becomes assembly thumb-side +X
                arm=beam((xx,yy,9.25),(sign*(half_width(yy,p)-2.0),yy,9.25),1.3)
                hx,hy=(-25.73,43.3) if yy==43. else (-27.0,66.3)
                ear=join(ear,arm).cut(cylinder(1.1,6,(hx,hy,7)))
            else:
                ear=ear.cut(slot)
                arm=beam((xx,yy,9.5),(sign*(half_width(yy,p)-2.0),yy,9.5),1.3)
                ear=join(ear,arm)
            additions.append(check(ear,'PCB_LOCAL_M2_EAR'))'''
assert src.count(old)==1;src=src.replace(old,new)
old="        tie=beam((-reach,yy,zz),(reach,yy,zz),rr)"
new=old+"\n        if yy==54.:tie=tie.intersect(box(12,8,8,(0,51,23)))"
assert src.count(old)==1;src=src.replace(old,new)
old="        additions.append(check(beam(a,hub,1.3),'RAISED_DIAGONAL_TIE'))"
new='''        if y>20:
            dx,dy=hub[0]-a[0],hub[1]-a[1];length=math.hypot(dx,dy)
            nx,ny=-dy/length*.8,dx/length*.8
            points=[(a[0]+nx,a[1]+ny),(hub[0]+nx,hub[1]+ny),
                    (hub[0]-nx,hub[1]-ny),(a[0]-nx,a[1]-ny)]
            tie=cq.Workplane('XY').polyline(points).close().extrude(2.8).val().translate((0,0,5.1))
        else:tie=beam(a,hub,1.3)
        additions.append(check(tie,'RAISED_DIAGONAL_TIE'))'''
assert src.count(old)==1;src=src.replace(old,new)
(HERE/'mechanics.py').write_text(src,encoding='utf8')
for name in ('surfaces.py','interfaces.py','wheel_mechanism.py','fasteners.py','interface_check.py'):
    shutil.copy2(ROOT/'cad/rebuild_r2'/name,HERE/name)
print('Versioned structural derivative generated; original mechanics unchanged')
