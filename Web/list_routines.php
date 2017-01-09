<?php
include_once 'includes/functions.php';
$title = "List of Routines";
$navIndex = 1;
addHeader();
?>

<p>
  Each row is a video of a routine. Label: Name the skills in a routine. Judge: Score each of the routines.
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
  ?>

  <div class="row vid-row vid-row-hover">
    <div class="col-md-7 col-8" style="word-break: break-word;"><?=$routine['name']?></div>
    <div class="col-md-2 col-4"><?=$routine['level']?></div>
    <div class="col-md-2 col-8">
      <?php if ($isLabelled){?>
        <span style="padding-right:1em; color:#aaa;" title="Already labelled">Labelled</span>
        <a href="judge_routine.php?routine_id=<?=$routine['id']?>"><i class="fa fa-star-half-o" aria-hidden="true"></i> Judge</a>
      <?php } else { ?>
        <a href="label_routine.php?routine_id=<?=$routine['id']?>" style="padding-right:1em"><i class="fa fa-tag" aria-hidden="true"></i> Label</a>
        <span style="padding-right:1em; color:#aaa;" title="Label first"><i class="fa fa-star-half-o" aria-hidden="true"></i> Judge</span>
      <?php }?>
    </div>
    <div class="col-md-1 col-4" title="No score yet" style="text-align:center"><span>N/A</span></div>
  </div>

  <?php
}
addFooter();
?>

