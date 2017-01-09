<?php
include_once 'includes/functions.php';
$title = 'FYP';
$navIndex = 0;
addHeader();
?>

<div class="jumbotron jumbotron-fluid">
  <div class="container">
    <h1 style="font-weight: 300;">Final Year Project</h1>
    <p class="lead">This website was made to help label and judge trampoline routine videos</p>
    <div>Click the Routines link to get to the action.</div>
  </div>
</div>

<h3>Tally</h3>
<?php
  $routines = $db->query("SELECT * FROM routines WHERE bounces!='[]' ORDER BY id ASC");
  $allBounceNames = [];
  $isLabelledCount = 0;
  while($routine = $routines->fetchArray(SQLITE3_ASSOC)){
    $bouncesJSON = json_decode($routine['bounces'], true);
    $isLabelled = ($bouncesJSON[0]['name'] != ""); // not the most fool proof way
    if ($isLabelled){
      $isLabelledCount+=1;
    }

    foreach ($bouncesJSON as $bounce) {
      array_push($allBounceNames, $bounce['name']);
    }
  }
  var_dump(array_count_values($allBounceNames));
  foreach (array_count_values($allBounceNames) as $name => $count) { ?>
    <!-- <canvas id="myChart" width="400" height="400"></canvas>
    <script>
    var ctx = document.getElementById("myChart");
    var myChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ["Red", "Blue", "Yellow", "Green", "Purple", "Orange"],
            datasets: [{
                label: '# of Votes',
                data: [12, 19, 3, 5, 2, 3],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                    'rgba(255, 159, 64, 0.2)'
                ],
                borderColor: [
                    'rgba(255,99,132,1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero:true
                    }
                }]
            }
        }
    });
    </script> -->
<?php
  }
addFooter();
?>
