<?php
ob_start();
error_reporting(0);
date_default_timezone_set('Asia/Tashkent');

/*
@ITACHI_UCHIHA_SONO_SHARINGAN
@Fav_ke

<---- 
Asosiy dasturchi: @obito_us 
Tog'irladilar: @Boltaboyev_Rahmatillo va @Fav_ke
---->

-------------------
Tog'irlangan bo'limlar

% == Tog'irlanganlik darajasi (taxminiy)

1. Zayafka 100% ishlaydi
2. Xabar yuborish ishlaydi (Lekin men ishlatib kurmadi.)
3. Post yuborish (Xoxlagancha kanalga 1 vaqtda) --> 100%
4. Majburiy obunaga Ijtimoi tarmoq ulash (Instagram va YouTube (faqat 2 ta)) --> 100%
5. Kontent cheklash yoki ulashish admin panel orqali --> 100%
6. Olinga va Orqaga bo'limi --> 100%
7. Birlamchi sozlamlar --> 100%
8. Anime tahrirlash --> 100%
9. Anime rasmini yoki videosini tahrirlash --> 100%
10. Video orqali Anime qo'shish --> 100%
11. Fanadub nomi anime qo'shishda --> 100%
12 Konkurs sozlamalari --> 100%
--------------

*/

// BOT SOZLAMALARI
$bot_token = "8742761350:AAFQ0jtcL32B1EznXrDr4EZwV2_eAbJXbqQ"; // Sizning bot tokeningiz
define('API_KEY', $bot_token);

// ADMIN ID - SIZNING TELEGRAM IDINGIZ
$obito_us = "7991544389"; // Sizning Telegram ID ingiz (asosiy admin)

// Ma'lumotlar bazasi sozlamalari (o'zingizning ma'lumotlaringizni kiriting)
$servername = "localhost"; 
$username = "anime_bot_user"; // Ma'lumotlar bazasi foydalanuvchi nomi
$password = "AnimeBot123!"; // Ma'lumotlar bazasi paroli
$dbname = "anime_bot_db"; // Ma'lumotlar bazasi nomi

// MySQL ga ulanish
$connect = mysqli_connect($servername, $username, $password, $dbname);
if (!$connect) {
    die("Ma'lumotlar bazasiga ulanishda xatolik: " . mysqli_connect_error());
}

// Adminlarni yuklash
$admins = @file_get_contents("admin/admins.txt");
$admin = explode("\n", $admins);
$studio_name = @file_get_contents("admin/studio_name.txt");
array_push($admin, $obito_us); // Sizning ID ingiz adminlar ro'yxatiga qo'shildi

$user = @file_get_contents("admin/user.txt");
$bot_info = bot('getme', ['bot'])->result;
$bot = $bot_info ? $bot_info->username : "anime_bot";
$soat = date('H:i');
$sana = date("d.m.Y");

$protocol = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? "https" : "http";
$host = $_SERVER['HTTP_HOST'];
$uri = $_SERVER['REQUEST_URI'];
$folder_path = rtrim(dirname($uri), '/\\');
$host_no_www = preg_replace('/^www\./', '', $host);
$web_urlis = "$protocol://$host_no_www$folder_path/animes.php";

// Qolgan funksiyalar o'zgarishsiz qoladi...
// (Kodning davomi)

function getAdmin($chat){
    $url = "https://api.telegram.org/bot".API_KEY."/getChatAdministrators?chat_id=@".$chat;
    $result = @file_get_contents($url);
    $result = json_decode($result);
    return $result->ok;
}

function deleteFolder($path){
    if(is_dir($path) === true){
        $files = array_diff(scandir($path), array('.', '..'));
        foreach ($files as $file)
            deleteFolder(realpath($path) . '/' . $file);
        return rmdir($path);
    }else if (is_file($path) === true)
        return unlink($path);
    return false;
}

function joinchat($userId, $key = null) {
    global $connect, $bot, $status, $bot_token;

    if ($status == 'VIP') return true;

    $userId = strval($userId);
    $query = $connect->query("SELECT channelId, channelType, channelLink FROM channels");
    if ($query->num_rows === 0) return true;

    $noSubs = 0;
    $buttons = [];
    $channels = $query->fetch_all(MYSQLI_ASSOC);

    foreach ($channels as $channel) {
        $channelId = $channel['channelId'];
        $channelLink = $channel['channelLink'];
        $channelType = $channel['channelType'];

        if ($channelType === "request") {
            $check = $connect->query("SELECT * FROM joinRequests WHERE BINARY channelId = '$channelId' AND BINARY userId = '$userId'");
            
            if ($check->num_rows === 0) {
                $connect->query("INSERT INTO joinRequests (channelId, userId) VALUES ('$channelId', '$userId')");
                $noSubs++;
                $buttons[] = [
                    'text' => "📨 So'rov yuborish ($noSubs)",
                    'url'  => "https://t.me/$bot?start=joinreq_$channelId"
                ];
            }
        } else {
            $chatMember = bot('getChatMember', [
                'chat_id' => $channelId,
                'user_id' => $userId
            ]);

            if (!isset($chatMember->result->status) || $chatMember->result->status === "left") {
                $noSubs++;
                $chatInfo = bot('getChat', ['chat_id' => $channelId]);
                $channelTitle = $chatInfo->result->title ?? "Kanal";
                $buttons[] = [
                    'text' => $channelTitle,
                    'url'  => $channelLink
                ];
            }
        }
    }

    if ($noSubs > 0) {
        $insta = @file_get_contents("admin/instagram.txt");
        $youtube = @file_get_contents("admin/youtube.txt");

        if (!empty($insta)) {
            $buttons[] = ['text' => "📸 Instagram", 'url' => $insta];
        }
        if (!empty($youtube)) {
            $buttons[] = ['text' => "📺 YouTube", 'url' => $youtube];
        }
        
        $callback = !empty($key) ? "chack=" . $key : "panel";
        $buttons[] = ['text' => "✅ Tekshirish", 'callback_data' => $callback];

        sms($userId, "<b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling yoki so'rov yuboring❗️</b>", json_encode([
            'inline_keyboard' => array_chunk($buttons, 1)
        ]));

        exit();
    }

    return true;
}

function accl($d, $s, $j=false){
    return bot('answerCallbackQuery', [
        'callback_query_id' => $d,
        'text' => $s,
        'show_alert' => $j
    ]);
}

function del(){
    global $cid, $mid, $cid2, $mid2;
    return bot('deleteMessage', [
        'chat_id' => $cid2 ?: $cid,
        'message_id' => $mid2 ?: $mid,
    ]);
}

function edit($id, $mid, $tx, $m){
    return bot('editMessageText', [
        'chat_id' => $id,
        'message_id' => $mid,
        'text' => $tx,
        'parse_mode' => "HTML",
        'disable_web_page_preview' => true,
        'reply_markup' => $m,
    ]);
}

function sms($id, $tx, $m){
    return bot('sendMessage', [
        'chat_id' => $id,
        'text' => $tx,
        'parse_mode' => "HTML",
        'disable_web_page_preview' => true,
        'reply_markup' => $m,
    ]);
}

function get($h){
    return @file_get_contents($h);
}

function put($h, $r){
    file_put_contents($h, $r);
}

function bot($method, $datas=[]){
    $url = "https://api.telegram.org/bot".API_KEY."/".$method;
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $datas);
    $res = curl_exec($ch);
    if(curl_error($ch)){
        var_dump(curl_error($ch));
    }else{
        return json_decode($res);
    }
}

function process_anime($cid, $id) {
    global $connect, $anime_kanal, $content;

    if (!is_numeric($id)) {
        sms($cid, "❗ Noto'g'ri ID kiritildi.");
        return;
    }

    $rew = mysqli_fetch_assoc(mysqli_query($connect, "SELECT * FROM animelar WHERE id = $id"));

    if ($rew) {
        $file_id = $rew['rams'];
        $first_char = strtoupper($file_id[0]);
        $media_type = ($first_char == 'B') ? 'sendVideo' : 'sendPhoto';
        $media_key = ($first_char == 'B') ? 'video' : 'photo';

        $cs = $rew['qidiruv'] + 1;
        mysqli_query($connect, "UPDATE animelar SET qidiruv = $cs WHERE id = $id");

        $kanal_text = is_array($anime_kanal) ? implode(", ", $anime_kanal) : $anime_kanal;

        bot($media_type, [
            'chat_id' => $cid,
            $media_key => $file_id,
            'caption' => "<b>🎬 Nomi: {$rew['nom']}</b>\n\n" .
                         "🎥 Qismi: {$rew['qismi']}\n" .
                         "🌍 Davlati: {$rew['davlat']}\n" .
                         "🇺🇿 Tili: {$rew['tili']}\n" .
                         "📆 Yili: {$rew['yili']}\n" .
                         "🎞 Janri: {$rew['janri']}\n\n" .
                         "🔍 Qidirishlar soni: $cs\n\n" .
                         "🍿 $kanal_text",
            'parse_mode' => "html",
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [['text' => "📥 Yuklab olish", 'callback_data' => "yuklanolish=$id=1"]]
                ]
            ]),
            'protect_content' => $content,
        ]);
    } else {
        sms($cid, "❌ Ma'lumot topilmadi.");
    }
}

function containsEmoji($string) {
    $emojiPattern = '/[\x{1F600}-\x{1F64F}]/u';
    $emojiPattern .= '|[\x{1F300}-\x{1F5FF}]';
    $emojiPattern .= '|[\x{1F680}-\x{1F6FF}]';
    $emojiPattern .= '|[\x{1F700}-\x{1F77F}]';
    $emojiPattern .= '|[\x{1F780}-\x{1F7FF}]';
    $emojiPattern .= '|[\x{1F800}-\x{1F8FF}]';
    $emojiPattern .= '|[\x{1F900}-\x{1F9FF}]';
    $emojiPattern .= '|[\x{1FA00}-\x{1FA6F}]';
    $emojiPattern .= '|[\x{2600}-\x{26FF}]';
    $emojiPattern .= '|[\x{2700}-\x{27BF}]';
    $emojiPattern .= '/u';
 
    return preg_match($emojiPattern, $string) === 1;
}

function adminsAlert($message){
    global $admin;
    foreach($admin as $adm){
        sms($adm, $message, null);
    }
}

// Webhook dan kelgan ma'lumotlarni olish
$alijonov = json_decode(file_get_contents('php://input'));
if (!$alijonov) {
    exit();
}

$message = $alijonov->message ?? null;
$callback_query = $alijonov->callback_query ?? null;

if ($message) {
    $cid = $message->chat->id;
    $name = $message->chat->first_name;
    $tx = $message->text;
    $step = @file_get_contents("step/$cid.step");
    $mid = $message->message_id;
    $type = $message->chat->type;
    $text = $message->text;
    $uid = $message->from->id;
    $name = $message->from->first_name;
    $familya = $message->from->last_name ?? '';
    $username = $message->from->username ?? '';
    $chat_id = $message->chat->id;
    $message_id = $message->message_id;
}

if ($callback_query) {
    $data = $callback_query->data;
    $qid = $callback_query->id;
    $cid2 = $callback_query->message->chat->id;
    $mid2 = $callback_query->message->message_id;
    $callfrid = $callback_query->from->id;
    $callname = $callback_query->from->first_name;
    $calluser = $callback_query->from->username ?? '';
}

// Papkalarni yaratish
@mkdir("tizim", 0777, true);
@mkdir("step", 0777, true);
@mkdir("admin", 0777, true);
@mkdir("tugma", 0777, true);
@mkdir("matn", 0777, true);

// Default tugmalar
if(!file_exists("tugma/key1.txt")) file_put_contents("tugma/key1.txt", "🔎 Anime izlash");
if(!file_exists("tugma/key2.txt")) file_put_contents("tugma/key2.txt", "💎 VIP");
if(!file_exists("tugma/key3.txt")) file_put_contents("tugma/key3.txt", "💰 Hisobim");
if(!file_exists("tugma/key4.txt")) file_put_contents("tugma/key4.txt", "➕ Pul kiritish");
if(!file_exists("tugma/key5.txt")) file_put_contents("tugma/key5.txt", "📚 Qo'llanma");
if(!file_exists("tugma/key6.txt")) file_put_contents("tugma/key6.txt", "💵 Reklama va Homiylik");

// Admin sozlamalari
if(!file_exists("admin/valyuta.txt")) file_put_contents("admin/valyuta.txt", "so'm");
if(!file_exists("admin/vip.txt")) file_put_contents("admin/vip.txt", "25000");
if(!file_exists("admin/holat.txt")) file_put_contents("admin/holat.txt", "Yoqilgan");
if(!file_exists("admin/anime_kanal.txt")) file_put_contents("admin/anime_kanal.txt", "@username");
if(!file_exists("tizim/content.txt")) file_put_contents("tizim/content.txt", "false");
if(!file_exists("matn/start.txt")) file_put_contents("matn/start.txt", "✨");

// Foydalanuvchi ma'lumotlarini olish
$user_data = mysqli_query($connect, "SELECT * FROM user_id WHERE user_id = $chat_id");
$user_row = mysqli_fetch_assoc($user_data);
$status = $user_row['status'] ?? 'Oddiy';

$kabinet_data = mysqli_query($connect, "SELECT * FROM kabinet WHERE user_id = $chat_id");
$kabinet_row = mysqli_fetch_assoc($kabinet_data);
$pul = $kabinet_row['pul'] ?? 0;
$odam = $kabinet_row['odam'] ?? 0;
$ban = $kabinet_row['ban'] ?? 'unban';

// Tugma matnlari
$key1 = file_get_contents("tugma/key1.txt");
$key2 = file_get_contents("tugma/key2.txt");
$key3 = file_get_contents("tugma/key3.txt");
$key4 = file_get_contents("tugma/key4.txt");
$key5 = file_get_contents("tugma/key5.txt");
$key6 = file_get_contents("tugma/key6.txt");

$turi = @file_get_contents("tizim/turi.txt");
$anime_kanal = @file("admin/anime_kanal.txt", FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) ?: ["@username"];
$narx = file_get_contents("admin/vip.txt");
$valyuta = file_get_contents("admin/valyuta.txt");
$holat = file_get_contents("admin/holat.txt");
$content = file_get_contents("tizim/content.txt");

// Panel tugmalari
$panel = json_encode([
    'resize_keyboard' => true,
    'keyboard' => [
        [['text' => "*️⃣ Birlamchi sozlamalar"]],
        [['text' => "📊 Statistika"], ['text' => "✉ Xabar Yuborish"]],
        [['text' => "📬 Post tayyorlash"], ['text' => "🚀 Konkurs"]],
        [['text' => "🎥 Animelar sozlash"], ['text' => "💳 Hamyonlar"]],
        [['text' => "🔎 Foydalanuvchini boshqarish"]],
        [['text' => "📢 Kanallar"], ['text' => "🎛 Tugmalar"], ['text' => "📃 Matnlar"]],
        [['text' => "📋 Adminlar"], ['text' => "🤖 Bot holati"]],
        [['text' => "◀️ Orqaga"]]
    ]
]);

$menu = json_encode([
    'resize_keyboard' => true,
    'keyboard' => [
        [['text' => "$key1"], ['text' => "🎁 Konkurs"]],
        [['text' => "$key2"], ['text' => "$key3"]],
        [['text' => "$key4"], ['text' => "$key5"]],
        [['text' => "$key6"]],
    ]
]);

$menus = json_encode([
    'resize_keyboard' => true,
    'keyboard' => [
        [['text' => "$key1"], ['text' => "🎁 Konkurs"]],
        [['text' => "$key2"], ['text' => "$key3"]],
        [['text' => "$key4"], ['text' => "$key5"]],
        [['text' => "$key6"]],
        [['text' => "🗄 Boshqarish"]],
    ]
]);

$back = json_encode([
    'resize_keyboard' => true,
    'keyboard' => [
        [['text' => "◀️ Orqaga"]],
    ]
]);

$boshqarish = json_encode([
    'resize_keyboard' => true,
    'keyboard' => [
        [['text' => "🗄 Boshqarish"]],
    ]
]);

// Admin tekshiruvi
$is_admin = in_array($cid, $admin) || $cid == $obito_us;
$menyu = $is_admin ? $menus : $menu;

// /start komandasi
if ($text == "/start" || $text == "◀️ Orqaga") {
    $start_text = file_get_contents("matn/start.txt");
    $start_text = str_replace(
        ["%first%", "%id%", "%botname%", "%hour%", "%date%"],
        [$name, $cid, $bot, $soat, $sana],
        $start_text
    );
    sms($cid, $start_text, $menyu);
    @unlink("step/$cid.step");
    exit();
}

echo "Bot ishga tushdi!";
?>
