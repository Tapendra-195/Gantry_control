import pgcamera as pg
import gantrycontrol as gc
import time

gantry = gc.gantrycontrol()
pgc = pg.pgcamera()
pgc.print_abilities()

# scan in yz plane
xfix = 80000
ymax = 77000
ny   = 20
zmax = 67000
nz   = 20

ystep = int(ymax/ny)
zstep = int(zmax/nz)

# zero the gantry
gantry.locate_home_xyz()
time.sleep(1)
# move to the xfix position
gantry.move( 100, 0, 0,0,0) # move to 100 mm
#gantry.move_rel( xfix, 0, 0 )
# time.sleep(5) # seconds
'''
# scan in z
for i in range( nz ):
    curz = zstep*i
    # scan in y
    for j in range( ny ):
        cury = ystep*j
        label = 'z'+str(curz)+'_y'+str(cury)
        print(label)
        #pgc.capture_image( '', label, False )
        gantry.move_rel( 0, ystep, 0 )
        time.sleep(1)
    gantry.move_rel( 0, 0, zstep )
    # flip sign of y step to step back!
    ystep = -ystep
    time.sleep(1)
'''
print('Done scan')
del gantry
del pgc
