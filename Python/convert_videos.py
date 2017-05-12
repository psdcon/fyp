from __future__ import print_function

import argparse
import os
import sqlite3
from subprocess import check_output

import cv2

import helpers.consts
from helpers import consts
from helpers import helper_funcs
from helpers.db_declarative import getDb, Routine
from image_processing import output_images


def main():
    # videoSize = "720x480"  # This is not 16:9, which the videos are recorded in...
    # https://pacoup.com/2011/06/12/list-of-true-169-resolutions/
    # videoSize = "896x504"  # divisible by 8
    videoSize = "1280x720"  # divisible by 8
    # videoSize = "960x540"  # half 1080p
    # videoSize = "1024x576"  #

    parser = argparse.ArgumentParser(description='Convert single .mp4 or all .mp4s in a directory to ' + videoSize)
    parser.add_argument('path', default='.', action="store", help='path to the directory containing mp4 inputFileNames to convert')
    args = parser.parse_args()

    # Source directory
    inputFileNames = []
    inputDirPath = os.path.abspath(args.path)
    if not os.path.exists(inputDirPath):
        print('No such file or directory ' + inputDirPath)
        exit()
    elif os.path.isdir(inputDirPath):
        # Get list of file names in inputDirPath directory
        inputFileNames = [inputFileName for inputFileName in os.listdir(inputDirPath) if '.mp4' in inputFileName.lower()]
        # Gopro save extensions as uppercase
        inputFileNames = [inputFileName.replace('.MP4', '.mp4') for inputFileName in inputFileNames]
        print("Found " + str(len(inputFileNames)) + " videos.")
        if len(inputFileNames) == 0:
            exit()
    else:  # It's a file
        inputFileNames = [inputDirPath]
        inputDirPath = os.path.dirname(inputDirPath)  # This removes file from path

    # Destination directory
    outputDirName = videoSize
    outputDirPath = os.path.abspath(os.path.join(inputDirPath, '..', outputDirName))
    if not os.path.exists(outputDirPath):
        print("Creating directory " + outputDirPath)
        os.makedirs(outputDirPath)
    print("Saving videos to " + outputDirPath)

    for inputFileName in inputFileNames:
        # Output path
        inputFilePath = os.path.join(inputDirPath, inputFileName)
        outputFilePath = os.path.join(outputDirPath, os.path.basename(inputFileName))
        print(outputFilePath)

        # Create ffmpeg command, e.g. ffmpeg.exe -i C:\Users\psdco\Videos\Inhouse\Originals\VID_20161106_120832.mp4 -an -s 720x480 "C:\Users\psdco\Videos\Inhouse\720x480\VID_20161106_120832_720x480.mp4"
        command = 'ffmpeg.exe -i {} -an -s {} "{}"'.format(inputFilePath, videoSize, outputFilePath)
        print(command)

        # Run command
        output = check_output(command)

        add_routine(inputFilePath, outputFilePath)


def add_routine(originalFilePath, routineFullPath):
    if not os.path.exists(routineFullPath):
        print("File not found:", routineFullPath)
        return

    # Open database
    db = getDb()

    routineRelPath = routineFullPath.replace(consts.videosRootPath, '')
    originalRelPath = originalFilePath.replace(consts.videosRootPath, '')
    competition = routineFullPath.split(os.sep)[-3]

    # Use OpenCV to get video meta data
    cap = helper_funcs.open_video(routineFullPath)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    try:
        routine = Routine(routineRelPath, originalRelPath, competition, height, width, fps, frame_count)
        db.add(routine)
        db.commit()
        print("Routine addded:", routineFullPath)

        output_images.generate_thumbnail(routine)

    except sqlite3.IntegrityError:
        print("Routine already in db:", routineFullPath)


# Adds all mp4's in path to database
def add_to_database(original, routine_path):
    # Open database
    db = getDb()

    # Check that the folder to use exists
    routine_path = os.path.abspath(routine_path)
    if not os.path.exists(routine_path):
        print('No such directory ' + routine_path)
        exit()

    print("Adding files to database")
    files = [f for f in os.listdir(routine_path) if os.path.isfile(os.path.join(routine_path, f)) and '.mp4' in f]
    for f in files:
        # Do path stuff
        absVideoPath = os.path.join(routine_path, f)  # make the absolute path to the file
        pathFromVideoRoot = absVideoPath.replace(os.path.abspath(helpers.consts.videosRootPath) + os.sep, "")  # Make the path relative to the videos root folder
        competition = pathFromVideoRoot.split(os.sep)[0]

        # Use OpenCV to get video meta data
        cap = cv2.VideoCapture(absVideoPath)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

        try:
            Routine(pathFromVideoRoot, competition, height, width, fps, frame_count)
        except sqlite3.IntegrityError:
            print("Routine already in db:", pathFromVideoRoot)
            continue
        print("Routine addded:", pathFromVideoRoot)

    db.commit()
    db.close()


if __name__ == '__main__':
    main()
