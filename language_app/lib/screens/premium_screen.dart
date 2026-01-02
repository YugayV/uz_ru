import 'package:flutter/material.dart';
import '../api/api_service.dart';

class PremiumScreen extends StatelessWidget {
  const PremiumScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Premium")),
      body: Center(
        child: ElevatedButton(
          onPressed: () async {
            await ApiService.buyPremium(1);
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text("Premium activated!")),
            );
          },
          child: const Text("Buy Premium \$5"),
        ),
      ),
    );
  }
}
