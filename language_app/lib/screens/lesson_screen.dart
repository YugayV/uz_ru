import 'package:flutter/material.dart';
import '../api/api_service.dart';

class LessonScreen extends StatefulWidget {
  final int levelId;
  const LessonScreen({super.key, required this.levelId});

  @override
  State<LessonScreen> createState() => _LessonScreenState();
}

class _LessonScreenState extends State<LessonScreen> {
  List lessons = [];

  @override
  void initState() {
    super.initState();
    load();
  }

  void load() async {
    lessons = await ApiService.getLessons(widget.levelId);
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Lessons")),
      body: ListView.builder(
        itemCount: lessons.length,
        itemBuilder: (_, i) {
          return ListTile(
            title: Text(lessons[i]["title"]),
          );
        },
      ),
    );
  }
}
