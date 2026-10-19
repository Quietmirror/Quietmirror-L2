"""Conservative maximum connected PCB outline in a declared planar bay.

This is a design envelope, not a measured ATK board. Maximum means the largest
connected planar free region after the stated cavity/clearance construction;
it does not claim a global optimum over arbitrary board heights or components.
All resulting solids must pass exact BRep clearance verification.
"""
import json,math
import numpy as np
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
from common import *
from surfaces import make_surfaces
Z=14.2;THICKNESS=1.2;GAP=.5;MESH_ALLOWANCE=.04

def ring(w):
    count=max(16,int(math.ceil(w.Length()/.15)))
    return [(p.x,p.y) for p in [w.positionAt(i/count) for i in range(count)]]

def section(s,z):
    faces=s.intersect(cq.Face.makePlane(basePnt=V(0,0,z))).Faces();polys=[]
    for f in faces:
        p=Polygon(ring(f.outerWire()),[ring(w) for w in f.innerWires()])
        if not p.is_valid:p=p.buffer(0)
        polys.append(p)
    return unary_union(polys)

def projected(s):
    if not s.Solids():return Polygon()
    vertices,faces=s.tessellate(.02,.1);v=np.array([p.toTuple() for p in vertices]);polys=[]
    for f in faces:
        p=Polygon(v[np.array(f),:2])
        if p.area>1e-10:polys.append(p)
    return unary_union(polys)

def solid(poly):
    outer=cq.Wire.makePolygon([V(x,y,Z) for x,y in poly.exterior.coords],close=True)
    holes=[cq.Wire.makePolygon([V(x,y,Z) for x,y in hole.coords],close=True) for hole in poly.interiors]
    return cq.Solid.extrudeLinear(outer,holes,V(0,0,THICKNESS))

def main():
    p=json.loads((ROOT/'cad/rebuild_r2/parameters.json').read_text());outer,inner,_=make_surfaces(p)
    inv=json.loads((RP/'assembly_inventory.json').read_text());body=load('BODY')
    # Preserve functional mechanical packages, power access and the battery.
    # The two H PCBs, their chips, headers and interboard routes are replaced
    # by a donor PCB and are therefore not treated as occupied D-space.
    keep=['BATTERY_CELL_EST','BATTERY_PLUG_EST','SWITCH_LEFT','SWITCH_RIGHT','SWITCH_MIDDLE',
          'SF_D2F_01F','SR_D2F_01F','USB_C_REFERENCE','USB_ADAPTER_PCB_REFERENCE',
          'POWER_SWITCH_BODY_EST','POWER_SWITCH_PCB_EST','POWER_SWITCH_TAB_EST']
    obs={n:load(n) for n in inv['printable']}
    obs.update({n:load(n,OUT/'reference') for n in keep})
    obs.update({n:load(n,OUT/'reference') for n in inv['H_hardware'] if n.startswith(('ENCODER_','WHEEL_M2','LEFT_KEY_M2','RIGHT_KEY_M2'))})
    cavity=None
    for z in np.linspace(Z,Z+THICKNESS,7):
        q=section(inner,float(z));cavity=q if cavity is None else cavity.intersection(q)
    cavity=cavity.buffer(-(GAP+MESH_ALLOWANCE),join_style='round')
    slab=box(-40,40,0,90,Z-GAP-MESH_ALLOWANCE,Z+THICKNESS+GAP+MESH_ALLOWANCE)
    removed=[]
    for n,s in obs.items():
        cut=s.intersect(slab);q=projected(cut)
        if not q.is_empty:removed.append(q.buffer(GAP+MESH_ALLOWANCE,join_style='round'))
    free=cavity.difference(unary_union(removed));pieces=[free] if free.geom_type=='Polygon' else list(free.geoms)
    pieces=[q for q in pieces if q.geom_type=='Polygon' and q.area>1]
    if not pieces:raise RuntimeError('No PCB region at the declared optical-stack board height')
    # Optical placement is a necessary constraint, not an optional scoring
    # term: the selected component must contain the existing sensor axis.
    optical=[q for q in pieces if q.covers(Point(0,66))]
    if not optical:raise RuntimeError('No connected donor board region includes the optical axis (0,66)')
    selected=max(optical,key=lambda q:q.area)
    inset=selected.simplify(.015,preserve_topology=True).buffer(-.02)
    # The final conservative inset may sever a narrow neck. Reapply both
    # single-board continuity and the mandatory optical-axis constraint.
    inset_parts=[inset] if inset.geom_type=='Polygon' else list(inset.geoms)
    inset_parts=[q for q in inset_parts if q.geom_type=='Polygon' and not q.is_empty]
    inset_optical=[q for q in inset_parts if q.covers(Point(0,66))]
    if not inset_optical:raise RuntimeError('Conservative inset disconnected the sensor axis from every printable board region')
    outline=max(inset_optical,key=lambda q:q.area)
    board=valid(solid(outline),'D_MAX_BOARD_ENVELOPE');checks=[pair(board,s,'D_MAX_BOARD_ENVELOPE',n,GAP) for n,s in obs.items()]
    outside=vol(board.cut(outer))
    cq.exporters.export(board,str(OUT/'D_MAX_BOARD_ENVELOPE.step'))
    # These are possible PCB hole-center regions only. They are NOT existing
    # fastening bosses, nor an invented donor drilling pattern.
    centers=outline.buffer(-3.0);regions=[]
    for q in ([centers] if centers.geom_type=='Polygon' else list(centers.geoms)):
        if q.is_empty or q.area<1:continue
        regions.append(dict(outer_xy_mm=list(q.exterior.coords),holes_xy_mm=[list(h.coords) for h in q.interiors]))
    save('donor_envelope.json',dict(status='DONOR_PENDING',candidate_geometric_pass=outside<=.001 and all(r['pass_check'] for r in checks),
        units='mm',bottom_z_mm=Z,thickness_mm=THICKNESS,area_mm2=outline.area,bounds_mm=bounds(board),outside_mother_mm3=outside,
        conservative_inset_components=len(inset_parts),discarded_disconnected_area_mm2=sum(q.area for q in inset_parts)-outline.area,
        construction='Largest optical-axis-containing component in seven-height cavity intersection minus expanded obstacle projections. Projection allowances are conservative; exact final-solid distances are separately checked.',
        scope='Maximum only within this declared conservative planar construction. Not global optimization, real donor outline, mounting-hole certification, or component-height clearance certification.',
        retained_components=list(obs),checks=checks,hole_center_regions=regions,
        hole_region_assumption='M2 nominal clearance hole 2.2 mm with 1.9 mm edge material: centers 3 mm inside this hypothetical outline. Mounting posts and supplier hole coordinates remain unassigned.'))
    print('D_ENVELOPE',outline.area,'mm2; exact checks',all(r['pass_check'] for r in checks),flush=True)

if __name__=='__main__':main()
