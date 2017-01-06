<?php
require_once('../includes/db.php');
setTitle("Videos List");
?>

<p>
  Each row is a video of a routine. Label: Name the skills in a routine. Judge: Score each of the routines.
</p>

<div>
  <div class="row vid-row" style="font-weight:bold;font-size:1.1rem">
    <div class="col-md-7 col-8">Name</div>
    <div class="col-md-2 col-4">Level</div>
    <div class="col-md-2 col-10">Actions</div>
    <div class="col-md-1 col-2" style="text-align:center">Score</div>
  </div>

    <?php
    $vids = $db->query("SELECT * FROM `videos` ORDER BY id ASC");
    while($video = $vids->fetchArray(SQLITE3_ASSOC)){
      $bounceJSON = json_decode($video['bounces'], true);
      if ($bounceJSON == [])
        continue; // ignore videos that haven't been analysed yet
      $isLabelled = ($bounceJSON[0]['title'] != ""); // not the most fool proof way
      ?>

      <div class="row vid-row vid-row-hover">
        <div class="col-md-7 col-8" style="word-break: break-word;"><?=$video['name']?></div>
        <div class="col-md-2 col-4"><?=$video['level']?></div>
        <div class="col-md-2 col-10">
          <?php if ($isLabelled){?>
            <span style="padding-right:1em; color:#aaa;" title="Already labelled">Labelled</span>
          <?php } else { ?>
            <a href="#!/label/<?=$video['id']?>" style="padding-right:1em"><i class="fa fa-tag" aria-hidden="true"></i> Label</a>
          <?php }?>
          <a href="#!/judge/<?=$video['id']?>"><i class="fa fa-star-half-o" aria-hidden="true"></i> Judge</a>
        </div>
        <div class="col-md-1 col-2" title="No score yet" style="text-align:center"><span>🤷</span></div>
      </div>

      <?php
    }
    ?>

</div>

<script>
  $('[data-toggle="tooltip"]').tooltip();
</script>
