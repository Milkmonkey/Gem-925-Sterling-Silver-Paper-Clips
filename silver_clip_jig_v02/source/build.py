"""Rebuild OpenSCAD parts, exact reference sweep, engineering drawings and previews."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/silver-clip-matplotlib')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/silver-clip-cache')
import json, math, subprocess, sys
from pathlib import Path
import numpy as np
from geometry import P, ROOT, geometry, final_path, segments, motion, takeup, to_local

PARTS=['base','bending_lever','additional_parts','liner_A','liner_B','liner_C',
       'clamp_A','clamp_B','clamp_C','tolerance_coupon']

def scad():
    (ROOT/'source/parameters.scad').write_text('// Generated from parameters.json by build.py. Edit the JSON, then rebuild.\n'+
       '\n'.join(f'{k} = {json.dumps(v)};' for k,v in P.items())+'\n')
    for part in PARTS:
        cmd=['openscad','-o',str(ROOT/'stl'/f'{part}.stl'),'-D',f'part="{part}"',str(ROOT/'source/silver_clip_jig_v02.scad')]
        r=subprocess.run(cmd,capture_output=True,text=True)
        (ROOT/'validation'/f'openscad_{part}.log').write_text(r.stdout+r.stderr)
        if r.returncode or 'ERROR:' in r.stderr or 'WARNING:' in r.stderr:
            raise RuntimeError(f'{part}: {r.stdout}\n{r.stderr}')
        print('STL',part,flush=True)

def reference():
    import cadquery as cq
    g=geometry();v=g['points'];cs=g['centers'];rs=g['radii'];z=P['wire_diameter']/2
    path=cq.Workplane('XY',origin=(0,0,z)).moveTo(*v[0]).lineTo(*v[1])
    for i in range(3):
        mid=cs[i]+[0,rs[i]*(1 if i!=1 else -1)]
        path=path.threePointArc(tuple(mid),tuple(v[2+2*i])).lineTo(*v[3+2*i])
    wire=cq.Workplane('XZ',origin=(v[0,0],v[0,1],z)).circle(z).sweep(path,isFrenet=False)
    assert wire.val().isValid() and len(wire.solids().vals())==1
    cq.exporters.export(wire,str(ROOT/'reference/gem_clip_reference.stl'),tolerance=.015,angularTolerance=.08)
    cq.exporters.export(wire,str(ROOT/'reference/gem_clip_reference.step'))
    (ROOT/'validation/reference_brep.json').write_text(json.dumps(dict(valid=wire.val().isValid(),solids=len(wire.solids().vals()),
       volume_mm3=wire.val().Volume(),bounding_box_mm=[wire.val().BoundingBox().xlen,wire.val().BoundingBox().ylen,wire.val().BoundingBox().zlen]),indent=2))
    print('Exact reference sweep exported',flush=True)

def setup_plot():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    fp=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    plt.rcParams.update({'font.family':fp.get_name(),'font.size':10,'axes.unicode_minus':False,
                         'svg.fonttype':'path','savefig.facecolor':'white'})
    return plt

def drawings():
    plt=setup_plot();g=geometry();path=final_path();d=P['wire_diameter'];colors=['#258ca8','#d68a24','#9472b2']
    fig,(ax,info)=plt.subplots(1,2,figsize=(12,10),gridspec_kw={'width_ratios':[1.3,1]})
    info.axis('off')
    for i,s in enumerate(segments()):
        ax.plot(s[:,0],s[:,1],lw=10,color='#bcc5cb',solid_capstyle='round')
        ax.plot(s[:,0],s[:,1],lw=1,color='#33434f',ls='--')
    for i,(c,r) in enumerate(zip(g['centers'],g['radii'])):
        ax.scatter(*c,marker='+',s=60,color=colors[i]);ax.annotate('ABC'[i],c,
              xytext=(6,2),textcoords='offset points',color=colors[i],fontsize=11)
    for i,j in [(0,1),(2,3),(4,5),(6,7)]:
        a,b=g['points'][[i,j]];xx=([-2.8,10,-1,12][i//2])
        ax.annotate('',(xx,a[1]),(xx,b[1]),arrowprops={'arrowstyle':'<->','color':'#637783'})
        ax.text(xx+.2,(a[1]+b[1])/2,f'S{i//2} = {abs(b[1]-a[1]):.2f}',fontsize=9)
    ax.annotate('',(-5,0),(-5,P['clip_length']),arrowprops={'arrowstyle':'<->'})
    ax.text(-5.8,14.5,'29.00 外形长度',rotation=90,va='center')
    ax.annotate('',(0,31),(P['clip_width'],31),arrowprops={'arrowstyle':'<->'})
    ax.text(4,31.5,'8.00 外形宽度',ha='center')
    for v,lab in [(g['points'][0],'起点 P0'),(g['points'][-1],'终点 P7')]:
        ax.scatter(*v,s=28,color='#a23f44');ax.annotate(lab,v,xytext=(0,-18),textcoords='offset points',ha='center')
    text='中心线几何 / mm\n\n'
    for i,(c,r) in enumerate(zip(g['centers'],g['radii'])):
        text+=f'{"ABC"[i]}   R {r:.2f}   中心 ({c[0]:.2f}, {c[1]:.2f})\n'
    text+=f'\n线径 {d:.2f}\n理论展开 {g["length"]:.3f}\n左侧净隙 {P["inner_gap"]:.2f}\n右侧净隙 {2*(P["bend_radius_C"]-P["bend_radius_B"])-d:.2f}\n\n所有圆弧均为 180°\n图中虚线：中心线路径\n\n展开坐标（自修平起点计）：\n'
    text+='\n'.join(f'P{i}: {s:.3f}' for i,s in enumerate(g['marks']))
    text+='\n\n初始工程几何；未实物校准。\n几何长度并非已校准的生产下料长度。'
    info.text(.02,.94,text,va='top',fontsize=10,linespacing=1.6)
    ax.set(aspect='equal',xlim=(-7,14),ylim=(-2,34),xlabel='X / mm',ylabel='Y / mm')
    ax.set_title('Gem V0.2 — 参数化中心线尺寸图',fontsize=17,pad=18);ax.grid(alpha=.15)
    fig.tight_layout();fig.savefig(ROOT/'reference/gem_clip_dimensions.png',dpi=180);fig.savefig(ROOT/'reference/gem_clip_reference.svg');plt.close(fig)
    # Pure 1:1 centreline SVG with explicit mm units, separate from annotated drawing.
    pts=' '.join(f'{x:.5f},{P["clip_length"]-y:.5f}' for x,y in path)
    w,h=P['clip_width'],P['clip_length']
    (ROOT/'reference/gem_clip_centerline_1to1.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}"><polyline points="{pts}" fill="none" stroke="#333" stroke-width="{d}" stroke-linecap="butt"/></svg>')
    fig,axs=plt.subplots(3,4,figsize=(15,15))
    for i in range(3):
        for j,phi in enumerate([0,90,180,180]):
            ax=axs[i,j];fixed,a,t=motion(i,phi)
            ax.plot(fixed[:,0],fixed[:,1],lw=2.3,color='#385f79')
            ax.plot(a[:,0],a[:,1],lw=2.3,color=colors[i]);ax.plot(t[:,0],t[:,1],lw=2.3,color='#d68a24')
            ax.add_patch(plt.Circle((0,0),g['radii'][i]-.5,color='#87969e',alpha=.7))
            # Show pusher where it first contacts the tangent, with 0.1 mm radial play.
            from geometry import pusher_center
            pc=pusher_center(i,phi)
            ax.add_patch(plt.Circle(pc,1.5,color='#ab5950'))
            ax.plot([-g['radii'][i]-.3]*2,[-14,-6],lw=4,color='#47a59b',alpha=.6)
            ax.annotate('',(8,5),(3,10),arrowprops={'arrowstyle':'->','color':'#ab5950','connectionstyle':'arc3,rad=-.4'})
            ax.set_title(f'{"ABC"[i]} — 弯曲 {phi}° / 杆转 {phi+takeup(i):.1f}°'+('（局部）' if j==3 else ''),fontsize=10)
            ax.set(aspect='equal',xlim=((-10,12) if j==3 else [(-12,85),(-12,65),(-12,40)][i]),
                   ylim=([(-16,9),(-26,9),(-26,9)][i] if j==3 else [(-85,85),(-60,65),(-30,36)][i]));ax.grid(alpha=.12)
            if j==0: ax.set_ylabel(f'工序 {"ABC"[i]} / mm')
    fig.suptitle('从直线坯料到 Gem：A → B → C；已弯部分夹住，余料顺时针绕弯\n蓝：已成形固定段  橙：未成形余料  灰：金属轴  红：压弯销  绿：夹持段\n理想无回弹、中心线不伸长模型；不表示银丝已经试制通过',fontsize=14,y=.995)
    fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(ROOT/'renders/bending_sequence.png',dpi=170);plt.close(fig)
    for i in range(3):
        from geometry import fixed_path
        x,y=P['axis_x'],P['axis_y'];w,h=P['base_width'],P['base_depth'];r=g['radii'][i]
        pts=' '.join(f'{x+u:.4f},{h-y-v:.4f}' for u,v in fixed_path(i))
        body=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">
<rect x="0.3" y="0.3" width="{w-.6}" height="{h-.6}" fill="white" stroke="#aaa" stroke-width="0.15"/>
<g fill="none" stroke="#555" stroke-width="0.15"><circle cx="{x}" cy="{h-y}" r="{r-P['wire_diameter']/2}"/>
<path d="M{x-5},{h-y}H{x+5}M{x},{h-y-5}V{h-y+5}"/></g>
<polyline points="{pts}" fill="none" stroke="#387a9d" stroke-width="{P['wire_diameter']}"/>
<path d="M{x-r},{h-y}V0" stroke="#e69931" stroke-width="0.2" stroke-dasharray="1,1"/>
<circle cx="{x-14}" cy="{h-y+10}" r="2.25" fill="none" stroke="#4d9689" stroke-width="0.2"/>
<g font-family="sans-serif" font-size="2.5" fill="#333"><text x="3" y="6">SETUP {"ABC"[i]}: 1:1 mm. No print scaling.</text>
<text x="3" y="11">Axis ({x}, {y}); wire X=axis-{r}; tangent Y=axis.</text>
<text x="3" y="{h-5}">Blue: formed wire. Orange: straight tail continues.</text></g></svg>'''
        (ROOT/'reference'/f'setup_{"ABC"[i]}.svg').write_text(body)

def scenes():
    # True per-pixel depth buffer over the actual STL triangles; no X/OpenGL server.
    import trimesh
    plt=setup_plot()
    def rasterize(tr,fc):
        from PIL import Image
        az=math.radians(-63);el=math.radians(32)
        camera=np.array([math.cos(az)*math.cos(el),math.sin(az)*math.cos(el),math.sin(el)])
        right=np.array([-math.sin(az),math.cos(az),0.]);up=np.cross(camera,right)
        q=tr@np.array([right,up,camera]).T
        low=q[:,:,:2].min(axis=(0,1));high=q[:,:,:2].max(axis=(0,1))
        width,height=1800,1300;scale=min((width-100)/(high[0]-low[0]),(height-100)/(high[1]-low[1]))
        q[:,:,0]=(q[:,:,0]-(low[0]+high[0])/2)*scale+width/2
        q[:,:,1]=height/2-(q[:,:,1]-(low[1]+high[1])/2)*scale
        zbuf=np.full((height,width),-np.inf);pixels=np.full((height,width,3),250,dtype=np.uint8)
        for t,col in zip(q,fc):
            x0,y0=np.maximum(np.floor(t[:,:2].min(axis=0)).astype(int),0)
            x1,y1=np.minimum(np.ceil(t[:,:2].max(axis=0)).astype(int),[width-1,height-1])
            if x1<x0 or y1<y0: continue
            den=(t[1,1]-t[2,1])*(t[0,0]-t[2,0])+(t[2,0]-t[1,0])*(t[0,1]-t[2,1])
            if abs(den)<1e-9: continue
            xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
            a=((t[1,1]-t[2,1])*(xx-t[2,0])+(t[2,0]-t[1,0])*(yy-t[2,1]))/den
            b=((t[2,1]-t[0,1])*(xx-t[2,0])+(t[0,0]-t[2,0])*(yy-t[2,1]))/den
            c=1-a-b;zz=a*t[0,2]+b*t[1,2]+c*t[2,2]
            target=zbuf[y0:y1+1,x0:x1+1];inside=(a>=-1e-8)&(b>=-1e-8)&(c>=-1e-8)&(zz>target)
            target[inside]=zz[inside];pixels[y0:y1+1,x0:x1+1][inside]=np.clip(np.asarray(col)*255,0,255).astype(np.uint8)
        return Image.fromarray(pixels).resize((1350,975),Image.Resampling.LANCZOS)
    for explode,name in [(False,'assembly'),(True,'exploded_view')]:
        triangles=[];facecolors=[]
        def add(mesh,col,offset=(0,0,0)):
            m=mesh.copy();m.apply_translation(offset)
            triangles.append(m.triangles)
            light=np.array([-.35,-.5,1]);light/=np.linalg.norm(light)
            shade=.55+.45*np.abs(m.face_normals@light)
            facecolors.append(np.asarray(col)[None,:]*shade[:,None])
        load=lambda n:trimesh.load(ROOT/'stl'/f'{n}.stl',force='mesh')
        x,y=P['axis_x'],P['axis_y'];z=P['base_thickness'];extra=35 if explode else 0
        add(load('base'),(.18,.40,.51))
        add(load('liner_C'),(.92,.65,.25),(x,y,extra))
        steel=(.65,.69,.72)
        add(trimesh.creation.cylinder(radius=3,height=40,sections=96),steel,(x,y,20+extra*2))
        # Collar geometry shown as annular solid, never a printed substitute.
        import cadquery as cq
        collar=cq.Workplane('XY').circle(7).circle(3).extrude(8)
        cq.exporters.export(collar,'/tmp/clip-collar.stl')
        add(trimesh.load('/tmp/clip-collar.stl',force='mesh'),steel,(x,y,z+1.5+extra*3))
        lever=load('bending_lever');lever.apply_translation([-44,0,0])
        th=math.radians(-takeup(2));rot=trimesh.transformations.rotation_matrix(th,[0,0,1]);lever.apply_transform(rot)
        add(lever,(.94,.61,.20),(x,y,z+9.5+extra*4))
        pitch=3.5+.5+1.5+.1
        add(trimesh.creation.cylinder(radius=1.5,height=25,sections=64),steel,
            (x+pitch*math.cos(th),y+pitch*math.sin(th),z+.15+12.5+extra*4))
        clamp=load('clamp_C');clamp.apply_translation([0,0,-5]);clamp.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0]))
        add(clamp,(.92,.65,.25),(x-14,y-10,z+extra*1.5))
        add(trimesh.creation.cylinder(radius=2,height=14,sections=32),steel,(x-14,y-10,z-4.4+extra*1.5))
        # Actual 90-degree M4 flat head; top slightly recessed in printed countersink.
        head=cq.Solid.makeCone(2,4,2)
        cq.exporters.export(head,'/tmp/clip-screw-head.stl')
        add(trimesh.load('/tmp/clip-screw-head.stl',force='mesh'),steel,(x-14,y-10,z+2.6+extra*1.5))
        wire=trimesh.load(ROOT/'reference/gem_clip_reference.stl',force='mesh')
        c=geometry()['centers'][2]
        add(wire,(.90,.92,.94),(x-c[0],y-c[1],z+extra*.8))
        tr=np.concatenate(triangles);fc=np.concatenate(facecolors)
        rasterize(tr,fc).save(ROOT/'renders'/f'{name}.png')
        print('render',name,flush=True)
    plt=setup_plot();from PIL import Image
    for name,title,note in [('assembly','V0.2 单轴换销工装 — 最后一道 C 工序','蓝：底座  橙：打印杆 / 夹块  灰：金属销及限位环  白：银丝参考\n金属件示意；夹持螺钉采用齐平沉头，底座固定在平整牺牲木板上'),('exploded_view','V0.2 爆炸示意 — 按高度分离','从下到上：底座及衬套 → 夹块 / 银丝 → 金属轴 → 金属限位环 → 压弯杆及压弯销\n只装当前工序所需的一根轴和一根压弯销；其余轴、压弯销全部拔下')]:
        im=Image.open(ROOT/'renders'/f'{name}.png');fig,ax=plt.subplots(figsize=(12,10));ax.imshow(im);ax.axis('off');ax.set_title(title,fontsize=18);fig.text(.5,.035,note,ha='center',fontsize=11);fig.tight_layout(rect=[0,.07,1,1]);fig.savefig(ROOT/'renders'/f'{name}.png',dpi=150);plt.close(fig)

if __name__=='__main__':
    tasks=sys.argv[1:] or ['scad','reference','drawings','scenes']
    for t in tasks: globals()[t]()
