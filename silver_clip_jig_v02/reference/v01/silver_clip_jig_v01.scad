/*
Silver paper-clip bending fixture V0.1 (concept prototype)
Inspired by William D. Middlebrook US636272A, 1899.
A manual reinterpretation, NOT a dimensional reproduction of the patent machine.

Print BASE and LEVER separately by changing part=...
Use removable SMOOTH METAL dowel pins (not 3D-printed pins).
Test with soft copper before 1.0 mm full-hard 925 silver wire.

Parameters are PROVISIONAL; pin spacing and bending arc require calibration
against a physical reference clip.  This is a manual experimental tool, not
validated manufacturing equipment.
*/
$fn = 72;
part = "base"; // "base" or "lever" or "both_preview"

wire_d = 1.0;
mandrel_d = 3.0;            // smooth round metal mandrel pins, diameter mm
mandrel_hole_d = 3.15;      // tune for your printer, ream if required
pusher_d = 2.0;             // smooth metal bending pin, diameter mm
pusher_hole_d = 2.12;
wire_clearance = 0.14;
station_pitch = 18.0;       // A--B--C, millimeters; tune after test
base_w = 42;
base_h = 80;
base_t = 8;
base_pin_socket_depth = 6.0;
lever_t = 9;

// Spacing between center of stationary mandrel and moving pusher.  Allows
// ~1.14mm between the pins' cylindrical surfaces for the 1mm silver wire.
pusher_pitch = mandrel_d/2 + pusher_d/2 + wire_d + wire_clearance;

module rounded_plate(w,h,r,t){
  linear_extrude(height=t) offset(r=r)
    square([w-2*r,h-2*r], center=true);
}

module base(){
  difference(){
    rounded_plate(base_w,base_h,5,base_t);
    for (i=[-1:1]) {
      y = i*station_pitch;
      translate([0,y,base_t-base_pin_socket_depth])
        cylinder(d=mandrel_hole_d, h=base_pin_socket_depth+0.2);
    }
    // Mark each station.  C / B / A in wire feed direction.
    for (i=[-1:1]) {
      station = i==1 ? "A" : (i==0 ? "B" : "C");
      translate([-12,i*station_pitch-2.1,base_t-0.38])
        linear_extrude(height=0.55) text(station, size=4.5, font="Liberation Sans:style=Bold", halign="center");
    }
    translate([10,-33,base_t-0.35])
      linear_extrude(height=0.5) text("v0.1",size=3,font="Liberation Sans",halign="center");
  }
}

module lever(){
  // Use a metal pusher pin of diameter pusher_d inserted through the second
  // hole. It must protrude below the lever to engage the wire. The lever must
  // be kept parallel to the base and supported by hand during rotation.
  pivot_x = -23;
  difference(){
    linear_extrude(height=lever_t)
      hull(){
        translate([pivot_x,0]) circle(r=7.5);
        translate([27,0]) circle(r=7.5);
      }
    translate([pivot_x,0,-0.1]) cylinder(d=mandrel_hole_d,h=lever_t+0.2);
    translate([pivot_x+pusher_pitch,0,-0.1]) cylinder(d=pusher_hole_d,h=lever_t+0.2);
  }
}

if (part=="base") base();
if (part=="lever") lever();
if (part=="both_preview") {
  base();
  translate([60,0,0]) lever();
}
