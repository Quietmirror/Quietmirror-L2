"""Portable extraction of named baseline BReps; no author-machine paths."""
from pathlib import Path
import json,zipfile,xml.etree.ElementTree as ET
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2]
def main():
    target=ROOT/'exports/rebuild_r3_2/assembly';target.mkdir(parents=True,exist_ok=True)
    work=ROOT/'_support/work/l2_r4/baseline_brep';work.mkdir(parents=True,exist_ok=True)
    z=zipfile.ZipFile(ROOT/'models/L2_r3/inputs/R32_BASELINE.FCStd');doc=ET.fromstring(z.read('Document.xml'));rows=[]
    for obj in doc.findall('./ObjectData/Object'):
        p=obj.find('./Properties/Property[@name="Shape"]')
        if p is None:continue
        name=obj.attrib['name'];fn=next(iter(p)).attrib.get('file')
        if not fn:continue
        output=target/(name+'.step')
        if not output.exists():
            f=work/(name+'.brep');f.write_bytes(z.read(fn));s=cq.importers.importBrep(str(f)).val()
            assert s.isValid() and len(s.Solids())==1,name;cq.exporters.export(s,str(output))
        rows.append(name)
    print('Restored/retained',len(rows),'baseline components',flush=True)
if __name__=='__main__':main()
