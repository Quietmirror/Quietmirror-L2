"""Exact local battery escape diagnostics; no automatic service pass."""
from common import *
from exact_distance import pair
def main():
    body=load('BODY');battery=load('BATTERY_CELL_EST',OUT/'reference');pivot=battery.Center()
    rows=[]
    for axis in range(3):
        for delta in [-2.,-1.,-.5,-.25,.25,.5,1.,2.]:
            shift=[0.,0.,0.];shift[axis]=delta
            r=pair(battery.translate(tuple(shift)),body,'BATTERY_CELL_EST','BODY',.5)
            rows.append(dict(kind='translation',axis=axis,delta=delta,**r));print(rows[-1],flush=True)
    for axis in range(3):
        end=pivot+V(*[1 if i==axis else 0 for i in range(3)])
        for angle in [-10.,-5.,-1.,1.,5.,10.]:
            r=pair(battery.rotate(pivot.toTuple(),end.toTuple(),angle),body,'BATTERY_CELL_EST','BODY',.5)
            rows.append(dict(kind='rotation',axis=axis,delta=angle,**r));print(rows[-1],flush=True)
    save('battery_escape_probe.json',dict(rows=rows,purpose='Identify exact restricting surfaces before choosing a general six-dimensional rigid service route.'))
if __name__=='__main__':main()
