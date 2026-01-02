import 'package:flutter/material.dart';
import 'lesson_screen.dart';
import 'ai_chat_screen.dart';
import 'premium_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Language AI")),
      body: Column(
        children: [
          ListTile(
            title: const Text("📚 Lessons"),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const LessonScreen(levelId: 1),
                ),
              );
            },
          ),
          ListTile(
            title: const Text("🤖 AI Tutor"),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const AiChatScreen(),
                ),
              );
            },
          ),
          ListTile(
            title: const Text("💎 Premium"),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const PremiumScreen(),
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}
