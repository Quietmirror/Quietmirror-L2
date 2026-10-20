"""Load integration from the preserved author evidence, adapted to portable paths.

Author source: cad/l2_fem_author/fem_variants.py @ f637118.
The two obsolete side fence cases are deliberately absent in both references
and R4, as required by the execute-all plan. The six actual loads are unchanged.
"""
import json
from pathlib import Path
import numpy as np
from surfaces import roof_z,half_width,roof_height
ROOT=Path(__file__).resolve().parents[2]
P2=json.loads((ROOT/'cad/rebuild_r2/parameters.json').read_text())
META=json.loads((ROOT/'reports/rebuild_r3_2/design_metadata.json').read_text())
META['mechanisms']['side_motions']=[]
FOOT_Z=5.2
FC=None
def foot_constraints(mesh):
    centers = np.asarray(P2['feet']['centers'])
    r = P2['feet']['diameter'] / 2
    feet = []
    for c in centers:
        idx = np.flatnonzero((np.abs(mesh.xyz[:, 2] - FOOT_Z) < 0.025) & (np.linalg.norm(mesh.xyz[:, :2] - c, axis=1) < r + 0.03))
        if len(idx) < 6:
            raise ValueError(f'Too few foot nodes at {c}: {len(idx)}')
        feet.append(idx)
    a = int(feet[0][np.argmin(np.linalg.norm(mesh.xyz[feet[0], :2] - centers[0], axis=1))])
    b = int(feet[1][np.argmin(np.linalg.norm(mesh.xyz[feet[1], :2] - centers[1], axis=1))])
    return ([(int(i), 3) for g in feet for i in g] + [(a, 1), (a, 2), (b, 2)], feet)

def outer_masks(mesh):
    """Faces lying on the mother OUTER surface (roof: |z - roof_z| < .35; side: ||x| - wall_x| < .35).
    The R2 masks also caught interior faces seen through the windows (e.g. the top of the severed
    Y54 cross tie), which loaded a floating beam (umax 280 mm). Only the shell exterior is loaded here."""
    x, y, z = mesh.centers.T
    rz = np.array([roof_z(a, b, P2) for a, b in zip(x, y)])
    w = np.array([half_width(b, P2) for b in y])
    h = np.array([roof_height(b, P2) for b in y])
    frac = np.clip((z - 5) / np.maximum(h - 5, 1e-06), 0, 1)
    wx = w * np.maximum(0, 1 - frac ** 3.4) ** (1 / 3.4)
    return (np.abs(z - rz) < 0.35, np.abs(np.abs(x) - wx) < 0.35)

def root_cases(mesh,interval=(35.5,42.5)):
    x,y,z=mesh.centers.T;nx,ny,nz=mesh.normals.T;lo,hi=interval
    return [FC.selected_load(mesh,(y>=lo)&(y<=hi)&(x>=6)&(x<=24)&(z>=11)&(nz>.2),[0,0,-1],5,'left_main_root_down_5N'),
            FC.selected_load(mesh,(y>=lo)&(y<=hi)&(x<=-6)&(x>=-24)&(z>=11)&(nz>.2),[0,0,-1],5,'right_main_root_down_5N')]

def cases(mesh):
    x, y, z = mesh.centers.T
    nx, ny, nz = mesh.normals.T
    roof_out, side_out = outer_masks(mesh)
    root = P2['main']['root_y']
    out = []
    out.append(FC.selected_load(mesh, (y >= 44) & (y <= 71) & (np.abs(x) <= 24) & (z >= 23) & (nz > 0.3) & roof_out, [0, 0, -1], 20, 'palm_down_20N'))
    # Execute-all Appendix B explicitly uses 35.5..42.5. The author's helper
    # derives 35..42 from the older root_y=38 parameter. Use the requested
    # interval and disclose this difference when comparing author numbers.
    out.extend(root_cases(mesh))
    for i, m in enumerate(META['mechanisms']['side_motions']):
        tip = np.asarray(m['plunger_tip'], float)
        fx = tip[0] - 7.5
        cy, cz = tip[1:]
        out.append(FC.selected_load(mesh, (np.abs(x - fx) < 0.04) & (np.abs(y - cy) <= 7.25) & (z >= cz - 2.9) & (z <= cz + 2.9) & (nx > 0.95), [-1, 0, 0], 5, f'side_{i + 1}_switch_fence_inward_5N'))
    lp, _ = FC.selected_load(mesh, (x > 20) & (y >= 45) & (y <= 70) & (z >= 8) & (z <= 14) & (nx > 0.5) & side_out, [-1, 0, 0], 2, 'squeeze_+X')
    lm, _ = FC.selected_load(mesh, (x < -20) & (y >= 45) & (y <= 70) & (z >= 8) & (z <= 14) & (nx < -0.5) & side_out, [1, 0, 0], 2, 'squeeze_-X')
    out.append((lp + lm, dict(name='LC3_squeeze_2x2N', magnitude_N=4.0, components=['+X side 2 N toward -X', '-X side 2 N toward +X'])))
    for nm, (px, py) in (('press_A_d16_x14_y60', (14.0, 60.0)), ('press_B_d16_x-14_y72', (-14.0, 72.0))):
        out.append(FC.selected_load(mesh, (np.hypot(x - px, y - py) <= 8.0) & (z >= 18) & (nz > 0.3) & roof_out, [0, 0, -1], 5, nm))
    return out
