"""Retain functional interfaces, lighten key undersides and wheel web."""
import math,json
from common import *
def main():
    outer=load('MOTHER_OUTER_FROM_R32_SURFACE',ROOT/'exports/l2_r2_diagnostic/support_reference')
    metadata=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())
    rows=[];details=[]
    for name in ('LEFT_KEY','RIGHT_KEY'):
        original=baseline(name)
        mo=next(m for m in metadata['mechanisms']['motions'] if m['part']==name)
        x=mo['actuation_point'][0]
        zone=box(-40,40,12,36,0,40).cut(cyl(4,50,(x,24,-5)))
        sx=23 if x>0 else -23
        zone=zone.cut(box(sx-3.5,sx+3.5,9.5,14,0,40))
        shave=outer.translate((0,0,-1.6)).cut(outer.translate((0,0,-2.001))).intersect(zone)
        result=original.cut(shave).clean()
        rib_layer=outer.translate((0,0,-1.4)).cut(outer.translate((0,0,-3.2)))
        # Follow the same outer surface. Clip to the original XY footprint;
        # keep actuator, pivot and nose thickness unchanged.
        cap_area=box(min(x-11,x+11),max(x-11,x+11),12.1,35.9,0,40)
        outline=original.projectToShape if False else None
        for xx in [x-5,x+5]:
            r=rib_layer.intersect(box(xx-.45,xx+.45,14.5,35.5,0,40)).intersect(cap_area)
            if r.Solids():result=result.fuse(r).clean()
        for sign in (-1,1):
            a=(x-5,16) if sign==1 else (x+5,16)
            b=(x+5,32) if sign==1 else (x-5,32)
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);nx,ny=-dy/length*.45,dx/length*.45
            pts=[(a[0]+nx,a[1]+ny),(b[0]+nx,b[1]+ny),(b[0]-nx,b[1]-ny),(a[0]-nx,a[1]-ny)]
            mask=cq.Workplane('XY').polyline(pts).close().extrude(40).val()
            r=rib_layer.intersect(mask)
            if r.Solids():result=result.fuse(r).clean()
        # Exact inherited rigid switch housing, conservatively boxed in its
        # own tilted frame, expanded 0.3 mm. Cut its inverse motion envelope
        # from added ribs so no rib can bottom on the housing before the stop.
        point=mo['actuation_point'];tilt=mo.get('switch_tilt_deg',0);axis1=[point[0]+1,*point[1:]]
        sw=baseline(mo['switch']).rotate(point,axis1,-tilt)
        rigid=sw.intersect(box(-50,50,0,90,0,point[2]-1.03));bb=rigid.BoundingBox()
        expanded=box(bb.xmin-.3,bb.xmax+.3,bb.ymin-.3,bb.ymax+.3,bb.zmin-.3,bb.zmax+.3).rotate(point,axis1,tilt)
        origin=mo['origin'];motion_axis=[origin[0]+1,*origin[1:]]
        tools_=[expanded.rotate(origin,motion_axis,-mo['end_deg']*i/20) for i in range(21)]
        result=result.cut(unite(*tools_)).clean()
        rows.append(export(result,name));details.append(dict(part=name,old_mm3=vol(original),new_mm3=vol(result),rigid_switch_relief='0.3 mm expanded rigid-housing box at 21 inverse poses, trigger boss preserved',root_fillet_R0p4='UNVERIFIED: final rib fillet not added if it compromises inherited cap topology'))
    import sys
    if '--keys-only' in sys.argv:
        save('key_wheel_changes.json',details);return
    original=baseline('WHEEL');b=original.BoundingBox();axis=(0,28,19)
    # R3.2 is mirrored in X; retain both actual shaft/hex end shapes.
    middle=box(-3.25,3.25,20,36,11,27)
    rim=cyl(6.25,6.5,(-3.25,28,19),(1,0,0)).cut(cyl(4.85,6.7,(-3.35,28,19),(1,0,0)))
    hub=cyl(2.5,6.5,(-3.25,28,19),(1,0,0));spokes=[]
    for i in range(5):spokes.append(box(-3.25,3.25,27.4,28.6,19,24.2).rotate(axis,(1,28,19),i*72))
    new=unite(rim,hub,*spokes,*original.cut(middle).Solids())
    rows.append(export(new,'WHEEL'));rows.append(export(baseline('WHEEL_CARRIER'),'WHEEL_CARRIER'))
    # Original hardware reused only where mechanisms are unchanged.
    old=json.loads((ROOT/'reports/rebuild_r3_2/cad_metrics.json').read_text())
    for n,row in old.items():
        if row['printable'] or 'SIDE_' in n or n.startswith('SWITCH_SIDE'):continue
        rows.append(export(baseline(n),n,False))
    save('remaining_solids.json',rows);save('key_wheel_changes.json',details)
if __name__=='__main__':main()
