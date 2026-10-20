"""Exact boundary comparison when coincident full-solid booleans misclassify.

Unchanged face definitions are compared as complete recursive STEP entity
graphs, including trim curves and surface orientation. Every remaining face is
compared bidirectionally outside an explicitly declared correction box. No
sampled distances or cropped BODY distances certify this comparison.
"""
import hashlib
import re
from collections import Counter
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.TopAbs import TopAbs_OUT
from common import *


def face_signature(face, path):
    cq.exporters.export(face, str(path))
    entities = dict(re.findall(r'#(\d+)\s*=\s*(.*?);', path.read_text(), re.S))
    cache = {}

    def signature(key):
        if key not in cache:
            raw = re.sub(r'\s+', '', entities[key])
            raw = re.sub(r'#(\d+)', lambda m: signature(m[1]), raw)
            cache[key] = hashlib.sha256(raw.encode()).hexdigest()
        return cache[key]

    faces = [k for k, v in entities.items() if v.strip().startswith('ADVANCED_FACE')]
    assert len(faces) == 1
    return signature(faces[0])


def delta(a, b):
    if not a.Solids():
        return cq.Compound.makeCompound([])
    return a.cut(b) if b.Solids() else a


def area(shape):
    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(shape.wrapped, props, 1e-8, False)
    return props.Mass()


def compare(old, new, limits, directory):
    directory.mkdir(parents=True, exist_ok=True)
    zone = box(*limits)
    sides = []
    for name, shape in [('old', old), ('new', new)]:
        classifier = BRepClass3d_SolidClassifier(shape.wrapped)
        classifier.PerformInfinitePoint(1e-7)
        assert shape.isValid() and len(shape.Solids()) == 1
        assert len(shape.Shells()) == 1 and classifier.State() == TopAbs_OUT
        assert vol(shape) > 0
        faces = shape.Faces()
        signatures = [face_signature(f, directory / 'face.step') for f in faces]
        sides.append((faces, signatures))
        print('BOUNDARY_SIGNATURES', name, len(faces), flush=True)
    old_faces, old_signatures = sides[0]
    new_faces, new_signatures = sides[1]
    common_counts = Counter(old_signatures) & Counter(new_signatures)

    def unmatched(faces, signatures):
        remaining = common_counts.copy()
        output = []
        for i, (face, signature) in enumerate(zip(faces, signatures)):
            if remaining[signature]:
                remaining[signature] -= 1
            else:
                output.append((i, face))
        return output

    old_changed = unmatched(old_faces, old_signatures)
    new_changed = unmatched(new_faces, new_signatures)
    rows = []
    for name, own, other in [('old', old_changed, new_changed),
                             ('new', new_changed, old_changed)]:
        other_faces = cq.Compound.makeCompound([f for _, f in other])
        for index, face in own:
            inside = face.intersect(zone)
            outside = face.cut(zone)
            # Surface partitions must conserve the original face and be valid.
            partition_error = abs(area(face) - area(inside) - area(outside))
            assert inside.isValid() and outside.isValid()
            assert partition_error <= 1e-6, (name, index, partition_error)
            difference = outside.cut(other_faces) if outside.Faces() and other else outside
            assert difference.isValid()
            difference_area = area(difference)
            row = dict(side=name, face_index=index, source_area_mm2=area(face),
                       inside_area_mm2=area(inside), outside_area_mm2=area(outside),
                       partition_area_error_mm2=partition_error,
                       exterior_difference_area_mm2=difference_area,
                       difference_regions=[dict(bounds_mm=bounds(f), area_mm2=area(f))
                                           for f in difference.Faces()])
            rows.append(row)
    exterior_difference = sum(r['exterior_difference_area_mm2'] for r in rows)
    local_old, local_new = old.intersect(zone), new.intersect(zone)
    assert local_old.isValid() and local_new.isValid()
    removed, added = delta(local_old, local_new), delta(local_new, local_old)
    assert removed.isValid() and added.isValid()
    removed_volume, added_volume = vol(removed), vol(added)
    # Independent whole-solid adaptive integration must agree with local change.
    balance_error = abs((vol(old) - vol(new)) - (removed_volume - added_volume))
    result = dict(method='Complete recursive STEP face identity plus bidirectional exact exterior face difference and local solid difference',
                  correction_box_mm=list(limits), old_face_count=len(old_faces),
                  new_face_count=len(new_faces), identical_face_count=sum(common_counts.values()),
                  unmatched_old_count=len(old_changed), unmatched_new_count=len(new_changed),
                  exterior_difference_area_mm2=exterior_difference, face_checks=rows,
                  old_volume_mm3=vol(old), new_volume_mm3=vol(new),
                  local_old_volume_mm3=vol(local_old), local_new_volume_mm3=vol(local_new),
                  removed_mm3=removed_volume, added_mm3=added_volume,
                  whole_local_volume_balance_error_mm3=balance_error,
                  change_regions=[dict(bounds_mm=bounds(s), volume_mm3=vol(s))
                                  for s in removed.Solids()+added.Solids()],
                  passed=exterior_difference <= 1e-7 and balance_error <= .001)
    return result, removed, added


def regression():
    """The comparison must detect changes outside its declared correction zone."""
    original = box(0, 10, 0, 10, 0, 10)
    corrected = original.cut(box(4, 6, 4, 6, 8, 11))
    limits = (3, 7, 3, 7, 7, 12)
    directory = WORK / 'boundary_regression'
    positive, _, _ = compare(original, corrected, limits, directory)
    outside_change = corrected.cut(box(-1, 1, 0, 2, 0, 2))
    negative, _, _ = compare(original, outside_change, limits, directory)
    assert positive['passed'] and not negative['passed']
    return dict(local_removal_detected_mm3=positive['removed_mm3'],
                outside_change_difference_area_mm2=negative['exterior_difference_area_mm2'],
                positive_passed=positive['passed'], outside_change_rejected=not negative['passed'])
