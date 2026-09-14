import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:speech_to_text/speech_to_text.dart';

import 'actions.dart';
import 'brain.dart';

void main() => runApp(const PhoneAssistantApp());

class PhoneAssistantApp extends StatelessWidget {
  const PhoneAssistantApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Миса',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: const Color(0xFF7C5CFF),
        brightness: Brightness.dark,
        useMaterial3: true,
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});
  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _speech = SpeechToText();
  final _tts = FlutterTts();
  final _log = <String>[];

  String _apiKey = '';
  bool _ready = false;
  bool _listening = false;
  String _status = 'Нажми микрофон и говори';

  @override
  void initState() {
    super.initState();
    _tts.setLanguage('ru-RU');
    _init();
  }

  Future<void> _init() async {
    final p = await SharedPreferences.getInstance();
    _apiKey = p.getString('groq_key') ?? '';
    _ready = await _speech.initialize(
      onStatus: (s) {
        if (s == 'done' || s == 'notListening') {
          setState(() => _listening = false);
        }
      },
      onError: (_) => setState(() => _listening = false),
    );
    if (_apiKey.isEmpty) {
      setState(() => _status = 'Введи ключ Groq (шестерёнка) →');
    }
    setState(() {});
  }

  Future<void> _handle(String text) async {
    if (text.trim().isEmpty) return;
    setState(() {
      _log.add('🗣 $text');
      _status = 'Думаю…';
    });
    if (_apiKey.isEmpty) {
      _reply('Сначала введи ключ Groq в настройках');
      return;
    }
    final brain = PhoneBrain(_apiKey);
    final action = await brain.interpret(text);
    final result = await PhoneActions.execute(action);
    _reply(result);
  }

  void _reply(String text) {
    setState(() {
      _log.add('🤖 $text');
      _status = 'Готово';
    });
    if (text.isNotEmpty) _tts.speak(text);
  }

  Future<void> _toggleMic() async {
    if (!_ready) {
      setState(() => _status = 'Микрофон недоступен (дай разрешение)');
      return;
    }
    if (_listening) {
      await _speech.stop();
      setState(() => _listening = false);
      return;
    }
    setState(() {
      _listening = true;
      _status = 'Слушаю…';
    });
    await _speech.listen(
      localeId: 'ru_RU',
      onResult: (res) {
        if (res.finalResult) {
          setState(() => _listening = false);
          _handle(res.recognizedWords);
        }
      },
    );
  }

  void _openSettings() {
    final keyC = TextEditingController(text: _apiKey);
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Ключ Groq'),
        content: TextField(
          controller: keyC,
          decoration: const InputDecoration(hintText: 'gsk_...'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () async {
              final p = await SharedPreferences.getInstance();
              await p.setString('groq_key', keyC.text.trim());
              setState(() {
                _apiKey = keyC.text.trim();
                _status = 'Готово к работе';
              });
              if (context.mounted) Navigator.pop(context);
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
            padding: const EdgeInsets.all(12),
            color: Colors.black26,
            child: Text(_status, textAlign: TextAlign.center),
          ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(14),
              reverse: true,
              itemCount: _log.length,
              itemBuilder: (_, i) {
                final line = _log[_log.length - 1 - i];
                final mine = line.startsWith('🗣');
                return Align(
                  alignment:
                      mine ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: mine
                          ? const Color(0xFF7C5CFF)
                          : const Color(0xFF2A2F38),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Text(line),
                  ),
                );
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(20),
            child: GestureDetector(
              onTap: _toggleMic,
              child: CircleAvatar(
                radius: 44,
                backgroundColor:
                    _listening ? Colors.red : const Color(0xFF7C5CFF),
                child: Icon(_listening ? Icons.stop : Icons.mic, size: 40),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
