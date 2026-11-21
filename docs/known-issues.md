# Known issues

These were found by reading the scripts inside
`Dodge the Meteors - Mugdho.sb3` with `tools/dump_scripts.py` and
`tools/validate_sb3.py`. The game is a single Scratch file, so each fix is
made in the Scratch editor: open the .sb3 file, change the scripts, and save
it back. Text tools cannot edit the .sb3 file, it is a zip archive.

## 1. A stray script drags the spaceship down

The Rocketship sprite has two scripts that run when the green flag is
clicked. The first one sets the ship up correctly: score to 0, Lives to 3,
Speed to 5, and go to (0, -140). The second one teleports the ship to a
random x position at y 170, then runs forever changing y by -5.

Effect: the ship starts at the top of the stage instead of the bottom, and
it sinks constantly, so the player has to hold the up arrow just to stay
in place.

Fix: delete the second script on the Rocketship (the one that starts with
"go to random x, 170" and "forever change y by -5"). The movement script
already controls the ship.

## 2. The left and right bounds only work while up and down are held

In the Rocketship movement script, the two "if x position > 220, set x to
220" and "if x position < -220, set x to -220" blocks sit inside the
"if down arrow pressed" block, which itself sits inside the "if up arrow
pressed" block. They are not steps of the forever loop, they are nested
inside the arrow key branches.

Effect: the ship can fly off the left and right edges of the stage. The
bounds only apply on frames where the player holds up and down at the
same time.

Fix: drag both "if x position" blocks out of the arrow key branches and
drop them into the forever loop, after the four movement blocks, so they
run on every frame.

## 3. There is no top or bottom bound at all

The movement script clamps x to -220..220 but never clamps y. Nothing
stops the ship from flying off the top or bottom of the stage.

Fix: add two blocks to the forever loop, after the x bounds: "if y
position > 160, set y to 160" and "if y position < -160, set y to -160".
160 matches the x margin: the stage is 480 by 360, so 240 - 20 is 220
for x and 180 - 20 is 160 for y.

## 4. The variable "my variable" is never used

The Stage declares a variable called "my variable" with value 0, and no
block in the project reads or changes it. `tools/validate_sb3.py` reports
it as a finding.

Fix: delete it from the Variables panel in the Scratch editor.

## 5. No sound is ever played

The project ships five sounds, and no block plays any of them: "pop" on
the Stage, "Space Ripple", "Laser1" and "Laser2" on the Rocketship, and
"Pop" on the Meteor. `tools/validate_sb3.py` reports all five as
findings.

Fix: either play the Meteor "Pop" sound when a meteor hits the ship (add
a "play sound Pop" block in the collision branch, before "change Lives
by -1"), or delete the sounds that are not needed.

## Note: the Stage checks Lives only once every 10 seconds

The Stage script waits 10 seconds, raises Speed by 1, and only then
checks whether Lives is 0. That check is harmless but redundant: the
Meteor script already switches to the Game Over backdrop and stops the
game the moment Lives drops below 1. Nothing needs to change here, it is
only worth knowing when reading the scripts.
