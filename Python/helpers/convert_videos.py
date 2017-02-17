from __future__ import print_function

import argparse
import os
import sqlite3

import cv2
from subprocess import check_output

import consts


def main():
    video_size = "720x480"

    parser = argparse.ArgumentParser(description='Convert all .mp4 files in path to ' + video_size)
    parser.add_argument('path', default='.', action="store", help='path to the directory containing mp4 files to convert')
    args = parser.parse_args()

    # Source directory
    files = []
    source = os.path.abspath(args.path)
    if not os.path.exists(source):
        print('No such file or directory ' + source)
        exit()
    elif os.path.isdir(source):
        # Get list of file names in source directory
        files = [f for f in os.listdir(source) if os.path.isfile(os.path.join(source, f)) and '.mp4' in f]
        print("Found " + str(len(files)) + " videos.")
    else:  # It's a file
        files = [source]
        source = os.path.dirname(source)  # This removes file from path

    # Destination directory
    outputDirectory = video_size
    destination = os.path.abspath(os.path.join(source, '..', outputDirectory))
    if not os.path.exists(destination):
        print("Creating directory " + destination)
        os.makedirs(destination)
    print(" Saving videos to " + destination)

    for f in files:
        # Output path
        outputFilePath = os.path.join(destination, os.path.basename(f))
        print(outputFilePath)

        # Create ffmpeg command, e.g. ffmpeg.exe -i C:\Users\psdco\Videos\Inhouse\Originals\VID_20161106_120832.mp4 -an -s 720x480 "C:\Users\psdco\Videos\Inhouse\720x480\VID_20161106_120832_720x480.mp4"
        command = 'ffmpeg.exe -i {} -an -s {} "{}"'.format(f, video_size, outputFilePath)
        print(command)

        # Run command
        # output = check_output(command)

    add_to_database(destination)


# Adds all mp4's in path to database
def add_to_database(path):
    # Open database
    db = sqlite3.connect(consts.databasePath)

    # Check that the folder to use exists
    source = os.path.abspath(path)
    if not os.path.exists(source):
        print('No such directory ' + source)
        exit()

    print("Adding files to database")
    files = [f for f in os.listdir(source) if os.path.isfile(os.path.join(source, f)) and '.mp4' in f]
    for f in files:
        # Do path stuff
        absVideoPath = os.path.join(source, f)  # make the absolute path to the file
        pathFromVideoRoot = absVideoPath.replace(os.path.abspath(consts.videosRootPath)+os.sep, "")  # Make the path relative to the videos root folder
        competition = pathFromVideoRoot.split(os.sep)[0]

        # Use OpenCV to get video meta data
        cap = cv2.VideoCapture(absVideoPath)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = cap.get(cv2.CAP_PROP_FPS)

        try:
            db.execute('INSERT INTO routines (path, competition, video_height, video_width, video_fps) VALUES (?,?,?,?,?)',
                   (pathFromVideoRoot, competition, height, width, fps,))
        except sqlite3.IntegrityError:
            print("Routine already in db:", pathFromVideoRoot)
            continue
        print("Routine addded:", pathFromVideoRoot)

    db.commit()
    db.close()


if __name__ == '__main__':
    main()
