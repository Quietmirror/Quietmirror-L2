"""R4-only wire layout corrections; historical electronics.json is preserved."""
import json
from common import ROOT
OVERRIDES={
 'SENSOR_ROUTE_EST':[(9.5,71,20.3),(13.85,71,20.3),(13.85,73,17.2),(12.5,74.5,16.25),(8,72,16.25)],
 'USB_ROUTE_EST':[(-2,19,8),(-2,19,6.8),(-2,22,6.8),(-5,24,9.8),(-7,29,11),(-7,34,12.7),(-6.2,37,14.2),(-6.2,44,14.8),(-6.2,53.3,14.8),(-6.2,56.5,20.7),(-6.2,56.5,22.4),(-3.2,56.5,22.4),(-3.2,56.5,21.5)]}
def definition():
    data=json.loads((ROOT/'cad/rebuild_r3_2/electronics.json').read_text())
    for r in data['routes']:
        if r['name'] in OVERRIDES:r['points']=OVERRIDES[r['name']]
    return data
