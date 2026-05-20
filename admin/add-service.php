<?php
/**
 * /admin/add-service.php
 *
 * Простая админ-панель для добавления услуг в data/services.json.
 *
 * ВНИМАНИЕ: это базовая реализация для локальной/тестовой работы.
 * Перед публикацией на боевой сервер обязательно:
 *   1) Защитите эту страницу авторизацией (htpasswd, сессия, токен).
 *   2) Используйте HTTPS.
 *   3) Загрузка изображений идёт в /images — проверьте права на запись.
 *   4) Сделайте резервную копию services.json перед изменениями.
 *
 * Требования: PHP 7.4+ с поддержкой загрузки файлов (file_uploads = On).
 */

declare(strict_types=1);

// ----- Конфигурация -----
$JSON_PATH      = __DIR__ . '/../data/services.json';
$IMAGES_DIR_FS  = __DIR__ . '/../images';   // абсолютный путь для записи
$IMAGES_DIR_WEB = 'images';                  // путь, который пишем в JSON
$ALLOWED_EXTS   = ['jpg', 'jpeg', 'png', 'webp', 'gif'];
$MAX_FILE_SIZE  = 5 * 1024 * 1024;           // 5 МБ

// ----- Переменные для отображения -----
$message = '';
$message_type = ''; // 'success' | 'error'

// ----- Обработка POST-запроса -----
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        // Получаем и очищаем поля
        $title       = isset($_POST['title']) ? trim((string)$_POST['title']) : '';
        $price       = isset($_POST['price']) ? trim((string)$_POST['price']) : '';
        $description = isset($_POST['description']) ? trim((string)$_POST['description']) : '';
        $popular     = isset($_POST['popular']) && $_POST['popular'] === 'on';

        // Базовая валидация
        if ($title === '' || mb_strlen($title) < 3) {
            throw new RuntimeException('Название услуги должно содержать минимум 3 символа.');
        }
        if ($price === '') {
            throw new RuntimeException('Укажите цену услуги.');
        }
        if ($description === '' || mb_strlen($description) < 10) {
            throw new RuntimeException('Описание должно содержать минимум 10 символов.');
        }

        // Обработка загруженного изображения
        $imageWebPath = '';
        if (isset($_FILES['image']) && $_FILES['image']['error'] === UPLOAD_ERR_OK) {
            $file = $_FILES['image'];

            // Проверка размера
            if ($file['size'] > $MAX_FILE_SIZE) {
                throw new RuntimeException('Изображение больше 5 МБ.');
            }

            // Проверка расширения
            $ext = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
            if (!in_array($ext, $ALLOWED_EXTS, true)) {
                throw new RuntimeException('Допустимые форматы: ' . implode(', ', $ALLOWED_EXTS));
            }

            // Проверка реального MIME-типа
            $finfo = finfo_open(FILEINFO_MIME_TYPE);
            $mime  = finfo_file($finfo, $file['tmp_name']);
            finfo_close($finfo);
            $allowedMimes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
            if (!in_array($mime, $allowedMimes, true)) {
                throw new RuntimeException('Файл не является корректным изображением.');
            }

            // Создаём папку, если её нет
            if (!is_dir($IMAGES_DIR_FS)) {
                if (!mkdir($IMAGES_DIR_FS, 0775, true) && !is_dir($IMAGES_DIR_FS)) {
                    throw new RuntimeException('Не удалось создать папку для изображений.');
                }
            }

            // Уникальное имя файла
            $slug = preg_replace('/[^a-z0-9]+/i', '-', $title);
            $slug = trim(strtolower($slug), '-');
            if ($slug === '') $slug = 'service';
            $filename = $slug . '-' . time() . '.' . $ext;

            $destFs  = $IMAGES_DIR_FS . '/' . $filename;
            $destWeb = $IMAGES_DIR_WEB . '/' . $filename;

            if (!move_uploaded_file($file['tmp_name'], $destFs)) {
                throw new RuntimeException('Не удалось сохранить файл изображения.');
            }
            $imageWebPath = $destWeb;
        }

        // Читаем существующий JSON
        if (!file_exists($JSON_PATH)) {
            throw new RuntimeException('Файл services.json не найден.');
        }
        $jsonContent = file_get_contents($JSON_PATH);
        $services = json_decode($jsonContent, true);
        if (!is_array($services)) {
            throw new RuntimeException('services.json содержит некорректный JSON.');
        }

        // Добавляем новую услугу в конец массива
        $newService = [
            'title'       => $title,
            'price'       => $price,
            'description' => $description,
            'image'       => $imageWebPath,
            'popular'     => $popular,
        ];
        $services[] = $newService;

        // Записываем обратно с красивым форматированием
        $written = file_put_contents(
            $JSON_PATH,
            json_encode($services, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\n"
        );
        if ($written === false) {
            throw new RuntimeException('Не удалось записать services.json. Проверьте права на файл.');
        }

        $message = 'Услуга «' . htmlspecialchars($title, ENT_QUOTES, 'UTF-8') . '» успешно добавлена!';
        $message_type = 'success';

    } catch (Throwable $e) {
        $message = $e->getMessage();
        $message_type = 'error';
    }
}

// ----- Подсчёт текущего количества услуг для информации -----
$serviceCount = 0;
if (file_exists($JSON_PATH)) {
    $current = json_decode((string)file_get_contents($JSON_PATH), true);
    if (is_array($current)) $serviceCount = count($current);
}
?>
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>Админ — Добавить услугу | РемонтПро</title>
    <link rel="stylesheet" href="../css/style.css">
    <style>
        /* Локальные стили только для админки */
        body { background: var(--color-bg-alt); padding: 40px 16px; }
        .admin {
            max-width: 720px;
            margin: 0 auto;
            background: var(--color-white);
            border-radius: var(--radius-lg);
            padding: 48px;
            box-shadow: var(--shadow-md);
        }
        .admin__header {
            margin-bottom: 32px;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--color-line);
        }
        .admin__back {
            display: inline-block;
            margin-bottom: 12px;
            font-size: 0.9rem;
            color: var(--color-text-soft);
        }
        .admin__back:hover { color: var(--color-accent-dark); }
        .admin__title { margin-bottom: 8px; }
        .admin__sub { color: var(--color-text-soft); }
        .alert {
            padding: 14px 18px;
            border-radius: var(--radius);
            margin-bottom: 24px;
            font-size: 0.95rem;
        }
        .alert--success {
            background: #DCFCE7;
            color: #166534;
            border: 1px solid #BBF7D0;
        }
        .alert--error {
            background: #FEF2F2;
            color: #991B1B;
            border: 1px solid #FECACA;
        }
        .checkbox-field {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 22px;
            cursor: pointer;
        }
        .checkbox-field input { width: auto; }
        .file-field input[type="file"] {
            padding: 10px;
            background: var(--color-bg);
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px;
            background: var(--color-bg-alt);
            border-radius: var(--radius);
            margin-top: 32px;
            font-size: 0.9rem;
            color: var(--color-text-soft);
        }
        .info-row strong { color: var(--color-dark); font-size: 1.1rem; }
    </style>
</head>
<body>

<div class="admin">
    <div class="admin__header">
        <a href="../index.html" class="admin__back">← На сайт</a>
        <h1 class="admin__title">Добавить услугу</h1>
        <p class="admin__sub">Новая услуга добавится в файл <code>data/services.json</code> и автоматически появится на сайте.</p>
    </div>

    <?php if ($message): ?>
        <div class="alert alert--<?= htmlspecialchars($message_type, ENT_QUOTES, 'UTF-8') ?>">
            <?= htmlspecialchars($message, ENT_QUOTES, 'UTF-8') ?>
        </div>
    <?php endif; ?>

    <form method="post" enctype="multipart/form-data" class="form" style="padding:0;box-shadow:none;">
        <div class="form__field">
            <label for="title">Название услуги *</label>
            <input type="text" id="title" name="title" placeholder="Например: Ремонт балкона" required maxlength="120">
        </div>

        <div class="form__field">
            <label for="price">Цена *</label>
            <input type="text" id="price" name="price" placeholder="Например: от 400$" required maxlength="60">
        </div>

        <div class="form__field">
            <label for="description">Описание *</label>
            <textarea id="description" name="description" rows="4" placeholder="Краткое описание услуги (минимум 10 символов)" required maxlength="500"></textarea>
        </div>

        <div class="form__field file-field">
            <label for="image">Изображение (опционально)</label>
            <input type="file" id="image" name="image" accept="image/jpeg,image/png,image/webp,image/gif">
            <small style="color:var(--color-text-soft);font-size:0.82rem;display:block;margin-top:6px;">
                JPG, PNG, WEBP или GIF. До 5 МБ. Если не загрузить — будет показан градиентный фон.
            </small>
        </div>

        <label class="checkbox-field" for="popular">
            <input type="checkbox" id="popular" name="popular">
            <span>Показывать в блоке «Популярные услуги» на главной</span>
        </label>

        <button type="submit" class="btn btn--primary btn--full">Добавить услугу</button>
    </form>

    <div class="info-row">
        <span>Всего услуг в каталоге:</span>
        <strong><?= (int)$serviceCount ?></strong>
    </div>
</div>

</body>
</html>
