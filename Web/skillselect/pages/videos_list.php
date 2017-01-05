<?php
require_once('../includes/db.php');
setTitle("Videos List");

// http://stackoverflow.com/questions/79960/how-to-truncate-a-string-in-php-to-the-word-closest-to-a-certain-number-of-chara
// not first answer
function stringShorten($string, $desiredLen = 100) {
  if (strlen($string) <= $desiredLen) {
    return $string;
  }
  return preg_replace('/\s+?(\S+)?$/', '', substr($string, 0, $desiredLen))."...";
}
?>

<h2>Videos</h2>
<p>
  Select a video to which to assign skills
</p>
<br>

<div class="vids">
<?php

  $vids = mysqli_query($db, "SELECT * FROM videos ORDER BY id ASC");
  while($vid = mysqli_fetch_assoc($vids)){
    ?>

    <div class="row vid-row vid-row-hover" ng-click="go('/videos/<?=$vid['id']?>')">
      <div class="col-md-2"><?=$vid['id']?>. <?=$vid['level']?></div>
      <div class="col-md-10"><?=$vid['name']?></div>
    </div>

    <?php
  }
?>
</div>

<script>
  $('[data-toggle="tooltip"]').tooltip();
</script>
