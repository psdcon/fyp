<?php
include_once 'includes/functions.php';
$routineId = $db->escapeString($_GET['routine_id']);

$routineQuery = $db->query("SELECT * FROM routines WHERE id=$routineId LIMIT 1");
$routine = $routineQuery->fetchArray(SQLITE3_ASSOC);
$bouncesJSON = json_decode($routine['bounces'], true);

// Create link to next unlabelled routine
$nextIdQuery = $db->query("SELECT * FROM routines WHERE id>$routineId AND bounces LIKE '%\"name\": \"\"%' LIMIT 1");
$nextId = $nextIdQuery->fetchArray(SQLITE3_ASSOC);
$nextBtn = ($nextId)?
  '<a href="label_routine.php?routine_id='.$nextId['id'].'" class="float-right btn btn-secondary js-do-next" title="Label the next routine: '.$nextId['name'].'">Label Next</a>':
  '<a href="list_routines.php" class="float-right btn btn-secondary js-do-next" title="None left to label">Back to Routines</a>';


$title = 'Label Routine';
// $navIndex = 1;
addHeader();
?>

<h4>
  <?=$routine['name']?>
  <small><?=$routine['level']?></small>
</h4>
<p>
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

    <div class="col-sm" style="text-align:right">
      <div class="js-current-playback-speed">Playback Speed: 1</div>
      <div class="js-current-loop-index">No bounce looping</div>
    </div>

  </div>

  <div class="col-md-6">

    <?php
      $startEndTimes = [];
      foreach ($bouncesJSON as $i => $bounce) {
        array_push($startEndTimes, ["start" => $bounce['startTime'], "end" => $bounce['endTime']]);
        ?>

        <div class="js-bounce" style="display:flex">
          <!-- Index -->
          <span class="index"><?=($i+1)?>.</span>
          <!-- Loop button -->
          <button class="btn-link btn-sm js-loop-btn">
            <i class="fa fa-repeat" aria-hidden="true"></i> <span class="hidden-xs-down">Loop</span>
          </button>
          <!-- Select skill -->
          <span style="flex-grow:1">
            <select class="js-select2" style="width:100%"></select>
          </span>
        </div>

        <?php
      }
    ?>

   <div style="padding-top: 0.5em;">
      <button class="btn btn-primary js-save">Save</button>
      <a href="judge_routine.php?routine_id=<?=$routineId?>" class="float-right btn btn-secondary js-do-next" style="margin-left: 0.3rem;" title="Judge this Routine">Judge This</a>
      <?=$nextBtn?>
   </div>
  </div>
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

  Label.init(
    <?=$routine['id']?>,
    <?=$routine['bounces']?>
  );

</script>

<?php
addFooter();
?>
