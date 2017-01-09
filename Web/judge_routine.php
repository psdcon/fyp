<?php
include_once 'includes/functions.php';

$routineQuery = $db->query("SELECT * FROM routines WHERE id=".$_GET['routine_id']." LIMIT 1");
$routine = $routineQuery->fetchArray(SQLITE3_ASSOC);
$bouncesJSON = json_decode($routine['bounces'], true);

$title = 'Judge Routine';
$navIndex = 1;
addHeader();
?>

<h4>
  <?=$routine['name']?>
  <small><?=$routine['level']?></small>
</h4>
<p>
  Tab will move along skills. Use Up and Down arrow keys to change the deduction. <br>
  <strong>Ctrl+Enter</strong> Save.
  <!-- <strong>n</strong> Label Next. -->
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
        <!-- <a href="#!/judge/<?=($_GET['routine_id']+1)?>" class="btn btn-secondary">Judge Next</a> -->
        <button class="btn btn-primary js-save">Save</button>
      </div>
      <div class="col-sm" style="text-align:right">
        <div class="js-current-playback-speed">Playback Speed: 1</div>
        <div>
          <strong>Score:</strong>
          <span class="js-score">7.0</span>
        </div>
      </div>
    </div>

    <!-- Saved pop up box -->
    <div class="alert alert-success alert-dismissible" style="display:none" role="alert">
      <button type="button" class="close" data-dismiss="alert" aria-label="Close">
        <span aria-hidden="true">&times;</span>
      </button>
      <strong>Saved!</strong> Thank you mucho.
    </div>
  </div>

  <div class="col-md-6">

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
            <button class="btn-link btn-sm js-loop-btn">
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

  Judge.init();

</script>


<?php
addFooter();
?>
