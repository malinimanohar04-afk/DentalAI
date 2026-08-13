import 'package:flutter/material.dart';
import 'dental_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Oral Cavity AI',
      theme: ThemeData(primarySwatch: Colors.teal),
      home: const DentalScreen(),
    );
  }
}