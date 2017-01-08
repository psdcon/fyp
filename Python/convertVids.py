from __future__ import print_function
from os import listdir
from os.path import isfile, join
from subprocess import check_output
import json

def main():
  # folder to search
  source = "."
  files = [f for f in listdir(source) if isfile(join(source, f)) and '.mp4' in f]
  for f in files:
    size = "720x480"
    command = 'ffmpeg.exe -i {3}/{0} -an -s {1} "480p/{2}_{1}.mp4"'.format(f, size, f[0:-4], source)
    print(command)

    # command = "ffmpeg -i {} -f ffmetadata metadata.txt".format(f)
    output = check_output(command)

    # lines = iter(output.splitlines())
    # for line in lines:
    #   print line
    #   if "creation_time" in line:
    #     print line
    #     break
    # print "ending"
    # check_output("del metadata.txt", shell=True)

def other():
  # folder to search
  dictionary = json.load(open("dictionary.json", "r"))
  print(dictionary)

  source = "Inhouse/480p/"
  files = [f for f in listdir(source) if isfile(join(source, f)) and ".mp4" in f]
  for f in files:
    # Check if file is already noted
    exists = 0
    for vid in dictionary:
      if vid["video_name"] == source+f:
        exists = 1
        break
    if exists == 1:
        continue
  dictionary.append({
    "video_name": source+f,
    "trampoline": {},
    "bounces" : [],
    "center_points": [],
    "ellipses": []
  })

  print(dictionary)
  json.dump(dictionary, open('dictionary.json', 'w'), indent=2)

if __name__ == '__main__':
  # main()
  other()
