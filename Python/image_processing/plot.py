import matplotlib.pyplot as plt
import numpy as np
from itertools import chain

def plot_data(routine):
    print("\nStarting plotting...")
    f, axarr = plt.subplots(4, sharex=True)

    # Plot bounce heights
    x_frames = [frame.frame_num / routine.video_fps for frame in routine.frames]
    y_travel = [frame.center_pt_x for frame in routine.frames]
    y_height = [frame.center_pt_y for frame in routine.frames]

    # List inside list gets flattened
    peaks_x = list(chain.from_iterable((bounce.start_time, bounce.max_height_frame / routine.video_fps) for bounce in routine.bounces))
    peaks_x.append(routine.bounces[-1].end_time)
    peaks_y = list(chain.from_iterable((bounce.start_height, bounce.max_height) for bounce in routine.bounces))
    peaks_y.append(routine.bounces[-1].end_height)

    axarr[0].set_title("Height")
    axarr[0].plot(x_frames, y_height, color="g")
    axarr[0].plot(peaks_x, peaks_y, 'r+')
    axarr[0].set_ylabel('Height (Pixels)')

    # Plot bounce travel
    axarr[1].set_title("Travel")
    axarr[1].set_ylabel('Rightwardness (Pixels)')
    axarr[1].plot(x_frames, y_travel, color="g")
    axarr[1].axhline(y=routine.trampoline_center, xmin=0, xmax=1000, c="blue")
    axarr[1].axhline(y=routine.trampoline_center + 80, xmin=0, xmax=1000, c="red")
    axarr[1].axhline(y=routine.trampoline_center - 80, xmin=0, xmax=1000, c="red")

    # Ellipse angles
    x_frames = np.array([frame.frame_num / routine.video_fps for frame in routine.frames])
    y_angle = np.array([frame.ellipse_angle for frame in routine.frames])
    # Changes angles
    y_angle = np.unwrap(y_angle, discont=90, axis=0)

    axarr[2].plot(x_frames, y_angle, color="g")
    axarr[2].set_title("Angle")
    axarr[2].set_ylabel('Angle (deg)')

    # Ellipse lengths
    y_major = np.array([frame.ellipse_len_major for frame in routine.frames])
    y_minor = np.array([frame.ellipse_len_minor for frame in routine.frames])

    axarr[3].scatter(x_frames, y_major, color="g")
    axarr[3].scatter(x_frames, y_minor, color='b')
    axarr[3].set_ylim([0, 300])
    axarr[3].set_title("Ellipse Axes Length")
    axarr[3].set_ylabel('Length')
    axarr[3].set_xlabel('Time (s)')

    plt.show()



def skill_into_filmstrip(cap, routine):
    capWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    capHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    bounces = json.loads(routine['bounces'])
    print('\nChoose a skill:')
    for i, b in enumerate(bounces):
        print('%d) %s' % (i + 1, b['name']))
    choice = 10
    # choice = readNum(len(bounces))

    bounce = bounces[choice - 1]
    start = bounce['startFrame'] + 6
    end = bounce['endFrame'] - 6
    step = (end - start) / 6
    step = int(step)
    framesToSave = range(start, end, step)

    whitespace = 4
    width = 255

    startPixel = int((capWidth * 0.55) - width / 2)
    endPixel = startPixel + width
    filmStrip = np.ones(shape=(capHeight * 0.8, (width * len(framesToSave)) + (whitespace * len(framesToSave) - 1), 3), dtype=np.uint8)

    for i, frameNum in enumerate(framesToSave):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frameNum)
        _ret, frame = cap.read()

        # possible improvement
        trackPerson = frame[0:capHeight * 0.8, startPixel:endPixel]
        start = ((whitespace + width) * i)
        filmStrip[0:capHeight * 0.8, start:start + width] = trackPerson

    imgName = "C:/Users/psdco/Videos/{}/{}.png".format(routine['name'][:-4], bounce['name'])
    print("Writing frame to {}".format(imgName))
    ret = cv2.imwrite(imgName, filmStrip)
    if not ret:
        print("Couldn't write image {}\nAbort!".format(imgName))
        exit()

