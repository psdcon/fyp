#! /usr/bin/python3
import os
from glob import glob
import subprocess
import threading
from collections import OrderedDict


# Usage
# To print processing status, run with -p
# To run only Lua code, run with -l
# To run print, Lua and Matlab, no args
#

class colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    def str(str, color):
        return color+str+colors.ENDC


# Check images, check hg,   check matlab, check hg imgs, check mat imgs
mdict = OrderedDict([
    ('f', 'frame_*.png'),
    ('HG', 'hg_heatmaps.h5'),
    ('MATLAB', 'monocap_preds_2d.h5'),
    ('HGIMG', 'posed_*'),
    ('MATIMG', 'smoothed_*'),
])


def getTODOArrays(shouldPrint=True):

    # videoDir = '/home/titan/paul_connolly/videos/'
    videoDir = 'C:\\Users\\psdco\\Videos\\Inhouse\\720x480\\'
    paths = glob(videoDir + '*')
    paths = sorted(paths)

    hgPathsQueue = []
    mlPathsQueue = []
    for p in paths:
        # Get the number of frames
        nFrames = len(glob(p + os.sep + mdict['f']))
        # If there's no frames, it's not of interest
        if nFrames == 0:
            continue

        # build the queues
        hgFile = os.path.exists(p + os.sep + mdict['HG'])
        # hgFile = len(glob(p + os.sep + mdict['HGIMG'])) > 0
        if not hgFile:
            hgPathsQueue.append(p)

        # Check if matlab's monocap_preds_2d.mat exists
        matFile = os.path.exists(p + os.sep + mdict['MATLAB'])
        # only add to matlab queue if not in lua queue, i.e., it's already been posed.
        if not matFile and p not in hgPathsQueue:
            mlPathsQueue.append(p)

        # Print the number of savedFrame files found
        if shouldPrint:
            for key in mdict:
                nFiles = len(glob(p+os.sep+mdict[key]))
                if nFiles == 0:
                    print(colors.str(key, colors.RED), end=' ')
                else:
                    print(colors.str(key, colors.GREEN), end=' ')

                if nFiles>1:
                    print('{:3}'.format(nFiles), end='   ')
                else:
                    print('{:3}'.format(nFiles), end='   ')

            # Print the dir/routine name at the end
            print(p.replace(videoDir,''))

    return hgPathsQueue, mlPathsQueue


def prettyPrintList(l):
    if not l:
        print("\tEmpty")
    for li in l:
        print('\t' + li)

def hgWorker():
    while True:
        # Get routines to be torched
        hgPathsQueue, _mlPathsQueue = getTODOArrays(False)
        if not hgPathsQueue:
            break

        print("TODO HG")
        prettyPrintList(hgPathsQueue)
        for i, p in enumerate(hgPathsQueue):
            # If we're starting the 2nd loop itteration and todoMatPaths
            # list was empty, start the matlab processing now
            if i==1 and not args.luaonly and not _mlPathsQueue:
                matThread.start()

            hgCmd = ["qlua", '/home/titan/paul_connolly/pose-hourglass/run-hg-framewise.lua', p]
            print("Running", hgCmd)
            subprocess.call(hgCmd)

    print('Finished hourglass thread')


def matWorker():
    while True:
        _hgPathsQueue, mlPathsQueue = getTODOArrays(False)
        if not mlPathsQueue:
            break

        print("TODO MAT")
        prettyPrintList(mlPathsQueue)
        for p in mlPathsQueue:
            # http://stackoverflow.com/questions/6657005/matlab-running-an-m-file-from-command-line
            matCmd = ['matlab', '-nodisplay', '-nosplash', '-nodesktop',
                      # '-r "datapath=\''+p+'\', run(\'/home/titan/paul_connolly/monocap/demoHG.m\'), exit"']
                      '-r "datapath=\''+p+'\', try, run(\'/home/titan/paul_connolly/monocap/demoHG.m\'), catch, exit, end, exit"']
            print("Running", matCmd)
            subprocess.call(matCmd)

    print('Finished MATLAB thread')


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Batch process hourglass pose and smooth it with matlab')
    parser.add_argument('-p', '--print', action="store_true", help='print the current status of the video folders')
    parser.add_argument('-l', '--luaonly', action="store_true", help='pose only, dont run matlab')

    global args
    args = parser.parse_args()
    print(args)

    if args.print:
        getTODOArrays()

    else:
        print("Starting batch run")
        # Get MatPaths list
        mlsQueueQueue, mlPathsQueue = getTODOArrays()

        # Create threds
        hgThread = threading.Thread(target=hgWorker)
        global matThread
        matThread = threading.Thread(target=matWorker)

        # Start hgThread first. When the first routine has been posed, matlab will run.
        hgThread.start()

        # If matlab has things to do, run it.
        # Otherwise it will be started by the hgThread after the first routine has been posed
        if not args.luaonly and mlPathsQueue:
            matThread.start()


if __name__ == '__main__':
    main()
