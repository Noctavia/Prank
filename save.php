<?php
// Connexion à la base de données MySQL
$pdo = new PDO("mysql:host=localhost;dbname=kong_db;charset=utf8", "root", "");

// Récupération des données JSON
$data = json_decode(file_get_contents("php://input"), true);

$ip         = $_SERVER['REMOTE_ADDR'];
$language   = $data['language'] ?? 'unknown';
$userAgent  = $data['userAgent'] ?? 'unknown';
$platform   = $data['platform'] ?? 'unknown';
$timezone   = $data['timezone'] ?? 'unknown';
$date       = $data['date'] ?? date('c');

// Insertion dans la base de données
$stmt = $pdo->prepare("INSERT INTO visiteurs (ip, langue, navigateur, appareil, fuseau, date_access) VALUES (?, ?, ?, ?, ?, ?)");
$stmt->execute([$ip, $language, $userAgent, $platform, $timezone, $date]);

// Écriture dans le fichier texte
$log = "[$date] IP: $ip | Langue: $language | Navigateur: $userAgent | Appareil: $platform | Fuseau: $timezone\n";
file_put_contents("visites.txt", $log, FILE_APPEND);
?>
