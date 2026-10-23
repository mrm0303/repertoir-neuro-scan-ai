import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart';

class DnaService {
  /// Génère l'ADN d'un fichier (Hash rapide basé sur les premiers et derniers 64 Ko)
  /// Cette méthode permet d'identifier un fichier vidéo de 50 Go en quelques millisecondes,
  /// même s'il a été renommé ou déplacé.
  static Future<String?> generateDna(String filePath) async {
    final file = File(filePath);
    if (!file.existsSync()) return null;

    try {
      final stat = await file.stat();
      if (stat.size == 0) return null;

      final raf = await file.open(mode: FileMode.read);
      
      const chunkSize = 64 * 1024; // 64 Ko
      final headSize = stat.size < chunkSize ? stat.size : chunkSize;
      final tailSize = stat.size < chunkSize * 2 ? 0 : chunkSize;

      // Lire la tête
      final headBytes = await raf.read(headSize);
      
      // Lire la queue
      List<int> tailBytes = [];
      if (tailSize > 0) {
        await raf.setPosition(stat.size - tailSize);
        tailBytes = await raf.read(tailSize);
      }

      await raf.close();

      // Combiner et hacher
      final combined = [...headBytes, ...tailBytes];
      final digest = md5.convert(combined);
      
      // L'ADN est le hash + la taille du fichier (pour éviter les collisions de hash partiel)
      return '${digest.toString()}-${stat.size}';
    } catch (e) {
      debugPrint('Erreur génération ADN pour $filePath : $e');
      return null;
    }
  }
}
