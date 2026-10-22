"""Failing assertions + measured CAD/mesh/swept-centreline evidence, not material FEA."""
import json, math, hashlib
from datetime import datetime, timezone
import numpy as np
import trimesh
from shapely.geometry import LineString, Point, box
from geometry import P,ROOT,geometry,segments,process_segments,final_path,motion,fixed_path,to_local,pusher_center,takeup

results_path=ROOT/'validation/results.json'
if results_path.exists(): results_path.unlink()  # never leave an earlier PASS after a failed run
g=geometry();d=P['wire_diameter'];ss=segments();report={'run_utc':datetime.now(timezone.utc).isoformat(),
    'parameters_sha256':hashlib.sha256((ROOT/'source/parameters.json').read_bytes()).hexdigest()}
assert LineString(final_path()).is_simple
gaps=[]
for i in range(7):
    for j in range(i+2,7):
        dist=LineString(ss[i]).distance(LineString(ss[j]));gaps.append(dict(pair=[i,j],surface_gap_mm=dist-d));assert dist>=d-1e-4
path=final_path();lo=path.min(axis=0)-d/2;hi=path.max(axis=0)+d/2
assert np.allclose(hi-lo,[P['clip_width'],P['clip_length']],atol=1e-5)
assert all(abs(np.linalg.norm(ss[i][-1]-ss[i+1][0]))<1e-8 for i in range(6))
sample_length=sum(LineString(x).length for x in ss)
assert abs(sample_length-g['length'])<.001
report['geometry']={'outside_mm':(hi-lo).tolist(),'theoretical_centerline_length_mm':g['length'],
  'sampled_length_mm':sample_length,'mass_g':g['length']*math.pi*d*d/4*.01036,
  'segments_mm':g['lengths'],'material_marks_from_trimmed_start_mm':g['marks'],
  'nonadjacent_gaps':gaps,'simple_continuous':True}
meshes={}
for path in sorted((ROOT/'stl').glob('*.stl'))+list((ROOT/'reference').glob('*.stl')):
    m=trimesh.load(path,force='mesh');bodies=m.split(only_watertight=False)
    assert m.is_watertight and m.is_winding_consistent and m.volume>0,path.name
    assert all(b.is_watertight and b.volume>0 for b in bodies)
    if path.parent.name=='stl':
        assert all(abs(b.bounds[0,2])<1e-5 for b in bodies),('floating print body',path.name)
    assert len(np.unique(np.round(m.vertices[:,2],4)))>1
    meshes[str(path.relative_to(ROOT))]=dict(watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),
      bodies=len(bodies),triangles=len(m.faces),volume_mm3=float(m.volume),bounds_mm=m.bounds.tolist(),
      sha256=hashlib.sha256(path.read_bytes()).hexdigest())
assert meshes['stl/additional_parts.stl']['bodies']==7
report['meshes']=meshes
def hole_section(name,z,expected):
    m=trimesh.load(ROOT/'stl'/f'{name}.stl',force='mesh')
    section=m.section(plane_origin=[0,0,z],plane_normal=[0,0,1]);assert section is not None
    measured=[]
    for poly in section.discrete:
        low=poly[:,:2].min(axis=0);high=poly[:,:2].max(axis=0)
        measured.append(((low+high)/2,high-low))
    result=[]
    for x,y,diameter in expected:
        candidates=[(center,extent) for center,extent in measured if np.linalg.norm(center-[x,y])<.01 and np.allclose(extent,[diameter,diameter],atol=.01)]
        assert len(candidates)==1,(name,x,y,candidates)
        center,extent=candidates[0]
        assert np.allclose(extent,[diameter,diameter],atol=.01),(name,extent,diameter)
        result.append(dict(center_mm=center.tolist(),diameter_xy_mm=extent.tolist()))
    return result
hole_checks={'base_z5':hole_section('base',5,[(P['axis_x'],P['axis_y'],8.2),(P['axis_x']-14,P['axis_y']-10,4.5)]),
             'lever_z2':hole_section('bending_lever',2,
                 [(22*i,0,2*r-d+P['pin_clearance']) for i,r in enumerate(g['radii'])]+
                 [(22*i+r+d/2+P['pusher_diameter']/2+P['pusher_clearance'],0,P['pusher_diameter']+.12) for i,r in enumerate(g['radii'])])}
for i in range(3):hole_checks['liner_'+'ABC'[i]]=hole_section('liner_'+'ABC'[i],5,[(0,0,2*g['radii'][i]-d+P['pin_clearance'])])
report['exported_hole_sections']=hole_checks
assert np.allclose(np.array(meshes['stl/base.stl']['bounds_mm'])[1]-np.array(meshes['stl/base.stl']['bounds_mm'])[0],
                   [P['base_width'],P['base_depth'],P['base_thickness']],atol=.001)
assert P['collar_bottom_clearance']>=d+.3
assert P['collar_height']+P['collar_bottom_clearance']>=5.5
assert 40>P['base_thickness']+P['collar_height']+P['collar_bottom_clearance']+P['lever_thickness']+2
stages=[]
for i in range(3):
    r=g['radii'][i];former=r-d/2
    previous=[LineString(to_local(s,i)) for s in process_segments()[:2*i]]
    # Full round metal former vs ALL previous wire, not only its final arc.
    former_clear=min((l.distance(Point(0,0))-former-d/2 for l in previous),default=None)
    assert former_clear is None or former_clear>=-.001
    mins={'earlier_wire_to_moving_arc':1e9,'earlier_wire_to_tail':1e9,'fixed_wire_to_pusher':1e9,'other_wire_to_clamp':1e9,'tail_to_incoming_away_from_join':1e9,'pusher_to_clamp':1e9}
    # Real clamp footprint from OpenSCAD STL, convex projected outline. Ignore incoming clamped segment.
    cm=trimesh.load(ROOT/'stl'/f'clamp_{"ABC"[i]}.stl',force='mesh')
    from shapely.geometry import MultiPoint
    clamp=MultiPoint(cm.vertices[:,:2]+[-14,-10]).convex_hull
    for phi in np.linspace(0,180,721):
        fixed,a,tail=motion(i,float(phi));la=LineString(a);lt=LineString(tail);pc=Point(pusher_center(i,float(phi)))
        # At zero angle a has coincident points, so Point is used for distance queries.
        ga=Point(a[0]) if phi==0 else la
        for earlier in previous:
            mins['earlier_wire_to_moving_arc']=min(mins['earlier_wire_to_moving_arc'],earlier.distance(ga)-d)
            mins['earlier_wire_to_tail']=min(mins['earlier_wire_to_tail'],earlier.distance(lt)-d)
            mins['other_wire_to_clamp']=min(mins['other_wire_to_clamp'],earlier.distance(clamp)-d/2)
        mins['fixed_wire_to_pusher']=min(mins['fixed_wire_to_pusher'],LineString(fixed).distance(pc)-(P['pusher_diameter']+d)/2)
        incoming=LineString([fixed[-2],[-r,-2*d]])
        mins['tail_to_incoming_away_from_join']=min(mins['tail_to_incoming_away_from_join'],lt.distance(incoming)-d)
        mins['pusher_to_clamp']=min(mins['pusher_to_clamp'],pc.distance(clamp)-P['pusher_diameter']/2)
        mins['other_wire_to_clamp']=min(mins['other_wire_to_clamp'],lt.distance(clamp)-d/2,ga.distance(clamp)-d/2)
    for k,v in mins.items(): assert v>=-.001,('collision',i,k,v)
    # Compensation sweep through 15 degrees: report the FIRST geometric limit.
    safe=0.;fail=None
    for delta in np.linspace(0,15,301):
        _,a,tail=motion(i,180+float(delta));pc=Point(pusher_center(i,180+float(delta)))
        clearance=min([l.distance(LineString(tail))-d for l in previous]+
                      [l.distance(LineString(a))-d for l in previous]+
                      [LineString(fixed_path(i)).distance(pc)-(P['pusher_diameter']+d)/2,
                       LineString(fixed_path(i)).distance(LineString(tail))-d,
                       LineString(tail).distance(clamp)-d/2])
        if clearance<-.001:fail=float(delta);break
        safe=float(delta)
    stages.append(dict(stage='ABC'[i],samples=721,angle_range_deg=[0,180],former_to_earlier_wire_gap_mm=former_clear,
       minimum_clearance_mm={k:(None if v==1e9 else v) for k,v in mins.items()},
       takeup_deg=takeup(i),last_sampled_safe_compensation_deg=safe,first_collision_compensation_deg=fail,
       notes='0.25 degree ideal inextensible wire steps; pusher vs current bent wire is intentional contact; no material simulation'))
report['motion']=stages
assert P['springback_compensation']<=min(s['last_sampled_safe_compensation_deg'] for s in stages)
report['height_stack_mm']={'wire_top_above_base':d,'collar_bottom_above_base':P['collar_bottom_clearance'],
  'lever_bottom_above_base':P['collar_bottom_clearance']+P['collar_height'],'clamp_top_above_base':5,
  'pusher_tip_above_base':.15,'mandrel_length':40,
  'lever_top_above_table':P['base_thickness']+P['collar_bottom_clearance']+P['collar_height']+P['lever_thickness']}
report['not_verified']=['silver ductility/cracking','springback','paper retention','plastic strength/creep under real load',
  'printer dimensional accuracy','friction/slip','continuous analytic collision proof between sampled states','real material neutral-axis shift']
results_path.write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'geometry':report['geometry'],'motion':stages,'mesh_count':len(meshes),'status':'PASS for stated ideal geometry and mesh checks only'},ensure_ascii=False,indent=2))
