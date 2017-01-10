<?php
require_once('functions.php');

if ($_POST['action'] == 'updateBounces'){
	$id = $db->escapeString($_POST['id']);
	$bounces = $db->escapeString($_POST['bounces']);

	$result = $db->exec("UPDATE routines SET bounces='$bounces' WHERE id='$id'");
	if ($result){
		//Good things happened
	}
	else{ //Unsuccessful
		echo $db->lastErrorMsg();
	}
}
else if ($_POST['action'] == 'judge') {
	$routine_id = $db->escapeString($_POST['id']);
	$deductions = $db->escapeString($_POST['deductions']);
	$userId = $db->escapeString($_COOKIE['userId']);

	$result = $db->exec("INSERT INTO judgements (routine_id, deductions, user_id) VALUES ('$routine_id', '$deductions', '$userId')");
	if ($result){
		//Good things happened
	}
	else{ //Unsuccessful
		echo $db->lastErrorMsg();
	}
}
else {
	echo "Error: Action not found";
}
