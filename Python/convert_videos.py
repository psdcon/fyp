from __future__ import print_function
from subprocess import check_output
import sqlite3
import argparse
import os
import cv2


def main():
    video_size = "720x480"

    parser = argparse.ArgumentParser(description='Convert all .mp4 files in path to '+video_size)
    parser.add_argument('path', default='.', action="store", help='path to the directory containing mp4 files to convert')
    args = parser.parse_args()

    # Source directory
    source = os.path.abspath(args.path)
    if not os.path.exists(source):
        print('No such directory '+source)
        exit()

    # Destination directory
    outputDirectory = video_size[-3:]+'p'  # video_size would be simplier
    destination = os.path.abspath(os.path.join(source, '..', outputDirectory))
    if not os.path.exists(destination):
        print("Creating directory "+destination)
        os.makedirs(destination)
    print(" Saving videos to "+destination)

    # Get list of file names in source directory
    files = [f for f in os.listdir(source) if os.path.isfile(os.path.join(source, f)) and '.mp4' in f]
    print("Found "+str(len(files))+" videos.")
    for f in files:
        # Input path
        inputFilePath = os.path.join(source, f)
        # Output path
        filename = os.path.splitext(f)[0]  # strip file extension
        outputFilePath = os.path.join(destination, filename+"_"+video_size+".mp4")

        # Create ffmpeg command, e.g. ffmpeg.exe -i C:\Users\psdco\Videos\Inhouse\Originals\VID_20161106_120832.mp4 -an -s 720x480 "C:\Users\psdco\Videos\Inhouse\720x480\VID_20161106_120832_720x480.mp4"
        command = 'ffmpeg.exe -i {} -an -s {} "{}"'.format(inputFilePath, video_size, outputFilePath)
        print(command)

        # Run command
        # output = check_output(command)

    addToDatabase(destination)

# Adds all mp4's in path to database
def addToDatabase(path):
    # Used to strip this from the path to video.
    videosRoot = "C:/Users/psdco/Videos/"

    # Open database
    dbPath = 'C:/Users/psdco/Documents/ProjectCode/Web/includes/videos.sqlite3'
    db = sqlite3.connect(dbPath)

    # folder to search
    source = os.path.abspath(path)
    if not os.path.exists(source):
        print('No such directory '+source)
        exit()

    print("Adding files to database")
    files = [f for f in os.listdir(source) if os.path.isfile(os.path.join(source, f)) and '.mp4' in f]
    for f in files:
        # Do path stuff
        absVideoPath = os.path.join(source, f)
        pathFromVideoRoot = absVideoPath[len(videosRoot):]

        # Use OpenCV to get video meta data
        cap = cv2.VideoCapture(absVideoPath)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = cap.get(cv2.CAP_PROP_FPS)

        db.execute('INSERT INTO _routines (path, video_height, video_width, video_fps) VALUES (?,?,?,?)',
                   (pathFromVideoRoot, height, width, fps,))

    db.commit()
    db.close()

if __name__ == '__main__':
     main()
