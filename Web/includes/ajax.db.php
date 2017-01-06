<?php
require_once('db.php');

if ($_POST['action'] == 'updateBounces'){
	$id = $db->escapeString($_POST['id']);
	$bounces = $db->escapeString($_POST['bounces']);
	$result = $db->exec("UPDATE videos SET bounces='$bounces' WHERE id='$id'");

	if ($result){
		//Good things happened
	}
	else{ //Unsuccessful
		echo $db->lastErrorMsg();
	}
}
else if ($_POST['action'] == 'judge') {
	$video_id = $db->escapeString($_POST['id']);
	$deductions = $db->escapeString($_POST['deductions']);
	$result = $db->exec("INSERT INTO judgements (video_id, deductions) VALUES ('$video_id', '$deductions')");

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
