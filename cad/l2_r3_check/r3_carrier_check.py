# L2 r3 side-key carrier: build from the r3 parameters and verify against retained R3.2 obstacles (BRep).
# Obstacles: mother side wall (L2 openings cut), main outer hinge, redesigned +X ears, rear foot strut, sensor tab,
# swept LEFT_KEY tail, H-scheme electronics envelopes. Unchanged-R3.2 BODY overlap is reported as context only.
import json, math
from pathlib import Path
import cadquery as cq
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

H = Path(__file__).resolve().parent
REF = Path(r'D:\Quietmirror_L2\_support\repo_L2_ab2240f3\x\Quietmirror-L2-ab2240f3\exports\l2_r2_diagnostic')
SCAN = Path(r'D:\Quietmirror_L2\l2_repo_scan\brep')
V = cq.Vector
def box(x0, x1, y0, y1, z0, z1): return cq.Solid.makeBox(x1-x0, y1-y0, z1-z0, V(x0, y0, z0))
def cyl(r, h, x, y, z): return cq.Solid.makeCylinder(r, h, V(x, y, z))
def vol(s):
    if not s.Solids(): return 0.0
    p = GProp_GProps(); BRepGProp.VolumeProperties_s(s.wrapped, p, 1e-8, True, False); return p.Mass()
def U(*s):
    r = s[0]
    for t in s[1:]: r = r.fuse(t)
    return r.clean()

P = json.load(open(H/'r3_parameters.json', encoding='utf-8-sig'))
C = P['carrier']

def carrier():
    f = C['floor']; floor = box(*f['x'], *f['y'], *f['z'])
    for w in C['floor_windows']: floor = floor.cut(box(*w['x'], *w['y'], f['z'][0]-1, f['z'][1]+1))
    wall = box(*C['back_wall']['x'], *C['back_wall']['y'], *C['back_wall']['z'])
    step = box(*C['sr_back_step']['x'], *C['sr_back_step']['y'], *C['sr_back_step']['z'])
    div = box(*C['divider']['x'], *C['divider']['y'], *C['divider']['z'])
    parts = [floor, wall, step, div]
    for k in ('sf', 'sr'):
        p = C['stop_posts'][k]
        parts += [box(*p['x_low'], *p['y'], p['z'][0], p['z_split']), box(*p['x_high'], *p['y'], p['z_split'], p['z'][1]),
                  box(*C['extensions'][k]['x'], *C['extensions'][k]['y'], *C['extensions'][k]['z'])]
    blocks = []
    for k in ('front', 'rear'):
        b = C['mount_blocks'][k]; blk = box(*b['x'], *b['y'], *b['z'])
        g = b.get('ear_rib_relief')
        if g: blk = blk.cut(box(*g['x'], *g['y'], b['z'][0]-0.1, b['z'][0]+g['depth']))
        blocks.append(blk); parts.append(blk)
    for s in C['pcb_seats']: parts.append(box(*s['x'], *s['y'], *s['z']))
    c = U(*parts)
    for k in ('front', 'rear'):
        b = C['mount_blocks'][k]; hx, hy = b['pilot_xy']
        c = c.cut(cyl(b['pilot_d']/2, b['z'][1]-b['z'][0]+0.2, hx, hy, b['z'][0]-0.1))
    return c.clean(), blocks

def ears():
    out = []
    for k in ('front', 'rear'):
        e = P['ears_r3'][k]; xx, yy = e['center']
        ear = box(xx-3.8, xx+3.8, yy-3.8, yy+3.8, 8.25, 10.75)
        a0 = V(xx+e['arm_start_dx'], yy, e['arm_z']); a1 = V(xx+2.0, yy, e['arm_z'])
        arm = cq.Solid.makeCylinder(1.3, (a1-a0).Length, a0, (a1-a0).normalized()).fuse(cq.Solid.makeSphere(1.3, a1)).fuse(cq.Solid.makeSphere(1.3, a0))
        out.append(ear.fuse(arm).cut(cyl(e['hole_d']/2, 4, *e['hole_xy'], 7.5)).clean())   # hole cut after the arm join
    return out

def main():
    car, blocks = carrier()
    sw = P['switches']
    sf = box(*sw['sf']['x'], *sw['sf']['y'], *sw['sf']['z']); sr = box(*sw['sr']['x'], *sw['sr']['y'], *sw['sr']['z'])
    pcb = box(*P['side_io_pcb']['x'], *P['side_io_pcb']['y'], *P['side_io_pcb']['z'])
    body = cq.importers.importBrep(str(SCAN/'BODY.brep')).val()
    inner = cq.importers.importStep(str(REF/'support_reference'/'MOTHER_INNER_FROM_R32_SURFACE.step')).val()
    outer = cq.importers.importStep(str(REF/'support_reference'/'MOTHER_OUTER_FROM_R32_SURFACE.step')).val()
    skin = outer.cut(inner)
    wall = skin.intersect(box(10, 40, 35, 75, 8, 21))
    for o in P['side_openings']: wall = wall.cut(box(20, 40, *o['y'], *o['z']))
    hinge = body.intersect(box(25.0, 30.0, 35.0, 43.3, 11.0, 22.0)).cut(skin)
    strut = cq.importers.importStep(str(REF/'REAR_FOOT_STRUT_REFERENCE.step')).val()
    tab = body.intersect(box(9.4, 15.6, 50.6, 59.4, 10.3, 12.9))
    ear_f, ear_r = ears()
    key = cq.importers.importBrep(str(SCAN/'LEFT_KEY.brep')).val()
    keys = [key.rotate(V(0, 38.5, 14.32), V(1, 38.5, 14.32), a) for a in (-0.5, 0.0, 1.4, 2.8, 3.1)]
    elec = {n: box(c[0]-s[0]/2, c[0]+s[0]/2, c[1]-s[1]/2, c[1]+s[1]/2, c[2]-s[2]/2, c[2]+s[2]/2) for n, (c, s) in P['h_electronics'].items()}
    rows = []
    def chk(an, a, bn, b, need, kind='clearance'):
        d = a.distance(b); iv = vol(a.intersect(b))
        ok = (iv <= 0.001 and d >= need-1e-6) if kind == 'clearance' else (iv <= 0.001)
        rows.append(dict(a=an, b=bn, gap_mm=round(d, 4), overlap_mm3=round(iv, 4), need_mm=need, kind=kind, pass_=ok)); print(rows[-1], flush=True)
    G = P['gaps']
    for n, s in (('carrier', car), ('SF_switch', sf), ('SR_switch', sr), ('SIDE_IO_PCB', pcb)):
        chk(n, s, 'side_wall(L2 openings cut)', wall, G['fixed_to_body'])
        chk(n, s, 'main_outer_hinge', hinge, G['fixed_to_body'])
        chk(n, s, 'rear_foot_strut', strut, G['fixed_to_body'])
        chk(n, s, 'sensor_tab', tab, G['fixed_to_body'])
        chk(n, s, 'LEFT_KEY_swept(-0.5..3.1deg)', U(*keys), G['moving_fdm'])
        for en, e in elec.items(): chk(n, s, en, e, G['fixed_to_electronics'])
    chk('front_block', blocks[0], 'front_ear_r3', ear_f, 0, 'contact')
    chk('rear_block', blocks[1], 'rear_ear_r3', ear_r, 0, 'contact')
    chk('SF_switch', sf, 'SF_stop_post_and_divider', car, 0, 'contact')
    chk('SR_switch', sr, 'carrier', car, 0, 'contact')
    chk('SIDE_IO_PCB', pcb, 'carrier', car, 0, 'contact')
    # named critical gaps inside the module
    posts = {k: U(box(*C['stop_posts'][k]['x_low'], *C['stop_posts'][k]['y'], C['stop_posts'][k]['z'][0], C['stop_posts'][k]['z_split']),
                  box(*C['stop_posts'][k]['x_high'], *C['stop_posts'][k]['y'], C['stop_posts'][k]['z_split'], C['stop_posts'][k]['z'][1])) for k in ('sf', 'sr')}
    chk('SF_stop_post', posts['sf'], 'SF_switch', sf, G['fixed_to_electronics'])
    chk('SR_stop_post', posts['sr'], 'SR_switch', sr, G['fixed_to_electronics'])
    chk('SR_stop_post', posts['sr'], 'SF_SR_partition_ring', box(26.5, 32, *P['partition_ring']['y'], 15.2, 19.8), G['fixed_to_body'])
    chk('SR_switch', sr, 'SR_back_support(-X face)', box(*C['sr_back_step']['x'], *C['sr_back_step']['y'], *C['sr_back_step']['z']), 0, 'contact')
    # side-key actuation (Fenrir-style revision): free-end retention tabs swept 0..sweep_deg about the vertical hinge axes
    A = P['side_keys_actuation']; ring = box(*A['partition_ring']['x'], *A['partition_ring']['y'], *A['partition_ring']['z'])
    for k in ('sf', 'sr'):
        t = A['tabs'][k]; tab = box(*t['x'], *t['y'], *t['z']); web = box(*t['web']['x'], *t['web']['y'], *t['web']['z']); hx, hy = A['hinge_axis_xy'][k]
        chk(f'{k.upper()}_tab_web_rest', web, 'partition_end_ring', ring, 0.3)
        tab = tab.fuse(web).clean()
        swept = [tab.rotate(V(hx, hy, 0), V(hx, hy, 1), t['sign']*a) for a in (0.0, 1.7, 3.45, 5.2, A['sweep_deg'])]
        sw_u = U(*swept)
        chk(f'{k.upper()}_tab_swept', sw_u, 'carrier', car, G['moving_fdm'])
        chk(f'{k.upper()}_tab_swept', sw_u, 'SF_switch', sf, G['moving_fdm'])
        chk(f'{k.upper()}_tab_swept', sw_u, 'SR_switch', sr, G['moving_fdm'])
        chk(f'{k.upper()}_tab_rest', box(*t['x'], *t['y'], *t['z']), 'partition_end_ring', ring, 0, 'contact')
        chk(f'{k.upper()}_tab_swept(>0)', U(*swept[1:]), 'partition_end_ring', ring, 0.05)
    chk('SF_tab', box(*A['tabs']['sf']['x'], *A['tabs']['sf']['y'], *A['tabs']['sf']['z']), 'SR_tab', box(*A['tabs']['sr']['x'], *A['tabs']['sr']['y'], *A['tabs']['sr']['z']), G['moving_fdm'])
    # PCB seats must stay >= 0.5 from the D2F terminal holes (dia 1.2) in the SIDE_IO_PCB
    holes = U(*[cyl(0.6, 4.0, 14.0, y, 0).rotate(V(14.0, y, 0), V(14.0, y+1, 0), 90).translate(V(0, 0, 16.6)) for k in ('sf', 'sr') for y in P['switch_terminals_y'][k]])
    for i, s in enumerate(C['pcb_seats']):
        chk(f'PCB_seat_{i+1}', box(*s['x'], *s['y'], *s['z']), 'terminal_holes', holes, G['fixed_to_electronics'])
    pb = P['side_io_pcb']; ok = all(y-0.6 >= pb['y'][0]+0.5 and y+0.6 <= pb['y'][1]-0.5 for k in ('sf', 'sr') for y in P['switch_terminals_y'][k]) and 16.6-0.6 >= pb['z'][0]+0.5 and 16.6+0.6 <= pb['z'][1]-0.5
    rows.append(dict(a='terminal_holes(d1.2, edge margin 0.5)', b='inside SIDE_IO_PCB outline', gap_mm=None, overlap_mm3=None, need_mm=0.5, kind='containment', pass_=ok)); print(rows[-1], flush=True)
    res = dict(carrier_solids=len(car.Solids()), carrier_valid=car.isValid(), carrier_volume_mm3=round(vol(car), 3),
               blocks_on_ear_bearing_mm2=None, context_unchanged_R32_BODY_overlap_mm3=round(vol(car.intersect(body)), 3),
               context_pcb_R32_overlap_mm3=round(vol(pcb.intersect(body)), 3), checks=rows,
               all_clearances_pass=all(r['pass_'] for r in rows))
    # bearing area of each block on its ear top (Z 10.75 face)
    for k, blk, ear in (('front', blocks[0], ear_f), ('rear', blocks[1], ear_r)):
        foot = blk.intersect(box(0, 40, 30, 80, 10.75, 10.8)); top = ear.intersect(box(0, 40, 30, 80, 10.7, 10.75))
        res[f'{k}_bearing_mm2'] = round(vol(foot.intersect(box(0, 40, 30, 80, 10.75, 10.8)).intersect(top.translate(V(0, 0, 0.05)))) / 0.05, 3) if top.Solids() else 0
    json.dump(res, open(H/'r3_check.json', 'w'), indent=1)
    cq.exporters.export(car, str(H/'R3_SIDE_SWITCH_CARRIER.step'))
    cq.exporters.export(cq.Compound.makeCompound([car, sf, sr, pcb, ear_f, ear_r]), str(H/'R3_SIDE_MODULE_LAYOUT.step'))
    print('SOLIDS', res['carrier_solids'], 'VALID', res['carrier_valid'], 'VOL', res['carrier_volume_mm3'], 'ALLPASS', res['all_clearances_pass'],
          'bearing', res['front_bearing_mm2'], res['rear_bearing_mm2'], flush=True)

if __name__ == '__main__': main()
