<?php
require_once('../includes/db.php');

$videoQuery = $db->query("SELECT * FROM videos WHERE id=".$_GET['video_id']." LIMIT 1");
$video = $videoQuery->fetchArray(SQLITE3_ASSOC);
$bounceJSON = json_decode($video['bounces'], true);

setTitle('Judge Routines');
?>

<h4>
  <?=$video['name']?>
  <small><?=$video['level']?></small>
</h4>
<p>
  Tab will move along skills. Use Up and Down arrow keys to change the deduction.
</p>

<div class="row">
  <div class="col-md-6">
    <video src="videos/<?=$video['name']?>" controls style="max-width:100%"></video>

    <p class="clearfix">
      <button class="btn btn-primary js-save">Save</button>

      <span class="float-right" style="padding: .5rem 1rem;">
        <strong>Score:</strong>
        <span class="js-score">7.0</span>
      </span>
    </p>

    <div class="alert alert-success alert-dismissible" style="display:none" role="alert">
      <button type="button" class="close" data-dismiss="alert" aria-label="Close">
        <span aria-hidden="true">&times;</span>
      </button>
      <strong>Saved!</strong> Thank you mucho.
    </div>
  </div>

  <div class="col-md-6">
    <div class="row" style="padding-bottom:0.3rem; font-weight:bold">
      <div class="col-8">Name</div>
      <div class="col-4" style="text-align:center">Deduction</div>
    </div>

    <?php
      $count = 1;
      foreach ($bounceJSON as $bounce) {
        if ($bounce['name'] == 'In/Out Bounce')
          continue;
        ?>

        <div class="row js-bounce">
          <div class="col-8">
            <span class="index"><?=$count?>.</span>
            <?=$bounce['name']?></div>
          <div class="col-4" style="text-align:center">
            <label for="number-input-<?=$count?>">0.</label>
            <input id="number-input-<?=$count?>" class="js-deduction" type="number" min="0" max="5" step="1" value="3" maxlength="1" size="1" style="max-width:2rem; border: 1px solid rgba(0,0,0,.15); border-radius: .25rem;">
          </div>
        </div>

        <?php
        $count++;
      }
    ?>

  </div>
</div>

<script>

  var Engine = {
    // Static vars
    vid: null,
    start: function() {
      this.vid = $('video')[0];
      this.bindUIActions();

      $('.js-deduction')[0].focus();

      $(".alert").alert();
    },
    calculateScore: function(){
      numBounces = $('.js-deduction').length;
      if (numBounces > 10) numBounces = 10;
      totalDeductions = 0;
      for (var i = 0; i < numBounces; i++) {
        totalDeductions += parseInt($('.js-deduction')[i].value)/10;
      }
      score = 10 - totalDeductions;
      $('.js-score').text(score.toFixed(1));
    },
    bindUIActions: function(){
      // Number input validation
      $('.js-deduction').on('input', function(){
        // leave empty if nan
        if (isNaN($(this).val())){
          $(this).val("0");
        }
        else if ($(this).val() < 0){
          $(this).val("0");
        }
        else if ($(this).val() > 5){
          $(this).val("5");
        }

        Engine.calculateScore();
      });

      $('.js-deduction').on('focus', function(){
        this.select();
      });


      // Save deduction to server
      $('.js-save').click(function(){
        $('.js-save').text('Saving...');

        // Get the deductions for all skills
        deductions = [];
        for (var i = 0; i < $(".js-deduction").length; i++) {
          deductions.push($(".js-deduction")[i].value);
        }

        // Send to server
        $.post({
          url: "includes/ajax.db.php",
          data: "action=judge" +
            "&id=<?=$_GET['video_id']?>"+
            "&deductions=" + JSON.stringify(deductions),
          dataType: "text",
          success: function (data) {
            $('.js-save').text('Save');
            $('.alert').show();
            if (data !== "") {
              $('.alert').html("<strong>Something went wrong:</strong> "+data);
            }
          }
        });
      });
    }
  };

  Engine.start();

</script>
