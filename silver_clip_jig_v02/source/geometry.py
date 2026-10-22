"""Millimetres; exact circular centreline, independent of graphics/CAD libraries."""
import json
import math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT / 'source/parameters.json').read_text())

def geometry(p=P):
    d = p['wire_diameter']; a,b,c = [p['bend_radius_'+k] for k in 'ABC']
    assert min(a,b,c) > d/2
    assert abs(2*c+d-p['clip_width']) < 1e-8, 'width = 2 R_C + d'
    assert abs(2*b-2*a-d-p['inner_gap']) < 1e-8, 'inner_gap = 2 R_B - 2 R_A - d'
    yc=p['clip_length']-d/2-c; yb=d/2+b; ya=p['inner_arc_y']; e=p['free_end_y']
    xl=d/2; xr=xl+2*b; xi=xr-2*a
    centers=np.array([[xr-a,ya],[xl+b,yb],[xl+c,yc]])
    pts=np.array([[xi,e],[xi,ya],[xr,ya],[xr,yb],[xl,yb],[xl,yc],[xl+2*c,yc],[xl+2*c,e]])
    lengths=[ya-e,math.pi*a,ya-yb,math.pi*b,yc-yb,math.pi*c,yc-e]
    assert min(lengths)>0
    return dict(centers=centers, points=pts, radii=[a,b,c], lengths=lengths,
                length=sum(lengths), marks=np.cumsum([0]+lengths).tolist())

def line(a,b,n=2):
    return np.linspace(a,b,n)

def arc(c,r,start,end,n=181):
    t=np.linspace(math.radians(start),math.radians(end),n)
    return np.asarray(c)+r*np.column_stack([np.cos(t),np.sin(t)])

def segments(p=P):
    g=geometry(p); v=g['points']; c=g['centers']; r=g['radii']
    return [line(v[0],v[1]),arc(c[0],r[0],180,0),line(v[2],v[3]),
            arc(c[1],r[1],0,-180),line(v[4],v[5]),arc(c[2],r[2],180,0),line(v[6],v[7])]

def final_path(p=P):
    return np.vstack([x if i==0 else x[1:] for i,x in enumerate(segments(p))])

def to_local(points, stage, p=P):
    g=geometry(p)
    return (np.asarray(points)-g['centers'][stage]) * (-1 if stage==1 else 1)

def process_segments(p=P):
    return segments(p)

def fixed_path(stage,p=P):
    # All previously formed material, up to the incoming tangent of current bend.
    return to_local(np.vstack(process_segments(p)[:2*stage+1]),stage,p)

def motion(stage, angle, p=P):
    """Inextensible centreline model. angle in degrees; tail consumes R*angle.

    Input: straight, trimmed blank. Earlier formed material is fixed. No material
    plasticity or springback is simulated. Overbending consumes extra tail length.
    """
    g=geometry(p); r=g['radii'][stage]; phi=math.radians(angle)
    rest=sum(g['lengths'][2*stage+1:])-r*phi
    assert rest>=0
    a=arc([0,0],r,180,180-angle,max(3,int(angle*2)+1))
    t=np.array([math.sin(phi),math.cos(phi)])
    tail=line(a[-1],a[-1]+rest*t,2)
    return fixed_path(stage,p),a,tail

def takeup(stage,p=P):
    r=geometry(p)['radii'][stage]
    q=r+p['wire_diameter']/2+p['pusher_diameter']/2
    return math.degrees(math.acos(q/(q+p['pusher_clearance'])))

def pusher_center(stage,angle,p=P):
    r=geometry(p)['radii'][stage]
    pitch=r+p['wire_diameter']/2+p['pusher_diameter']/2+p['pusher_clearance']
    th=math.radians(180-angle-takeup(stage,p))
    return pitch*np.array([math.cos(th),math.sin(th)])

if __name__=='__main__':
    g=geometry(); print(json.dumps({k:v.tolist() if hasattr(v,'tolist') else v for k,v in g.items()},indent=2))
