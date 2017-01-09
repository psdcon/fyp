<?php
include_once 'includes/functions.php';

$routineQuery = $db->query("SELECT * FROM routines WHERE id=".$_GET['routine_id']." LIMIT 1");
$routine = $routineQuery->fetchArray(SQLITE3_ASSOC);
$bouncesJSON = json_decode($routine['bounces'], true);

// Create link to next unlabelled routine
$nextLabelIdQuery = $db->query("SELECT * FROM routines WHERE id>".$_GET['routine_id']." AND bounces LIKE '%\"name\": \"\"%' LIMIT 1");
$nextLabelId = $nextLabelIdQuery->fetchArray(SQLITE3_ASSOC);
$labelNextBtn = ($nextLabelId)?
  '<a href="label_routine.php?routine_id='.$nextLabelId['id'].'" class="btn btn-secondary js-label-next" title="'.$nextLabelId['name'].'">Label Next</a>':
  '<a href="list_routines.php" class="btn btn-secondary js-label-next" title="None left to label">Back to Routines</a>';


$title = 'Label Routine';
$navIndex = 1;
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
  <strong>l</strong> Loop next bounce.
  <strong>j</strong> Loop previous bounce.
  <strong>i</strong> Stop looping.
  <strong>.</strong> Speed up video.
  <strong>,</strong> Slow down video.
</p>

<div class="row">
  <div class="col-md-6">
    <video src="videos/<?=$routine['name']?>" controls autobuffer style="max-width:100%"></video>
    <div class="row">
      <div class="col-sm">
        <?=$labelNextBtn?>
        <button class="btn btn-primary js-save">Save</button>
      </div>
      <div class="col-sm" style="text-align:right">
        <div class="js-current-playback-speed">Playback Speed: 1</div>
        <div class="js-current-loop-index">No bounce looping</div>
      </div>
    </div>

    <div class="alert alert-success alert-dismissible" style="display:none" role="alert">
      <button type="button" class="close" data-dismiss="alert" aria-label="Close">
        <span aria-hidden="true">&times;</span>
      </button>
      <strong>Saved!</strong> Thank you mucho.
    </div>
  </div>
  <div class="col-md-6">

    <?php
      $startEndTimes = [];
      foreach ($bouncesJSON as $i => $bounce) {
        array_push($startEndTimes, ["start" => $bounce['startTime'], "end" => $bounce['endTime']]);
        ?>

        <div class="row js-bounce">
          <!-- Index -->
          <span class="index"><?=($i+1)?>.</span>
          <!-- Loop button -->
          <button class="btn-link btn-sm js-loop-btn">
            <i class="fa fa-repeat" aria-hidden="true"></i> <span class="hidden-xs-down">Loop</span>
          </button>
          <!-- Select skill -->
          <select class="js-select2" style="width:80%"></select>
        </div>

        <?php
      }
    ?>

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
    <?=$routine['bounces']?>
  );

</script>

<?php
addFooter();
?>
