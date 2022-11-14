import pgcamera as pg
import gantrycontrol as gc
import time

gantry = gc.gantrycontrol()

# scan in a plane
x_top = 0
y_top = 62000
z_top = 0


x_bot = 130000
y_bot = 40000
z_bot = 67000

nxy  = 20 # step x and y together
nz   = 20

xstep = int( (x_bot - x_top)/nxy)
ystep = int( (y_bot - y_top)/nxy)
zstep = int(z_bot/nz)

# zero the gantry
gantry.locate_home_xyz()
print('done locating home')
# move to the top position
gantry.move_rel( x_top, y_top, z_top )
time.sleep(1) # seconds
print('done moving relative')

curx = x_top
cury = y_top
# scan in z
for i in range( nz ):
    curz = zstep*i
    # scan in xy
    for j in range( nxy ):
        pgc = pg.pgcamera()
        curx += xstep
        cury += ystep
        label = 'scan2_z'+str(curz)+'_y'+str(cury)+'_x'+str(curx)
        print(label)
        pgc.capture_image( '.', label, True )
        gantry.move_rel( xstep, ystep, 0 )
        time.sleep(1)
        del pgc
    gantry.move_rel( 0, 0, zstep )
    # flip sign of the x and y step to step back!
    xstep = -xstep
    ystep = -ystep
    time.sleep(1)

print('Done scan')
del gantry

