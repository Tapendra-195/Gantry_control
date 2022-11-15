import sys
import string
import gclib
import time





class gantrycontrol:
  """
  gantrycontrol is a class to control the gantry motion in 0RC39.

  It assumes the last saved position in 'fname' passed to the class is correct.
  If it isn't you can call

  Usage:

  > import gantrylib as gl           # import the code
  > gantry = gl.gantrycontrol()      # build the gantry control instance
  > gantry.print_position()          # print current position
  > gantry.move_xyz_rel( 1000, 0, 0 )    # move the gantry in x by 1000 steps from the origin
  > gantry.move_xyz_rel( 0, 1000, 0 )    # move the gantry in y by 1000 steps from the origin
  > gantry.move_xyz_rel( 0, 0, 1000 )    # move the gantry in z by 1000 steps from the origin
  > gantry.locate_home_xyz()         # jog the gantry to home (0,0,0)
  > del gantry                       # done using gantry, delete object (closes connections)
  """

  def __init__(self, fname='galil_last_position.txt'):
    self.g = gclib.py() #make an instance of the gclib python class
    self.c = self.g.GCommand #alias the command callable
    self.file_galilpos = fname

    print('gclib version:', self.g.GVersion())
    self.g.GOpen('192.168.42.10 -s ALL')
    print( self.g.GInfo() )
    self.load_position( ) # assume we are at last saved position

    print('Enable motors')
    self.c('SH') #Enable the motor

    print('Set smoothing on theta,phi axes')
    self.c('KS ,,,25,25')

    print(' done.')


  def __del__(self):
    '''
    Destructor saves position and closes connection
    '''
    self.g.GClose()


  def print_position(self,message='Positon: '):
    '''
      print position of gantry
    '''
    print( message + self.c('PA ?,?,?,?,?') )

  def save_position(self):
    '''
    Read the current position from the galil and save it to file.
    '''
    res = self.c('PA ?,?,?,?,?')
    print(self.file_galilpos)
    f = open(self.file_galilpos,'w')
    f.write(res)
    f.close()
    print('wrote (x,y,z,phi,theta) to galil_last_position.txt: ',res)

  def load_position(self):
    '''
    Load position from file
    '''
    f = open(self.file_galilpos,'r')
    res = f.readline()
    command = 'DP '+res
    print('Loading position with command =',command)
    self.c(command)


  def locate_home_xyz(self):
    '''
      Jogs the gantry until it hits the limit switches.
      Defines that as 0,0,0 in xyz
      Writes the position to file
    '''
    try:
      self.print_position('before homing: ')
      '''
      Checking limit switch status _LRA variable contains limit switch status of reverse limit switch in axis  A.
      If the limit switch is already activated  that axis is already at home so we don't want to move it.
      '''

      RLA_status = float(self.c('MG _LRA'))==1.0 #1 means limit switch not activated
      RLB_status = float(self.c('MG _LRB'))==1.0
      RLC_status = float(self.c('MG _LRC'))==1.0
      print('abc status = ',RLA_status,RLB_status , RLC_status )
      x_speed = -1000 if RLA_status else 0
      y_speed = -1000 if RLB_status else 0
      z_speed = -1000 if RLC_status else 0
      print('speed = ',x_speed, y_speed, z_speed)
      command = 'JG %g,%g,%g,%g,%g'% (x_speed, y_speed, z_speed, 0, 0)
      self.c(command)
      axes = ''
      axes = 'A' if RLA_status else axes
      axes = axes+'B' if RLB_status else axes
      axes = axes+'C' if RLC_status else axes
      print('axes to stop = '+ axes)
      if len(axes)>0:
        command = 'BG'+axes
        self.c(command) # only BG the axes that have speed otherwise the value of _BGX for X axis will stay 1.

      self.g.GMotionComplete('ABCDE')
      time.sleep(1)
      self.c('DP 0,0,0')
      self.print_position('after homing: ')
      self.save_position()
    except:
      print('Homing failed.  Disabling motor')
      self.c('ST;MO')
      self.c('TE')
      exit()

  #converts from mm to counts
  def convert(self,x,y,z,theta,phi):
    x=round(x/0.01113)#round((x-0.195)/0.01113)
    y=round(y/0.009382)#round((y-0.375)/0.009382)
    z=round(z/0.009355)#round((z-0.126)/0.009355)
    theta=round(theta/0.0226)#round((theta-0.44)/0.0226)
    phi=round(phi/0.02259)#round((phi-0.5357)/0.02259)
    return x,y,z,theta,phi

  # converts counts to mm
  def unconvert(self,curx,cury,curz,curtheta,curphi):
    x = 0.01113*curx
    y = 0.009382*cury
    z = 0.009355*curz
    theta = 0.0226*curtheta
    phi = 0.02259*curphi
    return x,y,z,theta,phi

  # returns current position in mm
  def get_cur_pos_mm(self):
    curx,cury,curz,curtheta,curphi = self.get_cur_pos()
    x,y,z,theta,phi = self.unconvert(curx,cury,curz,curtheta,curphi)
    return x,y,z,theta,phi

  # Prints current position in mm
  def print_cur_pos_mm(self):
    x,y,z,theta,phi = self.get_cur_pos_mm()
    print('current (x,y,z,theta,phi) (mm) =',x,y,z,theta,phi )

  # returns current position in counts
  def get_cur_pos(self):
    res = self.c('PA ?,?,?,?,?')
    curx,cury,curz,curtheta,curphi = res.split(',')
    curx = float(curx)
    cury = float(cury)
    curz = float(curz)
    curtheta = float(curtheta)
    curphi = float(curphi)
    return curx,cury,curz,curtheta,curphi

  #Prints current position in counts
  def print_cur_pos(self):
    curx,cury,curz,curtheta,curphi = self.get_cur_pos() 
    print('current (x,y,z,theta,phi) (counts)=',curx,cury,curz,curtheta,curphi )

  '''
  ***This Function is not used anymore******

  def axes_to_begin(self,x,y,z,theta,phi):
    res = self.c('PA ?,?,?,?,?')
    curx,cury,curz,curtheta,curphi = res.split(',')
    curx = float(curx)
    cury = float(cury)
    curz = float(curz)
    curtheta = float(curtheta)
    curphi = float(curphi)

    axes=''
    axes='A' if (x!=curx) else axes
    axes=axes+'B' if (y!=cury) else axes
    axes=axes+'C' if (z!=curz) else axes
    axes=axes+'D' if (theta!=curtheta) else axes
    axes=axes+'E' if (phi!=curphi) else axes
    return axes
  '''


  def move(self,x=-1,y=-1,z=-1,theta=-1,phi=-1,spx=1000,spy=1000,spz=1000,sptheta=1000,spphi=1000):
    '''
    move to absolute position and angle
    x,y,z in mm
    theta,phi in degrees
    default value is set to -1. -1 means don't move that axis. Can't use zero because it would mean move to absolute position 0.
    '''
    try:
      #check if we don't want to move some axis
      curx,cury,curz,curtheta,curphi = self.get_cur_pos()
      #-1 means don't move that axis.
      if x==-1:
        x=curx
      if y==-1:
        y=cury
      if z==-1:
        z=curz
      if theta==-1:
        theta=curtheta
      if phi==-1:
        phi=curphi

      #setting the speed up
      command = 'SP %g,%g,%g,%g,%g'% (spx,spy,spz,sptheta,spphi)
      print('SPEED COMMAND : ',command)
      self.c( command )

      print('current speed', self.c('SP ?,?,?,?,?'))

      # converting mm to counts
      x,y,z,theta,phi = self.convert(x,y,z,theta,phi)

      #Sending absolute move command
      command = 'PA %g,%g,%g,%g,%g'% (x,y,z,theta,phi)
      print('try running in move: ',command)
      self.c( command )

      '''
      #checking if the motion is completed. 0 means completed and 1 means not completed.
      #commented out for now.
      print(self.c('MG _BGA'))
      print(self.c('MG _BGB'))
      print(self.c('MG _BGC'))
      print(self.c('MG _BGD'))
      print(self.c('MG _BGE'))
      '''

      '''
      ******We can remove this block of code. We just have to make sure that we are not moving some axis with 0 speed.
        The way the program is setup I think it will avoid that problem. So this block is commented out ********
      #Only begin the axes whose Absolute position has changed
      axes = self.axes_to_begin(x,y,z,theta,phi) #This check is not necessary if someone doesn't set speed of some axis to 0 by accident.
      print('axes = '+axes)
      if len(axes)>0:
        self.c('BG'+axes) # Begin only if there is any axes to begin
      '''
      self.c('BG')
      self.g.GMotionComplete('ABCDE') # check if the motion has completed

    except:
      print("error returned by the controller during move command")
      #will implement code to print the error returned by controller in future
      self.c('ST;MO')
      self.c('TE')
      exit()

  #move x(counts) relative to current position
  def move_rel(self,x=0,y=0,z=0,theta=0,phi=0,spx=1000,spy=1000,spz=1000,sptheta=1000,spphi=1000):
    '''
    move relative distance x,y,z,theta,phi from current location
    distances are in motor steps
    saves position to file after moving
    '''
    try:
      #setting the speed up
      command = 'SP %g,%g,%g,%g,%g'% (spx,spy,spz,sptheta,spphi)
      self.c( command )

      self.print_cur_pos()

      command = 'PR %g,%g,%g,%g,%g'% (x,y,z,theta,phi)
      print('try running: ',command)
      self.c( command )
      self.c('BG')
      self.g.GMotionComplete('ABCDE')
      time.sleep(1)

      self.print_cur_pos()
      self.save_position()

    except:
      print("error returned by the controller during relative move command")
      #will implement code to print the error returned by controller in future
      self.c('ST;MO')
      self.c('TE')
      exit()

  # move x(mm) relative to current position
  def move_rel_mm(self,x=0,y=0,z=0,theta=0,phi=0,spx=1000,spy=1000,spz=1000,sptheta=1000,spphi=1000):
    self.print_cur_pos_mm()
    x,y,z,theta,phi = self.convert(x,y,z,theta,phi)
    self.move_rel(x,y,z,theta,phi,spx=1000,spy=1000,spz=1000,sptheta=1000,spphi=1000)
    self.print_cur_pos_mm()
