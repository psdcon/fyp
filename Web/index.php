<!DOCTYPE html>
<html lang="en" ng-app="fyp">

<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->
  <meta name="description" content="">
  <meta name="author" content="">
  <!-- <link rel="shortcut icon" href="images/main_icon.jpg"> -->

  <title>FYP</title>

  <!-- Bootstrap core CSS -->
  <link href="node_modules/bootstrap/dist/css/bootstrap.min.css" rel="stylesheet">

  <!-- Styles -->
  <link href="css/main.css" rel="stylesheet">
  <link href="node_modules/select2/dist/css/select2.min.css" rel="stylesheet">

  <!-- Icons - For the return to top arrow -->
  <link rel="stylesheet" href="node_modules/font-awesome/css/font-awesome.min.css">
</head>

<body>

  <nav class="navbar navbar-toggleable-md navbar-inverse bg-inverse">
    <div class="container">
      <button class="navbar-toggler navbar-toggler-right" type="button" data-toggle="collapse" data-target="#collapsingNavbar" aria-controls="collapsingNavbar" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <a class="navbar-brand" href="#!/" style="Final Year Project">FYP</a>

      <div class="collapse navbar-collapse" id="collapsingNavbar">
        <ul class="navbar-nav mr-auto">
          <li class="nav-item active">
            <a class="nav-link" href="#!/">Home <span class="sr-only">(current)</span></a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#!/videos">Videos</a>
          </li>
        </ul>
      </div>
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
  <script src="node_modules/tether/dist/js/tether.min.js"></script>
  <script src="node_modules/bootstrap/dist/js/bootstrap.min.js"></script>

  <!-- Angular
  ======================================================= -->
  <script src="node_modules/angular/angular.js"></script>
  <script src="node_modules/angular-route/angular-route.js"></script>
  <script src="node_modules/angular-animate/angular-animate.js"></script>

  <!-- Mine & MSC
  ======================================================= -->
  <script src="js/main.js"></script>
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
