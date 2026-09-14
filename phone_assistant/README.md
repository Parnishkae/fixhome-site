# 📱 Миса — голосовой помощник для телефона (как Алиса)

Самостоятельное Android-приложение: нажимаешь микрофон, говоришь команду —
телефон **сам** выполняет действие. Понимание команд — через твой ключ Groq.

> Это НЕ пульт для ПК (тот — в папке `mobile/`). Здесь помощник управляет
> самим телефоном.

## Что умеет
- «открой YouTube / Chrome / Telegram …» — запуск приложений
- «найди …», «открой сайт …» — поиск и сайты
- «позвони на номер …», «напиши смс на … текст …»
- «поставь будильник на 7 30», «таймер на 10 минут»
- «включи / выключи фонарик»
- «сколько заряда»
- «открой настройки Wi-Fi / Bluetooth»
- обычные вопросы — просто ответит голосом

Ограничения Android: напрямую включать Wi-Fi/Bluetooth нельзя (только открыть
настройки); звонок по имени из контактов пока не поддержан — только по номеру.

## Установка инструментов (один раз)
1. **Flutter SDK** — https://docs.flutter.dev/get-started/install
2. **Android Studio** (Android SDK). Затем `flutter doctor` — без критичных ошибок.

## Сборка
```bash
cd phone_assistant
flutter create .          # создаёт android/ и пр.
flutter pub get
# правки AndroidManifest — см. ниже
flutter build apk --release
# APK: build/app/outputs/flutter-apk/app-release.apk
```
Перекинь APK на телефон и установи (разреши установку из неизвестных источников).

## Правки AndroidManifest
Файл `android/app/src/main/AndroidManifest.xml`, внутри `<manifest>` **перед**
`<application>`:
```xml
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.RECORD_AUDIO"/>
<!-- Если «открой приложение» не срабатывает, добавь (для личной сборки ок): -->
<!-- <uses-permission android:name="android.permission.QUERY_ALL_PACKAGES"/> -->

<queries>
  <intent><action android:name="android.speech.RecognitionService"/></intent>
  <intent><action android:name="android.intent.action.TTS_SERVICE"/></intent>
  <intent>
    <action android:name="android.intent.action.VIEW"/>
    <data android:scheme="https"/>
  </intent>
  <intent>
    <action android:name="android.intent.action.DIAL"/>
    <data android:scheme="tel"/>
  </intent>
  <intent>
    <action android:name="android.intent.action.SENDTO"/>
    <data android:scheme="sms"/>
  </intent>
  <intent><action android:name="android.intent.action.MAIN"/></intent>
</queries>
```

## Первый запуск
1. Открой приложение, дай разрешение на **микрофон**.
2. ⚙️ вверху → вставь **ключ Groq** (`gsk_...`) → Сохрани.
3. Жми большой микрофон и говори: «открой ютуб», «поставь таймер на 5 минут»,
   «включи фонарик», «сколько заряда».

## Если что-то не работает
- **«Нет связи с ИИ»** — проверь ключ Groq и интернет.
- **Микрофон не слышит** — разрешение на микрофон + установлен голосовой ввод
  Google с русским языком.
- **«открой приложение» не запускает** — раскомментируй `QUERY_ALL_PACKAGES`
  в манифесте и пересобери.
- Ошибка сборки по конкретному плагину — пришли текст, уберём/заменим плагин.
