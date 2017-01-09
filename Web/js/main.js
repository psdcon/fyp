
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
