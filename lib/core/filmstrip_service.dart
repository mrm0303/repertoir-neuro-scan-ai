import 'dart:io';
import 'dart:async';
import 'package:path/path.dart' as p;
import 'package:crypto/crypto.dart';
import 'dart:convert';

/// Service de génération de filmstrips pour le hover-scrub.
/// Extrait N frames à intervalles réguliers via ffmpeg.
class FilmstripService {
  static const int defaultFrameCount = 8;
  static Directory? _cacheDir;

  /// Répertoire de cache pour les filmstrips
  static Future<Directory> get cacheDir async {
    if (_cacheDir != null) return _cacheDir!;
    final home = Platform.environment['HOME'] ?? '';
    final dir = Directory(p.join(home, 'Library', 'Caches', 'MediaSphere', 'filmstrips'));
    if (!dir.existsSync()) {
      await dir.create(recursive: true);
    }
    _cacheDir = dir;
    return dir;
  }

  /// Génère un identifiant unique pour un fichier basé sur son chemin
  static String _fileHash(String absPath) {
    final bytes = utf8.encode(absPath);
    return md5.convert(bytes).toString().substring(0, 12);
  }

  /// Vérifie si un filmstrip existe déjà en cache
  static Future<List<String>?> getCachedFilmstrip(String absPath, {int frameCount = defaultFrameCount}) async {
    final hash = _fileHash(absPath);
    final dir = await cacheDir;
    final frames = <String>[];

    for (int i = 0; i < frameCount; i++) {
      final framePath = p.join(dir.path, '${hash}_frame_$i.jpg');
      if (!File(framePath).existsSync()) return null;
      frames.add(framePath);
    }
    return frames;
  }

  /// Génère un filmstrip (liste de chemins vers les frames extraites)
  /// Retourne null si ffmpeg n'est pas disponible ou si le fichier n'existe pas
  static Future<List<String>?> generateFilmstrip(
    String absPath, {
    int frameCount = defaultFrameCount,
    double? duration,
  }) async {
    // Vérifier le cache d'abord
    final cached = await getCachedFilmstrip(absPath, frameCount: frameCount);
    if (cached != null) return cached;

    final file = File(absPath);
    if (!file.existsSync()) return null;

    // Obtenir la durée si pas fournie
    double videoDuration = duration ?? 0;
    if (videoDuration <= 0) {
      videoDuration = await _getVideoDuration(absPath) ?? 0;
    }
    if (videoDuration <= 0) return null;

    final hash = _fileHash(absPath);
    final dir = await cacheDir;
    final frames = <String>[];

    // Extraire les frames à intervalles réguliers
    for (int i = 0; i < frameCount; i++) {
      final timestamp = (videoDuration / (frameCount + 1)) * (i + 1);
      final outputPath = p.join(dir.path, '${hash}_frame_$i.jpg');

      try {
        final result = await Process.run('ffmpeg', [
          '-ss', timestamp.toStringAsFixed(2),
          '-i', absPath,
          '-vframes', '1',
          '-q:v', '6', // Qualité moyenne (rapide)
          '-vf', 'scale=320:-1', // 320px de large, ratio préservé
          '-y', // Écraser si existant
          outputPath,
        ]);

        if (result.exitCode == 0 && File(outputPath).existsSync()) {
          frames.add(outputPath);
        } else {
          // Si un frame échoue, on continue avec les autres
          frames.add('');
        }
      } catch (_) {
        frames.add('');
      }
    }

    // Si aucun frame n'a été extrait, retourner null
    if (frames.every((f) => f.isEmpty)) return null;
    return frames;
  }

  /// Obtient la durée d'une vidéo via ffprobe
  static Future<double?> _getVideoDuration(String absPath) async {
    try {
      final result = await Process.run('ffprobe', [
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        absPath,
      ]);

      if (result.exitCode == 0) {
        return double.tryParse((result.stdout as String).trim());
      }
    } catch (_) {}
    return null;
  }

  /// Génère les filmstrips pour une liste de fichiers en batch (arrière-plan)
  /// Retourne un Stream qui émet chaque résultat au fur et à mesure
  static Stream<FilmstripResult> generateBatch(
    List<Map<String, dynamic>> files, {
    int frameCount = defaultFrameCount,
    int concurrency = 2,
  }) async* {
    final queue = <Future<FilmstripResult>>[];

    for (final file in files) {
      final mountPath = file['mount_path'] as String? ?? '';
      final relPath = file['relative_path'] as String? ?? '';
      final absPath = p.join(mountPath, relPath);
      final fileId = file['id'] as int? ?? 0;
      final duration = file['duration'];
      final durationDouble = duration is num ? duration.toDouble() : double.tryParse(duration?.toString() ?? '');

      if (fileId == 0) continue;

      final future = generateFilmstrip(
        absPath,
        frameCount: frameCount,
        duration: durationDouble,
      ).then((frames) => FilmstripResult(
        fileId: fileId,
        absPath: absPath,
        frames: frames,
      ));

      queue.add(future);

      // Limiter la concurrence
      if (queue.length >= concurrency) {
        final result = await queue.removeAt(0);
        yield result;
      }
    }

    // Vider la queue restante
    for (final future in queue) {
      yield await future;
    }
  }

  /// Nettoie le cache (supprime les filmstrips de plus de N jours)
  static Future<int> cleanCache({int maxAgeDays = 30}) async {
    final dir = await cacheDir;
    int deleted = 0;
    final cutoff = DateTime.now().subtract(Duration(days: maxAgeDays));

    await for (final entity in dir.list()) {
      if (entity is File) {
        final stat = await entity.stat();
        if (stat.modified.isBefore(cutoff)) {
          await entity.delete();
          deleted++;
        }
      }
    }
    return deleted;
  }
}

/// Résultat de la génération d'un filmstrip
class FilmstripResult {
  final int fileId;
  final String absPath;
  final List<String>? frames;

  FilmstripResult({
    required this.fileId,
    required this.absPath,
    this.frames,
  });

  bool get success => frames != null && frames!.any((f) => f.isNotEmpty);
}
