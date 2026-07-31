# 📱 Мобильное приложение «Миса» (Android)

Нативный клиент: кнопка микрофона → телефон распознаёт речь → отправляет
команду на ПК → показывает и озвучивает ответ. Работает по домашней Wi-Fi.

Здесь лежит только код приложения (`lib/main.dart`, `pubspec.yaml`).
Платформенные папки (`android/`) создаёт сам Flutter командой ниже.

## Что нужно один раз установить (на ПК/ноуте, где собираешь)
1. **Flutter SDK** — https://docs.flutter.dev/get-started/install (Windows).
2. **Android Studio** — для Android SDK и сборки. После установки открой его
   один раз и доустанови Android SDK, когда предложит.
3. Проверь: в терминале `flutter doctor` — должно быть без критичных ошибок
   по Android.

## Сборка приложения
```bash
# 1) создаём платформенные папки прямо в этой папке mobile/
cd mobile
flutter create .

# 2) ставим зависимости (pubspec.yaml уже готов)
flutter pub get

# 3) правим AndroidManifest — см. раздел ниже (разрешения + HTTP)

# 4a) запуск на подключённом по USB телефоне (с включённой отладкой):
flutter run

# 4b) или собрать APK-файл, чтобы просто установить:
flutter build apk --release
# готовый файл: build/app/outputs/flutter-apk/app-release.apk
```
APK перекинь на телефон (кабель/облако) и установи (разреши установку из
неизвестных источников).

## Правки AndroidManifest (обязательно)
Файл `android/app/src/main/AndroidManifest.xml`.

1. Внутри `<manifest ...>` **перед** `<application>` добавь разрешения и queries:
```xml
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.RECORD_AUDIO"/>
<queries>
  <intent><action android:name="android.speech.RecognitionService"/></intent>
  <intent><action android:name="android.intent.action.TTS_SERVICE"/></intent>
</queries>
```
2. В теге `<application ...>` добавь атрибут (разрешить обычный HTTP к ПК по
   локальному IP):
```xml
android:usesCleartextTraffic="true"
```

## Первый запуск
1. На ПК включи сервер: в `config.yaml` `phone.enabled: true`, в `secrets.yaml`
   `phone_token: "..."`, перезапусти Мису.
2. В приложении нажми ⚙️ и введи **IP компьютера** (`ipconfig` → IPv4), порт
   `8756` и тот же **токен**. Сохрани.
3. Статус вверху должен стать «ПК на связи ✓».
4. Жми микрофон и говори — или пиши команды текстом.

## Частые проблемы
- **«Нет связи с ПК»** — телефон и ПК в одной Wi-Fi? Правильный IP? На ПК
  разрешён порт в брандмауэре (при первом запуске Windows спросит — «Разрешить
  доступ» для частных сетей)?
- **Микрофон не слышит** — дай приложению разрешение на микрофон в настройках
  телефона; на телефоне должен быть установлен голосовой ввод Google с русским.
- **Команды не выполняются** — проверь, что на ПК Миса запущена и токен совпадает.
