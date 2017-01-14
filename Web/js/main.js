
// ===== Scroll to Top Arrow ====
var scrollTrigger = 150; // px
var returnToTopElement = $('#return-to-top');
backToTop = function () {
  var scrollTop = $(window).scrollTop();
  if (scrollTop > scrollTrigger) {
    $('#return-to-top').addClass('show');
  } else {
    $('#return-to-top').removeClass('show');
  }
};
backToTop();
$(window).on('scroll', function () {
  backToTop();
});
$('#return-to-top').on('click', function (e) {
  e.preventDefault();
  $('html,body').animate({
    scrollTop: 0
  }, 700);
});


var Label = {
  bounces: [],
  skillNames: select2SkillNameData,

  init: function(routineId, bounces) {
    this.bounces = bounces;
    this.routineId = routineId;

    this.select2Setup();
    this.select2Preload();

    this.bindUIActions();

  },
  select2Setup: function(){
    var that = this;

    // Set up select2 inputs
    $(".js-select2")
      .select2({
        data: that.skillNames
      })
      // Any time the select2 dropdown is closed, give it focus. otherwise focus disappears, which sucks
      .on("select2:close", function (e) {
        $(this).focus();
      });
  },
  select2Preload: function() {
    // Preload selects with the names for each skill
    for (var i = 0; i < this.bounces.length; i++) {
      if (this.bounces[i].name)
        $(".js-select2")[i].value = this.bounces[i].name;
    }
    // Update all
    $(".js-select2").trigger('change');

  },
  bindUIActions: function(){
    var that = this;

    $('.js-save').click(that.save);

  },
  save: function(){
    var that = Label;

    $('.js-save').text('Saving...');

    // Get the names for each skill
    for (var i = 0; i < $(".js-select2").length; i++) {
      that.bounces[i].name = $(".js-select2")[i].value;
    }

    // Send to server
    $.post({
      url: "includes/ajax.db.php",
      data: "action=updateBounces" +
        "&id=" + that.routineId +
        "&bounces=" + JSON.stringify(that.bounces),
      dataType: "text",
      success: function (data) {
        if (data.length === 0) {
          $('.js-save').text('Saved!');
        }
        else {
          $('.js-save').text('Not Saved');

          console.log(data);
        }
      }
    });

  }
};


var Judge = {
  bounces: [],

  init: function(routineId, bounces) {
    this.bounces = bounces;
    this.routineId = routineId;

    this.bindUIActions();

    // Autofocus the first input
    $('.js-deduction')[0].focus();

  },
  bindUIActions: function(){
    that = this;
    // Number input validation
    $('.js-deduction').on('input', function(e){
      that.validateNumber($(this));

      that.calculateScore();
    });

    $('.js-save').click(that.save);
  },
  validateNumber: function($thatNumberInput) {
    val = $thatNumberInput.val();

    if (val.includes('.')){
      val = parseInt(val);
      val = (isNaN(val))? "0": val; // is NaN is val<1, i.e. '0.4'
      $thatNumberInput.val(val);
    }
    else if (val < 0){
      $thatNumberInput.val("0");
    }
    else if (val > 5){
      $thatNumberInput.val("5");
    }
  },
  calculateScore: function(){
    var numBounces = $('.js-deduction').length;
    numBounces = Math.min(numBounces, 10);
    var totalDeductions = 0;
    for (var i = 0; i < numBounces; i++) {
      totalDeductions += parseInt($('.js-deduction')[i].value)/numBounces;
    }

    var score = numBounces - totalDeductions;
    $('.js-score').text(score.toFixed(1));
  },
  save: function(){
    var that = Judge;

    if ($('.js-username').val().trim() === ""){
      alert('Please enter your name before saving.');
      $('.js-username').focus();
      return;
    }

    $('.js-save').text('Saving...');

    // Get the deductions for all skills
    var deductionsIndex = 0; // separate index thanks to the ...
    var deductions = [];
    for (var i = 0; i < that.bounces.length; i++) {
      var bounce = that.bounces[i];
      var score = null;
      if (bounce.name != "In/Out Bounce" && bounce.name != "Broken") {
        score = ($(".js-deduction")[deductionsIndex].value/10).toFixed(1);
        deductionsIndex++;
      }
      deductions.push(score);
    }

    // Send to server
    $.post({
      url: "includes/ajax.db.php",
      data: "action=judge" +
        "&id=" + that.routineId +
        "&userName=" + $('.js-username').val().trim() +
        "&deductions=" + JSON.stringify(deductions),
      dataType: "text",
      success: function (data) {
        if (data.length === 0) {
          $('.js-save').text('Saved!');
        }
        else {
          $('.js-save').text('Not Saved');

          console.log(data);
        }
      }
    });
  }
};

// Chart stuff
var Tally = {
  labels: ["0.0", "0.1", "0.2", "0.3", "0.4", "0.5"],
  backgroundColors: [
    'rgba(255, 99, 132, 0.2)',
    'rgba(54, 162, 235, 0.2)',
    'rgba(255, 206, 86, 0.2)',
    'rgba(75, 192, 192, 0.2)',
    'rgba(153, 102, 255, 0.2)',
    'rgba(255, 159, 64, 0.2)'
  ],
  borderColors: [
    'rgba(255,99,132,1)',
    'rgba(54, 162, 235, 1)',
    'rgba(255, 206, 86, 1)',
    'rgba(75, 192, 192, 1)',
    'rgba(153, 102, 255, 1)',
    'rgba(255, 159, 64, 1)'
  ],
  options: {
      scales: {
          yAxes: [{
              ticks: {
                  beginAtZero:true,
                  stepSize: 1,
                  suggestedMax: 5
              }
          }]
      },
      legend: {
        display: false
      }
  },
  init: function() {
    var that = this;

    $('canvas').each(function( index ) {
      thisData = $(this).data('chart-data');
      new Chart(this, {
          type: 'bar',
          data: {
              labels: that.labels,
              datasets: [{
                  data: thisData,
                  backgroundColor: that.backgroundColors,
                  borderColor: that.borderColors,
                  borderWidth: 1
              }]
          },
          options: that.options
      });
    });

  }
};
