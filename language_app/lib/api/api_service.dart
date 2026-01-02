import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = "http://YOUR_SERVER_IP:8000";

  static Future<List<dynamic>> getLessons(int levelId) async {
    final res = await http.get(
      Uri.parse("$baseUrl/lessons/level/$levelId"),
    );
    return json.decode(res.body);
  }

  static Future<Map<String, dynamic>> aiChat(
      int userId, String message) async {
    final res = await http.post(
      Uri.parse("$baseUrl/ai/chat/$userId?message=$message"),
    );
    return json.decode(res.body);
  }

  static Future<Map<String, dynamic>> buyPremium(int userId) async {
    final res = await http.post(
      Uri.parse("$baseUrl/premium/buy/$userId"),
    );
    return json.decode(res.body);
  }
}
