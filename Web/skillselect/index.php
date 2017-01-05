<?php
require_once ('includes/db.php');
?>

<!DOCTYPE html>
<html lang="en" ng-app="skillselect">

<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->
  <meta name="description" content="">
  <meta name="author" content="">
  <!-- <link rel="shortcut icon" href="images/main_icon.jpg"> -->

  <title>Skill Select</title>

  <!-- Bootstrap core CSS -->
  <link href="node_modules/bootstrap/dist/css/bootstrap.min.css" rel="stylesheet">

  <!-- Styles -->
  <link href="css/main.css" rel="stylesheet">
  <link href="node_modules/select2/dist/css/select2.min.css" rel="stylesheet">

  <!-- Icons - For the return to top arrow -->
  <link rel="stylesheet" href="node_modules/font-awesome/css/font-awesome.min.css">
</head>

<body>
  <nav class="navbar navbar-full navbar-dark bg-inverse">
    <div class="container">
      <a class="navbar-brand" href="#/">
        Skill Select
      </a>
      <button class="navbar-toggler hidden-sm-up pull-right" type="button" data-toggle="collapse" data-target="#collapsingNavbar" aria-controls="exCollapsingNavbar2" aria-expanded="false" aria-label="Toggle navigation">
        <!-- Hamburger icon -->
        &#9776;
      </button>

      <div class="collapse navbar-toggleable-xs" id="collapsingNavbar">
        <ul class="nav navbar-nav">
          <li class="nav-item">
            <a class="nav-link" href="#/">Home</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#videos">Videos</a>
          </li>
        </ul>
      </div><!-- /.collapse -->
    </div>
  </nav>

  <div class="container main">

      <!-- Return to top arrow -->
      <a href="javascript:" id="return-to-top"><i class="fa fa-chevron-up" aria-hidden="true"></i></a>

      <div class="page" ng-view>

        <!-- Content goes here -->

    </div>
  </div>

  <!-- Bootstrap core JavaScript
  ================================================== -->
  <!-- Placed at the end of the document so the pages load faster -->
  <script src="node_modules/jquery/dist/jquery.js"></script>
  <script src="node_modules/bootstrap/node_modules/tether/dist/js/tether.min.js"></script>
  <script src="node_modules/bootstrap/dist/js/bootstrap.min.js"></script>

  <!-- Angular
  ======================================================= -->
  <script src="node_modules/angular/angular.js"></script>
  <script src="node_modules/angular-route/angular-route.js"></script>
  <script src="node_modules/angular-animate/angular-animate.js"></script>

  <!-- Mine & MSC
  ======================================================= -->
  <script src="js/skillselect.js"></script>

  <script src="node_modules/select2/dist/js/select2.min.js"></script>

  <script>
    // Add .active to nav item on click
    $("nav .navbar-nav .nav-item").click(function() {
      $("nav .navbar-nav .nav-item").removeClass('active');
      $(this).addClass('active');
    });


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
  </script>

</body>

</html>
