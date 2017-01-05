<?php
require_once('db.php');

if ($_POST['action']=='updateBounces'){

	$id = mysqli_real_escape_string($db, $_REQUEST['id']);
	$bounces = mysqli_real_escape_string($db, $_REQUEST['bounces']);
	$dbQuery = mysqli_query($db, "UPDATE videos SET bounces='$bounces' WHERE id='$id'");

	if (mysqli_connect_errno()) {
		/* Couldn't connect to the database*/
		echo "Failed to connect to MySQL: " . mysqli_connect_error($db);
	}
	else if ($dbQuery){
		//Good things happened
	}
	else{ //Unsuccessfuly entry
		// var_dump($dbQuery);
		echo 'Database error: '.$dbQuery.mysqli_error($db);
	}
}
