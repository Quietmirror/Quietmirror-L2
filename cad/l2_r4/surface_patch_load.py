"""Integrate a fixed rectangular traction patch over quadratic mesh faces.

Clip each planar boundary triangle in YZ before integrating its six shape
functions. This keeps the physical loading area independent of mesh size.
"""
import numpy as np
from shapely.geometry import Polygon,box

def rectangle_load(mesh,xplane,y0,y1,z0,z1,force,name):
    patch=box(y0,z0,y1,z1);loads=np.zeros((len(mesh.ids),3));area=0.;first=np.zeros(2);triangles=0
    selected=np.flatnonzero((np.abs(mesh.centers[:,0]-xplane)<.02)&(mesh.normals[:,0]>.95))
    for i in selected:
        ids=mesh.faces[i];coords=mesh.xyz[ids];yz=coords[:3,1:]
        clipped=Polygon(yz).intersection(patch)
        if clipped.is_empty or clipped.area<1e-12:continue
        assert clipped.geom_type=='Polygon'
        # SecondOrderLinear=1 makes corner-barycentric coordinates exact.
        assert np.allclose(coords[3:],[(coords[0]+coords[1])/2,(coords[1]+coords[2])/2,(coords[2]+coords[0])/2],atol=1e-7,rtol=0)
        inverse=np.linalg.inv(np.vstack([yz.T,np.ones(3)]));points=np.array(clipped.exterior.coords)[:-1];weights=np.zeros(6)
        for j in range(1,len(points)-1):
            tri=points[[0,j,j+1]];a=abs(float(np.linalg.det((tri[1:]-tri[0]).T)))/2
            if a<1e-14:continue
            # Three symmetric points exactly integrate quadratic shape functions.
            for bary in [[2/3,1/6,1/6],[1/6,2/3,1/6],[1/6,1/6,2/3]]:
                point=np.array(bary)@tri;l,u,v=inverse@np.r_[point,1.]
                weights+=(a/3)*np.array([l*(2*l-1),u*(2*u-1),v*(2*v-1),4*l*u,4*u*v,4*v*l])
        np.add.at(loads[:,0],ids,-weights)
        area+=float(clipped.area);first+=float(clipped.area)*np.array(clipped.centroid.coords[0]);triangles+=1
    expected=(y1-y0)*(z1-z0)
    assert abs(area-expected)<max(1e-6,expected*1e-5),(name,'Incomplete/duplicate physical loading surface',area,expected)
    loads*=force/area;centroid=np.r_[xplane,first/area]
    assert np.allclose(loads.sum(0),[-force,0,0],atol=1e-9,rtol=0)
    assert np.allclose(np.cross(mesh.xyz,loads).sum(0),np.cross(centroid,[-force,0,0]),atol=1e-7,rtol=0)
    return loads,dict(name=name,magnitude_N=force,direction=[-1,0,0],selected_triangles=triangles,surface_area_mm2=area,expected_area_mm2=expected,pressure_magnitude_MPa=force/area,area_centroid_mm=centroid.tolist(),actual_force_sum_N=loads.sum(0).tolist(),distribution='Exact planar clipping to the specified rectangular 1.2 x 0.5 mm equivalent stop-load patch, with quadratic consistent nodal traction and resultant/moment checks.')

def self_check():
    from types import SimpleNamespace
    # A rectangle that cuts both source triangles, rather than selecting
    # centroids, must keep its 0.6 mm2 area and exact force/moment.
    corners=[np.array([[0,0,0],[0,2,0],[0,2,1]],float),np.array([[0,0,0],[0,2,1],[0,0,1]],float)]
    xyz=[]
    for c in corners:xyz.extend([*c,(c[0]+c[1])/2,(c[1]+c[2])/2,(c[2]+c[0])/2])
    m=SimpleNamespace(xyz=np.array(xyz),ids=np.arange(12),faces=np.arange(12).reshape(2,6),centers=np.array([c.mean(0) for c in corners]),normals=np.array([[1,0,0],[1,0,0]]))
    _,report=rectangle_load(m,0,.4,1.6,.25,.75,5.,'clipped_rectangle_self_check')
    return report
if __name__=='__main__':print(self_check())
