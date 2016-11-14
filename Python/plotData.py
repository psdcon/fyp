import matplotlib.pyplot as plt
import numpy as np
import json

from peakdetect import peakdetect

# Create plot
f, axarr = plt.subplots(3, sharex=True)

# Plot bounces
# Plot bounce height
x = centroids[:, 0]
y = centroids[:, 2]

maxima, minima = peakdetect(y, x, 3, 30)
peaks = maxima + minima
bounces = []
for i in range(1, len(minima), 1):
    thisPt = minima[-i]
    prevPt = minima[-(i - 1)]  # previous point in time is next point in the list because working form the back
    midlPt = maxima[-i]
    bodyLanding = 1 if (thisPt['y'] < trampolineTop+20) else 0
    bounce = {
        'end': (thisPt['x'], thisPt['y']),
        'start': (prevPt['x'], prevPt['y']),
        'maxHeight': (midlPt['x'], midlPt['y']),
        'index': bounceIndex,
        'isBodyLanding': bodyLanding,
        'title': "",
    }
    bounces.append(bounce)
    bounceIndex -= 1

print json.dumps(bounces[::-1])

peaksx = [pt['x'] for pt in peaks]
peaksy = [pt['y'] for pt in peaks]

# Two subplots, the axes array is 1-d
axarr[0].set_title("<0 in bounces,  0 tap,  >0 skills,  >10 out bounce.  red = body landing")
axarr[0].plot(x, y, color="g")
axarr[0].plot(peaksx, peaksy, 'r+')
axarr[0].set_ylabel('Height (Pixels)')
axarr[0].axhline(y=trampolineTop, xmin=0, xmax=1000, c="blue")
for bounce in bounces:
    c = "r" if bounce['isBodyLanding'] else "black"
    c = c if (bounce['index'] >= 1 and bounce['index'] <= 10) else "grey"
    axarr[0].annotate(bounce['index'],
                      xy=(bounce['maxHeight'][0], bounce['maxHeight'][1]),
                      xytext=(bounce['maxHeight'][0], bounce['maxHeight'][1]+10), color=c )

#
# Plot bounce travel
#
x = centroids[:, 0]
y = centroids[:, 1]

axarr[1].set_title("Travel in x direction")
axarr[1].set_ylabel('Rightwardness (Pixels)')
axarr[1].scatter(x, y, color="g")
axarr[1].axhline(y=trampolineCenter, xmin=0, xmax=1000, c="blue")
axarr[1].axhline(y=trampolineCenter+80, xmin=0, xmax=1000, c="red")
axarr[1].axhline(y=trampolineCenter-80, xmin=0, xmax=1000, c="red")

#
# Plot ellipsoids
#
x = np.array([pt[0] for pt in ellipsoids])
y = np.array([pt[3] for pt in ellipsoids])
y += 90
y %= 180

axarr[2].scatter(x, y)
axarr[2].set_title("0deg Ground plane. 90deg is standing up.")
axarr[2].set_ylabel('Angle (deg)')

axarr[2].set_xlabel('Frame Number')
plt.show()
