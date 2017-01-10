var VideoControls = {
  video: null,
  isLooping: false,
  loopStartTime: 0,
  loopEndTime: 0,
  intervalRate: 28,
  intervalInstance: null,

  loopedBounceIdx: -1, // set -1 so that when 'l' is pressed it starts looping at 0
  highlightedRowIndex: -1,

  loopingTrueStr: "Looping bounce ",
  loopingFalseStr: "No bounce looping",

  init: function(videoElement, startEndTimes, $rowsToHighlight) {
    this.video = videoElement;
    this.startEndTimes = startEndTimes;
    this.$rowsToHighlight = $rowsToHighlight;

    this.$playBackSpeed = $('.js-current-playback-speed');
    this.$loopBtns = $('.js-loop-btn');
    this.$loopBtnIndex = $('.js-current-loop-index');
    this.$doNextBtn = $('.js-do-next');

    this.bindUIActions();
  },
  bindUIActions: function () {
    var that = this;

    $(this.video).bind('play', function(e) {
      that.intervalInstance = setInterval(that.doIntervalLoop, that.intervalRate);
    });

    $(this.video).bind('stop pause', function(e) {
      clearInterval(that.intervalInstance);
    });

    // Bind 'Loop' button
    this.$loopBtns.click(function () {
      // that.loopBounce($(this).data('index'));

      thisIndex = that.$loopBtns.index($(this));
      that.loopBounce(thisIndex);
    });

    // Bind keyboard shortcuts
    document.addEventListener('keyup', function(e) {
      that.keyboardShortcuts(e);
    }, false);

  },
  loopBounce: function (index) {
    this.isLooping = true;
    this.loopedBounceIdx = index;
    this.updateLoopingMsg();

    this.loopStartTime = this.startEndTimes[index].start;
    this.loopEndTime = this.startEndTimes[index].end;

    this.video.currentTime = this.loopStartTime;

    if (this.video.paused){
      this.video.play();
    }
  },
  stopLooping: function () {
    this.isLooping = false;
    this.updateLoopingMsg();
  },
  updateLoopingMsg: function () {
    if (this.isLooping)
      this.$loopBtnIndex.text(this.loopingTrueStr+(this.loopedBounceIdx+1));
    else
      this.$loopBtnIndex.text(this.loopingFalseStr);
  },
  keyboardShortcuts: function(e) {
    // Handle Ctrl + combinations
    if (e.ctrlKey) {
      // Ctrl+Enter
      if (e.keyCode == 13){
        this.save();
      }
      // Exit
      return;
    }

    // Ignore keypress if inside select2 input
    if ($(":focus").is($(".select2-search__field")))
      return;

    // console.log(e.keyCode);
    // k = play.pause video
    if (e.keyCode == 75){ // k
      if (this.video.paused)
        this.video.play();
      else {
        this.video.pause();
      }
    }
    // j = loop next bounce
    else if (e.keyCode == 74){ // j
      nextLoopIndex = this.loopedBounceIdx-1;
      if (nextLoopIndex < 0){
        nextLoopIndex = this.startEndTimes.length-1;
      }
      this.loopBounce(nextLoopIndex);
    }
    // l = loop previous bounce
    else if (e.keyCode == 76){ // l
      nextLoopIndex = this.loopedBounceIdx+1;
      if (nextLoopIndex >= this.startEndTimes.length-1){
        nextLoopIndex = 0;
      }
      this.loopBounce(nextLoopIndex);
    }
    //  i = stop looping
    else if (e.keyCode == 73){ // i
      this.stopLooping();
    }
    // ',' = slow down
    else if (e.keyCode == 188){ // ','
      this.videoSpeed('-');
    }
    // '.' = speed up
    else if (e.keyCode == 190){ // '.'
      this.videoSpeed('+');
    }
    // n = label next
    else if (e.keyCode == 78){ // n
      this.$doNextBtn.text('Going...');
      this.$doNextBtn[0].click();
    }
  },
  doIntervalLoop: function() {
    var that = VideoControls;
    // Reset video time to start of bounce end of bounce is exceeded
    if (that.isLooping && that.video.currentTime >= that.loopEndTime){
      that.video.currentTime = that.loopStartTime;
    }

    // Highlight background
    for (var i = 0; i < that.startEndTimes.length; i++) {
      // Update the current move to the one being shown. Happens every 25 ms.
      if (that.video.currentTime >= that.startEndTimes[i].start &&
          that.video.currentTime < that.startEndTimes[i].end &&
          i != that.highlightedRowIndex){

        // Remove highlightSkill from any old rows and add it to the current row element. Old happens when current skill changes.
        $('.highlightSkill').removeClass('highlightSkill');
        that.$rowsToHighlight.eq(i).addClass('highlightSkill');
        that.highlightedRowIndex = i;

        break; // leave the loop, the row has been found
      }
    }

    // If the video is 3 seconds after the last skill, remove highlighting (It's probably finished).
    if (that.video.currentTime > that.startEndTimes[that.startEndTimes.length-1].end){
        $('.highlightSkill').removeClass('highlightSkill');
        that.highlightedRowIndex = -1;
    }

  },
  videoSpeed:function(direction){
    var step = 0.25;
    if (direction == '+')
      newPbr = this.video.playbackRate + step;
    else
      newPbr = this.video.playbackRate - step;

    newPbr = Math.min(newPbr, 2);
    newPbr = Math.max(newPbr, step);

    this.video.playbackRate = newPbr;
    this.$playBackSpeed.text('Playback Speed: '+newPbr);
  }
};
