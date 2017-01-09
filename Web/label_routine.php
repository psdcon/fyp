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
      foreach ($bouncesJSON as $i => $bounce) {
        ?>

        <div class="row js-bounce" style="margin-bottom:0.3rem">
          <!-- Index -->
          <span class="index"><?=($i+1)?>.</span>
          <!-- Loop button -->
          <button class="btn-link btn-sm js-loop-btn" data-index="<?=$i?>" data-start="<?=$bounce['startTime']?>" data-end="<?=$bounce['endTime']?>">
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
addFooter();
?>

<script>

  var Engine = {
    // Static vars
    vid: null,
    loopStartTime: 0,
    loopEndTime: 0,
    intervalRate: 28,

    currentlyLoopingIndex: -1, // set -1 so that when 'l' is pressed it starts looping at 0
    previousHighlightedRow: -1,

    bounces: <?=$routine['bounces']?>,
    skillNames: select2SkillNameData,

    loopingTrue: "Looping bounce ",
    loopingFalse: "No bounce looping",

    go: function() {
      this.vid = $('video')[0];
      this.select2Setup();
      this.bindUIActions();

      $(".alert").alert();

      // Preload selects with the names for each skill
      for (var i = 0; i < Engine.bounces.length; i++) {
        if (Engine.bounces[i].name)
          $(".js-select2")[i].value = Engine.bounces[i].name;
      }
      $(".js-select2").trigger('change');

    },
    select2Setup: function(){
      // Set up select2 inputs
      $(".js-select2")
        .select2({
          data: Engine.skillNames
        })
        // Any time the select2 dropdown is closed, give it focus. otherwise focus disappears, which sucks
        .on("select2:close", function (e) {
          $(this).focus();
        });
    },
    bindUIActions: function(){
      // Push.pushButton.addEventListener('change', function () {});
      // Play pause vid when 'k' pressed
      document.addEventListener('keyup', function (e) {
        if (e.ctrlKey) {
          if (e.keyCode == 13){
          // Ctrl+Enter
            Engine.save();
          }
          return
        }

        // Ignore keypress if inside select2 input
        if ($(":focus").is($(".select2-search__field")))
          return;
        console.log(e.keyCode)
        if (e.keyCode == 75){ // k
          if (Engine.vid.paused)
            Engine.vid.play();
          else {
            Engine.vid.pause();
          }
        }
        else if (e.keyCode == 74){ // j, next bounce
          // Engine.previousBounce()
          nextLoopIndex = Engine.currentlyLoopingIndex-1
          if (nextLoopIndex < 0)
            nextLoopIndex = Engine.bounces.length-1;
          $('.js-loop-btn').eq(nextLoopIndex).trigger("click");
        }
        else if (e.keyCode == 76){ // l, previous bounce
          // Engine.nextBounce()
          nextLoopIndex = Engine.currentlyLoopingIndex+1
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
                $('.js-loop-btn').eq(i).parent().addClass('highlightSkill')
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

      $('.js-stop-loop').click(function(){
        $('.js-current-loop-index').text(Engine.loopingFalse);
        Engine.loopEndTime = 0;
      });

      $('.js-save').click(Engine.save);
    },
    videoSpeed:function(amount){
      newPbr = this.vid.playbackRate + amount;
      if (newPbr > 2){
        newPbr = 2
      }
      else if (newPbr < 0.25){
        newPbr = 0.25
      }
      console.log(newPbr);
      this.vid.playbackRate = newPbr;
      $('.js-current-playback-speed').text('Playback Speed: '+newPbr);
    },
    save: function(){
      $('.js-save').text('Saving...');

      // Get the names for each skill
      for (var i = 0; i < $(".js-select2").length; i++) {
        Engine.bounces[i].name = $(".js-select2")[i].value;
      }

      // Send to server
      $.post({
        url: "includes/ajax.db.php",
        data: "action=updateBounces" +
          "&id=<?=$_GET['routine_id']?>"+
          "&bounces=" + JSON.stringify(Engine.bounces),
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

  Engine.go();

</script>
