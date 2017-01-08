<?php
require_once('../includes/db.php');

$videoQuery = $db->query("SELECT * FROM videos WHERE id=".$_GET['video_id']." LIMIT 1");
$video = $videoQuery->fetchArray(SQLITE3_ASSOC);
$bounceJSON = json_decode($video['bounces'], true);

setTitle('Label Video');
?>

<h4>
  <?=$video['name']?>
  <small><?=$video['level']?></small>
</h4>

<div class="row">
  <div class="col-md-6">
    <video src="videos/<?=$video['name']?>" controls style="max-width:100%"></video>
    <div class="js-current-loop-index" style="text-align:right">No bounce looping</div>

    <p class="clearfix">
      <button class="btn btn-primary js-save">Save</button>
        <button class="float-right btn btn-secondary js-loop-next">Loop Next</button>
        <button class="float-right btn btn-secondary js-stop-loop" style="margin-right: 0.3rem;">No Loop</button>
    </p>

    <div class="alert alert-success alert-dismissible" style="display:none" role="alert">
      <button type="button" class="close" data-dismiss="alert" aria-label="Close">
        <span aria-hidden="true">&times;</span>
      </button>
      <strong>Saved!</strong> Thank you mucho.
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

<script>

  var Engine = {
    // Static vars
    vid: null,
    loopStartTime: 0,
    loopEndTime: 0,
    intervalRate: 28,
    lastBtnClicked: 0,
    bounces: <?=$video['bounces']?>,
    skillNames: <?=getAllSkillNamesJSON()?>,

    loopingTrue: "Looping bounce ",
    loopingFalse: "No bounce looping",

    go: function() {
      this.vid = $('video')[0];
      this.select2Setup();
      this.bindUIActions();

      $(".alert").alert();

      // Preload selects with the names for each skill
      for (var i = 0; i < $(".js-select2").length; i++) {
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

      setInterval(function(){
        // Do looping if skill set to loop
        if (Engine.loopEndTime > 0 && Engine.vid.currentTime > Engine.loopEndTime){
          Engine.vid.currentTime = Engine.loopStartTime;
        }

        // Highlight background
        // $('.js-bounce');
      }, Engine.intervalRate);

      $('.js-loop-btn').click(function () {
        var start = $(this).data('start');
        var end = $(this).data('end');
        var thisBtnIndex = $(this).data('index');

        Engine.lastBtnClicked = thisBtnIndex;
         $('.js-current-loop-index').text(Engine.loopingTrue+(thisBtnIndex+1));

        Engine.loopStartTime = start;
        Engine.loopEndTime = end;
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
        $('.js-save').text('Saving...');

        // Get the names for each skill
        for (var i = 0; i < $(".js-select2").length; i++) {
          Engine.bounces[i].name = $(".js-select2")[i].value;
        }

        // Send to server
        $.post({
          url: "includes/ajax.db.php",
          data: "action=updateBounces" +
            "&id=<?=$_GET['video_id']?>"+
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
      });
    }
  };

  Engine.go();

</script>
