"""S3/S4/S5/S9 and shim-range calculations from the current source and STEP.

These are geometric/ideal-lever calculations. Switch physical travel, force,
optics, current consumption and printed mass remain explicitly unmeasured.
"""
import json,math
import numpy as np
from common import *
from side_module import KEYS,PAD_RADIUS

def main():
    act=[]
    for k,x0,y0,tip in [(KEYS[0],18.5,41.85,25.62),(KEYS[1],19.,56.05,26.12)]:
        c=load(k['name']);film=load(k['short']+'_TUNING_SHIM_0p33',OUT/'reference')
        ori=(k['hinge_x'],k['hinge_y'],0);axis=(k['hinge_x'],k['hinge_y'],1)
        # Crown is a translated spherical patch. At these small rotations its
        # -X extremum stays on that patch and inside the covered flat button.
        radius=PAD_RADIUS;cx=k['rod_end']-.33+radius;cy=k['rod_y']+k['pad_y_offset']
        def extreme(a):
            t=math.radians(a);return k['hinge_x']+(cx-k['hinge_x'])*math.cos(t)-(cy-k['hinge_y'])*math.sin(t)-radius
        gap=extreme(0)-tip
        def inward(a):return extreme(0)-extreme(a)
        lo,hi=0.,abs(k['angle'])
        for _ in range(60):
            mid=(lo+hi)/2
            if inward(mid*k['sign'])<gap+.5:lo=mid
            else:hi=mid
        trigger=(lo+hi)/2*k['sign'];samples=[]
        housing=box(x0,x0+6.5,y0,y0+12.8,13.7,19.5)
        for angle in np.linspace(0,k['angle'],31):
            moved=c.rotate(ori,axis,float(angle));shim=film.rotate(ori,axis,float(angle))
            samples.append(dict(angle_deg=float(angle),depression_mm=max(0.,inward(angle)-gap),
                crown_min_x_mm=extreme(angle),key_rigid_housing_overlap_mm3=vol(moved.intersect(housing)),
                film_rigid_housing_overlap_mm3=vol(shim.intersect(housing))))
        # "Quarter" means one quarter of exposed usable length from hinge to
        # far cap edge, made explicit because the author's prose coordinates
        # do not uniquely define the quoted force numbers.
        far=k['y1'] if k['sign']>0 else k['y0'];L=abs(far-k['hinge_y']);positions=[]
        for label,yy in [('cap_midpoint',(k['y0']+k['y1'])/2),('quarter_hinge_to_far',k['hinge_y']+k['sign']*L/4),('far_edge',far)]:
            arm=abs(yy-k['hinge_y']);positions.append(dict(location=label,y_mm=yy,touch_arm_mm=arm,ideal_force_N=.74*abs(cy-k['hinge_y'])/arm))
        act.append(dict(part=k['name'],nominal_film_mm=.33,unshimmed_free_gap_mm=k['rod_end']-tip,
            residual_gap_mm=gap,stop_deg=k['angle'],max_PT_assumption_mm=.5,calculated_PT_max_trigger_deg=trigger,
            stop_button_depression_mm=inward(k['angle'])-gap,available_generic_plunger_protrusion_mm=.63,
            housing_samples=samples,force_positions=positions,switch_OF_max_N=.74,
            source='https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf',
            formula='F_touch = 0.74 * abs(pad_center_y - hinge_y) / abs(touch_y - hinge_y); ideal static lever, ignores friction/compliance.',
            physical='FP/OP/TTP, force and PET adjustment require the selected physical D2F-01F.',
            cad_pass=0<=gap<=.03 and abs(trigger)<abs(k['angle']) and inward(k['angle'])-gap<.63 and all(max(s['key_rigid_housing_overlap_mm3'],s['film_rigid_housing_overlap_mm3'])<=.001 for s in samples)))
    # Exhaust every 0.001 mm chain value and select a 0.01-mm stack increment;
    # adjustable range 0..0.70 mm includes the complete +/-0.35 mm chain.
    tuning=[]
    for base in np.linspace(0,.70,701):
        thick=min(.70,max(0,math.floor((float(base)+1e-9)/.01)*.01));res=float(base)-thick
        tuning.append(dict(unshimmed_gap_mm=float(base),film_mm=thick,residual_mm=res))
    save('side_actuation_force_and_tuning.json',dict(keys=act,film_range_mm=[0,.70],film_increment_assumption_mm=.01,
        tolerance_chain_mm=[-.35,.35],chain_samples=tuning,range_pass=all(-1e-8<=s['residual_mm']<=.03 for s in tuning),
        adjustment='Select PET plus adhesive stack by measured total thickness; values are stack targets, not a claim that nominal film gauges equal glued thickness.'))
    lens=load('MATCHED_LENS_EST',OUT/'reference');lens_z=lens.BoundingBox().zmin
    save('optical_stack_and_power.json',dict(lens_bottom_z_mm=lens_z,foot_glue_z_mm=5.2,skate_mm=.8,
        ground_z_mm=4.4,lens_bottom_to_ground_mm=lens_z-4.4,optical_axis=[0,0,-1],
        optical_scope='Geometric lens-envelope bottom to pad; true focal datum and PAW3950 working distance HARDWARE_PENDING.',
        runtime_requirement_h=12,usable_capacity_fraction=.75,
        capacity_scenarios=[dict(average_current_mA=i,required_nominal_capacity_mAh=12*i/.75) for i in [10,15,20,25]],
        power_scope='No actual cell capacity, current, radio latency, firmware, receiver, macro, LOD or DPI behavior has been measured. Package size does not imply cell capacity.',
        target_features=['400-6400 DPI','1000 Hz wireless','no sync technologies','macros','adjustable LOD','two thumb buttons','wheel + middle click','power switch','USB-C charging','12 h full-power runtime']))
    solids=json.loads((RP/'solids.json').read_text());rows=[]
    for s in solids:
        rows.append(dict(part=s['name'],volume_mm3=s['volume_mm3'],PA12_density_g_cm3=1.01,PA12_mass_g=s['volume_mm3']*1.01/1000,PLA_density_g_cm3=1.24,solid_PLA_mass_g=s['volume_mm3']*1.24/1000))
    save('CAD_mass.json',dict(parts=rows,total_volume_mm3=sum(r['volume_mm3'] for r in rows),total_PA12_g=sum(r['PA12_mass_g'] for r in rows),total_solid_PLA_g=sum(r['solid_PLA_mass_g'] for r in rows),volume_method='BRepGProp.VolumeProperties_s(shape,props,1e-8,True,False)',scope='Printed polymer geometry only; density assumptions; slicer support/infill mass is separate. No fabricated hardware mass or physical weigh-in.'))
    print('ACTUATION',[(k['part'],k['cad_pass']) for k in act],flush=True)

if __name__=='__main__':main()
