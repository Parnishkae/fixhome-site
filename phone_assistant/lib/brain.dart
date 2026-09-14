import 'dart:convert';
import 'package:http/http.dart' as http;

/// Понимание команды: текст -> действие. Использует Groq (OpenAI-совместимый).
/// Возвращает Map: {action, ...параметры, say}.
class PhoneBrain {
  final String apiKey;
  final String model;
  PhoneBrain(this.apiKey, {this.model = 'llama-3.3-70b-versatile'});

  static const _system = '''
Ты — голосовой помощник на телефоне (Android). Пользователь говорит команду,
ты решаешь, что сделать, и отвечаешь СТРОГО одним объектом JSON без пояснений.

Формат: {"action": "...", "say": "короткий ответ вслух", ...параметры}

Возможные action и параметры:
  {"action":"open_app","package":"<android package>","say":"..."}   // напр. youtube = com.google.android.youtube
  {"action":"web_search","query":"...","say":"..."}
  {"action":"open_url","url":"https://...","say":"..."}
  {"action":"call","number":"+7...","say":"..."}
  {"action":"sms","number":"+7...","text":"...","say":"..."}
  {"action":"set_alarm","hour":7,"minute":30,"say":"..."}
  {"action":"set_timer","seconds":600,"say":"..."}
  {"action":"open_settings","screen":"wifi|bluetooth|location|main","say":"..."}
  {"action":"flashlight","on":true,"say":"..."}
  {"action":"battery","say":""}          // ответ подставит приложение
  {"action":"say","say":"обычный разговорный ответ"}

Правила:
- Для «открой <приложение>» выбери правильный android package известного
  приложения (youtube, chrome, whatsapp, telegram, instagram, vk и т.п.).
- Если не знаешь package — используй web_search.
- Wi-Fi/Bluetooth напрямую включать нельзя — открывай настройки (open_settings).
- "say" короткое, по-русски, дружелюбно.
''';

  Future<Map<String, dynamic>> interpret(String text) async {
    try {
      final r = await http
          .post(
            Uri.parse('https://api.groq.com/openai/v1/chat/completions'),
            headers: {
              'Authorization': 'Bearer $apiKey',
              'Content-Type': 'application/json',
            },
            body: jsonEncode({
              'model': model,
              'temperature': 0.2,
              'messages': [
                {'role': 'system', 'content': _system},
                {'role': 'user', 'content': text},
              ],
            }),
          )
          .timeout(const Duration(seconds: 20));
      if (r.statusCode != 200) {
        return {'action': 'say', 'say': 'Ошибка ИИ: ${r.statusCode}'};
      }
      final content =
          jsonDecode(utf8.decode(r.bodyBytes))['choices'][0]['message']['content']
              as String;
      return _extractJson(content);
    } catch (_) {
      return {'action': 'say', 'say': 'Нет связи с ИИ. Проверь интернет и ключ'};
    }
  }

  Map<String, dynamic> _extractJson(String s) {
    final start = s.indexOf('{');
    final end = s.lastIndexOf('}');
    if (start != -1 && end > start) {
      try {
        return Map<String, dynamic>.from(jsonDecode(s.substring(start, end + 1)));
      } catch (_) {}
    }
    return {'action': 'say', 'say': s.trim().isEmpty ? 'Не поняла' : s.trim()};
  }
}
