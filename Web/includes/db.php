<?php
$dbPath = dirname(__FILE__).DIRECTORY_SEPARATOR.'videos.sqlite3'; // No matter where script is included from
$db = new SQLite3($dbPath) or die('Unable to open database: '.$db->lastErrorMsg());


// Sets the title on page load
function setTitle($title){
  echo '
    <script>
      window.document.title = "'.$title.'";
    </script>
  ';
}


// Replace word boundaries with nothing
function string2SafeID($level) {
  return preg_replace('/\W+/','',strtolower($level));
}

// Used by select2's
function getAllSkillNamesJSON(){
  global $db;

  // Get names of skills for select2 with structure as below
  // [{
  //     text     : "Header One",
  //     children : [{
  //         id   : 0,
  //         text : "Item One"
  //     }, {
  //         ...
  //     }]
  // }]

  // Get the sql data into an assoc array grouped by level
  $groupedSkills = array();
  $skills = $db->query("SELECT name,level FROM skills ORDER BY id ASC");
  while($selectSkill = $skills->fetchArray(SQLITE3_ASSOC)){
    // Group by making assoc arrays with level as the key
    $groupedSkills[$selectSkill['level']][] = $selectSkill;
  }

  // Format the grouped assoc array as specified by select2 to minic optgroup
  $spitOutJSONSkills = '[
    {
      "id": "In/Out Bounce",
      "text": "In/Out Bounce"
    },';
  foreach ($groupedSkills as $level => $skills) {
    $spitOutJSONSkills .= '{
      "text": "'.$level.'",
      "children": [
    ';
    foreach ($skills as $selectSkill) {
      $spitOutJSONSkills .= '{
        "id": "'.$selectSkill['name'].'",
        "text": "'.$selectSkill['name'].'"
      },';
    }

    $spitOutJSONSkills .= '
      ]
    },';
  }
  $spitOutJSONSkills .= "]";

  return $spitOutJSONSkills;
}

?>
