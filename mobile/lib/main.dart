import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:speech_to_text/speech_to_text.dart';

void main() => runApp(const MisaApp());

class MisaApp extends StatelessWidget {
  const MisaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Миса',
      theme: ThemeData(
        colorSchemeSeed: const Color(0xFF5B8DEF),
        brightness: Brightness.dark,
        useMaterial3: true,
      ),
      home: const HomePage(),
    );
  }
}

class Msg {
  final String text;
  final bool mine; // true — я (телефон), false — ответ Мисы
  Msg(this.text, this.mine);
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});
  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _speech = SpeechToText();
  final _tts = FlutterTts();
  final _input = TextEditingController();
  final _log = <Msg>[];

  String _host = '';
  int _port = 8756;
  String _token = '';
  bool _listening = false;
  bool _speechReady = false;
  String _status = 'Настрой подключение (шестерёнка) →';

  @override
  void initState() {
    super.initState();
    _load();
    _initSpeech();
    _tts.setLanguage('ru-RU');
  }

  Future<void> _load() async {
    final p = await SharedPreferences.getInstance();
    setState(() {
      _host = p.getString('host') ?? '';
      _port = p.getInt('port') ?? 8756;
      _token = p.getString('token') ?? '';
    });
    if (_host.isNotEmpty) _ping();
  }

  Future<void> _save() async {
    final p = await SharedPreferences.getInstance();
    await p.setString('host', _host);
    await p.setInt('port', _port);
    await p.setString('token', _token);
  }

  Future<void> _initSpeech() async {
    _speechReady = await _speech.initialize(
      onStatus: (s) {
        if (s == 'done' || s == 'notListening') {
          setState(() => _listening = false);
        }
      },
      onError: (_) => setState(() => _listening = false),
    );
    setState(() {});
  }

  String get _base => 'http://$_host:$_port';

  Future<void> _ping() async {
    try {
      final r = await http
          .get(Uri.parse('$_base/ping'))
          .timeout(const Duration(seconds: 4));
      final ok = r.statusCode == 200 && r.body.contains('"ok"');
      setState(() => _status = ok ? 'ПК на связи ✓' : 'ПК не отвечает');
    } catch (_) {
      setState(() => _status = 'Нет связи с ПК');
    }
  }

  Future<void> _send(String text) async {
    text = text.trim();
    if (text.isEmpty) return;
    if (_host.isEmpty) {
      setState(() => _status = 'Сначала укажи IP компьютера');
      return;
    }
    setState(() {
      _log.add(Msg(text, true));
      _status = 'Отправляю…';
    });
    _input.clear();
    try {
      final r = await http
          .post(
            Uri.parse('$_base/command'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'token': _token, 'text': text}),
          )
          .timeout(const Duration(seconds: 30));
      if (r.statusCode == 200) {
        final reply =
            (jsonDecode(utf8.decode(r.bodyBytes))['reply'] ?? '').toString();
        setState(() {
          _log.add(Msg(reply, false));
          _status = 'ПК на связи ✓';
        });
        if (reply.isNotEmpty) _tts.speak(reply);
      } else if (r.statusCode == 403) {
        setState(() => _status = 'Неверный токен');
      } else {
        setState(() => _status = 'Ошибка ПК: ${r.statusCode}');
      }
    } catch (_) {
      setState(() => _status = 'Не удалось отправить (проверь Wi-Fi/IP)');
    }
  }

  Future<void> _toggleMic() async {
    if (!_speechReady) {
      setState(() => _status = 'Микрофон недоступен (дай разрешение)');
      return;
    }
    if (_listening) {
      await _speech.stop();
      setState(() => _listening = false);
      return;
    }
    setState(() => _listening = true);
    await _speech.listen(
      localeId: 'ru_RU',
      onResult: (res) {
        if (res.finalResult) {
          final text = res.recognizedWords;
          setState(() => _listening = false);
          if (text.trim().isNotEmpty) _send(text);
        }
      },
    );
  }

  void _openSettings() {
    final hostC = TextEditingController(text: _host);
    final portC = TextEditingController(text: _port.toString());
    final tokenC = TextEditingController(text: _token);
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Подключение к ПК'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: hostC,
              decoration: const InputDecoration(
                  labelText: 'IP компьютера', hintText: '192.168.1.50'),
              keyboardType: TextInputType.number,
            ),
            TextField(
              controller: portC,
              decoration: const InputDecoration(labelText: 'Порт'),
              keyboardType: TextInputType.number,
            ),
            TextField(
              controller: tokenC,
              decoration: const InputDecoration(labelText: 'Токен (phone_token)'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () async {
              setState(() {
                _host = hostC.text.trim();
                _port = int.tryParse(portC.text.trim()) ?? 8756;
                _token = tokenC.text.trim();
              });
              await _save();
              if (context.mounted) Navigator.pop(context);
              _ping();
            },
            child: const Text('Сохранить'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Миса'),
        actions: [
          IconButton(
              onPressed: _openSettings, icon: const Icon(Icons.settings)),
        ],
      ),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(10),
            color: Colors.black26,
            child: Text(_status, textAlign: TextAlign.center),
          ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: _log.length,
              itemBuilder: (_, i) {
                final m = _log[_log.length - 1 - i];
                return Align(
                  alignment:
                      m.mine ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: m.mine
                          ? const Color(0xFF5B8DEF)
                          : const Color(0xFF2A2F38),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Text(m.text),
                  ),
                );
              },
              reverse: true,
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(10),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _input,
                    decoration: const InputDecoration(
                      hintText: 'Команда текстом…',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: _send,
                  ),
                ),
                const SizedBox(width: 8),
                FloatingActionButton(
                  onPressed: _toggleMic,
                  backgroundColor: _listening ? Colors.red : null,
                  child: Icon(_listening ? Icons.stop : Icons.mic),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
