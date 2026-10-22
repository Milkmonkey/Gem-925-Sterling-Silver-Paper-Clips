Silver paper-clip bending fixture V0.1 — UNTESTED CONCEPT / first prototype

Purpose:
Manual experimental reinterpretation of the staged bending concept in
William D. Middlebrook US636272A (1899); not a faithful reconstruction.
For 1 mm 925 silver wire (use copper first).  The original patent makes a
classic Gem wire clip, not the triangular Deli 0051 type.

STL:
  silver_clip_base_v01.stl  base 42 x 80 x 8 mm
  silver_clip_lever_v01.stl turning lever ~65 x 15 x 9 mm
SCAD editable parametric source:
  silver_clip_jig_v01.scad

Hardware (NOT included in print):
  Three SMOOTH metal pins diameter 3.0 mm, length >= 20 mm
  One SMOOTH metal push-pin diameter 2.0 mm, length >= 12 mm
  (Avoid threaded screws contacting the silver: they can mar its surface.)

Base uses blind sockets nominally 3.15 mm diameter / 6 mm depth.
Metal pins remain removable; the A and B formers must be removable before
later stages.  Adjust hole size in SCAD according to printed tolerance;
light hand reaming with a 3 mm drill is an option if holes print too small.

Lever through hole at pivot diameter 3.15 mm; pusher hole 2.12 mm.
At the lever use the 2 mm metal push pin, extending approx 2-3 mm under
the underside of the lever, so it can contact the wire on the base.
For rotation, hold lever 2-3 mm above the base around the mandrel pin.
A ~20 mm main mandrel pin should protrude adequately above the base.

Suggested PETG printing: 0.2 mm layers; 4-6 walls; 40-60% infill.
Print base flat and lever flat.  A printing company can assist.

IMPORTANT:
  - Prototype station pitch A-B=B-C is 18 mm, not derived from a scale
    drawing or measured reference clip.  This is NOT a validated 29 mm
    finished paper-clip mold.  Measure a reference clip and iterate.
  - The original mechanism additionally uses moving clamps/jaws and
    retracting winders.  This fixture alone does not automate all bends.
  - Full-hard 925 silver may crack at tight radius even with steel pins.
    Test a short wire sample around one mandrel before a full clip.
  - The bending arm is a small manually held prototype.  Never use it as a
    lever for heavy loads; watch for plastic cracking or metal pin pull-out.
  - First prototype with cheap 1 mm copper wire; verify geometry, bend
    sequence, removal of pins, and final clamp strength using the actual
    silver before manufacturing 10 pieces.
  - Use safety glasses; cut wire and pins may have sharp ends.

Reference: https://patents.google.com/patent/US636272A/en
