<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->
  <meta name="description" content="">
  <meta name="author" content="">
  <!-- <link rel="shortcut icon" href="images/main_icon.jpg"> -->

  <title><?=$title?></title>
  <!-- <base href="/fyp/"> -->

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
      <a class="navbar-brand" href="index.php" style="Final Year Project">FYP</a>

      <div class="collapse navbar-collapse" id="collapsingNavbar">
        <ul class="navbar-nav mr-auto">
          <li class="nav-item <?=$navIndex==0?'active':'';?>">
            <a class="nav-link" href="index.php">Home</a>
          </li>
          <li class="nav-item <?=$navIndex==1?'active':'';?>">
            <a class="nav-link" href="list_routines.php">Routines</a>
          </li>
        </ul>
      </div>
    </div>
  </nav>

  <div class="container main">

      <!-- Return to top arrow -->
      <a href="javascript:" id="return-to-top"><i class="fa fa-chevron-up" aria-hidden="true"></i></a>

        <!-- Content goes here -->
