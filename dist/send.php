<?php
// Modtager bordbestillinger, kontaktbeskeder og julefrokost-forespørgsler fra jylkat-bar.dk
// og sender dem som mail til info@jylkat-bar.dk. Hver henvendelse gemmes også i data/henvendelser.jsonl,
// så de senere kan flyttes ind i et bookingsystem.
header('Content-Type: application/json; charset=utf-8');
$TO = 'info@jylkat-bar.dk';
$FROM = 'bestilling@jylkat-bar.dk';

function out($ok, $code = 200) { http_response_code($code); echo json_encode(['ok' => $ok]); exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') out(false, 405);
if (!empty($_POST['_hp_company'])) out(true);               // robot-fælde

$labels = [
  'form' => 'Formular', 'lang' => 'Sprog', 'full_name' => 'Navn', 'company' => 'Firma', 'phone' => 'Telefon',
  'submitter_email' => 'E-mail', 'date' => 'Dato', 'time' => 'Tidspunkt', 'guests' => 'Antal personer',
  'preferred_date' => 'Ønsket dato', 'preferred_time' => 'Ca. tidspunkt', 'overnight' => 'Overnatning',
  'exclusive_venue' => 'Hele stedet', 'drinks_package' => 'Drinkspakke', 'message' => 'Besked',
];
$d = [];
foreach ($labels as $k => $l) {
  if (isset($_POST[$k])) $d[$k] = trim(mb_substr(strip_tags((string)$_POST[$k]), 0, 3000));
}
$email = filter_var($d['submitter_email'] ?? '', FILTER_VALIDATE_EMAIL);
if (!$email || empty($d['full_name'])) out(false, 400);

$kind = $d['form'] ?? 'Henvendelse';
$subject = $kind . ': ' . $d['full_name'];
if (!empty($d['date'])) $subject .= ' – ' . $d['date'] . ' kl. ' . ($d['time'] ?? '') . ', ' . ($d['guests'] ?? '?') . ' pers.';
if (!empty($d['preferred_date'])) $subject .= ' – ' . $d['preferred_date'] . ', ' . ($d['guests'] ?? '?') . ' pers.';

$body = '';
foreach ($d as $k => $v) if ($v !== '') $body .= str_pad($labels[$k] . ':', 18) . $v . "\n";
$body .= "\nSendt fra jylkat-bar.dk " . date('d.m.Y H:i') . "\nSvar direkte på denne mail for at svare gæsten.\n";

$headers = "From: Jylkat Bar <$FROM>\r\nReply-To: " . str_replace(["\r", "\n"], '', $d['full_name']) . " <$email>\r\n"
  . "MIME-Version: 1.0\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: 8bit";
$sent = mail($TO, '=?UTF-8?B?' . base64_encode($subject) . '?=', $body, $headers, '-f' . $FROM);

// Gem en kopi (beskyttet mappe)
$dir = __DIR__ . '/data';
if (!is_dir($dir)) { @mkdir($dir, 0750); @file_put_contents($dir . '/.htaccess', "Require all denied\n"); }
@file_put_contents($dir . '/henvendelser.jsonl', json_encode(['t' => date('c'), 'mail_ok' => $sent] + $d, JSON_UNESCAPED_UNICODE) . "\n", FILE_APPEND | LOCK_EX);

out((bool)$sent, $sent ? 200 : 500);
