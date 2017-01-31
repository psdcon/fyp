def judge_real_basic():
    # Started 22:54
    # Open the database and find all the straddle jumps
    db = sqlite3.connect(c.dbPath)
    db.row_factory = sqlite3.Row

    # Get all the routines with straddle jumps
    routines = db.execute("SELECT * FROM routines WHERE bounces LIKE '%Straddle%'")
    routines = routines.fetchall()  # copy everything pointed to by the cursor into an object.

    deductionCats = {
        "0.0": {"x": [], "y": []},
        "0.1": {"x": [], "y": []},
        "0.2": {"x": [], "y": []},
        "0.3": {"x": [], "y": []},
        "0.4": {"x": [], "y": []},
        "0.5": {"x": [], "y": []}
    }
    colors = ['r', 'g', 'b', 'cyan', 'magenta', 'yellow']

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    deductionColors = {
        "0.0": 'r',
        "0.1": 'g',
        "0.2": 'b',
        "0.3": 'cyan',
        "0.4": 'magenta',
        "0.5": 'yellow'
    }

    # For each one, get the frame no for midpoint, its major and minor ellipse axis at that frame, it's deduction
    for ri, routine in enumerate(routines):
        if ri == 3:
            continue
        deductionsQuery = db.execute("SELECT * FROM judgements WHERE routine_id=? ORDER BY id ASC LIMIT 1", (routine['id'],))
        deductionsQuery = deductionsQuery.fetchone()

        deductions = json.loads(deductionsQuery[2])
        bounces = json.loads(routine['bounces'])
        ellipses = json.loads(routine['ellipses'])

        for i, bounce in enumerate(bounces):
            if bounce['name'] == "Straddle Jump":
                startFrame = bounce['startFrame']
                endFrame = bounce['endFrame']
                # (frame, (cx, cy), (MA, ma), angle)
                ellipsePts = ellipses[startFrame: endFrame]
                cx = np.array([float(pt[1][0]) for pt in ellipsePts])
                cx /= cx[0] # normalise
                cy = np.array([float(pt[1][1]) for pt in ellipsePts])
                cy /= cy[0] # normalise
                z = range(len(ellipsePts))

                deduction = deductions[i]
                color = deductionColors[deduction]
                # deductionCats[deduction]["x"].append(major)
                # deductionCats[deduction]["y"].append(minor)

                ax.scatter(z, cx, cy, c=color)

        if ri == 5:
            break

    # print(deductionCats)
    # Plot

    # handles = []
    # for i, cat in enumerate(deductionCats):
    #     handles.append(mpatches.Patch(color=colors[i], label=cat))
    #     thisdict = deductionCats[cat]
    #     plt.scatter(thisdict['x'], thisdict['y'], color=colors[i], marker='o')
    # plt.legend(handles=handles)
    ax.set_ylabel('Horizontal Travel')
    ax.set_zlabel('Height')
    ax.set_xlabel('Time (Frames)')

    plt.show()
