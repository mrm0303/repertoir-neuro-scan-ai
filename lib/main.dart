import 'package:flutter/material.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'core/database.dart';
import 'ui/studio_layout.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;
  await DatabaseService.init();
  runApp(const RepertoirApp());
}

class RepertoirApp extends StatelessWidget {
  const RepertoirApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Repertoir MAM',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF0F1115),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF3880FF),
          surface: Color(0xFF16181F),
        ),
      ),
      home: const MainStudioLayout(),
    );
  }
}
