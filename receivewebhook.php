<?php

if($json = json_decode(file_get_contents("php://input"))) {
 	
	print_r($json);
 	$data = $json;


	$fp = fopen('index.html', 'w');

	fwrite($fp, '<!DOCTYPE html><html lang="de"><head>');
	fwrite($fp, '<meta http-equiv="Pragma" content="no-cache">');
	fwrite($fp, '<meta http-equiv="Cache-Control" content="no-cache">');
	fwrite($fp, '<meta http-equiv="Expires" content="0">');
	fwrite($fp, '<meta charset="utf-8">');
	fwrite($fp, '<meta name="viewport" content="width=device-width, initial-scale=1.0">');
	fwrite($fp, '<title>Mein Hyundai Kona Ladestand</title>');
	fwrite($fp, '</head><body><div align=center>');
	fwrite($fp, '<p><font size="4">SOC<font size="8">&nbsp;');
	fwrite($fp, $json->soc);
	fwrite($fp, '&nbsp;%&nbsp;<font size="4">von&nbsp;');
	fwrite($fp, date('d.m H:i',$json->soctime));
	fwrite($fp, '<br><font size="4">Position vom&nbsp;');
	fwrite($fp, date('d.m H:i',$json->lonlattime));
	fwrite($fp, '<br>');
	fwrite($fp, '<iframe width="340" height="420" src = "https://maps.google.com/maps?q=');
	fwrite($fp, $json->lat);
	fwrite($fp, ',');
	fwrite($fp, $json->lon);
	fwrite($fp, '&hl=de;z=2&amp;output=embed"></iframe>');
	fwrite($fp, '</div></body></html>');
	fclose($fp);
}

?>
