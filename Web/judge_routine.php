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
      <div class="col-8">Name</div>
      <div class="col-4" style="text-align:center">Deduction</div>
    </div>

    <?php
      $count = 1;
      foreach ($bouncesJSON as $bounce) {
        if ($bounce['name'] == 'In/Out Bounce')
          continue;
        ?>

        <div class="row js-bounce">
          <div class="col-9">
            <span class="index"><?=$count?>.</span>

            <!-- Loop button -->
            <button class="btn-link btn-sm js-loop-btn" data-index="<?=$count?>" data-start="<?=$bounce['startTime']?>" data-end="<?=$bounce['endTime']?>">
              <i class="fa fa-repeat" aria-hidden="true"></i> <span class="hidden-xs-down">Loop</span>
            </button>

            <?=$bounce['name']?>
          </div>

          <div class="col-3" style="text-align:center">
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

<?php
addFooter();
?>

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
      $('.js-deduction').on('input', function(e){
        // leave empty if nan
        if (!$.isNumeric($(this).val())){
          $(this).val("");
        }
        else if ($(this).val() < 0){
          $(this).val("0");
        }
        else if ($(this).val() > 5){
          $(this).val("5");
        }

        Engine.calculateScore();
      });

      // Push.pushButton.addEventListener('change', function () {});
      // Play pause vid when 'k' pressed
      document.addEventListener('keyup', function (e) {
        if (e.ctrlKey) {
          if (e.keyCode == 13){
          // Ctrl+Enter
            Engine.save();
          }
          return;
        }

        console.log(e.keyCode);
        if (e.keyCode == 75){ // k
          if (Engine.vid.paused)
            Engine.vid.play();
          else {
            Engine.vid.pause();
          }
        }
        else if (e.keyCode == 74){ // j, next bounce
          // Engine.previousBounce()
          nextLoopIndex = Engine.currentlyLoopingIndex-1;
          if (nextLoopIndex < 0)
            nextLoopIndex = Engine.bounces.length-1;
          $('.js-loop-btn').eq(nextLoopIndex).trigger("click");
        }
        else if (e.keyCode == 76){ // l, previous bounce
          // Engine.nextBounce()
          nextLoopIndex = Engine.currentlyLoopingIndex+1;
          if (nextLoopIndex > Engine.bounces.length-1)
            nextLoopIndex = 0;
          $('.js-loop-btn').eq(nextLoopIndex).trigger("click");
        }
        else if (e.keyCode == 73){ // i, stop looping
          $('.js-current-loop-index').text(Engine.loopingFalse);
          Engine.loopEndTime = 0;
        }
        else if (e.keyCode == 188){ // ',', slow down
          Engine.videoSpeed(-0.25);
        }
        else if (e.keyCode == 190){ // '.', speed up
          Engine.videoSpeed(+0.25);
        }
        else if (e.keyCode == 78){ // 'n', label next
          $('.js-label-next').text('Going...');
          $('.js-label-next')[0].click();
        }
      }, false);

      setInterval(function(){
        // Do looping if skill set to loop
        if (Engine.loopEndTime > 0 // acts as an enable
            && Engine.vid.currentTime >= Engine.loopEndTime){
          Engine.vid.currentTime = Engine.loopStartTime;
        }

        // Highlight background
        // $('.js-bounce');
        for (var i = 0; i < $('.js-loop-btn').length; i++) {
          var start = $('.js-loop-btn').eq(i).data('start');
          var end = $('.js-loop-btn').eq(i).data('end');

          // Update the current move to the one being shown. Happens every 25 ms.
          ct = Engine.vid.currentTime;
          if (ct >= start && ct < end && i != Engine.previousHighlightedRow){
            // Remove highlightSkill from any old rows and add it to the current row element. Old happens when current skill changes.
            $('.highlightSkill').removeClass('highlightSkill');
            // $rows.eq(i).addClass('highlightSkill');
            $('.js-loop-btn').eq(i).parent().addClass('highlightSkill');
            Engine.previousHighlightedRow = i;
            break; // leave the loop
          }
        }
      }, Engine.intervalRate);

      $('.js-loop-btn').click(function () {
        var start = $(this).data('start');
        var end = $(this).data('end');
        var thisBtnIndex = $(this).data('index');

        Engine.currentlyLoopingIndex = thisBtnIndex;
        $('.js-current-loop-index').text(Engine.loopingTrue+(thisBtnIndex+1));

        Engine.loopStartTime = start;
        Engine.loopEndTime = end;
        Engine.vid.currentTime = Engine.loopStartTime;
        if (Engine.vid.paused)
          Engine.vid.play();
      });

      $('.js-save').click(Engine.save);
    },
    videoSpeed:function(amount){
      newPbr = this.vid.playbackRate + amount;
      if (newPbr > 2){
        newPbr = 2;
      }
      else if (newPbr < 0.25){
        newPbr = 0.25;
      }
      console.log(newPbr);
      this.vid.playbackRate = newPbr;
      $('.js-current-playback-speed').text('Playback Speed: '+newPbr);
    },
    save: function(){
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
          "&id=<?=$_GET['routine_id']?>"+
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
    }

  };

  Engine.start();

</script>
