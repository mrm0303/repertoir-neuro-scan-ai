import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../core/database.dart';
import '../core/filmstrip_service.dart';

class CinemaMode extends StatefulWidget {
  final List<Map<String, dynamic>> files;
  final int initialIndex;

  const CinemaMode({
    super.key,
    required this.files,
    required this.initialIndex,
  });

  @override
  State<CinemaMode> createState() => _CinemaModeState();
}

class _CinemaModeState extends State<CinemaMode> {
  late PageController _pageController;
  int _currentIndex = 0;
  bool _showHud = true;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex;
    _pageController = PageController(initialPage: _currentIndex);
    
    // Entrer en plein écran
    // Note: window_manager serait idéal ici, mais on utilise une approche Flutter UI par défaut
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _toggleHud() {
    setState(() {
      _showHud = !_showHud;
    });
  }

  String _formatBytes(int bytes) {
    if (bytes >= 1024 * 1024 * 1024) {
      return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(2)} Go';
    }
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} Mo';
  }
  
  String _formatDuration(num? seconds) {
    if (seconds == null) return '00:00:00';
    final dur = Duration(seconds: seconds.toInt());
    return dur.toString().split('.').first.padLeft(8, '0');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black, // Noir absolu
      body: CallbackShortcuts(
        bindings: {
          const SingleActivator(LogicalKeyboardKey.escape): () => Navigator.pop(context),
          const SingleActivator(LogicalKeyboardKey.space): _toggleHud,
          const SingleActivator(LogicalKeyboardKey.arrowRight): () {
            if (_currentIndex < widget.files.length - 1) {
              _pageController.nextPage(duration: const Duration(milliseconds: 400), curve: Curves.easeInOut);
            }
          },
          const SingleActivator(LogicalKeyboardKey.arrowLeft): () {
            if (_currentIndex > 0) {
              _pageController.previousPage(duration: const Duration(milliseconds: 400), curve: Curves.easeInOut);
            }
          },
        },
        child: Focus(
          autofocus: true,
          child: GestureDetector(
            onTap: _toggleHud,
            child: Stack(
              fit: StackFit.expand,
              children: [
                // 1. CAROUSEL DES MÉDIAS (Plein écran)
                PageView.builder(
                  controller: _pageController,
                  physics: const BouncingScrollPhysics(),
                  onPageChanged: (idx) {
                    setState(() => _currentIndex = idx);
                  },
                  itemCount: widget.files.length,
                  itemBuilder: (context, index) {
                    final file = widget.files[index];
                    final thumbPath = file['thumb_path'] as String?;
                    
                    return AnimatedBuilder(
                      animation: _pageController,
                      builder: (context, child) {
                        // Effet parallax / Cover Flow léger
                        double value = 1.0;
                        if (_pageController.position.haveDimensions) {
                          value = _pageController.page! - index;
                          value = (1 - (value.abs() * 0.3)).clamp(0.0, 1.0);
                        }
                        return Transform.scale(
                          scale: Curves.easeOut.transform(value),
                          child: child,
                        );
                      },
                      child: Container(
                        margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 48),
                        decoration: BoxDecoration(
                          color: const Color(0xFF0A0A0A),
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withValues(alpha: 0.8),
                              blurRadius: 40,
                              spreadRadius: 10,
                            )
                          ],
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(16),
                          child: thumbPath != null && File(thumbPath).existsSync()
                              ? Image.file(
                                  File(thumbPath),
                                  fit: BoxFit.contain, // Respecter le ratio cinéma
                                )
                              : Center(
                                  child: Icon(Icons.movie, size: 80, color: Colors.white.withValues(alpha: 0.2)),
                                ),
                        ),
                      ),
                    );
                  },
                ),

                // 2. HUD SCI-FI (Heads Up Display)
                AnimatedOpacity(
                  opacity: _showHud ? 1.0 : 0.0,
                  duration: const Duration(milliseconds: 300),
                  child: Stack(
                    children: [
                      // Bouton Quitter (Haut Gauche)
                      Positioned(
                        top: 24,
                        left: 24,
                        child: IconButton(
                          icon: const Icon(Icons.close, color: Colors.white70, size: 32),
                          onPressed: () => Navigator.pop(context),
                          tooltip: 'Quitter le mode cinéma (Échap)',
                        ),
                      ),
                      
                      // Infos Projet (Haut Droite)
                      Positioned(
                        top: 32,
                        right: 32,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          decoration: BoxDecoration(
                            color: Colors.black.withValues(alpha: 0.5),
                            border: Border.all(color: const Color(0xFF7C3AED).withValues(alpha: 0.5)),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            'PRESENTATION MODE • ${widget.files.length} CLIPS',
                            style: const TextStyle(
                              color: Color(0xFF7C3AED),
                              fontFamily: 'monospace',
                              fontWeight: FontWeight.bold,
                              letterSpacing: 2.0,
                            ),
                          ),
                        ),
                      ),

                      // Métadonnées du clip actif (Bas)
                      Positioned(
                        bottom: 0,
                        left: 0,
                        right: 0,
                        child: Container(
                          padding: const EdgeInsets.all(40),
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.bottomCenter,
                              end: Alignment.topCenter,
                              colors: [
                                Colors.black.withValues(alpha: 0.9),
                                Colors.transparent,
                              ],
                            ),
                          ),
                          child: _buildMetadataHud(widget.files[_currentIndex]),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMetadataHud(Map<String, dynamic> file) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        // Infos principales
        Expanded(
          flex: 2,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                file['filename'] ?? 'Sans_titre',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 32,
                  fontWeight: FontWeight.w300,
                  letterSpacing: 1.2,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  _hudBadge(Icons.camera_alt, file['camera_model'] ?? 'N/A'),
                  const SizedBox(width: 12),
                  _hudBadge(Icons.hd, file['resolution'] ?? 'Inconnu'),
                  const SizedBox(width: 12),
                  _hudBadge(Icons.speed, '${file['fps'] ?? 24} FPS'),
                  const SizedBox(width: 12),
                  _hudBadge(Icons.timer, _formatDuration(file['duration'])),
                ],
              ),
            ],
          ),
        ),
        
        // Progress et infos techniques
        Expanded(
          flex: 1,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${_currentIndex + 1} / ${widget.files.length}',
                style: const TextStyle(
                  color: Colors.white54,
                  fontSize: 24,
                  fontFamily: 'monospace',
                  fontWeight: FontWeight.w100,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'CODEC: ${file['codec'] ?? 'RAW'}  •  SIZE: ${_formatBytes(file['size_bytes'] ?? 0)}',
                style: const TextStyle(
                  color: Color(0xFF10B981), // Émeraude tech
                  fontFamily: 'monospace',
                  fontSize: 12,
                  letterSpacing: 1.5,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _hudBadge(IconData icon, String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: Colors.white.withValues(alpha: 0.2)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: Colors.white70),
          const SizedBox(width: 6),
          Text(
            text,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 12,
              fontWeight: FontWeight.bold,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    );
  }
}
