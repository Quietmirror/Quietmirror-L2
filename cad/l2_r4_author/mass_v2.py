import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
def vol(s):
    p = GProp_GProps(); BRepGProp.VolumeProperties_s(s.wrapped, p, 1e-8, True, False); return p.Mass()
for n, f in (('BODY_L2r3', r'D:\Quietmirror_L2\fem3d\variants\BODY_L2r3.step'), ('BODY_V2', r'D:\Quietmirror_L2\fem3d\variants\BODY_V2.step'), ('FRAME', r'D:\Quietmirror_L2\fem3d\variants\R4_SIDE_FRAME_ONLY.step')):
    print(n, round(vol(cq.importers.importStep(f).val()), 2), flush=True)
B = lambda x0,x1,y0,y1,z0,z1: cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))
sf = B(17.3,18.5,41.8,55.3,13.7,19.5).fuse(B(16.6,18.5,41.8,44.6,13.7,17.2))
sr = B(17.3,19.0,55.3,71.2,13.7,19.5).fuse(B(16.6,18.5,68.4,71.2,13.7,17.2))
print('SF_RETAINER', round(vol(sf),2), 'SR_RETAINER', round(vol(sr),2))
