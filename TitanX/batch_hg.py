#! /usr/bin/python3
# from __future__ import print_function

import os
import subprocess
import threading
from collections import OrderedDict
from glob import glob

# Usage
# To print processing status, run with -p
# To run only Lua code, run with -l
# To run print, Lua and Matlab, no args
#


# Check images, check hg,   check matlab, check hg imgs, check mat imgs
mdict = OrderedDict([
    ('f', 'frame_*.png'),
    ('HG', 'hg_heatmaps.h5'),
    ('MATLAB', 'monocap_preds_2d.h5'),
    ('HGIMG', 'posed_*'),
    ('MATIMG', 'smoothed_*'),
])

# Swap depending on environment
videoDir = '/home/titan/paul_connolly/videos/'
# videoDir = 'C:\\Users\\psdco\\Videos\\Inhouse\\720x480\\'

# Get all folders in videoDir that have frame_* in them
paths = []
for path in glob(videoDir + '*'):
    # Only of interest if there are frame_*.png files in the folder
    nFrames = len(glob(path + os.sep + mdict['f']))
    if nFrames > 0:
        paths.append(path)
paths = sorted(paths)

# Global variables so that lua thread can start matlab thread
matThread = None
startMlThreadFromHgThread = None


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Batch process hourglass pose and smooth it with matlab')
    parser.add_argument('-p', '--print', action="store_true", help='print the current status of the video folders')
    parser.add_argument('-l', '--luaonly', action="store_true", help='pose only, dont run matlab')

    args = parser.parse_args()
    print(args)

    if args.print:
        printStatus()

    else:
        print("Starting batch run")
        printStatus()
        # hgPathsQueue = getHgQueue()
        mlPathsQueue = getMlQueue()

        # Create threads. Make matlab thread global so it can be started from hgThread
        global matThread
        global startMlThreadFromHgThread
        startMlThreadFromHgThread = False
        matThread = threading.Thread(target=matWorker)
        hgThread = threading.Thread(target=hgWorker)

        # Start hgThread first. When the first routine has been posed, matlab will run.
        hgThread.start()

        # If matlab has things to do, run it.
        # Otherwise it will be started by the hgThread after the first routine has been posed
        if not args.luaonly and mlPathsQueue:
            print("Starting MATLAB organically")
            matThread.start()
        elif not mlPathsQueue:  # not lua only is implied
            # MATLAB will start once
            startMlThreadFromHgThread = True


def printStatus():
    for p in paths:
        for key in mdict:
            nFiles = len(glob(p + os.sep + mdict[key]))
            if nFiles == 0:
                print(colors.str(key, colors.RED), end=' ')
            else:
                print(colors.str(key, colors.GREEN), end=' ')

            if nFiles > 1:
                print('{:3}'.format(nFiles), end='   ')
            else:
                print('{:3}'.format(nFiles), end='   ')

        # Print the dir/routine name at the end
        print(p.replace(videoDir, ''))


def getHgQueue():
    hgPathsQueue = []
    for p in paths:
        hgFile = os.path.exists(p + os.sep + mdict['HG'])
        # hgFile = len(glob(p + os.sep + mdict['HGIMG'])) > 0
        if not hgFile:
            hgPathsQueue.append(p)

    return hgPathsQueue


def getMlQueue():
    mlPathsQueue = []
    for p in paths:
        # Check if matlab's monocap_preds_2d.mat exists
        matFile = os.path.exists(p + os.sep + mdict['MATLAB'])

        # only add to matlab queue lua files exists
        hgFile = os.path.exists(p + os.sep + mdict['HG'])
        if not matFile and hgFile:
            mlPathsQueue.append(p)

    return mlPathsQueue


def prettyPrintList(l):
    if not l:
        print("\tEmpty")
    for li in l:
        print('\t' + li)


def hgWorker():
    global startMlThreadFromHgThread
    while True:
        # Get routines to be torched
        hgPathsQueue = getHgQueue()
        if not hgPathsQueue:
            break

        print("Hourglass Queue: {}".format(len(hgPathsQueue)))
        # prettyPrintList(hgPathsQueue)
        for i, p in enumerate(hgPathsQueue):
            # If we're starting the 2nd loop iteration and todoMatPaths
            # list was empty, start the matlab processing now
            if i == 1 and startMlThreadFromHgThread:
                print("Starting MATLAB now that it has work to do")
                startMlThreadFromHgThread = False  # set it to false so that it doesnt get run multiple times when queue changes
                matThread.start()

            hgCmd = ["qlua", '/home/titan/paul_connolly/pose-hourglass/run-hg-framewise.lua', p]
            print("Running", hgCmd)
            subprocess.call(hgCmd)

    print('Finished hourglass thread')


def matWorker():
    while True:
        mlPathsQueue = getMlQueue()
        if not mlPathsQueue:
            break

        print("MATLAB Monocap Queue: {}".format(len(mlPathsQueue)))
        # prettyPrintList(mlPathsQueue)
        for p in mlPathsQueue:
            # http://stackoverflow.com/questions/6657005/matlab-running-an-m-file-from-command-line
            matCmd = ['matlab', '-nodisplay', '-nosplash', '-nodesktop',
                      # '-r "datapath=\''+p+'\', run(\'/home/titan/paul_connolly/monocap/demoHG.m\'), exit"']
                      '-r "datapath=\'' + p + '\', try, run(\'/home/titan/paul_connolly/monocap/demoHG.m\'), catch, exit, end, exit"']
            print("Running", matCmd)
            subprocess.call(matCmd)

    print('Finished MATLAB thread')


class colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

    def str(s, color):
        return color + s + colors.ENDC


if __name__ == '__main__':
    main()
