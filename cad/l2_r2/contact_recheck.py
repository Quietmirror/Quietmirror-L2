"""Resolve the r2 ear-height claim over the complete mounting footprint.

This is an independent reconstruction of the generic ear features in the
archived mechanics.py, using dimensions rather than its builder functions.
No production BODY is modified.
"""
from pathlib import Path
import json
import numpy as np
import cadquery as cq
import geometry_recheck as g

ROOT=g.ROOT;OUT=g.OUT;V=cq.Vector

def ear(x,y):
    block=g.box(x-3.8,x+3.8,y-3.8,y+3.8,8.25,10.75)
    arm=g.capsule((x,y,9.5),(x+2,y,9.5),1.3)
    slot=cq.Solid.makeCylinder(1.2,5,V(x,y-.8,7)).fuse(
        cq.Solid.makeCylinder(1.2,5,V(x,y+.8,7)),g.box(x-1.2,x+1.2,y-.8,y+.8,7,12))
    # The archived source cuts the slot in the block before joining its arm.
    return block.cut(slot).fuse(arm).clean()

def ray_top(s,x,y):
    edge=cq.Edge.makeLine(V(x,y,8),V(x,y,12))
    vs=s.intersect(edge).Vertices()
    return max((p.Z for p in vs),default=None)

def main():
    body=g.load('BODY');c=g.carrier_geometry()
    hinge=cq.importers.importStep(str(g.EXP/'MAIN_OUTER_HINGE_REFERENCE.step')).val()
    skin=cq.importers.importStep(str(g.EXP/'LOW_MOTHER_SKIN_REFERENCE.step')).val()
    rows=[];ears=[];hits=[]
    for i,(x,y,ly,z) in enumerate(((27.331028099073382,43.,43.,10.8),(28.60429589691332,66.,66.8,10.525))):
        e=ear(x,y);ears.append(e)
        leg=c['legs'][i].cut(cq.Solid.makeCylinder(1.2,6,V(x,ly,9)))
        # Check the actual source feature against BODY to detect reconstruction drift.
        same=g.vol(e.intersect(body));missing=g.vol(e.cut(body))
        overlap=g.vol(leg.intersect(e))
        sample=[]
        for dx,dy in ((-1.5,0),(1.5,0),(0,-1.75),(0,1.75),(1.4,-.8),(1.4,.8)):
            px=x+dx;py=ly+dy
            sample.append(dict(x=px,y=py,reference_top_z=ray_top(e,px,py),actual_BODY_top_z=ray_top(body,px,py)))
        rows.append(dict(name=('front','rear')[i],ear_center=[x,y,9.5],leg_center=[x,ly],
                         document_leg_bottom_z=z,planar_ear_top_z=10.75,rounded_arm_max_z=10.8,
                         ear_source_volume_mm3=g.vol(e),source_common_with_BODY_mm3=same,
                         source_outside_BODY_mm3=missing,leg_vs_ear_intersection_mm3=overlap,
                         leg_vs_ear_distance_mm=leg.distance(e),sample_top_heights=sample,
                         top_profile_x=x+1.4,
                         top_profile=[[float(py),ray_top(e,x+1.4,float(py))] for py in np.linspace(ly-2,ly+2,65)],
                         correction='Use a footprint-level contact datum and a profiled adapter seat; a height at one point is not a flat mounting plane.'))
        g.export(e,('FRONT','REAR')[i]+'_EAR_SOURCE_REFERENCE')
        if overlap>.001:hits.append(leg.intersect(e))
    pairs=[]
    for i in (0,1):
        for kind in ('legs','bridges','collars'):
            pairs.append(g.checkpair(c[kind][i],hinge,('front','rear')[i]+'_'+kind,'main_outer_hinge'))
    pairs += [g.checkpair(c['carrier'],hinge,'whole_carrier','main_outer_hinge'),
              g.checkpair(c['carrier'],skin,'whole_carrier','low_mother_skin')]
    for ob in (hinge,skin):
        hit=c['carrier'].intersect(ob)
        if g.vol(hit)>.001:hits.append(hit)
    g.export(cq.Compound.makeCompound(hits),'R2_COLLISION_REGIONS')
    g.save('K9_r2_contact_audit.json',dict(ears=rows,pairs=pairs,
        classification='Measured on unmodified R3.2 STEP plus independently reconstructed source features',
        note='The ear has planar lands at Z10.75 and a rounded connecting arm reaching Z10.80. Rear leg Y66.8 is not the ear-center Y66.0. Do not substitute a point-ray height for a complete support plane.',
        stack_height_formula='12.1 - z_actual_adapter_top; positive alone does not prove minimum structural thickness',
        nominal_stack_threshold_mm=1.30,
        layer_1p6_conflict='A 1.6-mm adapter above even the planar 10.75 datum reaches 12.35, exceeding the carrier underside 12.1 by 0.25 mm.'))
    print(json.dumps(rows,indent=2),flush=True)

if __name__=='__main__':main()
