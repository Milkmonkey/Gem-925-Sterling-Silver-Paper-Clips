"""Record prototype dimensions, rejected reverse order, and basic load assumptions."""
import json, math
import numpy as np
import trimesh
from shapely.geometry import LineString
from geometry import P,ROOT,geometry,segments,arc,line

g=geometry();ss=segments();reverse=[s[::-1].copy() for s in ss[::-1]]
reverse_results=[]
for stage in range(3):
    idx=2-stage;r=g['radii'][idx];center=g['centers'][idx];rot=-1 if stage==1 else 1
    fixed=[LineString((s-center)*rot) for s in reverse[:2*stage]]
    first=None;minimum=1e9
    for phi in np.linspace(0,180,721):
        tail_length=sum(g['lengths'][::-1][2*stage+1:])-r*math.radians(phi)
        a=arc([0,0],r,0,phi,max(3,int(phi*2)+1));th=math.radians(phi)
        t=line(a[-1],a[-1]+tail_length*np.array([-math.sin(th),math.cos(th)]))
        gap=min([s.distance(LineString(t))-P['wire_diameter'] for s in fixed],default=1e9)
        minimum=min(minimum,gap)
        if gap<-.001 and first is None:first=float(phi)
    reverse_results.append(dict(stage='CBA'[stage],first_collision_angle_deg=first,
        min_tail_surface_gap_mm=None if minimum==1e9 else minimum,
        note='Independent static earlier segments; later stages assume preceding ideal bends could be completed.'))
assert reverse_results[1]['first_collision_angle_deg'] is not None
v01={}
for path in sorted((ROOT/'reference/v01').glob('*.stl')):
    m=trimesh.load(path,force='mesh');v01[path.name]={'watertight':bool(m.is_watertight),
       'bounds_mm':m.bounds.tolist(),'extents_mm':m.extents.tolist(),'bodies':len(m.split(only_watertight=False))}
force=40.;bearing_height=13.5;pin=2.5
load={'assumed_pusher_force_N':force,'assumed_upper_pivot_reaction_N':force,'upper_bearing_height_above_base_mm':bearing_height,
      'A_pin_cantilever_stress_MPa':32*force*bearing_height/(math.pi*pin**3),
      'A_pin_elastic_deflection_mm_assuming_steel_E_200GPa':force*bearing_height**3/(3*200000*(math.pi*pin**4/64)),
      'nominal_minimum_lever_web_mm':.94,'nominal_web_average_shear_MPa':force/(.94*8),
      'meaning':'Order-of-magnitude assumptions, NOT FEA, material certification, or approved working load. Force 40 N is not a measured silver requirement.'}
report={'v01_meshes':v01,'rejected_order_CBA':reverse_results,'preliminary_load_estimates':load}
(ROOT/'validation/design_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
