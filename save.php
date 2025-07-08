<?php
$dbFile = 'visiteurs.db';

try {
    // Connexion SQLite
    $pdo = new PDO("sqlite:$dbFile");
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Créer la table si elle n'existe pas encore
    $pdo->exec("
        CREATE TABLE IF NOT EXISTS visiteurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            langue TEXT,
            navigateur TEXT,
            appareil TEXT,
            fuseau TEXT,
            date_access TEXT
        );
    ");

    // Récupérer les données JS
    $data = json_decode(file_get_contents("php://input"), true);

    $ip         = $_SERVER['REMOTE_ADDR'];
    $language   = $data['language'] ?? 'unknown';
    $userAgent  = $data['userAgent'] ?? 'unknown';
    $platform   = $data['platform'] ?? 'unknown';
    $timezone   = $data['timezone'] ?? 'unknown';
    $date       = $data['date'] ?? date('c');

    // Insertion dans la base
    $stmt = $pdo->prepare("INSERT INTO visiteurs (ip, langue, navigateur, appareil, fuseau, date_access) VALUES (?, ?, ?, ?, ?, ?)");
    $stmt->execute([$ip, $language, $userAgent, $platform, $timezone, $date]);

    // Facultatif : log dans fichier texte aussi
    $log = "[$date] IP: $ip | Langue: $language | Navigateur: $userAgent | Appareil: $platform | Fuseau: $timezone\n";
    file_put_contents("visites.txt", $log, FILE_APPEND);

    echo json_encode(['status' => 'ok']);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['status' => 'error', 'message' => $e->getMessage()]);
}
