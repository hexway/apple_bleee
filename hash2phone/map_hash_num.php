<?php

$dbconn = pg_connect('host=localhost port=5432 dbname=phones user=lookup password=h3xwayp4ssw0rd');

$time_start = microtime(true);

if (!$_GET['hash']) {

    $result = pg_query($dbconn, 'SELECT count(*) FROM map');
    if (!$result) {
        echo 'Err =(';
        exit;
    }

    if ($row = pg_fetch_row($result)) {
        echo "current: {$row[0]}";
    }

} else {

    $hash = preg_replace('/[^a-zA-Z0-9]/', '', $_GET['hash']);

    $result = pg_query($dbconn, "SELECT phone FROM map where hash='\\x{$hash}'");
    if (!$result) {
        echo 'Err  =(';
        exit;
    }

    $candidates = array_column(pg_fetch_all($result), 'phone');

    $time_end = microtime(true);
    $time     = $time_end - $time_start;

    echo json_encode(compact('candidates', 'time'));

}
