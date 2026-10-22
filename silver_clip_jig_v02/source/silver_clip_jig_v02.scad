/* V0.2 engineering trial fixture. mm. Metal formers and pusher, NOT printed.
   Single axis, three interchangeable flush liners. All unused metal pins removed.
   SCAD is the printable source; parameters.scad is generated from parameters.json.
   Geometry/sweep checks and copper/silver testing are mandatory after editing.
   Parts: base, bending_lever, additional_parts, liner_A/B/C, clamp_A/B/C,
          tolerance_coupon, reference, assembly, exploded.
*/
include <parameters.scad>
part="base";
$fn=96;
R=[bend_radius_A,bend_radius_B,bend_radius_C];
D=[for(r=R) 2*r-wire_diameter];
piv=[0,22,44];
lever_bottom=base_thickness+collar_bottom_clearance+collar_height;
assert(abs(2*bend_radius_C+wire_diameter-clip_width)<0.001);
assert(abs(2*bend_radius_B-2*bend_radius_A-wire_diameter-inner_gap)<0.001);
function pitch(i)=R[i]+wire_diameter/2+pusher_diameter/2+pusher_clearance;
function xc(i)=piv[i]+pitch(i);
module plate(w,h,r,t) {
 linear_extrude(t) hull() for(x=[r,w-r],y=[r,h-r]) translate([x,y]) circle(r=r);
}
module bore(x,y,d,z,h) {translate([x,y,z]) cylinder(d=d,h=h);}
module txt(s,x,y,z,size=2,h=.35) {
 translate([x,y,z]) linear_extrude(h) text(s,size=size,font="Liberation Sans",halign="center");
}
module capsule(a,b,r,h,z=0) {
 translate([0,0,z]) linear_extrude(h) hull(){translate(a) circle(r=r);translate(b) circle(r=r);}
}
module ref2d(w=0.18){
 d=wire_diameter; a=R[0];b=R[1];c=R[2];
 ya=inner_arc_y;yb=d/2+b;yc=clip_length-d/2-c; e=free_end_y;
 xr=d/2+2*b;xi=xr-2*a;
 pts=concat([[xi,e],[xi,ya]],
  [for(t=[178:-2:0]) [xr-a+a*cos(t),ya+a*sin(t)]],[[xr,yb]],
  [for(t=[-2:-2:-180]) [d/2+b+b*cos(t),yb+b*sin(t)]],[[d/2,yc]],
  [for(t=[178:-2:0]) [d/2+c+c*cos(t),yc+c*sin(t)]],[[d/2+2*c,e]]);
 for(j=[0:len(pts)-2]) hull(){translate(pts[j]) circle(d=w,$fn=12);translate(pts[j+1]) circle(d=w,$fn=12);}
}
module base(){
 difference(){
  plate(base_width,base_depth,4,base_thickness);
  // Through socket, underside flange seat; liners sit flush and push out downwards.
  bore(axis_x,axis_y,8.2,-.1,base_thickness+.2);
  bore(axis_x,axis_y,12.3,-.1,2.1);
  // M4 clamp, captive nut from underneath. All top hardware must be flush.
  bore(axis_x-14,axis_y-10,4.5,-.1,base_thickness+.2);
  translate([axis_x-14,axis_y-10,-.1]) rotate([0,0,30]) cylinder(d=8.35,h=3.5,$fn=6);
  for(x=[6,base_width-6],y=[6,base_depth-6]) bore(x,y,4.5,-.1,base_thickness+.2);
  // Shallow reference only: never an interference-fit nest.
  translate([76,22,base_thickness-.3]) linear_extrude(.5) ref2d();
  for(x=[75,85]) translate([x,21,base_thickness-.3]) cube([.2,31,.5]);
  for(y=[21,51]) translate([75,y,base_thickness-.3]) cube([10,.2,.5]);
  txt("29 x 8",80,55,base_thickness-.3,2.4,.5);
  txt("A 2.5 / B 4 / C 6",31,65,base_thickness-.3,2.4,.5);
  txt("ONE PIN ONLY",31,60,base_thickness-.3,2.2,.5);
  txt("V0.2  TEST COPPER FIRST",48,4,base_thickness-.3,2.1,.5);
  // Outside-dimension ticks: 29 between horizontal inner edges, 8 between vertical inner edges.
  translate([76,22,base_thickness-.3]) cube([8,.15,.5]);
  translate([76,51,base_thickness-.3]) cube([8,.15,.5]);
  translate([76,22,base_thickness-.3]) cube([.15,29,.5]);
  translate([84,22,base_thickness-.3]) cube([.15,29,.5]);
  // A/B/C incoming tangent alignment ticks. No raised stops in the swept area.
  for(i=[0:2]) translate([axis_x-R[i]-.08,axis_y-6,base_thickness-.25]) cube([.16,3,.4]);
 }
}
module liner(i){
 difference(){
  union(){cylinder(d=12,h=2);translate([0,0,2]) cylinder(d=8,h=base_thickness-2);}
  bore(0,0,D[i]+pin_clearance,-.1,base_thickness+.2);
  txt(str(["A","B","C"][i]),-4,0,0,1.7,.3);
 }
}
module lever(){
 difference(){
  translate([-8,-8,0]) plate(119,16,7.5,lever_thickness);
  for(i=[0:2]){
   bore(piv[i],0,D[i]+pin_clearance,-.1,lever_thickness+.2);
   bore(xc(i),0,pusher_diameter+.12,-.1,lever_thickness+.2);
   // Tap M3, short grub screw holds the pusher at the selected position.
   translate([xc(i),-8.1,lever_thickness/2]) rotate([-90,0,0]) cylinder(d=2.6,h=8.2);
   txt(["A","B","C"][i],piv[i],4,lever_thickness-.35,2.2,.6);
  }
  txt("REMOVE UNUSED PUSHERS",78,1.8,lever_thickness-.35,1.8,.6);
 }
}
module clamp_raw(i){
 // Local origin is the screw. Nose stops only 0.65 mm past incoming wire centre.
 reach=14-R[i]+.65;
 difference(){
  union(){
   hull(){cylinder(r=4,h=5);translate([reach-1.2,0,0]) cylinder(r=1.2,h=5);}
  }
  bore(0,0,4.5,-.1,5.2);
  // 90 degree countersink: radial increase 2.25 over height 2.25.
  translate([0,0,2.85]) cylinder(d1=4.5,d2=9,h=2.25);
  // Toe underside exactly at top of nominal 1 mm wire, with a recessed pad pocket.
  translate([5,-5,-.1]) cube([reach,10,wire_diameter+.1]);
  txt(["A","B","C"][i],reach-4,0,4.65,1.8,.5);
 }
}
module clamp(i){clamp_raw(i);}
module coupon(){
 difference(){
  plate(56,14,2,3);
  for(i=[0:4]){
   bore(6+11*i,7,3+[0,.1,.15,.2,.25][i],-.1,3.2);
   txt(str([0,.1,.15,.2,.25][i]),6+11*i,1.3,2.7,1.5,.5);
  }
 }
}
module clamp_print(i){translate([0,0,5]) rotate([180,0,0]) clamp(i);}
module extra(){
 for(i=[0:2]) translate([8+i*20,8,0]) liner(i);
 for(i=[0:2]) translate([8+i*23,26,0]) clamp_print(i);
 translate([2,38,0]) coupon();
}
module reference(){linear_extrude(wire_diameter,center=true) ref2d(wire_diameter);}
module assembly(explode=0){
 color([.2,.45,.6]) base();
 i=2;
 color([.8,.5,.15]) translate([axis_x,axis_y,explode*12]) liner(i);
 color("silver") bore(axis_x,axis_y,D[i],explode*28,40);
 color("gray") translate([axis_x,axis_y,base_thickness+collar_bottom_clearance+explode*40])
  difference(){cylinder(d=collar_max_diameter,h=collar_height);bore(0,0,D[i],-.1,collar_height+.2);}
 beta=acos((R[i]+wire_diameter/2+pusher_diameter/2)/pitch(i));
 color([.85,.55,.2]) translate([axis_x,axis_y,lever_bottom+explode*65]) rotate([0,0,-beta]) translate([-piv[i],0,0]) lever();
 color([.8,.5,.15]) translate([axis_x-14,axis_y-10,base_thickness+explode*25]) clamp(i);
 color("silver") translate([axis_x,axis_y,0]) rotate([0,0,-beta]) bore(pitch(i),0,pusher_diameter,base_thickness+.15+explode*65,25);
}
if(part=="base") base();
if(part=="bending_lever") lever();
if(part=="additional_parts") extra();
if(part=="tolerance_coupon") coupon();
for(i=[0:2]){
 if(part==str("liner_",["A","B","C"][i])) liner(i);
 if(part==str("clamp_",["A","B","C"][i])) clamp_print(i);
}
if(part=="reference") reference();
if(part=="assembly") assembly();
if(part=="exploded") assembly(1);
