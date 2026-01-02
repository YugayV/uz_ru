import 'package:flutter/material.dart';
import '../api/api_service.dart';

class AiChatScreen extends StatefulWidget {
  const AiChatScreen({super.key});

  @override
  State<AiChatScreen> createState() => _AiChatScreenState();
}

class _AiChatScreenState extends State<AiChatScreen> {
  final controller = TextEditingController();
  String reply = "";

  void send() async {
    final res = await ApiService.aiChat(1, controller.text);
    reply = res["reply"];
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("AI Tutor")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(controller: controller),
            ElevatedButton(onPressed: send, child: const Text("Send")),
            const SizedBox(height: 20),
            Text(reply),
          ],
        ),
      ),
    );
  }
}
