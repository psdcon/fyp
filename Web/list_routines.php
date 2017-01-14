<?php
include_once 'includes/functions.php';
$title = "List of Routines";
$navIndex = 1;
addHeader();
?>

<p>
  Each row is a video of a routine. Frowny face means something went wrong with the tracking and there are two skills labelled as one.<br>
  <strong>Label</strong>: Name the skills in a routine. <br>
  <strong>Judge</strong>: Score each of the routines.
</p>

<div class="row vid-row" style="font-weight:bold;font-size:1.1rem">
  <div class="col-md-7 col-8">Name</div>
  <div class="col-md-2 col-4">Level</div>
  <div class="col-md-2 col-8">Actions</div>
  <div class="col-md-1 col-4" style="text-align:center">Score</div>
</div>

<?php
$routines = $db->query("SELECT * FROM routines WHERE bounces!='[]' ORDER BY id ASC");
while($routine = $routines->fetchArray(SQLITE3_ASSOC)){
  $bouncesJSON = json_decode($routine['bounces'], true);
  $isLabelled = ($bouncesJSON[0]['name'] != ""); // not the most fool proof way

  $isBroken = false;
  foreach ($bouncesJSON as $key => $bounce) {
    if ($bounce['name'] == 'Broken'){
      $isBroken = True;
    }
  }

  // Check to see if this users has judged this routine
  $isJudged = false;
  $userId = $db->escapeString($_COOKIE['userId']);
  $judgementsQuery = $db->query("SELECT * FROM judgements WHERE routine_id=".$routine['id']." AND user_id='$userId' ORDER BY id DESC LIMIT 1");
  while ($judgements = $judgementsQuery->fetchArray(SQLITE3_ASSOC)){
    $isJudged = True;
    $deductions = json_decode($judgements['deductions'], true);
    $first_10_deductions = array_slice($deductions, 0, 10);
    $score = count($first_10_deductions) - array_sum($first_10_deductions);
  }
  ?>

  <div class="row vid-row">
    <div class="col-md-7 col-8" style="word-break: break-word;"><?=$routine['name']?></div>
    <div class="col-md-2 col-4">
      <?=$routine['level']?>
      <?=($isBroken)?'<i class="fa fa-frown-o" aria-hidden="true" title="Indicates one of the skills are broken"></i>':''?>
    </div>
    <div class="col-md-2 col-8">
      <?php if ($isLabelled){?>
        <span style="padding-right:1em; color:#aaa;" title="Already labelled">Labelled</span>
        <a href="judge_routine.php?routine_id=<?=$routine['id']?>" style="white-space: nowrap">
          <?php if ($isJudged) { ?>
            <i class="fa fa-star" aria-hidden="true"></i> Judged
          <?php } else { ?>
            <i class="fa fa-star-o" aria-hidden="true"></i> Judge
          <?php } ?>
        </a>
      <?php } else { ?>
        <a href="label_routine.php?routine_id=<?=$routine['id']?>" style="white-space: nowrap;padding-right:1rem;"><i class="fa fa-tag" aria-hidden="true"></i> Label</a>
        <span style="padding-right:1em; color:#aaa; white-space: nowrap;" title="Label first"><i class="fa fa-star-o" aria-hidden="true"></i> Judge</span>
      <?php }?>
    </div>
    <div class="col-md-1 col-4" title="No score yet" style="text-align:center">
      <?=($isJudged)? $score: 'N/A'?>
    </div>
  </div>

  <?php
}
addScripts();
addFooter();
?>

