# Side-key actuation numbers for the Fenrir-style revision (rigid-body rotation about the vertical hinge pin).
import json, math
from pathlib import Path
H = Path(__file__).resolve().parent
P = json.load(open(H/'r3_parameters.json', encoding='utf-8-sig'))
A = P['side_keys_actuation']
# outer mother-surface X at Z16.6 (FINAL §3.4 table), linear interpolation in Y
TAB = [(41.8, 30.23), (46.0, 30.73), (50.8, 31.44), (56.3, 32.14), (58.1, 32.24), (62.0, 32.34), (66.0, 31.82), (70.8, 30.62)]
def xo(y):
    for (y0, x0), (y1, x1) in zip(TAB, TAB[1:]):
        if y0 <= y <= y1: return x0 + (x1-x0)*(y-y0)/(y1-y0)
OF, PT, OT, MD, OPTOL = 0.74, 0.5, 0.25, 0.12, 0.3
keys = {'sf': dict(face=(44.2, 56.3), py=50.25, tip=P['switches']['sf']['tip']), 'sr': dict(face=(58.1, 70.8), py=64.45, tip=P['switches']['sr']['tip'])}
out = {}
for k, d in keys.items():
    hx, hy = A['hinge_axis_xy'][k]; g0 = A['nominal_rest_gap']; S = A['stop_travel_at_pushrod']
    inner = xo(d['py']) + 0.20 - 1.2                     # key inner surface at the pushrod (outer offset +0.20, shell 1.2)
    end_x = d['tip'][0] + g0                             # pushrod end at rest
    L = inner - end_x
    dx, dy = end_x - hx, d['py'] - hy                    # pushrod end relative to the hinge axis
    s = 1 if dy > 0 else -1
    def disp(phi):                                       # rotate toward -X
        c, sn = math.cos(phi), math.sin(phi)
        nx = dx*c - s*dy*sn; ny = s*dx*sn + dy*c
        return dx - nx, ny - dy                          # inward travel (+), Y slide
    def solve(target):
        lo, hi = 0.0, 0.3
        for _ in range(60):
            m = (lo+hi)/2
            if disp(m)[0] < target: lo = m
            else: hi = m
        return (lo+hi)/2
    phi_stop = solve(S); phi_contact0 = solve(0.0)
    # tuned (zero play): contact at rest; trigger when plunger has moved PT (worst 0.5) -> pushrod travel PT
    phi_trig_max = solve(PT)
    far = max(abs(d['face'][0]-hy), abs(d['face'][1]-hy)); near_q = abs(d['face'][0 if k == 'sf' else 1]-hy) + (d['face'][1]-d['face'][0])/4
    arm = abs(dy)
    out[k] = dict(pushrod_length_nominal=round(L, 3), key_inner_x=round(inner, 3), pushrod_end_rest_x=round(end_x, 3),
                  hinge=[hx, hy], arm=round(arm, 3), dx_pivot_to_rod=round(dx, 3),
                  stop_angle_deg=round(math.degrees(phi_stop), 3), y_slide_at_stop=round(disp(phi_stop)[1], 3),
                  trigger_angle_worst_deg=round(math.degrees(phi_trig_max), 3),
                  far_end_travel_at_stop=round(far*math.sin(phi_stop), 3),
                  plunger_drive_at_stop_tuned=S, post_travel_after_trigger_worst=round(S-PT, 3),
                  force_N=dict(at_pushrod=OF, quarter_from_pivot=round(OF*arm/((d['face'][1]-d['face'][0])/4), 3),
                               face_centre=round(OF*arm/abs((d['face'][0]+d['face'][1])/2-hy), 3), far_end=round(OF*arm/far, 3)),
                  hinge_reaction_N=round(OF*(1+arm/arm), 3), z_ecc_moment_Nmm=round(OF*0.9, 3))
# tolerance stack for the untuned rest gap (RSS): switch OP +-0.3, carrier X (hole clearance) +-0.1, BODY ear/hinge +-0.1, key rod +-0.1, hinge pin fit +-0.05
rss = math.sqrt(0.3**2 + 0.1**2 + 0.1**2 + 0.1**2 + 0.05**2)
out['tolerance'] = dict(rss_mm=round(rss, 3), untuned_gap_range=[round(A['nominal_rest_gap']-rss, 3), round(A['nominal_rest_gap']+rss, 3)],
                        tuning='PET adhesive dots 0.05/0.10 on the pushrod end (add) or sand <=0.10 (remove); target rest gap 0.00..0.03',
                        r3_untuned_verdict='r3 (gap 0.05, no tuning): plunger drive at stop 0.55 +- 0.36 -> 0.19..0.91: some units never trigger (<0.5), some exceed PT+OT')
json.dump(out, open(H/'side_key_actuation.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
