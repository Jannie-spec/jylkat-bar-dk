<?php
// Jylkat – formularer fra hjemmesiden sendes som mail til Zendesk.
// Samme modtager og samme opbygning som den gamle Aida-formular, så
// bestillingerne lander i Zendesk præcis som før (gæsten står som afsender).

const TO        = 'support@hotelklippenogthernshotel.zendesk.com';
const FROM      = 'info@jylkat-bar.dk';
const FROM_NAME = 'Jylkat hjemmeside';
const MAX_PER_HOUR = 10;   // pr. IP-adresse

$FORMS = [
  'Bordbestilling' => [
    'subject' => 'Ny bordbestilling fra {full_name}',
    'intro'   => "Ny bordbestilling\n\nDer er kommet en ny bordbestilling gennem hjemmesiden:",
    'outro'   => "Kontakt gæsten for at bekræfte bordet.\n\nSendt via bordbestillingsformularen på jylkat-bar.dk",
    'fields'  => ['full_name' => 'Navn', 'submitter_email' => 'Email', 'phone' => 'Telefon', 'guests' => 'Antal personer',
                  'date' => 'Dato', 'time' => 'Tidspunkt', 'message' => 'Besked (valgfrit)'],
    'required'=> ['full_name', 'submitter_email', 'phone', 'guests', 'date', 'time'],
  ],
  'Kontakt' => [
    'subject' => 'Ny besked fra {full_name}',
    'intro'   => "Ny besked\n\nDer er kommet en ny besked gennem kontaktformularen:",
    'outro'   => 'Sendt via kontaktformularen på jylkat-bar.dk',
    'fields'  => ['full_name' => 'Navn', 'submitter_email' => 'Email', 'phone' => 'Telefon', 'message' => 'Besked'],
    'required'=> ['full_name', 'submitter_email', 'message'],
  ],
  'Julefrokost' => [
    'subject' => 'Julefrokost-forespørgsel fra {full_name}',
    'intro'   => 'Ny julefrokost-forespørgsel',
    'outro'   => 'Sendt via julefrokost-siden på jylkat-bar.dk',
    'fields'  => ['full_name' => 'Navn', 'phone' => 'Telefon', 'submitter_email' => 'E-mail', 'preferred_date' => 'Ønsket dato',
                  'preferred_time' => 'Ca. tidspunkt', 'guests' => 'Antal personer', 'overnight' => 'Kunne I tænke jer overnatning',
                  'message' => 'Besked'],
    'required'=> ['full_name', 'phone', 'submitter_email', 'preferred_date', 'guests'],
  ],
  'Firmajulefrokost' => [
    'subject' => 'Julefrokost-forespørgsel (firma) fra {company}',
    'intro'   => 'Ny firmajulefrokost-forespørgsel',
    'outro'   => 'Sendt via julefrokost-firma-siden på jylkat-bar.dk',
    'fields'  => ['company' => 'Firma', 'full_name' => 'Kontaktperson', 'phone' => 'Telefon', 'submitter_email' => 'E-mail',
                  'preferred_date' => 'Ønsket dato', 'guests' => 'Antal personer', 'exclusive_venue' => 'Ønsker I hele stedet for jer selv',
                  'drinks_package' => 'Interesseret i en drinkspakke', 'overnight' => 'Kunne nogen tænke sig overnatning',
                  'message' => 'Besked'],
    'required'=> ['company', 'full_name', 'phone', 'submitter_email', 'preferred_date', 'guests'],
  ],
];
$LANGS = ['da' => '', 'en' => 'engelsk', 'de' => 'tysk', 'sv' => 'svensk'];

$ajax = isset($_SERVER['HTTP_X_REQUESTED_WITH']);
function done($ok, $code, $http = 200) {
  global $ajax;
  http_response_code($http);
  if ($ajax) {
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode(['ok' => $ok, 'code' => $code]);
  } else {
    header('Content-Type: text/html; charset=utf-8');
    $msg = $ok ? 'Tak! Vi har modtaget din besked og vender tilbage hurtigst muligt.'
               : 'Beskeden kunne ikke sendes. Ring eller skriv til info@jylkat-bar.dk.';
    echo '<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><meta name="viewport" content="width=device-width">'
       . '<title>Jylkat</title><p style="font:18px/1.5 sans-serif;max-width:32em;margin:3em auto;padding:0 1em">'
       . htmlspecialchars($msg) . '<br><br><a href="/">Tilbage til jylkat-bar.dk</a></p>';
  }
  exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') done(false, 'method', 405);

// Kun fra vores egen side
$origin = $_SERVER['HTTP_ORIGIN'] ?? ($_SERVER['HTTP_REFERER'] ?? '');
if ($origin !== '' && !preg_match('~^https://(www\.)?jylkat-bar\.dk(/|$)~', $origin)) done(false, 'origin', 403);

$kind = $_POST['form'] ?? '';
if (!isset($FORMS[$kind])) done(false, 'form', 400);
$F = $FORMS[$kind];

// Robotfælde: feltet er skjult for mennesker. Robotten får "tak", men intet sendes.
if (!empty($_POST['_hp_company'])) done(true, 'ok');

// Begræns antal afsendelser pr. IP
$ip = $_SERVER['REMOTE_ADDR'] ?? '0';
$rl = sys_get_temp_dir() . '/jylkat_rl_' . md5($ip);
$hits = array_filter(array_map('intval', @file($rl, FILE_IGNORE_NEW_LINES) ?: []), fn($t) => $t > time() - 3600);
if (count($hits) >= MAX_PER_HOUR) done(false, 'rate', 429);

function clean($v, $multiline = false) {
  $v = is_string($v) ? trim($v) : '';
  $v = mb_substr($v, 0, $multiline ? 4000 : 200);
  $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $v) ?? '';
  return $multiline ? str_replace("\r\n", "\n", $v) : preg_replace('/\s+/u', ' ', $v);
}

$v = [];
foreach ($F['fields'] as $name => $label) $v[$name] = clean($_POST[$name] ?? '', $name === 'message');
foreach ($F['required'] as $name) if ($v[$name] === '') done(false, 'missing', 400);
$email = $v['submitter_email'];
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) done(false, 'email', 400);

$lang = $_POST['lang'] ?? 'da';
$lines = [$F['intro'], ''];
foreach ($F['fields'] as $name => $label) { $lines[] = "$label: " . $v[$name]; $lines[] = ''; }
if (!empty($LANGS[$lang])) { $lines[] = 'Gæsten skrev fra den ' . $LANGS[$lang] . 'e side.'; $lines[] = ''; }
$lines[] = $F['outro'];
$body = implode("\n", $lines);

$subject = preg_replace_callback('/\{(\w+)\}/', fn($m) => $v[$m[1]] ?? '', $F['subject']);
$enc = fn($s) => '=?UTF-8?B?' . base64_encode($s) . '?=';
$guest = $v['full_name'] !== '' ? $v['full_name'] : $email;

$headers = implode("\r\n", [
  'From: ' . $enc(FROM_NAME) . ' <' . FROM . '>',
  'Reply-To: ' . $enc($guest) . ' <' . $email . '>',
  'MIME-Version: 1.0',
  'Content-Type: text/plain; charset=UTF-8',
  'Content-Transfer-Encoding: 8bit',
  'X-Jylkat-Form: ' . $kind,
]);

$sent = mail(TO, $enc($subject), $body, $headers, '-f' . FROM);
if (!$sent) done(false, 'mail', 500);

$hits[] = time();
@file_put_contents($rl, implode("\n", $hits));
done(true, 'ok');
