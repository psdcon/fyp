<?php
include_once 'includes/functions.php';
$title = 'FYP';
$navIndex = 0;
addHeader();
?>

<div class="jumbotron jumbotron-fluid">
  <div class="container">
    <h1 style="font-weight: 300;">Final Year Project</h1>
    <p class="lead">This website was made to help label and judge trampoline routine videos.</p>
    <div>Click the <a href="list_routines.php">Routines</a> link to get to the action.</div>
  </div>
</div>

<h3>Tally</h3>
<?php
  // Vars for counting
  $isLabelledCount = 0;
  $routinesCount = 0;
  $bounceCount = 0;
  $bounceLabelledCount = 0;
  $routinesJudgedCount = 0;
  // Thee data array
  $labelledBounceData = [];
  // Populate array by looping through all tracked routines
  $routines = $db->query("SELECT * FROM routines WHERE bounces!='[]' ORDER BY id ASC");
  while ($routine = $routines->fetchArray(SQLITE3_ASSOC)){
    $bouncesJSON = json_decode($routine['bounces'], true);
    $isLabelled = ($bouncesJSON[0]['name'] != ""); // not the most fool proof way
    // Count
    $routinesCount++;
    if ($isLabelled){
      $isLabelledCount += 1;
    }

    // Get a judgement (currently the first) of this routine. If no judgement, deductions is null.
    $deductions = null;
    $judgementsQuery = $db->query("SELECT * FROM judgements WHERE routine_id=".$routine['id']." ORDER BY id ASC LIMIT 1");
    while ($judgements = $judgementsQuery->fetchArray(SQLITE3_ASSOC)){
      $routinesJudgedCount++;
      $deductions = json_decode($judgements['deductions'], true);
    }

    // Populate data array by looping through each bounce in the routine
    foreach ($bouncesJSON as $i => $bounce) {
      $bounceCount++;

      // Give unlabelled bounce a prettier name. Also saves from a JS error
      if ($bounce['name'] == ""){
        $bounce['name'] = "Not Labelled";
      }
      else{
        // Bounce has been labelled, increment that count
        $bounceLabelledCount++;
      }

      // If entry for this bounce name doesn't exist yet, create it
      if (!isset($labelledBounceData[$bounce['name']])){
        $labelledBounceData[$bounce['name']] = [
          "count" => 1,
          "judgements" => [
            "0.0" => 0,
            "0.1" => 0,
            "0.2" => 0,
            "0.3" => 0,
            "0.4" => 0,
            "0.5" => 0
          ]
        ];
      }
      else {
        // Assoc entry exists. Increment it's count
        $labelledBounceData[$bounce['name']]['count']++;
      }
      // If this skill has been judged, increment its entry.
      if (isset($deductions[$i])){
        $labelledBounceData[$bounce['name']]['judgements'][$deductions[$i]]++;
      }
    }
  }

  // Comparison function
  // Sorts $labelledBounceData DESC by the value of each entry's 'count' value
  function cmp($a, $b) {
      if ($a['count'] == $b['count']) {return 0;}
      return ($a['count'] > $b['count']) ? -1 : 1;
  }
  uasort($labelledBounceData, 'cmp');

  // Calculate percentages, for fun
  $labelPercentComplete = (int) (($bounceLabelledCount/$bounceCount)*100);
  $judgePercentComplete = (int) (($routinesJudgedCount/$isLabelledCount)*100);

  // All routines in database, included untracked
  $totalRoutinesCountQuery = $db->query("SELECT count(1) AS c FROM routines");
  $totalRoutinesCount = $totalRoutinesCountQuery->fetchArray(SQLITE3_ASSOC)['c'];
  $trackedPercentComplete = (int) (($routinesCount/$totalRoutinesCount)*100)

?>

  <div class="row">

    <div class="col-md" style="padding-bottom: 1rem">
      Tracked <?=$routinesCount?> of <?=$totalRoutinesCount?> recorded routines.
      <div class="progress">
        <div class="progress-bar bg-warning" role="progressbar" style="width: <?=$trackedPercentComplete?>%" aria-valuenow="<?=$trackedPercentComplete?>" aria-valuemin="0" aria-valuemax="100"><?=$trackedPercentComplete?>%</div>
      </div>
    </div>

    <div class="col-md" style="padding-bottom: 1rem">
      Labelled <?=$isLabelledCount?> of <?=$routinesCount?> tracked routines.
      <div class="progress">
        <div class="progress-bar bg-success" role="progressbar" style="width: <?=$labelPercentComplete?>%" aria-valuenow="<?=$labelPercentComplete?>" aria-valuemin="0" aria-valuemax="100"><?=$labelPercentComplete?>%</div>
      </div>
    </div>

    <div class="col-md" style="padding-bottom: 1rem">
      Judged <?=$routinesJudgedCount?> of <?=$isLabelledCount?> labelled routines.
      <div class="progress">
        <div class="progress-bar bg-info" role="progressbar" style="width: <?=$judgePercentComplete?>%" aria-valuenow="<?=$judgePercentComplete?>" aria-valuemin="0" aria-valuemax="100"><?=$judgePercentComplete?>%</div>
      </div>
    </div>

  </div>
<!--
  <div class="row">
    <div class="col">
      Labelled <?=$bounceLabelledCount?> of <?=$bounceCount?> bounces. Total of <?=count($labelledBounceData)?> individual skills
    </div>
  </div> -->

  <div class="row">

  <?php
  foreach ($labelledBounceData as $bounceName => $bounceData) {
    if ($bounceName == "Broken")
      continue;
    // Strip ASSOC keys so that only data is left. This is picked up by Chart.datasets.data
    $judgementsCount = array_sum(array_values($bounceData['judgements']));
    $chartData = json_encode(array_values($bounceData['judgements']));
    ?>
    <div class="col-sm-6 col-md-4 col-lg-3">

      <div class="card" style="margin-bottom:1rem;">
        <div class="card-block">

          <h6 class="card-title">
            <?=$bounceName?>
            <small class="float-right"><?=$judgementsCount?>/<?=$bounceData['count']?></small>
          </h6>

          <canvas id="<?=$bounceName?>" data-chart-data="<?=$chartData?>" style="width:100%;"></canvas>

          <div style="text-align:center">
            <small>Deduction</small>
          </div>

        </div> <!-- card block -->
      </div> <!-- card -->

    </div> <!-- col -->
<?php
  }
?>

</div> <!-- row -->

<?php
  addScripts();
?>

<script>
  Tally.init();
</script>

<?php
addFooter();
?>

