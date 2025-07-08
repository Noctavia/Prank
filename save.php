<?php
try {
    // Connexion à la base de données
    $pdo = new PDO("mysql:host=localhost;dbname=kong_db;charset=utf8", "root", "", [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
    ]);

    // Récupération des données JSON
    $data = json_decode(file_get_contents("php://input"), true);

    // Anonymisation partielle de l'IP
    $ip = $_SERVER['REMOTE_ADDR'];
    if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4)) {
        $ip = preg_replace('/\.\d+$/', '.0', $ip); // Exemple : 192.168.1.42 => 192.168.1.0
    } elseif (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV6)) {
        $ip = substr($ip, 0, strrpos($ip, ':')) . '::';
    }

    // Données envoyées par le client
    $language   = $data['language'] ?? 'unknown';
    $userAgent  = $data['userAgent'] ?? 'unknown';
    $platform   = $data['platform'] ?? 'unknown';
    $timezone   = $data['timezone'] ?? 'unknown';
    $date       = $data['date'] ?? date('c');

    // Insertion dans la base de données
    $stmt = $pdo->prepare("INSERT INTO visiteurs (ip, langue, navigateur, appareil, fuseau, date_access) VALUES (?, ?, ?, ?, ?, ?)");
    $stmt->execute([$ip, $language, $userAgent, $platform, $timezone, $date]);

    // Enregistrement dans le fichier texte
    $log = "[$date] IP: $ip | Langue: $language | Navigateur: $userAgent | Appareil: $platform | Fuseau: $timezone\n";
    file_put_contents("visites.txt", $log, FILE_APPEND);

    // Réponse au client
    http_response_code(200);
    echo json_encode(['status' => 'ok']);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['status' => 'error', 'message' => $e->getMessage()]);
}
