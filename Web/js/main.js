
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

  init: function(bounces) {
    this.bounces = bounces;

    this.select2Setup();
    this.select2Preload();

    this.bindUIActions();

    $(".alert").alert();
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
    var that = this;

    $('.js-save').text('Saving...');

    // Get the names for each skill
    for (var i = 0; i < $(".js-select2").length; i++) {
      that.bounces[i].name = $(".js-select2")[i].value;
    }

    // Send to server
    $.post({
      url: "includes/ajax.db.php",
      data: "action=updateBounces" +
        "&id=<?=$_GET['routine_id']?>"+
        "&bounces=" + JSON.stringify(that.bounces),
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


var Judge = {
  init: function() {
    this.bindUIActions();

    // Autofocus the first input
    $('.js-deduction')[0].focus();

    $(".alert").alert();
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
  validateNumber: function($this) {
    val = $this.val();
    if (!$.isNumeric(val)){
      $this.val("");
    }
    else if (val < 0){
      $this.val("0");
    }
    else if (val > 5){
      $this.val("5");
    }
  },
  calculateScore: function(){
    numBounces = $('.js-deduction').length;
    if (numBounces > 10)
      numBounces = 10;

    totalDeductions = 0;
    for (var i = 0; i < numBounces; i++) {
      totalDeductions += parseInt($('.js-deduction')[i].value)/10;
    }

    score = 10 - totalDeductions;
    $('.js-score').text(score.toFixed(1));
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

