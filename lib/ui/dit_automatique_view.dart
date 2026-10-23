import 'dart:async';
import 'package:flutter/material.dart';

class DitAutomatiqueView extends StatefulWidget {
  const DitAutomatiqueView({super.key});

  @override
  State<DitAutomatiqueView> createState() => _DitAutomatiqueViewState();
}

class _DitAutomatiqueViewState extends State<DitAutomatiqueView> {
  bool _isIngesting = false;
  bool _isComplete = false;
  double _progress = 0.0;
  String _currentStep = 'EN ATTENTE DE CONNEXION...';
  final List<String> _logs = [];
  final ScrollController _logScrollController = ScrollController();

  void _addLog(String message) {
    if (!mounted) return;
    setState(() {
      _logs.add('[${DateTime.now().toIso8601String().split('T').last.substring(0, 8)}] $message');
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_logScrollController.hasClients) {
        _logScrollController.animateTo(
          _logScrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _startIngestSimulation() async {
    setState(() {
      _isIngesting = true;
      _isComplete = false;
      _progress = 0.0;
      _logs.clear();
    });

    // Phase 1: Détection
    _currentStep = 'DÉTECTION DU VOLUME';
    _addLog('Volume détecté : /Volumes/RED_MAG_A');
    _addLog('Analyse du système de fichiers...');
    await Future.delayed(const Duration(seconds: 1));
    _progress = 0.1;

    // Phase 2: Indexation
    _currentStep = 'INDEXATION ET LECTURE DES MÉTADONNÉES';
    _addLog('Scan terminé : 42 fichiers trouvés (142 Go).');
    await Future.delayed(const Duration(milliseconds: 500));
    for (int i = 1; i <= 5; i++) {
      if (!mounted) return;
      _addLog('Extraction métadonnées fichier A001_C00$i.R3D...');
      setState(() => _progress = 0.1 + (i * 0.04));
      await Future.delayed(const Duration(milliseconds: 200));
    }

    // Phase 3: Checksums et Copie
    _currentStep = 'CALCUL CHECKSUM (SHA-256) ET COPIE SÉCURISÉE';
    _addLog('Début du transfert vers le NAS Principal et Archive Cloud...');
    for (int i = 0; i <= 20; i++) {
      if (!mounted) return;
      if (i % 4 == 0) _addLog('Copie sécurisée en cours... ${i * 5}% (1400 MB/s)');
      setState(() => _progress = 0.3 + (i * 0.03));
      await Future.delayed(const Duration(milliseconds: 150));
    }

    // Phase 4: Génération du rapport
    _currentStep = 'GÉNÉRATION DU RAPPORT DIT';
    _addLog('Vérification Byte-à-Byte terminée. Hashs identiques.');
    _addLog('Génération du rapport de tournage PDF...');
    setState(() => _progress = 0.95);
    await Future.delayed(const Duration(seconds: 1));

    if (!mounted) return;
    setState(() {
      _progress = 1.0;
      _currentStep = 'INGEST TERMINÉ AVEC SUCCÈS';
      _isIngesting = false;
      _isComplete = true;
      _addLog('DIT Workflow achevé. Le disque peut être éjecté en toute sécurité.');
    });
  }

  void _reset() {
    setState(() {
      _isIngesting = false;
      _isComplete = false;
      _progress = 0.0;
      _logs.clear();
      _currentStep = 'EN ATTENTE DE CONNEXION...';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF0A0B10),
      padding: const EdgeInsets.all(40.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'DIT INGEST AUTOMATIQUE',
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 1.5),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Copie sécurisée, Checksum et Renommage intelligent',
                    style: TextStyle(fontSize: 14, color: Color(0xFF8B90A0)),
                  ),
                ],
              ),
              if (!_isIngesting && !_isComplete)
                ElevatedButton.icon(
                  onPressed: _startIngestSimulation,
                  icon: const Icon(Icons.usb, color: Colors.white),
                  label: const Text('Simuler Connexion Disque'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF10B981),
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                    textStyle: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
              if (_isComplete)
                ElevatedButton.icon(
                  onPressed: _reset,
                  icon: const Icon(Icons.refresh, color: Colors.white),
                  label: const Text('Nouvel Ingest'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF2E384D),
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 48),
          
          // ZONES PRINCIPALES
          Expanded(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Colonne de gauche: Statut graphique
                Expanded(
                  flex: 2,
                  child: Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFF13161F),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: _isComplete ? const Color(0xFF10B981) : const Color(0xFF2E384D)),
                    ),
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          _isComplete ? Icons.check_circle : (_isIngesting ? Icons.sync : Icons.sd_storage),
                          size: 100,
                          color: _isComplete 
                              ? const Color(0xFF10B981) 
                              : (_isIngesting ? const Color(0xFF7C3AED) : Colors.white24),
                        ),
                        const SizedBox(height: 32),
                        Text(
                          _currentStep,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 2.0,
                            color: _isIngesting ? const Color(0xFF7C3AED) : Colors.white,
                          ),
                        ),
                        const SizedBox(height: 24),
                        // Barre de progression
                        ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: LinearProgressIndicator(
                            value: _progress,
                            minHeight: 12,
                            backgroundColor: Colors.white.withValues(alpha: 0.1),
                            valueColor: AlwaysStoppedAnimation<Color>(
                              _isComplete ? const Color(0xFF10B981) : const Color(0xFF7C3AED),
                            ),
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          '${(_progress * 100).toInt()}%',
                          style: const TextStyle(color: Colors.white54, fontFamily: 'monospace', fontSize: 24),
                        ),
                      ],
                    ),
                  ),
                ),
                
                const SizedBox(width: 24),
                
                // Colonne de droite: Console de logs
                Expanded(
                  flex: 3,
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.black,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFF2E384D)),
                    ),
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.terminal, color: Colors.white54, size: 16),
                            SizedBox(width: 8),
                            Text('DIT CONSOLE', style: TextStyle(color: Colors.white54, fontFamily: 'monospace')),
                          ],
                        ),
                        const Divider(color: Color(0xFF2E384D)),
                        Expanded(
                          child: ListView.builder(
                            controller: _logScrollController,
                            itemCount: _logs.length,
                            itemBuilder: (ctx, i) {
                              return Padding(
                                padding: const EdgeInsets.symmetric(vertical: 4),
                                child: Text(
                                  _logs[i],
                                  style: TextStyle(
                                    fontFamily: 'monospace',
                                    fontSize: 12,
                                    color: _logs[i].contains('SUCCÈS') || _logs[i].contains('terminée') 
                                        ? const Color(0xFF10B981)
                                        : Colors.greenAccent.shade100,
                                  ),
                                ),
                              );
                            },
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
