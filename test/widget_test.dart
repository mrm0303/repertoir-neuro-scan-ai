import 'package:flutter_test/flutter_test.dart';
import 'package:repertoir/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    expect(const RepertoirApp(), isNotNull);
  });
}
