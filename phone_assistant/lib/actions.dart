import 'package:android_intent_plus/android_intent.dart';
import 'package:android_intent_plus/flag.dart';
import 'package:battery_plus/battery_plus.dart';
import 'package:external_app_launcher/external_app_launcher.dart';
import 'package:torch_light/torch_light.dart';
import 'package:url_launcher/url_launcher.dart';

/// Выполняет действие, разобранное мозгом. Возвращает текст для озвучки.
class PhoneActions {
  static Future<String> execute(Map<String, dynamic> a) async {
    final action = (a['action'] ?? 'say').toString();
    final say = (a['say'] ?? '').toString();
    try {
      switch (action) {
        case 'open_app':
          await LaunchApp.openApp(
              androidPackageName: (a['package'] ?? '').toString());
          return say.isEmpty ? 'Открываю' : say;

        case 'web_search':
          final q = Uri.encodeComponent((a['query'] ?? '').toString());
          await _open('https://www.google.com/search?q=$q');
          return say.isEmpty ? 'Ищу' : say;

        case 'open_url':
          await _open((a['url'] ?? '').toString());
          return say.isEmpty ? 'Открываю' : say;

        case 'call':
          await _open('tel:${a['number']}');
          return say.isEmpty ? 'Звоню' : say;

        case 'sms':
          final t = Uri.encodeComponent((a['text'] ?? '').toString());
          await _open('sms:${a['number']}?body=$t');
          return say.isEmpty ? 'Открываю сообщение' : say;

        case 'set_alarm':
          await AndroidIntent(
            action: 'android.intent.action.SET_ALARM',
            arguments: {
              'android.intent.extra.alarm.HOUR': a['hour'] ?? 8,
              'android.intent.extra.alarm.MINUTES': a['minute'] ?? 0,
              'android.intent.extra.alarm.SKIP_UI': true,
            },
          ).launch();
          return say.isEmpty ? 'Будильник поставлен' : say;

        case 'set_timer':
          await AndroidIntent(
            action: 'android.intent.action.SET_TIMER',
            arguments: {
              'android.intent.extra.alarm.LENGTH': a['seconds'] ?? 60,
              'android.intent.extra.alarm.SKIP_UI': true,
            },
          ).launch();
          return say.isEmpty ? 'Таймер запущен' : say;

        case 'open_settings':
          await _openSettings((a['screen'] ?? 'main').toString());
          return say.isEmpty ? 'Открываю настройки' : say;

        case 'flashlight':
          if (a['on'] == true) {
            await TorchLight.enableTorch();
            return say.isEmpty ? 'Фонарик включён' : say;
          } else {
            await TorchLight.disableTorch();
            return say.isEmpty ? 'Фонарик выключен' : say;
          }

        case 'battery':
          final level = await Battery().batteryLevel;
          return 'Заряд батареи $level процентов';

        case 'say':
        default:
          return say.isEmpty ? 'Готово' : say;
      }
    } catch (e) {
      return 'Не получилось: $e';
    }
  }

  static Future<void> _open(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  static Future<void> _openSettings(String screen) async {
    final actions = {
      'wifi': 'android.settings.WIFI_SETTINGS',
      'bluetooth': 'android.settings.BLUETOOTH_SETTINGS',
      'location': 'android.settings.LOCATION_SOURCE_SETTINGS',
      'main': 'android.settings.SETTINGS',
    };
    await AndroidIntent(
      action: actions[screen] ?? actions['main']!,
      flags: <int>[Flag.FLAG_ACTIVITY_NEW_TASK],
    ).launch();
  }
}
