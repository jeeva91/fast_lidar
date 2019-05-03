import os
import sys
import argparse
import struct
import time


#constants to control the frame start
WAIT_NSTART = 2
WAIT_START = 3
NWAIT_NSTART = 0


# device files names
PHOTONCOUNT_FILE = '/dev/xillybus_photoncount'
STATUS_FILE = '/dev/xillybus_status'
CONTROL_FILE = '/dev/xillybus_pixels_dwelltime_control'

def  change_ctrl(control_fd, ctrl_val):
    '''function to change the control of the frame start'''
    os.lseek(control_fd, 0, os.SEEK_SET)
    os.write(control_fd, struct.pack('<I', ctrl_val))


def get_counts(ctrl_fd, pxl_cnt):
    change_ctrl(ctrl_fd, WAIT_NSTART)
    change_ctrl(ctrl_fd, WAIT_START)
    capture_done = 0
    # check if capture done is asserted
    while(capture_done==0):
        with open(STATUS_FILE, 'rb') as sts_fd:
            status = sts_fd.read(4)
            status, = struct.unpack('>I',status)
        capture_done = 0x100 & status
    # open the count file
    #read the counts        
    data=[]
    with open(PHOTONCOUNT_FILE, 'rb')as cnt_fd:
        for pixels in range(0, pxl_cnt):
            count = cnt_fd.read(4)
            data.append(struct.unpack('<I', count)[0])

    change_ctrl(ctrl_fd, NWAIT_NSTART)
    return data


def open_ctrl(dwell_time, pixel_count):
    
    global CONTROL_FILE, STATUS_FILE, PHOTONCOUNT_FILE

    control_fd = os.open(CONTROL_FILE, os.O_WRONLY)
    

    # change the dwell_time and the pixel count
    if(control_fd>0):
        os.lseek(control_fd, 4, os.SEEK_SET)
        dwell_time = struct.pack('<I', dwell_time)
        os.write(control_fd, dwell_time);
        pixel_count = struct.pack('<I', pixel_count)
        os.write(control_fd, pixel_count)
        change_ctrl(control_fd, WAIT_NSTART)
        time.sleep(0.1)
        change_ctrl(control_fd, NWAIT_NSTART)
        time.sleep(0.1)

    else:
        print('unable to open the control file')
        sys.exit(-1)

    return control_fd
        



def close_devices(ctrl_fd):
    os.close(ctrl_fd)


parser = argparse.ArgumentParser()
parser.add_argument('-d', '--dwell_time', type=int, help='dual time to count the photons', default=100)
parser.add_argument('-p', '--pixel_count', type=int, help='number of pixels in a line', default=30)
parser.add_argument('-l', '--line_count', type=int, help='number of lines in a frame', default=2)
parser.add_argument('-f', '--file_name', type=str, help='filename ot save the data', default='lidar.csv')
parser.add_argument('-z', '--zmin', type=float, help='Minimum delay value in pico seconds', default=0)
parser.add_argument('-Z', '--zmax', type=float, help='Maximum delay value in pico seconds', default=50)
parser.add_argument('-m', '--zmicro', type=float, help='z micro step size', default=2)
parser.add_argument('-M', '--zmacro', type=float, help='z Macro step size', default=10)



args = parser.parse_args()



ctrl_fd = open_ctrl(args.dwell_time, args.pixel_count)

for line in range(0, args.line_count):
    data = get_counts(ctrl_fd, args.pixel_count)
    print(data)



