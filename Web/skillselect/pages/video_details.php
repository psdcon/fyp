<?php
require_once('../includes/db.php');

$videoQuery = mysqli_query($db, "SELECT * FROM videos WHERE id=".$_GET['video_id']." LIMIT 1");
$video = mysqli_fetch_assoc($videoQuery);

$bounceJSON = json_decode($video['bounces'], true);

setTitle('Video Select Skills');
?>

<h4><?=$video['name']?></h4>
<div class="row">
  <div class="col-md-6">
    <video src="videos/<?=$video['name']?>" controls style="max-width:100%"></video>
    <div class="js-current-loop-index">No bounce looping</div>

    <button class="btn btn-primary js-save">Save</button>
    <div class="pull-right">
      <button class="btn btn-secondary js-stop-loop">Stop Looping</button>
      <button class="btn btn-secondary js-loop-next">Loop Next</button>
    </div>
  </div>
  <div class="col-md-6">

    <?php
      foreach ($bounceJSON as $i => $bounce) {
        ?>

        <div class="row js-bounce" style="padding-bottom:0.3rem">
          <!-- Index -->
          <span class="index"><?=($i+1)?>.</span>
          <!-- Loop button -->
          <button class="btn-link js-loop-btn" data-index="<?=$i?>" data-start="<?=$bounce['end'][0]?>" data-end="<?=$bounce['start'][0]?>">
            <i class="fa fa-repeat" aria-hidden="true"></i> Loop
          </button>
          <!-- Select skill -->
          <select class="js-select2" style="width:80%"></select>
        </div>

        <?php
      }
    ?>

  </div>
</div>

<script>

  var Engine = {
    // Static vars
    fps: 30,
    vid: null,
    loopStartTime: 0,
    loopEndTime: 0,
    refreshRate: 25,
    lastBtnClicked: 0,
    bounces: <?=$video['bounces']?>,
    skillNames: <?=getAllSkillNamesJSON()?>,

    loopingTrue: "Looping bounce ",
    loopingFalse: "No bounce looping",

    go: function() {
      this.select2Setup();
      this.bindUIActions();
      this.vid = $('video')[0];

      setInterval(function(){
        // Do looping if skill set to loop
        if (Engine.loopEndTime > 0 && Engine.vid.currentTime > Engine.loopEndTime){
          Engine.vid.currentTime = Engine.loopStartTime;
        }

        // Highlight background
        $('.js-bounce');
      }, this.refreshRate);

      // Get the names for each skill
      for (var i = 0; i < $(".js-select2").length; i++) {
        $(".js-select2")[i].value = Engine.bounces[i].title;
        $(".js-select2").eq(i).trigger('change');
      }

    },
    select2Setup: function(){
      // Set up select2 inputs
      $(".js-select2").select2({
        data: Engine.skillNames
      });
    },
    bindUIActions: function(){
      // Push.pushButton.addEventListener('change', function () {});

      $('.js-loop-btn').click(function () {
        var start = $(this).data('start');
        var end = $(this).data('end');
        var thisBtnIndex = $(this).data('index');

        Engine.lastBtnClicked = thisBtnIndex;
         $('.js-current-loop-index').text(Engine.loopingTrue+(thisBtnIndex+1));

        Engine.loopStartTime = start/Engine.fps;
        Engine.loopEndTime = end/Engine.fps;
        Engine.vid.currentTime = Engine.loopStartTime;
      });

      $('.js-loop-next').click(function(){
        $('.js-loop-btn').eq(Engine.lastBtnClicked+1).trigger("click");
      });

      $('.js-stop-loop').click(function(){
        $('.js-current-loop-index').text(Engine.loopingFalse);
        Engine.loopEndTime = 0;
      });

      $('.js-save').click(function(){
        console.log("Saving")
        $('.js-save').text('Saving...');

        // Get the names for each skill
        for (var i = 0; i < $(".js-select2").length; i++) {
          Engine.bounces[i].title = $(".js-select2")[i].value;
        }

        // Send to server
        $.post({
          url: "includes/ajax.db.php",
          data: "action=updateBounces" +
            "&id=<?=$_GET['video_id']?>"+
            "&bounces=" + JSON.stringify(Engine.bounces),
          dataType: "text",
          success: function (data) {
            console.log(data)
            $('.js-save').text('Save');
          }
        });
      });
    }
  };

  Engine.go();

</script>
