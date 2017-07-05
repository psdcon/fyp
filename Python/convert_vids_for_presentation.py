from os import listdir, remove
from os.path import isfile, join
from subprocess import check_output

mypath = "C:\\Users\\psdco\\Videos\\"

videoSize = "1280x720"  # divisible by 8

onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f)) and 'avi' in f]

for filename in onlyfiles:
    # command = 'ffmpeg.exe -i {} -an -s {} "{}"'.format(mypath+filename, videoSize, mypath+filename.replace('avi', 'mp4'))
    command = 'C:\\Program Files\\VideoLAN\\VLC\\vlc.exe -I dummy %s :sout=#transcode{vcodec=h264,acodec=mp4a,ab=128,channels=2,samplerate=44100}:file{dst=%s} vlc://quit' \
              % (mypath+filename, mypath+filename.replace('avi', 'mp4'))
    print(command)

    # Run command
    output = check_output(command)

    # Delete original file
    remove(mypath+filename)
