Function.prototype.bind = function(obj) {
  var method = this,
   temp = function() {
    return method.apply(obj, arguments);
   };

  return temp;
 }

var VideoControls = {
    video: null,
    isLooping: false,
    loopStartTime: 0,
    loopEndTime: 0,
    intervalRate: 28,
    intervalInstance: null,

    bounceLoopedIdx: -1, // set -1 so that when 'l' is pressed it starts looping at 0
    highlightedRowIndex: -1,

    loopingTrueStr: "Looping bounce ",
    loopingFalseStr: "No bounce looping",

    init: function (videoElement, startEndTimes, $rowsToHighlight) {
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

        $(this.video).on('click', function (e) {
            this.paused ? this.play() : this.pause();
        });

        // Once video is playing, start the check for looping skill func
        $(this.video).bind('play', function (e) {
            that.intervalInstance = setInterval(that.doIntervalLoop, that.intervalRate);
        });
        // Turn this off so as not to be burning cpu cycles when the video is paused
        $(this.video).bind('stop pause', function (e) {
            clearInterval(that.intervalInstance);
        });

        //Set up buttons below video
        $('.js-btn-speed-down').on('click', function () {
            that.videoSpeed('-')
        });
        $('.js-btn-speed-up').on('click', function () {
            that.videoSpeed('+')
        });

        $('.js-btn-prev-skill').on('click', this.playPrevBounce.bind(this));
        $('.js-btn-loop-skill').on('click', this.startStopLoop.bind(this));
        $('.js-btn-next-skill').on('click', this.playNextBounce.bind(this));

        // Bind 'Loop' button
        this.$loopBtns.click(function () {
            // Get current index of this button to give it's index in the list of skills
            thisIndex = that.$loopBtns.index($(this));
            // Setup loop and explicitly play the video.
            that.loopBounce(thisIndex);
            that.playBounce(thisIndex);
        });

        // Bind keyboard shortcuts
        document.addEventListener('keyup', function (e) {
            that.keyboardShortcuts(e);
        }, false);

    },
    playBounce: function (index) {
        this.video.currentTime = this.startEndTimes[index].start;

        if (this.video.paused) {
            this.video.play();
        }
    },
    loopBounce: function (index) {
        this.isLooping = true;
        this.bounceLoopedIdx = index;
        this.updateLoopingUI();

        this.loopStartTime = this.startEndTimes[index].start;
        this.loopEndTime = this.startEndTimes[index].end;
    },
    stopLooping: function () {
        this.isLooping = false;
        this.updateLoopingUI();
    },
    updateLoopingUI: function () {
        if (this.isLooping){
            $('.js-btn-loop-skill').html('<i class="fa fa-stop" aria-hidden="true"></i>');
            this.$loopBtnIndex.text(this.loopingTrueStr + (this.bounceLoopedIdx + 1));
        }
        else{
            $('.js-btn-loop-skill').html('<i class="fa fa-repeat" aria-hidden="true"></i>');
            this.$loopBtnIndex.text(this.loopingFalseStr);
        }
    },
    startStopLoop: function () {
        if (this.isLooping)
            this.stopLooping();
        else
            this.loopBounce(this.highlightedRowIndex);
    },
    playPrevBounce: function () {
        nextLoopIndex = this.highlightedRowIndex - 1;
        if (nextLoopIndex < 0) {
            nextLoopIndex = this.startEndTimes.length - 1;
        }
        this.playBounce(nextLoopIndex);
        if (this.isLooping) {
            this.loopBounce(nextLoopIndex);
        }
    },
    playNextBounce: function () {
        nextLoopIndex = this.highlightedRowIndex + 1;
        if (nextLoopIndex > this.startEndTimes.length - 1) {
            nextLoopIndex = 0;
        }
        this.playBounce(nextLoopIndex);
        if (this.isLooping) {
            this.loopBounce(nextLoopIndex);
        }
    },
    keyboardShortcuts: function (e) {
        // Handle Ctrl + combinations
        if (e.ctrlKey) {
            // Ctrl+Enter
            if (e.keyCode == 13) {
                this.save();
            }
            // Exit
            return;
        }

        // Ignore keypress if inside select2 input on /label and username input on /judge
        if ($(":focus").is($(".select2-search__field")) || $(":focus").is($(".js-username")))
            return;

        // console.log(e.keyCode);
        // k = play.pause video
        if (e.keyCode == 75) { // k
            if (this.video.paused)
                this.video.play();
            else {
                this.video.pause();
            }
        }
        // j = previous bounce
        else if (e.keyCode == 74) { // j
            this.playPrevBounce();
        }
        // l = next bounce
        else if (e.keyCode == 76) { // l
            this.playNextBounce();
        }
        //  i = stop looping
        else if (e.keyCode == 73) { // i
            this.startStopLoop()
        }
        // ',' = slow down
        else if (e.keyCode == 188) { // ','
            this.videoSpeed('-');
        }
        // '.' = speed up
        else if (e.keyCode == 190) { // '.'
            this.videoSpeed('+');
        }
        // n = label next
        else if (e.keyCode == 78) { // n
            this.$doNextBtn.text('Going...');
            this.$doNextBtn[0].click();
        }
    },
    doIntervalLoop: function () {
        var that = VideoControls;
        // Reset video time to start of bounce end of bounce is exceeded
        if (that.isLooping && that.video.currentTime >= that.loopEndTime) {
            that.video.currentTime = that.loopStartTime;
        }

        // Highlight background
        for (var i = 0; i < that.startEndTimes.length; i++) {
            // Update the current move to the one being shown. Happens every 25 ms.
            if (that.video.currentTime >= that.startEndTimes[i].start &&
                that.video.currentTime < that.startEndTimes[i].end &&
                i != that.highlightedRowIndex) {

                // Remove highlightSkill from any old rows and add it to the current row element. Old happens when current skill changes.
                $('.highlightSkill').removeClass('highlightSkill');
                that.$rowsToHighlight.eq(i).addClass('highlightSkill');
                that.highlightedRowIndex = i;

                break; // leave the loop, the row has been found
            }
        }

        // If the video is 3 seconds after the last skill, remove highlighting (It's probably finished).
        if (that.video.currentTime > that.startEndTimes[that.startEndTimes.length - 1].end) {
            $('.highlightSkill').removeClass('highlightSkill');
            that.highlightedRowIndex = -1;
        }

    },
    videoSpeed: function (direction) {
        var step = 0.25;
        if (direction == '+')
            newPbr = this.video.playbackRate + step;
        else
            newPbr = this.video.playbackRate - step;

        newPbr = Math.min(newPbr, 2);
        newPbr = Math.max(newPbr, step);

        this.video.playbackRate = newPbr;
        this.$playBackSpeed.text('Playback Speed: ' + newPbr);
    }
};
