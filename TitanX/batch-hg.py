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
labels = ['HG', 'MATLAB', 'HGIMG', 'MATIMG']
fs = ['frame_*.png', 'preds.h5', 'preds_2d.mat', 'posed_*', 'smoothed_*']
paths = glob(videoDir+'*')
paths = sorted(paths)
todoHGPaths = []
todoMatPaths = []
for p in paths:
    nFrames = len(glob(p+os.sep+fs[0]))
    if len(glob(p+os.sep+fs[0])) == 0:
        continue
    else:
        print('{:4} '.format(nFrames), end='')



    for l,f in zip(labels, fs[1:]):
        # Didnt find file
        nFiles = len(glob(p+os.sep+f))
        if nFiles == 0:
            if l == 'HGIMG':
                todoHGPaths.append(p)
            if l == "MATIMG" and p not in todoHGPaths:
                todoMatPaths.append(p)
            print(colors.str(l, colors.RED), '{:4}'.format(nFiles), end='\t')
        else:
            print(colors.str(l, colors.GREEN), '{:4}'.format(nFiles), end='\t')

    print(p.replace(videoDir,''))
exit()

def prettyPrintList(l):
	if not l:
		print("\tEmpty")
	for li in l:
		print('\t' + li)

def hgWorker():
    print("TODO HG")
    prettyPrintList(todoHGPaths)
    for p in todoHGPaths:
        hgCmd = ["qlua", '/home/titan/paul_connolly/pose-hourglass/run-hg-framewise.lua', p, 'png']
        print("Running", hgCmd)
        subprocess.call(hgCmd)

def matWorker():
    print("TODO MAT")
    prettyPrintList(todoMatPaths)
    for p in todoMatPaths:
        matCmd = ['matlab', '-nodisplay', '-nosplash', '-nodesktop', '-r "datapath=\''+p+'\', run(\'/home/titan/paul_connolly/monocap/demoHG.m\'), exit"']
        print("Running", matCmd)
        subprocess.call(matCmd)

hgThread = threading.Thread(target=hgWorker)
hgThread.start()
matThread  = threading.Thread(target=matWorker)
matThread.start()
