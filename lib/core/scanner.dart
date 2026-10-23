import 'dart:io';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

class ScannerService {
  static Directory? _thumbCacheDir;

  static Future<Directory> getThumbCacheDir() async {
    if (_thumbCacheDir != null) return _thumbCacheDir!;
    final home = Platform.environment['HOME'] ?? '';
    final pythonThumbDir = Directory(p.join(home, 'CatalogueDisques', 'thumbnails'));
    if (pythonThumbDir.existsSync()) {
      _thumbCacheDir = pythonThumbDir;
      return pythonThumbDir;
    }

    final tmp = await getTemporaryDirectory();
    final cacheDir = Directory(p.join(tmp.path, 'repertoir_thumbnails'));
    if (!cacheDir.existsSync()) {
      await cacheDir.create(recursive: true);
    }
    _thumbCacheDir = cacheDir;
    return cacheDir;
  }

  /// Génère une vignette rapide pour une vidéo ou image sur macOS via qlmanage ou ffmpeg
  static Future<String?> generateThumbnail(String absPath) async {
    if (!Platform.isMacOS) return null;
    final file = File(absPath);
    if (!file.existsSync()) return null;

    final ext = p.extension(absPath).replaceAll('.', '').toLowerCase();
    final cacheDir = await getThumbCacheDir();
    final hashName = '${absPath.hashCode.abs()}_${p.basenameWithoutExtension(absPath)}.jpg';
    final targetThumb = File(p.join(cacheDir.path, hashName));

    if (targetThumb.existsSync()) {
      return targetThumb.path;
    }

    // Pour les images légères, on peut directement utiliser le fichier
    if (['jpg', 'jpeg', 'png', 'webp', 'bmp'].contains(ext)) {
      return absPath;
    }

    // Utilisation de qlmanage (natif sur macOS, supporte QuickTime, ProRes, MP4, RAW, etc.)
    try {
      final res = await Process.run('qlmanage', [
        '-t',
        '-s', '360',
        '-o', cacheDir.path,
        absPath,
      ]);

      if (res.exitCode == 0) {
        final expectedThumb = File(p.join(cacheDir.path, '${p.basename(absPath)}.png'));
        if (expectedThumb.existsSync()) {
          return expectedThumb.path;
        }
      }
    } catch (_) {}

    return null;
  }
}
