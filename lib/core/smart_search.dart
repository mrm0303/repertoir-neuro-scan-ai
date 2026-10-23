/// Moteur de recherche sémantique pour MediaSphere.
/// Parse des requêtes en langage naturel et les transforme en SQL structuré.
///
/// Exemples de requêtes supportées :
///   "plans drone coucher de soleil en 4K"
///   "interview RED 8K prores"
///   "vidéos de plus de 10 minutes en slowmo"
///   "toutes les photos du mois dernier"
class SmartSearchEngine {
  /// Parse une requête en langage naturel et retourne un objet SearchQuery
  static SearchQuery parse(String input) {
    final query = SearchQuery();
    String remaining = input.toLowerCase().trim();

    // 1. Extraire les filtres de résolution
    remaining = _extractResolution(remaining, query);

    // 2. Extraire les filtres de caméra
    remaining = _extractCamera(remaining, query);

    // 3. Extraire les filtres de type de fichier
    remaining = _extractFileType(remaining, query);

    // 4. Extraire les filtres de FPS
    remaining = _extractFps(remaining, query);

    // 5. Extraire les filtres de codec
    remaining = _extractCodec(remaining, query);

    // 6. Extraire les filtres de durée
    remaining = _extractDuration(remaining, query);

    // 7. Extraire les filtres de taille
    remaining = _extractSize(remaining, query);

    // 8. Le reste devient une recherche textuelle sur le nom/chemin/tags
    final cleanedRemaining = remaining
        .replaceAll(RegExp(r'\s+'), ' ')
        .replaceAll(RegExp(r'(^|\s)(de|du|le|la|les|un|une|des|en|au|aux|et|ou|avec|pour|sur|dans|qui|que|dont|par|tous|tout|toutes|mon|mes|ses|nos|vos|leurs|cette|ces|ce|cet)\s'), ' ')
        .replaceAll(RegExp(r'(^|\s)(find|show|get|search|cherche|trouve|montre|affiche|donne|liste)\s'), ' ')
        .replaceAll(RegExp(r'(^|\s)(plans?|clips?|fichiers?|rushs?|shots?|séquences?|files?)\s'), ' ')
        .trim();

    if (cleanedRemaining.isNotEmpty && cleanedRemaining.length > 1) {
      query.textKeywords = cleanedRemaining
          .split(RegExp(r'\s+'))
          .where((w) => w.length > 1)
          .toList();
    }

    return query;
  }

  /// Génère la clause WHERE SQL et les paramètres à partir d'un SearchQuery
  static SqlClause toSql(SearchQuery query) {
    final conditions = <String>[];
    final params = <dynamic>[];

    // Résolution
    if (query.minWidth != null) {
      conditions.add('f.width >= ?');
      params.add(query.minWidth);
    }
    if (query.maxWidth != null) {
      conditions.add('f.width <= ?');
      params.add(query.maxWidth);
    }

    // Caméra
    if (query.cameraPatterns.isNotEmpty) {
      final camConds = query.cameraPatterns.map((_) => 'f.camera LIKE ?').join(' OR ');
      conditions.add('($camConds)');
      for (final pat in query.cameraPatterns) {
        params.add('%$pat%');
      }
    }

    // Type de fichier
    if (query.fileType != null) {
      conditions.add('f.category = ?');
      params.add(query.fileType);
    }

    // FPS
    if (query.minFps != null) {
      conditions.add('f.fps >= ?');
      params.add(query.minFps);
    }

    // Codec
    if (query.codecPatterns.isNotEmpty) {
      final codecConds = query.codecPatterns.map((_) => 'f.codec LIKE ?').join(' OR ');
      conditions.add('($codecConds)');
      for (final pat in query.codecPatterns) {
        params.add('%$pat%');
      }
    }

    // Durée
    if (query.minDuration != null) {
      conditions.add('f.duration >= ?');
      params.add(query.minDuration);
    }
    if (query.maxDuration != null) {
      conditions.add('f.duration <= ?');
      params.add(query.maxDuration);
    }

    // Taille
    if (query.minSize != null) {
      conditions.add('f.size >= ?');
      params.add(query.minSize);
    }

    // Mots-clés textuels (nom, chemin, tags)
    for (final keyword in query.textKeywords) {
      conditions.add('(f.name LIKE ? OR f.rel_path LIKE ? OR EXISTS (SELECT 1 FROM file_tags ft JOIN tags t ON ft.tag_id = t.id WHERE ft.file_id = f.id AND t.name LIKE ?))');
      params.add('%$keyword%');
      params.add('%$keyword%');
      params.add('%$keyword%');
    }

    final whereClause = conditions.isEmpty ? '' : 'WHERE ${conditions.join(' AND ')}';
    return SqlClause(whereClause: whereClause, params: params, filtersApplied: conditions.length);
  }

  // ============================================================
  // EXTRACTEURS DE FILTRES
  // ============================================================

  static String _extractResolution(String input, SearchQuery query) {
    // 8K
    if (RegExp(r'\b8k\b').hasMatch(input)) {
      query.minWidth = 7680;
      input = input.replaceAll(RegExp(r'\b8k\b'), '');
    }
    // 6K
    else if (RegExp(r'\b6k\b').hasMatch(input)) {
      query.minWidth = 6144;
      query.maxWidth = 7679;
      input = input.replaceAll(RegExp(r'\b6k\b'), '');
    }
    // 4K / UHD
    else if (RegExp(r'\b(4k|uhd|ultra\s*hd)\b').hasMatch(input)) {
      query.minWidth = 3840;
      query.maxWidth = 6143;
      input = input.replaceAll(RegExp(r'\b(4k|uhd|ultra\s*hd)\b'), '');
    }
    // 2K / Full HD
    else if (RegExp(r'\b(2k|full\s*hd|1080p?|fhd)\b').hasMatch(input)) {
      query.minWidth = 1920;
      query.maxWidth = 2559;
      input = input.replaceAll(RegExp(r'\b(2k|full\s*hd|1080p?|fhd)\b'), '');
    }
    // HD / 720p
    else if (RegExp(r'\b(hd|720p?)\b').hasMatch(input)) {
      query.minWidth = 1280;
      query.maxWidth = 1919;
      input = input.replaceAll(RegExp(r'\b(hd|720p?)\b'), '');
    }
    // Haute résolution (générique)
    else if (RegExp(r'\b(haute\s*résolution|high\s*res|hi-?res)\b').hasMatch(input)) {
      query.minWidth = 3840;
      input = input.replaceAll(RegExp(r'\b(haute\s*résolution|high\s*res|hi-?res)\b'), '');
    }
    return input;
  }

  static String _extractCamera(String input, SearchQuery query) {
    final cameraMap = <String, List<String>>{
      'red': ['RED', 'DSMC', 'HELIUM', 'MONSTRO', 'KOMODO', 'RANGER', 'RAPTOR'],
      'arri': ['ARRI', 'ALEXA', 'AMIRA', 'MINI LF'],
      'blackmagic': ['Blackmagic', 'BMPCC', 'URSA', 'Pocket'],
      'sony': ['Sony', 'VENICE', 'FX', 'A7', 'FS'],
      'canon': ['Canon', 'EOS', 'C70', 'C300', 'C500', 'R5'],
      'panasonic': ['Panasonic', 'GH', 'S1', 'S5', 'EVA', 'VARICAM'],
      'dji': ['DJI', 'Mavic', 'Inspire', 'Phantom', 'Air', 'Mini'],
      'gopro': ['GoPro', 'HERO'],
      'iphone': ['iPhone', 'Apple'],
      'drone': ['DJI', 'Mavic', 'Inspire', 'Phantom', 'drone', 'aérien'],
    };

    for (final entry in cameraMap.entries) {
      if (RegExp('\\b${entry.key}\\b', caseSensitive: false).hasMatch(input)) {
        query.cameraPatterns.addAll(entry.value);
        input = input.replaceAll(RegExp('\\b${entry.key}\\b', caseSensitive: false), '');
      }
    }

    // Patterns spécifiques
    final specificCameras = [
      'alexa mini', 'alexa lf', 'alexa 35',
      'red helium', 'red monstro', 'red komodo', 'red raptor',
      'sony venice', 'canon c300', 'canon c500',
      'bmpcc 6k', 'bmpcc 4k', 'ursa mini',
    ];
    for (final cam in specificCameras) {
      if (input.contains(cam)) {
        query.cameraPatterns.add(cam);
        input = input.replaceAll(cam, '');
      }
    }

    return input;
  }

  static String _extractFileType(String input, SearchQuery query) {
    // Vidéo
    if (RegExp(r'\b(vidéos?|videos?|clips?|rushs?|rushes|footage|séquences?|movies?|films?)\b').hasMatch(input)) {
      query.fileType = 'video';
      input = input.replaceAll(RegExp(r'\b(vidéos?|videos?|clips?|rushs?|rushes|footage|séquences?|movies?|films?)\b'), '');
    }
    // Image
    else if (RegExp(r'\b(images?|photos?|pictures?|stills?|captures?)\b').hasMatch(input)) {
      query.fileType = 'image';
      input = input.replaceAll(RegExp(r'\b(images?|photos?|pictures?|stills?|captures?)\b'), '');
    }
    // Audio
    else if (RegExp(r'\b(audio|sons?|musiques?|music|sound|wav|mp3|aiff)\b').hasMatch(input)) {
      query.fileType = 'audio';
      input = input.replaceAll(RegExp(r'\b(audio|sons?|musiques?|music|sound|wav|mp3|aiff)\b'), '');
    }
    return input;
  }

  static String _extractFps(String input, SearchQuery query) {
    // Slow motion
    if (RegExp(r'\b(slow\s*mo|slowmo|slow\s*motion|ralenti)\b').hasMatch(input)) {
      query.minFps = 60;
      input = input.replaceAll(RegExp(r'\b(slow\s*mo|slowmo|slow\s*motion|ralenti)\b'), '');
    }
    // FPS spécifique
    final fpsMatch = RegExp(r'\b(\d+)\s*fps\b').firstMatch(input);
    if (fpsMatch != null) {
      query.minFps = int.tryParse(fpsMatch.group(1)!);
      input = input.replaceAll(fpsMatch.group(0)!, '');
    }
    // Patterns comme "120p" ou "240p" (souvent = fps en contexte caméra)
    final highFpsMatch = RegExp(r'\b(120|240|480)\s*[pi]?\b').firstMatch(input);
    if (highFpsMatch != null && query.minFps == null) {
      final val = int.tryParse(highFpsMatch.group(1)!);
      if (val != null && val >= 60) {
        query.minFps = val;
        input = input.replaceAll(highFpsMatch.group(0)!, '');
      }
    }
    return input;
  }

  static String _extractCodec(String input, SearchQuery query) {
    final codecMap = <String, String>{
      'prores': 'ProRes',
      'prores 4444': 'ProRes 4444',
      'prores 422': 'ProRes 422',
      'prores hq': 'ProRes HQ',
      'h264': 'h264',
      'h.264': 'h264',
      'h265': 'h265',
      'h.265': 'h265',
      'hevc': 'hevc',
      'raw': 'RAW',
      'r3d': 'R3D',
      'arriraw': 'ARRIRAW',
      'braw': 'BRAW',
      'dnxhd': 'DNxHD',
      'dnxhr': 'DNxHR',
      'cineform': 'CineForm',
      'xavc': 'XAVC',
    };

    for (final entry in codecMap.entries) {
      if (RegExp('\\b${RegExp.escape(entry.key)}\\b', caseSensitive: false).hasMatch(input)) {
        query.codecPatterns.add(entry.value);
        input = input.replaceAll(RegExp('\\b${RegExp.escape(entry.key)}\\b', caseSensitive: false), '');
      }
    }
    return input;
  }

  static String _extractDuration(String input, SearchQuery query) {
    // "plus de X minutes" / "more than X min"
    final moreThanMin = RegExp(r'(plus de|more than|supérieur[e]?\s*à|>\s*|au\s*moins)\s*(\d+)\s*(min(utes?)?|mn)').firstMatch(input);
    if (moreThanMin != null) {
      final minutes = int.tryParse(moreThanMin.group(2)!);
      if (minutes != null) {
        query.minDuration = minutes * 60.0;
        input = input.replaceAll(moreThanMin.group(0)!, '');
      }
    }

    // "moins de X minutes" / "less than X min"
    final lessThanMin = RegExp(r'(moins de|less than|inférieur[e]?\s*à|<\s*|max)\s*(\d+)\s*(min(utes?)?|mn)').firstMatch(input);
    if (lessThanMin != null) {
      final minutes = int.tryParse(lessThanMin.group(2)!);
      if (minutes != null) {
        query.maxDuration = minutes * 60.0;
        input = input.replaceAll(lessThanMin.group(0)!, '');
      }
    }

    // "courts" / "longs" / "short" / "long"
    if (RegExp(r'\b(courts?|short)\b').hasMatch(input) && query.maxDuration == null) {
      query.maxDuration = 60; // < 1 minute
      input = input.replaceAll(RegExp(r'\b(courts?|short)\b'), '');
    }
    if (RegExp(r'\b(longs?|long)\b').hasMatch(input) && query.minDuration == null) {
      query.minDuration = 300; // > 5 minutes
      input = input.replaceAll(RegExp(r'\b(longs?|long)\b'), '');
    }

    return input;
  }

  static String _extractSize(String input, SearchQuery query) {
    // "plus de X Go" / "more than X GB"
    final sizeMatch = RegExp(r'(plus de|more than|>\s*)\s*(\d+)\s*(go|gb|gio)').firstMatch(input);
    if (sizeMatch != null) {
      final gb = int.tryParse(sizeMatch.group(2)!);
      if (gb != null) {
        query.minSize = gb * 1024 * 1024 * 1024;
        input = input.replaceAll(sizeMatch.group(0)!, '');
      }
    }

    // "lourds" / "gros fichiers"
    if (RegExp(r'\b(lourds?|gros|heavy|large)\b').hasMatch(input) && query.minSize == null) {
      query.minSize = 10 * 1024 * 1024 * 1024; // > 10 Go
      input = input.replaceAll(RegExp(r'\b(lourds?|gros|heavy|large)\b'), '');
    }

    return input;
  }
}

/// Représente une requête de recherche structurée
class SearchQuery {
  // Résolution
  int? minWidth;
  int? maxWidth;

  // Caméra
  List<String> cameraPatterns = [];

  // Type de fichier
  String? fileType;

  // FPS
  int? minFps;

  // Codec
  List<String> codecPatterns = [];

  // Durée (en secondes)
  double? minDuration;
  double? maxDuration;

  // Taille (en octets)
  int? minSize;

  // Mots-clés textuels restants
  List<String> textKeywords = [];

  /// Résumé lisible des filtres appliqués
  String describe() {
    final parts = <String>[];
    if (minWidth != null) {
      if (minWidth! >= 7680) parts.add('8K+');
      else if (minWidth! >= 3840) parts.add('4K');
      else if (minWidth! >= 1920) parts.add('Full HD');
      else parts.add('≥${minWidth}px');
    }
    if (cameraPatterns.isNotEmpty) parts.add('Caméra: ${cameraPatterns.take(2).join("/")}');
    if (fileType != null) parts.add('Type: $fileType');
    if (minFps != null) parts.add('≥${minFps}fps');
    if (codecPatterns.isNotEmpty) parts.add('Codec: ${codecPatterns.join("/")}');
    if (minDuration != null) parts.add('≥${(minDuration! / 60).round()}min');
    if (maxDuration != null) parts.add('≤${(maxDuration! / 60).round()}min');
    if (minSize != null) parts.add('≥${(minSize! / (1024 * 1024 * 1024)).round()}Go');
    if (textKeywords.isNotEmpty) parts.add('"${textKeywords.join(" ")}"');
    return parts.isEmpty ? 'Tous les médias' : parts.join(' · ');
  }

  bool get hasFilters =>
      minWidth != null ||
      maxWidth != null ||
      cameraPatterns.isNotEmpty ||
      fileType != null ||
      minFps != null ||
      codecPatterns.isNotEmpty ||
      minDuration != null ||
      maxDuration != null ||
      minSize != null ||
      textKeywords.isNotEmpty;
}

/// Clause SQL générée par le moteur de recherche
class SqlClause {
  final String whereClause;
  final List<dynamic> params;
  final int filtersApplied;

  SqlClause({
    required this.whereClause,
    required this.params,
    required this.filtersApplied,
  });
}
