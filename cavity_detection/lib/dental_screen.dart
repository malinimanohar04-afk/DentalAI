import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class DentalScreen extends StatefulWidget {
  const DentalScreen({super.key});

  @override
  State<DentalScreen> createState() => _DentalScreenState();
}

class _DentalScreenState extends State<DentalScreen> {
  Uint8List? _webImageBytes;
  Map<String, dynamic>? _results;
  bool _isLoading = false;

  // ------------------- STEP 1: Capture & Analyze -------------------
  Future<void> captureAndAnalyze() async {
    setState(() {
      _isLoading = true;
      _results = null;
      _webImageBytes = null;
    });

    try {
      var uri = Uri.parse('http://192.168.1.35:8000/capture');
      // Android Emulator: http://10.0.2.2:8000/capture
      // Real Device: http://<YOUR_PC_IP>:8000/capture

      var response = await http.get(uri);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final bytes = base64Decode(data['image_base64']);

        setState(() {
          _webImageBytes = bytes;
          _results = data;
        });
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: ${response.statusCode}')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  // ------------------- BUILD UI -------------------
  @override
  Widget build(BuildContext context) {
    final hasImage = _webImageBytes != null;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Oral Cavity AI Detector"),
        backgroundColor: Colors.teal,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Container(
              height: 200,
              color: Colors.grey[200],
              child: Center(
                child: hasImage
                    ? Image.memory(_webImageBytes!, height: 200)
                    : const Text("No image captured"),
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: captureAndAnalyze,
              icon: const Icon(Icons.camera_alt),
              label: const Text("Capture & Analyze"),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
            ),
            const SizedBox(height: 30),
            if (_isLoading) const CircularProgressIndicator(),
            if (_results != null && !_isLoading) ...[
              Text("🧠 Analysis Results", style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 10),
              _buildResultCard("Lesion", _results!['lesion']),
              _buildResultCard("Cavity", _results!['cavity']),
              _buildResultCard("Cancer", _results!['cancer']),
            ],
          ],
        ),
      ),
    );
  }

  // ------------------- Result Card -------------------
  Widget _buildResultCard(String title, Map<String, dynamic> data) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: ListTile(
        leading: const Icon(Icons.medical_services, color: Colors.teal),
        title: Text(title),
        subtitle: Text(data['label']),
        trailing: Text("${data['confidence']}%"),
      ),
    );
  }
}