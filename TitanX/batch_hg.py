#! /usr/bin/python3
import os
from glob import glob
import subprocess
import threading

class colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    def str(str, color):
        return color+str+colors.ENDC

videoDir = '/home/titan/paul_connolly/videos/'

# Check images, check hg,   check matlab, check hg imgs, check mat imgs
labels =               ['HG',       'MATLAB',       'HGIMG',   'MATIMG']
fs =    ['frame_*.png', 'preds.h5', 'preds_2d.mat', 'posed_*', 'smoothed_*']
paths = glob(videoDir+'*')
paths = sorted(paths)

def getTODOArrays(shouldPrint=True):
    todoHGPaths = []
    todoMatPaths = []
    for p in paths:
        # Get the number of frames
        nFrames = len(glob(p + os.sep + fs[0]))
        # If there's no frames, it's not of interest
        if nFrames > 0:
            if shouldPrint:
                print('{:4} '.format(nFrames), end='')

            for l,f in zip(labels, fs[1:]):
                # Didnt find file
                nFiles = len(glob(p+os.sep+f))
                if nFiles == 0:
                    if l == 'HGIMG':
                        todoHGPaths.append(p)
                    # only add to matlab queue if not in lua queue, i.e., it's already been posed.
                    elif l == "MATIMG" and p not in todoHGPaths:
                        todoMatPaths.append(p)
                    if shouldPrint:
                        print(colors.str(l, colors.RED), '{:4}'.format(nFiles), end='\t')
                else:
                    if shouldPrint:
                        print(colors.str(l, colors.GREEN), '{:4}'.format(nFiles), end='\t')
    
            if shouldPrint:
                print(p.replace(videoDir,''))
    return todoHGPaths, todoMatPaths


def prettyPrintList(l):
    if not l:
        print("\tEmpty")
    for li in l:
        print('\t' + li)

def hgWorker():
    while True:
        # Get routines to be torched
        todoHGPaths, _todoMatPaths = getTODOArrays(False)    
        if not todoHGPaths:
            break

        print("TODO HG")
        prettyPrintList(todoHGPaths)
        for i, p in enumerate(todoHGPaths):
            # If we're starting the 2nd loop itteration and todoMatPaths 
            # list was empty, start the matlab processing now
            if i==1 and not _todoMatPaths:
                matThread.start()

            hgCmd = ["qlua", '/home/titan/paul_connolly/pose-hourglass/run-hg-framewise.lua', p, 'png']
            print("Running", hgCmd)
            subprocess.call(hgCmd)
        
    print('Finished hourglass thread')


def matWorker():
    while True:
        _todoHGPaths, todoMatPaths = getTODOArrays(False)
        if not todoMatPaths:
            break
        
        print("TODO MAT")
        prettyPrintList(todoMatPaths)
        for p in todoMatPaths:
            matCmd = ['matlab', '-nodisplay', '-nosplash', '-nodesktop', '-r "datapath=\''+p+'\', run(\'/home/titan/paul_connolly/monocap/demoHG.m\'), exit"']
            print("Running", matCmd)
            subprocess.call(matCmd)

    print('Finished MATLAB thread')


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Batch process hourglass pose and smooth it with matlab')
    parser.add_argument('-p', '--print', action="store_true", help='print the current status of the video folders')

    args = parser.parse_args()
    if args.print:
        getTODOArrays()

    else:
        print("Starting batch run")
        # Get MatPaths list
        _todoHGPaths, todoMatPaths = getTODOArrays()        

        # Create threds
        hgThread = threading.Thread(target=hgWorker)
        global matThread
        matThread = threading.Thread(target=matWorker)

        # Start hgThread first. When the first routine has been posed, matlab will run.
        hgThread.start()

        # If matlab has things to do, run it. 
        # Otherwise it will be started by the hgThread after the first routine has been posed
        if todoMatPaths:
            matThread.start()


if __name__ == '__main__':
    main()
