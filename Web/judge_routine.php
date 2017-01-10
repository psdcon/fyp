<?php
include_once 'includes/functions.php';
$routineId = $db->escapeString($_GET['routine_id']);
$userId = $db->escapeString($_COOKIE['userId']);

$routineQuery = $db->query("SELECT * FROM routines WHERE id=$routineId LIMIT 1");
$routine = $routineQuery->fetchArray(SQLITE3_ASSOC);
$bouncesJSON = json_decode($routine['bounces'], true);
$isLabelled = ($bouncesJSON[0]['name'] != ""); // not the most fool proof way

// Create link to next unjudged routine
$nextIdQuery = $db->query("SELECT * FROM routines WHERE routines.id>$routineId AND routines.id NOT IN (
                            SELECT judgements.routine_id FROM judgements WHERE judgements.user_id='$userId'
                          ) LIMIT 1");
$nextId = $nextIdQuery->fetchArray(SQLITE3_ASSOC);
$nextBtn = ($nextId)?
  '<a href="judge_routine.php?routine_id='.$nextId['id'].'" class="float-right btn btn-secondary js-do-next" title="Label the next routine: '.$nextId['name'].'">Judge Next</a>':
  '<a href="list_routines.php" class="float-right btn btn-secondary js-do-next" title="None left to judge">Back to Routines</a>';

$title = 'Judge Routine';
// $navIndex = 1;
addHeader();
?>

<h4>
  <?=$routine['name']?>
  <small><?=$routine['level']?></small>
</h4>
<p>
  Tab will move along skills. Use Up and Down arrow keys to change the deduction. If you're a bit rusty on the judging, check out the <a href="http://www.fig-gymnastics.com/publicdir/rules/files/tra/TRA-CoP_2017-2020-e.pdf">2017 - 2020 Code Of Points</a>, page 36 and on. <br>
  <strong>Ctrl+Enter</strong> Save.
  <strong>n</strong> Label Next.
  <strong>k</strong> Play/pause the video.
  <strong>l</strong> Play next bounce.
  <strong>j</strong> Play previous bounce.
  <strong>i</strong> Toggle looping.
  <strong>.</strong> Speed up video.
  <strong>,</strong> Slow down video.
</p>

<div class="row">
  <div class="col-md-6">
    <video src="videos/<?=$routine['name']?>" controls autobuffer style="max-width:100%"></video>

    <div style="text-align:right;">
      <div class="js-current-playback-speed">Playback Speed: 1</div>
      <div class="js-current-loop-index">No bounce looping</div>
    </div>
  </div>

  <div class="col-md-6">

    <?php if (!$isLabelled) { ?>
        <p>The bounces in this routine have not been labelled yet. Please click the button, and then come back.</p>
        <div style="text-align:center;">
          <a href="label_routine.php?routine_id=<?=$routine['id']?>" class="btn btn-primary">Label This Routine</a>
        </div>
    <?php } else { ?>

    <div class="row" style="padding-bottom:0.3rem; font-weight:bold">
      <div class="col-9">Name</div>
      <div class="col-3" style="text-align:center">Deduction</div>
    </div>

    <?php
      $count = 0;
      $startEndTimes = [];
      foreach ($bouncesJSON as $bounce) {
        if ($bounce['name'] == 'In/Out Bounce')
          continue;
        else
          array_push($startEndTimes, ["start" => $bounce['startTime'], "end" => $bounce['endTime']]);
        ?>

        <div class="row js-bounce">
          <div class="col-9">
            <span class="index"><?=$count+1?>.</span>

            <!-- Loop button -->
            <button class="btn-link btn-sm js-loop-btn" tabindex="-1">
              <i class="fa fa-repeat" aria-hidden="true"></i> <span class="hidden-xs-down">Loop</span>
            </button>

            <?=$bounce['name']?>
          </div>

          <div class="col-3" style="text-align:center">
            <!-- Don't allow judging if skill is broken -->
            <?php if ($bounce['name'] == 'Broken') { ?>
              N/A
            <?php } else { ?>
              <label for="number-input-<?=$count?>">0.</label>
              <input id="number-input-<?=$count?>" class="js-deduction" type="number" min="0" max="5" step="1" value="3" maxlength="1" size="1" style="max-width:2rem; border: 1px solid rgba(0,0,0,.15); border-radius: .25rem;">
            <?php } ?>
          </div>
        </div>

        <?php
        $count++;
      }
    ?>

    <div class="row">
      <div class="col" style="text-align:center">
        <strong>Score:</strong>
        <span class="js-score">7.0</span>
      </div>
    </div>

    <div class="row">
      <div class="col">
        <button class="btn btn-primary js-save">Save</button>
        <?=$nextBtn?>
      </div>
    </div>

    <?php } ?> <!-- else isLabelled -->
  </div> <!-- col-md-6 -->
</div>

<?php
addScripts();
?>

<script>

  VideoControls.init(
    $('video')[0],
    <?=json_encode($startEndTimes)?>,
    $('.js-bounce')
  );

  Judge.init(
    <?=$routine['id']?>,
    <?=$routine['bounces']?>
  );

</script>


<?php
addFooter();
?>
