from __future__ import print_function

from collections import OrderedDict

import cv2
from sqlalchemy.orm import sessionmaker

from gui.showRoutineSelectDialog import show_selection_menu
from helpers import helper, consts
from helpers.db_declarative import *
from image_processing import plot, track, trampoline, segment_bounces

# https://github.com/opencv/opencv/issues/6055
cv2.ocl.setUseOpenCL(False)


def main():
    # engine = create_engine('sqlite:///'+consts.dbPath)
    engine = create_engine('sqlite:///db.sqlite3')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    db = DBSession()

    ask = False
    # Ask the user to select routine from database
    routines = db.query(Routine).all()
    if ask:
        routinesAsDict = []
        for routine in routines:
            routinesAsDict.append(OrderedDict([
                ('id', str(routine.id)),
                ('path', routine.path),
                ('competition', routine.competition),
                ('level', routine.level),
                ('tracked', 'Yes' if routine.isTracked() else 'No'),
                ('note', routine.note)
            ]))

        selectedRoutineIndices = show_selection_menu(routinesAsDict)
    else:
        selectedRoutineIndices = [0]
    selectedRoutines = [routines[i] for i in selectedRoutineIndices]

    # Execute
    for i, routine in enumerate(selectedRoutines):
        # Open the video with some error handling
        cap = helper.open_video(routine.path)

        '''
        If the routine is not tracked:
            detect trampoline
            track
            find bounces
        Else is tracked, present with option to:
            detect trampoline
            track and save
            track without save
            find bounces
            plot
        '''
        if not routine.isTracked():
            # Detect Trampoline
            trampoline.detect_trampoline(db, cap, routine)

            # Track gymnast and save
            track.track_and_save(db, cap, routine)

            # Find bounces and save
            segment_bounces.segment_bounces_and_save(db, routine)

            # Plot
            plot.plot_data(routine)

        else:
            # Show options loop
            options = [
                "Detect Trampoline",
                "Track and Save",
                "Track without Save",
                "Segment Bounces",
                "Plot",
                "Exit",
            ]
            while True:
                print("This routine has already been tracked. What would you like to do?")
                for ii, op in enumerate(options):
                    print('%d) %s' % (ii + 1, op))
                choiceInt = helper.read_num(len(options))
                choiceStr = options[choiceInt - 1]

                if choiceStr == "Detect Trampoline":
                    trampoline.detect_trampoline(db, cap, routine)
                elif choiceStr == "Track and Save":
                    track.track_and_save(db, cap, routine)
                elif choiceStr == "Track without Save":
                    track.track_gymnast(cap, routine)
                elif choiceStr == "Segment Bounces":
                    segment_bounces.segment_bounces_and_save(db, routine)
                elif choiceStr == "Plot":
                    plot.plot_data(routine)
                elif choiceStr == "Exit":
                    break
                else:
                    print("No such choice")

        print("Finished routine {} of {}".format(i + 1, len(routines)))

    db.close()
    print("Done")


if __name__ == '__main__':
    main()


def visualise_pose(cap, routine, padding=100):
    # colours = [red, green, blue, yellow, purple, cyan,  red, green, blue, cyan, purple, yellow, red, green] bgr
    # [rfoot, rknee, rhip, lhip, lknee, lfoot, rhand, relbow, rshoulder, lshoulder, lelbow, lhand, neck, head top]
    colours = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 0, 255), (255, 255, 0), (0, 0, 255),
               (0, 255, 0), (255, 0, 0), (255, 255, 0), (255, 0, 255), (0, 255, 255), (0, 0, 255), (0, 255, 0)]

    # TODO this assumes there is a file with all poses for each frame in it
    # posePath = videoPath + routine['name'][:-4] + "/pose.npz"
    # poses = np.load(posePath)['poses']

    # This assumes file for individual frame
    poses = {}
    for frameNo in range(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT) + 1)):
        posePath = videoPath + routine['name'][:-4] + "/frame {}_pose.npz".format(frameNo)
        try:
            pose = np.load(posePath)['pose']
        except IOError:
            continue
        poses.update({frameNo: pose})

    # # Filter pose
    # frameNos = [frameNo for frameNo in poses]  # frame no
    # x = [poses[frameNo][0, 0] for frameNo in poses]  # rfoot x
    # y = [poses[frameNo][1, 0] for frameNo in poses]  # rfoot y
    #
    # b, a = signal.ellip(4, 0.01, 120, 0.055)  # Filter to be applied.
    # xFilt = signal.filtfilt(b, a, x, method="gust")
    # yFilt = signal.filtfilt(b, a, y, method="gust")
    #
    # for idx, frameNo in enumerate(frameNos):
    #     # Save rfoot pts in rknee
    #     poses[frameNo][0, 1] = poses[frameNo][0, 0]  # x
    #     poses[frameNo][1, 1] = poses[frameNo][1, 0]  # y
    #     # Overwrite rfoot with filtered sig
    #     poses[frameNo][0, 0] = xFilt[idx]
    #     poses[frameNo][1, 0] = yFilt[idx]

    routine['center_points'] = json.loads(routine['center_points'])
    routine['center_points'] = {cp[0]: [cp[1], cp[2]] for cp in routine['center_points']}

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('C:/Users/psdco/Videos/Trainings/480p/posed_cropped.avi', fourcc, 30.0, (200,200))
    # out = cv2.VideoWriter('C:/Users/psdco/Videos/Trainings/480p/posed_full.avi', fourcc, 30.0, (720,480))

    while 1:
        ret, frame = cap.read()
        frameNo = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        if frameNo not in routine['center_points']:
            continue

        cpt = routine['center_points'][frameNo]
        cx = cpt[0]
        cy = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) - cpt[1])

        # pose points are relative to the top left (cx cy = ix iy; 0 0 = ix-100 iy-100) of the 200x200 cropped frame
        # pose given by (0 + posex, 0 + posey) => cx-100+posex, cy-100+posey
        frameCropped = frame[cy-100:cy+100, cx-100:cx+100]  # [y1:y2, x1:x2]
        pose = poses[frameNo]
        for p_idx in range(14):  # [0, 1]:
            # posex = int((cx - padding) + pose[0, p_idx])
            # posey = int((cy - padding) + pose[1, p_idx])
            # cv2.circle(frame, (posex, posey), 5, colours[p_idx], thickness=-1)  # -ve thickness = filled
            cv2.circle(frameCropped, (int(pose[0, p_idx]), int(pose[1, p_idx])), 5, colours[p_idx], thickness=-1)  # -ve thickness = filled

        # Lines between points
        #  Could loop in pairs and link skipping ones that shouldnt be linked.
        # cv2.line(trackPerson,
        #          (int(thisFramePose[0, 0]), int(thisFramePose[1, 0])),
        #          (int(thisFramePose[0, 1]), int(thisFramePose[1, 1])),
        #          colours[0], 4)

        cv2.imshow('frame', frameCropped)
        out.write(frameCropped)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

        # Finish playing the video when we get to the end.
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            break

    out.release()
    cv2.destroyAllWindows()
    # print(poses)
    # x = [frameNo for frameNo in poses]  # frame no
    # y = [480-poses[frameNo][1, 0] for frameNo in poses]  # rfoot
    #
    # b, a = signal.ellip(4, 0.01, 120, 0.055)  # Filter to be applied.
    # fgust = signal.filtfilt(b, a, y, method="gust")
    #
    # plt.plot(x, y, label="Original")
    # plt.plot(x, fgust, label="fgust")

    frameNos = [frameNo for frameNo in poses]  # frame no
    # x = [poses[frameNo][0, 0] for frameNo in poses]  # rfoot x
    y = [poses[frameNo][1, 0] for frameNo in poses]  # rfoot y
    diffy = np.diff(y)
    myDiff = []
    newY = y
    for i, _ in enumerate(newY[:-2]):
        thisPt = newY[i]
        nextPt = newY[i + 1]
        diff = nextPt - thisPt
        myDiff.append(diff)
        if abs(diff) > 20:
            avg = (newY[i] + newY[i + 2]) / 2
            newY[i + 1] = avg
    y = np.array(y) - 10

    plt.plot(frameNos, y, label="y original")
    plt.plot(frameNos, newY, label="newY")
    plt.plot(frameNos[:-1], diffy, label="diff y")
    plt.plot(frameNos[:-2], myDiff, label="my diff y")
    plt.legend(loc='best')
    plt.show()


def create_video():
    import re

    def atoi(text):
        return int(text) if text.isdigit() else text

    def natural_keys(text):
        '''
        alist.sort(key=natural_keys) sorts in human order
        http://nedbatchelder.com/blog/200712/human_sorting.html
        (See Toothy's implementation in the comments)
        '''
        return [atoi(c) for c in re.split('(\d+)', text)]

    cap = cv2.VideoCapture(0)
    mypath = 'C:/Users/psdco/Videos/Trainings/480p/0 day1 rout2 720x480/'
    videoFramesPaths = [mypath + f for f in listdir(mypath) if (isfile(join(mypath, f)) and '_vis' in f)]
    print(videoFramesPaths.sort(key=natural_keys))

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('C:/Users/psdco/Videos/Trainings/480p/output.avi', fourcc, 30.0, (200, 200))

    for vfp in videoFramesPaths:
        frame = cv2.imread(vfp)
        out.write(frame)
        # cv2.imshow('frame', frame)
        # if cv2.waitKey(10) & 0xFF == ord('q'):
        #     break

    # Release everything if job is finished
    out.release()
    cv2.destroyAllWindows()

