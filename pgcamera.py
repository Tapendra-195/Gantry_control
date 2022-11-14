'''

pgcamera.py

pgcamera class to help with photo collection from multiple cameras.

Blair Jamieson

Oct. 2022

'''


import gphoto2 as gp
import time
import os
import subprocess
import sys

class pgcamera:

    def __init__( self, camerafile='pgcamera_cameras.txt', buildcamerafile=False, setcamno=-1 ):
        """
        Setup camera control object to keep track of all
        cameras available, or just use ones in a list in a textfile.

        If buildcamerafile is True then the list_of_cameras_file
        is overwritten with the list of cameras found.

        If buildcamerafile is False then try to find all the
        cameras in the file.

        setcamno is the camera number to use from startup
        """
        try:
            self.camera = gp.Camera()
            self.cameras_dict = {}  # ser_no : camera_no
            self.sernos_dict = {} # camera_no : ser_no
            self.camvitals = []        # Build list of lists holding camera vitals
            # Each entry in camvitals will have [serno, camno, addr, camname ]
            # These will be sorted by serno
            self.port_info_list = gp.PortInfoList()
            self.port_info_list.load()
            self.abilities_list = gp.CameraAbilitiesList()
            self.abilities_list.load()
            self.camera_list = self.abilities_list.detect( self.port_info_list )

            if buildcamerafile == False:
                self.read_list_of_cameras( camerafile )

            for i,cam in enumerate( self.camera_list ):
                print(i,cam)
                addr = cam[1]
                iport  = self.port_info_list.lookup_path( addr )
                self.camera.set_port_info( self.port_info_list[ iport ] )
                time.sleep(0.5)
                iab    = self.abilities_list.lookup_model( cam[0] )
                self.camera.set_abilities( self.abilities_list[ iab ] )
                time.sleep(0.5)
                settings_list = self.camera.get_summary().text.split( '\n' )
                ser_no = settings_list[3].strip().split(' ')[2]

                # we have camno, and serno (all stored as strings
                # print(buildcamerafile)
                if buildcamerafile:
                    self.camvitals.append( [ser_no, str(i), addr, cam[0] ] )
                else:
                    camno = self.get_camera_no( ser_no )
                    if camno != None:
                        self.camvitals.append( [ser_no, camno, addr, cam[0]] )

            sorted( self.camvitals, key=lambda x : x[0] ) # sort on ser_no

            if buildcamerafile:
                f=open( camerafile, 'w' )
                # reassign camno in order of serno, and build dictionaries
                for i,camvital in enumerate( self.camvitals ):
                    camvital[ 1 ] = str(i)
                    self.cameras_dict[ camvital[0] ] = camvital[1]
                    self.sernos_dict[ camvital[1] ] = camvital[0]
                    f.write( camvital[1]+' '+camvital[0]+'\n')
                f.close()

            self.print_camera_list()

            # set camera to first one
            if setcamno == -1:
                setcamno = self.camvitals[0][1]
            self.set_camera( setcamno )
            self.camera.init()
            print('Connected to camera',setcamno)

        except :
            print('Error in intializing pgcamera object')
            print( sys.exc_info()[0] )
            sys.exit(0)


    def __del__(self):
        print('Disconnecting from camera')
        self.camera.exit()

    def print_camera_list(self):
        for vital in self.camvitals:
            print('Camera',vital[1],': Serial number:',vital[0],' Address:',vital[2],' Type:',vital[3])


    def get_camera_port(self,camera_no):
        for vital in self.camvitals:
            if int(vital[1]) == int(camera_no):
                return vital[2]
        return ''


    def get_camera_ports(self):
        '''
        return a dictionary of port : camera_no
        Make port of form XXX/YYY (ie. strip usb: and replace comma with /)
        '''
        retval = {}
        for vital in self.camvitals:
            port = vital[2][4:].replace(',','/')
            retval[ port ] = vital[1]
        return retval


    def read_list_of_cameras( self, fname ):
        '''
        Looks for file fname which holds the mapping between serial number
        and camera number that can be written by the __init__ function.

        Note that since the usb port numbers can change, those aren't
        stored, but are refound each time.
        '''
        try:
            self.cameras_dict = {}  # build dictionary camera_dict[ serno ] = camno
            self.sernos_dict = {}    # build dictionary sernos_dict[ camno ] = serno
            f=open(fname,'r')
            lines = f.readlines()
            retval = '-1'
            for line in lines:
                curcam, curserno = line.split(' ')
                curserno = curserno.strip('\n')
                self.cameras_dict[ curserno ] = curcam
                self.sernos_dict[ curcam ] = curserno
            f.close()
        except:
            print('read_list_of_cameras failed')



    def get_camera_serno( self ):
        '''
           Returns the camera serial number for the camera being referred to
           by the camera object.
        '''
        settings_list = self.camera.get_summary().text.split( '\n' )
        ser_no = settings_list[3].strip().split(' ')[2]
        return ser_no


    def get_camera_no( self, serno ):
        '''
            Assumes the dictionaries are already generated in __init__

            Returns the camera number, or -1 if it isn't found
        '''
        try:
            camno = self.cameras_dict[ serno ]
            return camno # otherwise return none
        except:
            print('get_camera_no(',serno,'), error.')
            return -1

    def get_camvital_idx( self, camera_no ):
        camera_no = int(camera_no)
        idx=0
        for i,icam in enumerate(self.camvitals):
            if int( icam[1] ) == camera_no:
                idx = i
                break
        return idx


    def set_camera( self, camera_no ):
        '''
        Sets the camera object to be referring to the camera with
        camera number.
        Returns True if it succeeds and False if it fails.
        '''
        try:
            camera_no = int(camera_no)
            idx   = self.get_camvital_idx( camera_no )
            if idx >= len(self.camvitals):
                 print('Index out of range')
                 return False
            #resetport = self.camvitals[idx][2][4:].replace(',','/')
            #print('>usbreset',resetport)

            addr = self.camvitals[ idx ][2]
            iport  = self.port_info_list.lookup_path(addr)
            print(self.camvitals[idx])
            self.camera.set_port_info( self.port_info_list[ iport ] )
            #time.sleep(0.5) # sleep 1/2 second
            iab    = self.abilities_list.lookup_model( self.camvitals[ idx ][3] )
            #time.sleep(0.5) # sleep 1/2 second
            self.camera.set_abilities( self.abilities_list[ iab ] )
            #time.sleep(0.5) # sleep 1/2 second
            print('Camera set to number:',camera_no)

            return True

        except:
            print('Set_camera camera_no:',camera_no,' error!')
            print( sys.exc_info()[0] )
            return False


    def print_abilities( self ):
        '''
        Prints the camera settings, aka abilities of currently set
        camera.  Ignore generic unamed properties.
        '''
        try:
            settings_list = self.camera.get_summary().text.split( '\n' )
            for settings in settings_list[:5]:
                print(settings)
            for settings in settings_list[17:]:
                setlist = settings.split('(')
                setname = setlist[0].strip(': ()')
                setlist = settings.split(' ')
                setvalue = setlist[-1].strip(' ()')
                # skip generic unamed properties
                if setname.split(' ')[0] != 'Property' and setname != '':
                    print(setname+', value: '+setvalue)

        except:
            print('print_abilities error!')
            print( sys.exc_info()[0] )
            return False

    def capture_abilities( self, outfilename ):
        '''
        outfilename: textfile name into which the
        settings will be stored.

        Saves the camera settings, aka abilities into outfilename.
        Ignore generic unamed properties.
        '''
        try:
            f = open(outfilename,'w')

            settings_list = self.camera.get_summary().text.split( '\n' )
            #time.sleep(0.5) # sleep 1/2 second

            # print first few lines as is
            for settings in settings_list[:5]:
                f.write(settings+'\n')
            for settings in settings_list[17:]:
                setlist = settings.split('(')
                setname = setlist[0].strip(': ()')
                setlist = settings.split(' ')
                setvalue = setlist[-1].strip(' ()')
                # skip generic unamed properties
                if setname.split(' ')[0] != 'Property' and setname != '':
                    f.write(setname+', value: '+setvalue+'\n')

            f.close()
        except:
            print('capture_abilities error file:',outfilename,' not complete.')
            print( sys.exc_info()[0] )


    def capture_image( self , dir='', label='img', append_date=True ):
        '''
        Takes a photo from the currently selected camera and saves it as filename:
        'dir/c<num>_'+label[+date].jpg'

        Stores the camera settings in:
        'dir/c<unm>_'+label[+date].txt'
        '''
        try:
            serno = self.get_camera_serno(  )
            camno = self.get_camera_no( serno )

            print('camno=',camno,'serno=',serno)
            if int(camno) < 0:
                print('capture_image error, unknown camera nubmer')
                return
            imgname = dir+'/'
            if dir == '':
                imgname = '';
            imgname = imgname + 'c' + str(camno) + '_' + label
            if append_date:
                imgname = imgname + time.strftime('%Y%m%d-%H:%M:%S%Z')
            metaname = imgname + '.txt'
            imgname = imgname + '.jpg'
            cfg = self.camera.get_config()
            capturetarget_cfg = cfg.get_child_by_name('capturetarget')
            capturetarget = capturetarget_cfg.get_value()
            capturetarget_cfg.set_value('Internal RAM')
            self.camera.set_config(cfg)
            time.sleep(1)
            print('Capture image!')
            #evtype, evdata = self.camera.wait_for_event( 10000 )#########*****
            #self.camera.wait_for_event( 10000 )
            port = self.get_camera_port( camno )
            command = ['gphoto2',
                       '--wait-event=7s',
                       '--capture-image-and-download',
                       '--port='+port,
                       '--filename='+imgname ]
            print(command)
            self.camera.exit()
            subprocess.run( command )
            print('Done collecting image')
            self.camera = gp.Camera()

            #file_path = self.camera.capture( gp.GP_CAPTURE_IMAGE )
            #file_path = self.camera.capture( gp.GP_OPERATION_CAPTURE_PREVIEW )
            #time.sleep(1) # sleep 1 second
            #print('Copying image to',imgname)
            #camera_file = self.camera.file_get( file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
            #time.sleep(0.5) # sleep 1/2 second
            #camera_file.save( imgname )
            #self.camera.file_delete( file_path.folder, file_path.name )
            print('Copying done.')
            self.capture_abilities( metaname )
            print('Metadata saved to: ',metaname)
            capturetarget_cfg.set_value(capturetarget)
            self.camera.set_config(cfg)

        except gp.GPhoto2Error as ex:
            print('capture_image error!')
            print(str(ex))

