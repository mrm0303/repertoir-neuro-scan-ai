# -*- coding: utf-8 -*-
"""
المحتوى العربي للدليل الشامل لبرنامج Repertoir Neuro Scan.AI (الإصدار السادس V6)
"""

def get_ar_toc():
    return '''
    <nav class="sidebar-toc" id="toc-ar">
        <div class="toc-title">فهرس الدليل الشامل</div>
        <ul class="toc-list">
            <li><a href="#ar-intro" class="toc-link">1. البدء السريع والتثبيت</a></li>
            <li><a href="#ar-dashboard" class="toc-link">2. لوحة التحكم والإحصائيات</a></li>
            <li><a href="#ar-scanner" class="toc-link">3. فحص الأقراص المحلية</a></li>
            <li><a href="#ar-servers" class="toc-link">4. الخوادم البعيدة وNAS</a></li>
            <li><a href="#ar-dit" class="toc-link">5. تفريغ الذاكرة DIT الآمن</a></li>
            <li><a href="#ar-search" class="toc-link">6. البحث وسلة المونتاج</a></li>
            <li><a href="#ar-chat" class="toc-link">7. المساعد الذكي وSQL</a></li>
            <li><a href="#ar-renamer" class="toc-link">8. إعادة تسمية المشاهد</a></li>
            <li><a href="#ar-sync" class="toc-link">9. مزامنة الكاميرات وصوت Zoom F8</a></li>
            <li><a href="#ar-tags" class="toc-link">10. الوسوم والذكاء البصري</a></li>
            <li><a href="#ar-duplicates" class="toc-link">11. كاشف وحاذف الملفات المكررة</a></li>
            <li><a href="#ar-projects" class="toc-link">12. إدارة المشاريع وربط الميديا</a></li>
            <li><a href="#ar-settings" class="toc-link">13. الإعدادات والتحديث الذاتي</a></li>
            <li><a href="#ar-web" class="toc-link">14. الوصول عبر الويب والهاتف</a></li>
            <li><a href="#ar-faq" class="toc-link">15. حل المشكلات والأسئلة الشائعة</a></li>
        </ul>
    </nav>
    '''

def get_ar_content():
    return '''
    <main class="main-doc-content lang-content" id="content-ar">
        
        <!-- SECTION 1: QUICK START & INSTALLATION -->
        <section class="doc-section" id="ar-intro">
            <div class="section-header">
                <span class="section-icon">🚀</span>
                <div>
                    <h2>1. البدء السريع والتثبيت على كافة الأنظمة</h2>
                    <p style="margin:0;">تثبيت بنقرة واحدة لأنظمة ماك، ويندوز ولينكس — دون أي تعقيدات تقنية للمحترفين.</p>
                </div>
            </div>

            <p><strong>برنامج ريبيرتوار (Repertoir Neuro Scan.AI - V6)</strong> هو محطة متكاملة لإدارة الأصول الرقمية (MAM)، الفهرسة فائقة السرعة، مزامنة الكاميرات المتعددة الاحترافية، والتحليل الذكي لمراحل ما بعد الإنتاج والمونتاج. يعمل البرنامج <strong>محلياً بالكامل (100% Offline)</strong> على جهازك دون إرسال أي وسائط أو بيانات خارج حاسوبك.</p>

            <div class="callout callout-info">
                <span class="callout-icon">💡</span>
                <div class="callout-content">
                    <strong>جاهز لمواقع التصوير المعزولة:</strong> يمكنك تشغيل البرنامج في مواقع التصوير الصحراوية، سيارات البث الخارجي أو غرف المونتاج دون الحاجة لأي اتصال بالإنترنت.
                </div>
            </div>

            <h3>خطوات التثبيت خطوة بخطوة حسب نظام التشغيل:</h3>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🍎 التثبيت على أجهزة ماك (macOS معالجات Apple Silicon M1/M2/M3/M4 وإنتل)</span>
                    <span class="btn-badge tag-green">موصى به</span>
                </div>
                <div class="btn-desc">انقر نقراً مزدوجاً على الملف <code>Installer_Repertoir_Mac.command</code>.</div>
                <div class="btn-steps">
                    <ol>
                        <li>انقر بزر الفأرة الأيمن على ملف التثبيت واختر <strong>Open (فتح)</strong> لتجاوز حماية Gatekeeper في نظام ماك.</li>
                        <li>يقوم برنامج التثبيت تلقائياً بإنشاء بيئة بايثون معزولة، وتثبيت الحزم المطلوبة وتجهيز محركات FFmpeg.</li>
                        <li>لبدء تشغيل التطبيق في أي وقت، انقر نقراً مزدوجاً على <code>Lancer_App.command</code>.</li>
                    </ol>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🪟 التثبيت على نظام ويندوز (Windows 10 / 11)</span>
                    <span class="btn-badge tag-cyan">تثبيت تلقائي</span>
                </div>
                <div class="btn-desc">انقر نقراً مزدوجاً على الملف <code>Installer_Repertoir_Windows.bat</code>.</div>
                <div class="btn-steps">
                    <ol>
                        <li>إذا ظهرت نافذة حماية Windows SmartScreen، انقر على <em>More info (مزيد من المعلومات)</em> ثم <em>Run anyway (تشغيل على أية حال)</em>.</li>
                        <li>يتم إعداد البيئة الافتراضية <code>.venv</code> الخاصة بويندوز دون تغيير إعدادات حاسوبك العامة.</li>
                        <li>لتشغيل البرنامج لاحقاً، انقر على <code>Lancer_App_Windows.bat</code>.</li>
                    </ol>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🐧 التثبيت على نظام لينكس (Ubuntu, Debian, Fedora, Arch)</span>
                    <span class="btn-badge">ملف شل</span>
                </div>
                <div class="btn-desc">افتح الطرفية (Terminal) في المجلد واكتب: <code>bash Installer_Repertoir_Linux.sh</code>.</div>
                <div class="btn-steps">
                    <ol>
                        <li>يتأكد السكربت من توفر بايثون 3 وحزم <code>python3-tk</code>.</li>
                        <li>لتشغيل البرنامج، استخدم <code>./Lancer_App_Linux.sh</code>.</li>
                    </ol>
                </div>
            </div>
        </section>

        <!-- SECTION 2: MASTER DASHBOARD -->
        <section class="doc-section" id="ar-dashboard">
            <div class="section-header">
                <span class="section-icon">📊</span>
                <div>
                    <h2>2. لوحة التحكم الشاملة (Dashboard)</h2>
                    <p style="margin:0;">مؤشرات آنية، خريطة تخزين مرئية تفاعلية ومحلل ذكاء اصطناعي لسلامة الأصول.</p>
                </div>
            </div>

            <h3>شريط المؤشرات الرئيسية</h3>
            <p>يستعرض الشريط العلوي إحصائيات مكتبتك في الوقت الفعلي: <strong>عدد الأقراص المفهرسة</strong>، <strong>إجمالي عدد الملفات</strong> و<strong>الحجم الكلي المشغول (جيجابايت / تيرابايت)</strong>.</p>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🗺️ الخريطة المرئية التفاعلية (Treemap / Sunburst / Tree)</span>
                    <span class="btn-badge tag-cyan">مستكشف التخزين</span>
                </div>
                <div class="btn-desc">استكشاف المجلدات والمشاريع الأكثر استهلاكاً للمساحة بصرياً.</div>
                <div class="btn-steps">
                    <ul>
                        <li><strong>قائمة اختيار القرص:</strong> تصفح قرصاً محدداً أو استعراض كامل مساحة التخزين المجمعة.</li>
                        <li><strong>التنقل بالنقر:</strong> انقر على أي مستطيل ملون للتعمق داخل المجلد الفرعي. انقر على المسار العلوي للرجوع للخلف.</li>
                        <li><strong>تغيير نمط العرض:</strong> يمكنك الاختيار بين <em>خريطة المستطيلات المتناسبة (Treemap)</em>، <em>الأقراص الدائرية (Sunburst)</em> أو <em>الشجرة</em> من نافذة الإعدادات.</li>
                    </ul>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">📈 المخططات البيانية والتحليلية</span>
                    <span class="btn-badge">رسوم إحصائية</span>
                </div>
                <div class="btn-desc">في اللوحة الجانبية اليمنى:</div>
                <div class="btn-steps">
                    <ul>
                        <li><strong>تطور البيانات عبر السنوات:</strong> رسم بياني يوضح حجم إنتاج المواد المصورة موزعة حسب سنة التصوير.</li>
                        <li><strong>أكثر الوسوم والكلمات الدلالية تكراراً:</strong> مخطط بياني يبرز أكثر المشاهد والمواضيع توثيقاً بالذكاء الاصطناعي.</li>
                    </ul>
                </div>
            </div>

            <h3>أزرار الإجراءات السريعة</h3>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔍 زر «بدء فحص قرص (Lancer un Scan)»</span>
                    <span class="btn-badge tag-green">اختصار مباشر</span>
                </div>
                <div class="btn-desc">ينقلك مباشرة إلى شاشة فحص الأقراص المحلية لفهرسة قرص أو بطاقة ذاكرة جديدة.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">👯 زر «كشف الملفات المكررة (Chercher des Doublons)»</span>
                    <span class="btn-badge tag-amber">تنظيف المساحة</span>
                </div>
                <div class="btn-desc">يفتح وحدة الكشف عن التكرارات لاستعادة المساحة التخزينية المهدورة.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">📅 زر «جدول التصوير الزمني (Calendrier de Tournage)»</span>
                    <span class="btn-badge">التسلسل الزمني</span>
                </div>
                <div class="btn-desc">يعرض تقويماً تفاعلياً يرتب المشاهد زمنياً حسب أيام التصوير، الكاميرات والمشاريع.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🌙 زر «تشغيل التصنيف التلقائي الذكي (Lancer l'Auto-étiquetage IA)»</span>
                    <span class="btn-badge tag-purple">معالجة خلفية</span>
                </div>
                <div class="btn-desc">يشغل محرك الفهرسة الذاتية في الخلفية لتحليل الفيديوهات وتوليد الكلمات المفتاحية دون التأثير على سرعة المونتاج. انقر مجدداً للإيقاف المؤقت.</div>
            </div>

            <h3>🤖 وكيل التحليل الذكي (AI Analyst Agent)</h3>
            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">زر «توليد رؤية تحليلية (Générer un Insight)»</span>
                    <span class="btn-badge tag-cyan">ذكاء اصطناعي</span>
                </div>
                <div class="btn-desc">يطلب من الوكيل الذكي المحلي فحص توزيع الملفات، واكتشاف الأقراص الموشكة على الامتلاء، والوسائط المعزولة، ثم تقديم توصيات احترافية.</div>
                <div class="btn-steps">
                    <ul>
                        <li>إذا اكتشف الوكيل نقاط تحسين، يقترح عليك زراً لتصدير <strong>تقرير تدقيق تخزين شامل</strong> بصيغة Markdown (.md).</li>
                    </ul>
                </div>
            </div>
        </section>

        <!-- SECTION 3: SCANNER LOCAL DISKS -->
        <section class="doc-section" id="ar-scanner">
            <div class="section-header">
                <span class="section-icon">💽</span>
                <div>
                    <h2>3. التخزين > فحص الأقراص المحلية</h2>
                    <p style="margin:0;">فهرسة فائقة السرعة للأقراص الصلبة، وحدات NVMe SSD وبطاقات CFexpress وSD.</p>
                </div>
            </div>

            <h3>جدول سجل الأقراص</h3>
            <p>يستعرض الأقراص المسجلة مع أسمائها، حالة الاتصال الحالية (● متصل باللون الأخضر / ○ غير متصل بالرمادي)، الرقم التسلسلي، نقطة التوصيل، عدد الملفات، والمساحة المستغلة.</p>

            <h3>شريط العمليات والأزرار</h3>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔄 زر «اكتشاف الأقراص المتصلة (Détecter les disques branchés)»</span>
                    <span class="btn-badge tag-green">فحص عتادي</span>
                </div>
                <div class="btn-desc">يفحص منافذ Thunderbolt وUSB-C وSATA لتحديث حالة اتصال الأقراص في اللحظة ذاتها.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">▶️ زر «بدء الفهرسة (Analyser)»</span>
                    <span class="btn-badge tag-green">مسح شامل</span>
                </div>
                <div class="btn-desc">يبدأ فهرسة القرص المحدد بسرعة هائلة في الخلفية مع عرض معدل الإنجاز (ملف/ثانية) والوقت المتبقي المقدر.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🗑️ زر «حذف من الفهرس (Supprimer du catalogue)»</span>
                    <span class="btn-badge tag-red">إدارة الفهرس</span>
                </div>
                <div class="btn-desc">يحذف بيانات القرص من قاعدة بيانات البرنامج. <em>تنبيه: ملفاتك المادية على القرص تظل آمنة تماماً ولا يتم مسها أبداً.</em></div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🏷️ زر «ملاحظة / موقع الحفظ الفعلي (Note / Emplacement)»</span>
                    <span class="btn-badge">أرشفة الأرفف والخزائن</span>
                </div>
                <div class="btn-desc">تسجيل المكان الفعلي للقرص عندما يكون مفصولاً (مثال: «الخزانة 3، الرف B، صندوق تصوير مسلسل دراما»). يتيح لك العثور على القرص الفعلي فوراً بمجرد البحث عن أي مشهد فيه!</div>
            </div>

            <h3>خيارات الفحص (خانات الاختيار)</h3>
            <table>
                <thead>
                    <tr>
                        <th style="width:25%;">الخيار</th>
                        <th style="width:20%;">الحالة الافتراضية</th>
                        <th>الأهمية التقنية للمونتير وفني الـ DIT</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>☑️ البصمة السريعة (XXHash64)</strong></td>
                        <td>مفعل</td>
                        <td>توليد بصمة تشفيرية سريعة جداً (تتجاوز 4 جيجابايت/ثانية) لكشف التطابق والمكررات دون إبطاء الفحص.</td>
                    </tr>
                    <tr>
                        <td><strong>☑️ بيانات EXIF و ffprobe</strong></td>
                        <td>مفعل</td>
                        <td>استخراج الدقة الكاملة (4K, ProRes, BRAW)، الترميز، معدل الإطارات (fps)، نوع الكاميرا والتايم كود.</td>
                    </tr>
                    <tr>
                        <td><strong>☑️ التحليل الأولي المسبق</strong></td>
                        <td>مفعل</td>
                        <td>حساب سريع لعدد المجلدات والملفات لعرض مؤشر تقدم زمني حقيقي ودقيق.</td>
                    </tr>
                    <tr>
                        <td><strong>☑️ الفحص التراكمي الذكي</strong></td>
                        <td>مفعل</td>
                        <td>فحص الملفات الجديدة أو المعدلة أو المحذوفة فقط منذ آخر فحص. يقلل زمن إعادة الفحص بنسبة 95%!</td>
                    </tr>
                    <tr>
                        <td><strong>☑️ تجاهل ملفات النظام</strong></td>
                        <td>مفعل</td>
                        <td>استبعاد الملفات غير المرغوبة تلقائياً مثل <code>.DS_Store</code> و <code>Thumbs.db</code> وسلة المهملات.</td>
                    </tr>
                    <tr>
                        <td><strong>☑️ الصور المصغرة للفيديو</strong></td>
                        <td>مفعل</td>
                        <td>إنشاء أشرطة لقطات للمعاينة البصرية السريعة بمجرد تمرير الفأرة فوق الفيديو.</td>
                    </tr>
                </tbody>
            </table>
        </section>

        <!-- SECTION 4: REMOTE SERVERS & NAS -->
        <section class="doc-section" id="ar-servers">
            <div class="section-header">
                <span class="section-icon">🌐</span>
                <div>
                    <h2>4. التخزين > الخوادم البعيدة ووحدات التخزين الشبكي NAS</h2>
                    <p style="margin:0;">ربط وفهرسة خوادم QNAP وSynology وTrueNAS عبر بروتوكولات SMB وNFS.</p>
                </div>
            </div>

            <p>يتيح هذا القسم ربط وفهرسة خوادم الاستوديو المشتركة عبر الشبكة المحلية ومراقبة محتواها دون الحاجة لتحريك محطات العمل.</p>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">➕ زر «إضافة خادم (Ajouter un serveur)»</span>
                    <span class="btn-badge tag-green">إعداد الاتصال</span>
                </div>
                <div class="btn-desc">نافذة إدخال عنوان IP الخاص بالخادم، واسم المستخدم، وكلمة المرور ومسار المجلد المشترك.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">📡 زر «فحص هذا القرص البعيد (Scanner ce disque distant)»</span>
                    <span class="btn-badge tag-cyan">فحص شبكي</span>
                </div>
                <div class="btn-desc">فهرسة محتويات السيرفر مع تنظيم تدفق البيانات لتجنب إشغال شبكة المونتاج أثناء العمل.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">☁️ زر «نسخ احتياطي لقاعدة البيانات إلى السيرفر (Backup Sécurisé)»</span>
                    <span class="btn-badge tag-purple">حماية ومزامنة</span>
                </div>
                <div class="btn-desc">إنشاء لقطة مضغوطة من قاعدة بيانات <code>catalogue.db</code> وحفظها تلقائياً في مجلد النسخ الاحتياطي على خادم NAS لضمان عدم ضياع الأرشيف أبداً.</div>
            </div>
        </section>

        <!-- SECTION 5: DIT OFFLOAD -->
        <section class="doc-section" id="ar-dit">
            <div class="section-header">
                <span class="section-icon">📥</span>
                <div>
                    <h2>5. التخزين > تفريغ الذاكرة DIT الآمن (Offload)</h2>
                    <p style="margin:0;">تفريغ بطاقات الذاكرة وفق المعايير السينمائية مع التحقق بايت-بايت وملفات MHL المعتمدة.</p>
                </div>
            </div>

            <p>مصمم خصيصاً لمساعدي الكاميرا وفنيي الصورة الرقمية (DIT) في موقع التصوير لضمان عدم مسح أي بطاقة تصوير قبل التأكد الرياضي القاطع من مطابقة النسخ بنسبة 100%.</p>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎴 منطقة سحب وإفلات بطاقة الذاكرة (Source)</span>
                    <span class="btn-badge">المصدر</span>
                </div>
                <div class="btn-desc">اسحب وأفلت بطاقة CFexpress أو SD أو RED Mini-Mag مباشرة في هذه المنطقة.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎯 قرص الوجهة ومنشئ شجرة المجلدات القياسية</span>
                    <span class="btn-badge">هيكلية المشروع</span>
                </div>
                <div class="btn-desc">اختر قرص النسخ المستهدف. يقوم البرنامج تلقائياً بإنشاء التدرج الشجري السينمائي الموحد:<br>
                <code>[اسم_المشروع] / [تاريخ_التصوير] / [كاميرا_A] / RUSHES</code>.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔐 اختيار خوارزمية البصمة والتحقق (Checksum)</span>
                    <span class="btn-badge tag-amber">محرك التحقق</span>
                </div>
                <div class="btn-desc">
                    <ul>
                        <li><strong>XXHash64:</strong> أسرع خوارزمية في العالم (تتجاوز 4 جيجابايت/ثانية على أقراص NVMe). مثالية لتفريغ ملفات 8K RAW الضخمة بسرعة.</li>
                        <li><strong>MD5:</strong> المعيار التقليدي للبث التلفزيوني ومطابق لبرامج الفحص الخارجية مثل Silverstack وShotPut Pro.</li>
                        <li><strong>SHA1 / SHA256:</strong> حماية تشفيرية فائقة للأفلام الوثائقية والأرشيف الوطني.</li>
                    </ul>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🚀 زر «بدء النقل الآمن (Démarrer le Transfert Sécurisé)»</span>
                    <span class="btn-badge tag-green">تنفيذ آمن</span>
                </div>
                <div class="btn-desc">يقوم بنسخ البيانات عبر مخازن مزدوجة، وحساب البصمة أثناء النسخ، وإعادة قراءة الملفات من الوجهة لمطابقتها بايت-بايت، وتوليد ملف بيان رسمي <code>.mhl</code> معتمد من جمعية المصورين السينمائيين الأمريكية (ASC).</div>
            </div>
        </section>

        <!-- SECTION 6: SEARCH -->
        <section class="doc-section" id="ar-search">
            <div class="section-header">
                <span class="section-icon">🔍</span>
                <div>
                    <h2>6. محرك البحث الشامل وسلة المونتاج (Rushes Basket)</h2>
                    <p style="margin:0;">بحث لحظي متعدد المعايير، بحث دلالي بالذكاء الاصطناعي وتصدير مباشر لبرامج المونتاج.</p>
                </div>
            </div>

            <h3>شريط البحث وأدوات التصفية الرئيسية</h3>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">⌨️ حقل البحث وقائمة نطاق البحث</span>
                    <span class="btn-badge">بحث مرن</span>
                </div>
                <div class="btn-desc">اكتب أي كلمة (اسم ممثل، مشهد، مدينة، رقم لقطة). حدد النطاق من القائمة:
                <em>الكل (Partout)</em>، <em>اسم الملف</em>، <em>المجلد</em>، <em>نوع الكاميرا</em>، <em>الامتداد</em>، <em>الترميز (Codec)</em> أو <em>البيانات الوصفية</em>.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🗂️ أزرار التصنيفات السريعة</span>
                    <span class="btn-badge tag-cyan">تصفية سريعة</span>
                </div>
                <div class="btn-desc">تصفية نوعية بنقرة واحدة: <strong>[الكل]</strong>، <strong>[فيديو]</strong>، <strong>[صوت]</strong>، <strong>[صور]</strong>، <strong>[مشاريع مونتاج]</strong>، <strong>[مستندات]</strong>.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🧠 مفتاح «البحث الدلالي بالذكاء الاصطناعي (Recherche Sémantique)»</span>
                    <span class="btn-badge tag-purple">لغة طبيعية</span>
                </div>
                <div class="btn-desc">تفعيل الفهم البصري للمحتوى باللغة الطبيعية. يمكنك البحث عن أوصاف مثل: <em>«غروب الشمس فوق البحر تصوير طائرة درون»</em> أو <em>«لقطة مقربة لممثل غاضب»</em> حتى لو لم تكن هذه الكلمات مكتوبة في اسم الملف!</div>
            </div>

            <h3>فلاتر المواصفات التقنية</h3>
            <p>تصفية النتائج بدقة حسب: <strong>الدقة</strong> (4K DCI, UHD, 1080p)، <strong>معدل الإطارات</strong> (24, 25, 50, 100, 120 إطار لتصوير الحركة البطيئة Slo-Mo)، <strong>النطاق الزمني</strong> و<strong>الحجم الأدنى للملف</strong>.</p>

            <h3>قائمة الزر الأيمن واختصارات لوحة المفاتيح</h3>
            <table>
                <thead>
                    <tr>
                        <th style="width:25%;">الإجراء / الاختصار</th>
                        <th>الوظيفة وسير العمل</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><kbd>المسافة (Spacebar)</kbd></td>
                        <td>معاينة فورية للفيديو عبر QuickLook على ماك أو المشغل المدمج على ويندوز ولينكس.</td>
                    </tr>
                    <tr>
                        <td><strong>فتح في المجلد (Finder / Explorer)</strong></td>
                        <td>فتح مكان تواجد الملف الأصلي مباشرة على القرص الفعلي المعني.</td>
                    </tr>
                    <tr>
                        <td><strong>نسخ المسار الكامل (Copier le chemin)</strong></td>
                        <td>نسخ مسار الملف بالكامل إلى الحافظة لاستخدامه في برامج المونتاج أو أوامر النظام.</td>
                    </tr>
                    <tr>
                        <td><strong>البطاقة التقنية للملف (Fiche Technique)</strong></td>
                        <td>استعراض مواصفات الصوت والصورة الكاملة، القنوات الصوتية، وملف الألوان (Log, Rec709, HDR).</td>
                    </tr>
                    <tr>
                        <td><strong>فحص سلامة الميديا (Santé Média)</strong></td>
                        <td>فحص الملف والتأكد من خلوه تماماً من أي عطب أو لقطات ساقطة (Dropped Frames).</td>
                    </tr>
                </tbody>
            </table>

            <h3>سلة المونتاج وعمليات التصدير الاحترافية</h3>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🛒 أزرار «إضافة للسلة» و «إفراغ السلة»</span>
                    <span class="btn-badge">تجميع المشاهد</span>
                </div>
                <div class="btn-desc">تجميع لقطات مختارة من أقراص مختلفة في سلة واحدة لتنفيذ عمليات مجمعة عليها.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎞️ زر «توليد ملفات البروكسي (Générer Proxies)»</span>
                    <span class="btn-badge tag-green">تحويل سريع</span>
                </div>
                <div class="btn-desc">تحويل المشاهد المختارة في الخلفية إلى صيغ مونتاج خفيفة وسلسة (Apple ProRes Proxy أو H.264 MP4 بدقة 1080p) مع الحفاظ التام على التايم كود والقنوات الصوتية.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎬 زر «تصدير تايم لاين XML (Exporter Timeline XML)»</span>
                    <span class="btn-badge tag-cyan">تكامل المونتاج NLE</span>
                </div>
                <div class="btn-desc">توليد ملف FCPXML أو Final Cut 7 XML معياري. افتحه مباشرة في <strong>أدوبي بريمير برو 2026 (Premiere Pro)</strong>، <strong>دافينشي ريزولف (DaVinci Resolve)</strong> أو <strong>فاينل كت برو (Final Cut Pro)</strong> لتجد مشاهدك مصفوفة على التايم لاين مع أسمائها وبياناتها دون الحاجة لإعادة سحبها يدوياً!</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">📝 زر «توليد ملفات البيانات المرافقة (Générer XMP Sidecars)»</span>
                    <span class="btn-badge">بيانات وصفية</span>
                </div>
                <div class="btn-desc">حفظ الوسوم، التقييم بالنجوم والأوصاف الذكية مباشرة في ملفات <code>.xmp</code> متوافقة تماماً مع حزمة برامج أدوبي (Premiere, Bridge, After Effects).</div>
            </div>
        </section>

        <!-- SECTION 7: AI CHAT -->
        <section class="doc-section" id="ar-chat">
            <div class="section-header">
                <span class="section-icon">💬</span>
                <div>
                    <h2>7. مختبر الذكاء الاصطناعي > المساعد الذكي واستعلامات SQL</h2>
                    <p style="margin:0;">تحدث مع مكتبتك الفلمية باللغة الطبيعية دون الحاجة لمعرفة لغات البرمجة.</p>
                </div>
            </div>

            <p>يتصل المساعد الذكي مباشرة ببياناتك المحلية، ويمكنك سؤاله أسئلة إنتاجية معقدة مثل:</p>
            <ul>
                <li><em>«كم ساعة من لقطات ProRes قمنا بتصويرها في عام 2025 بكاميرا Sony FX6؟»</em></li>
                <li><em>«أظهر لي أضخم 10 ملفات حجماً على القرص SSD_TOUR_02.»</em></li>
                <li><em>«اعثر على كل المشاهد التي تظهر فيها سيارة والمصورة بسرعة 50 إطاراً في الثانية.»</em></li>
            </ul>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">زر الإرسال وحاجز أمان SQL (Read-Only)</span>
                    <span class="btn-badge tag-green">أمان مطلق</span>
                </div>
                <div class="btn-desc">يترجم المساعد طلبك إلى استعلام SQL منظم ينفذ <strong>في وضع القراءة فقط (SELECT)</strong> لضمان استحالة تعديل أو حذف أي ملف بالخطأ. تظهر الإجابة مباشرة مصحوبة بجدول النتائج.</div>
            </div>
        </section>

        <!-- SECTION 8: BATCH RENAMER -->
        <section class="doc-section" id="ar-renamer">
            <div class="section-header">
                <span class="section-icon">🪄</span>
                <div>
                    <h2>8. مختبر الذكاء الاصطناعي > إعادة تسمية المشاهد (Batch Renamer)</h2>
                    <p style="margin:0;">إعادة تسمية جماعية منظمة وفق معايير البث والقنوات التلفزيونية.</p>
                </div>
            </div>

            <p>تخلص من الأسماء التلقائية العشوائية للكاميرات (مثل <code>C0001.MP4</code>) التي تسبب مشاكل وتضارباً أثناء المونتاج.</p>

            <h3>بناء قالب التسمية (العناصر المتاحة)</h3>
            <p>انقر على العناصر لتركيب صيغة التسمية المطلوبة:</p>
            <div style="display:flex; flex-wrap:wrap; gap:8px; margin: 12px 0;">
                <code>{camera}</code> <code>{date}</code> <code>{reel}</code> <code>{scene}</code> <code>{take}</code> <code>{resolution}</code> <code>{fps}</code> <code>{counter}</code> <code>{orig_name}</code>
            </div>

            <p>صيغة موصى بها لمشاريع الأفلام والمسلسلات:<br>
            <code>PROJ_FILM_{date}_CAM{camera}_S{scene}_T{take}</code></p>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">👁️ زر «معاينة المحاكاة (Prévisualiser)»</span>
                    <span class="btn-badge tag-cyan">تحقق بصري مسبق</span>
                </div>
                <div class="btn-desc">يعرض جدولاً مقارناً جنباً إلى جنب (الاسم الأصلي مقابل الاسم الجديد المقترح) مع تنبيه فوري في حال وجود أي تشابه أو تكرار محتمل قبل التطبيق الفعلي.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">✅ زر «تطبيق إعادة التسمية (Appliquer le Renommage)»</span>
                    <span class="btn-badge tag-green">تنفيذ</span>
                </div>
                <div class="btn-desc">إعادة تسمية الملفات المادية على القرص وتحديث سجلات قاعدة بيانات SQLite فوراً دون كسر أي مسارات أو روابط.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">↩️ زر «تراجع عن التسمية بنقرة واحدة (Undo)»</span>
                    <span class="btn-badge tag-amber">إلغاء آمن</span>
                </div>
                <div class="btn-desc">بفضل سجل المعاملات الآمن، يمكنك التراجع فوراً واستعادة الأسماء الأصلية للملفات بضغطة زر واحدة!</div>
            </div>
        </section>

        <!-- SECTION 9: MULTI-CAM & ZOOM F8 SYNC -->
        <section class="doc-section" id="ar-sync">
            <div class="section-header">
                <span class="section-icon">🎬</span>
                <div>
                    <h2>9. مختبر الذكاء الاصطناعي > مزامنة الكاميرات المتعددة وصوت Zoom F8</h2>
                    <p style="margin:0;">ربط آلي لزوايا التصوير المتعددة مع فصل مسارات الصوت متعدد القنوات (Polyphonic WAV).</p>
                </div>
            </div>

            <p>يحل هذا القسم إحدى أكبر معضلات المونتاج عند تصوير المشاهد بكاميرات متعددة (كاميرا A، كاميرا B، كاميرا C...) مع تسجيل صوت احترافي مستقل عبر أجهزة مسجلات الصوت الميدانية (مثل Zoom F8 و Sound Devices 833 و Tentacle Sync).</p>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎥 إدارة زوايا الكاميرات المتعددة (Multi-Cam)</span>
                    <span class="btn-badge tag-cyan">زوايا الكاميرا</span>
                </div>
                <div class="btn-desc">
                    <ul>
                        <li><strong>كاميرا 1 (الزاوية الرئيسية A):</strong> اختر ملف أو مجلد الكاميرا الأولى.</li>
                        <li><strong>زر «[+] إضافة كاميرا» :</strong> إضافة زاوية كاميرا جديدة ديناميكياً (كاميرا B، كاميرا C، كاميرا D...). يمكنك إضافة عدد لا نهائي من زوايا الكاميرات!</li>
                        <li><strong>زر «[-] حذف زاوية» :</strong> إزالة زاوية كاميرا غير مرغوبة.</li>
                    </ul>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎙️ ملف الصوت الرئيسي ودعم مسجلات Zoom F8 (WAV متعدد القنوات)</span>
                    <span class="btn-badge tag-green">صوت متعدد المسارات</span>
                </div>
                <div class="btn-desc">
                    اختر ملف الصوت الرئيسي المسجل من جهاز Zoom F8 أو Sound Devices بصيغة Broadcast Wave (BWF / Polyphonic WAV).
                    <br><br>
                    <strong>☑️ خيار «فصل المسارات المستقلة تلقائياً (Séparer pistes multipistes)» :</strong>
                    عند تفعيل هذا الخيار، يقوم المحرك تلقائياً بفصل كل ميكروفون في مسار صوتي منفصل:
                    <br>• المسار A1 : ميكروفون البوم الرئيسي (Boom)
                    <br>• المسار A2 : ميكروفون لافالير الممثل الأول (Lavalier 1)
                    <br>• المسار A3 : ميكروفون لافالير الممثل الثاني (Lavalier 2)
                    <br>• المسار A4 : ميكروفون محيطي للغرفة (Ambience)
                    <br>يتم توزيع كل صوت على تراك خاص به على التايم لاين لسهولة المكس والمونتاج دون دمج مشوه!
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">⚡ خوارزميات المزامنة فائقة الدقة</span>
                    <span class="btn-badge tag-purple">مطابقة صوتية</span>
                </div>
                <div class="btn-desc">
                    <ul>
                        <li><strong>المطابقة البصرية للموجات الصوتية (Waveform Cross-Correlation):</strong> تحليل البصمة الترددية لصوت الكاميرا ومطابقتها مع صوت مسجل Zoom F8 بدقة أجزاء من الألف من الثانية، وهي مثالية عند عدم استخدام أجهزة تايم كود في موقع التصوير.</li>
                        <li><strong>التايم كود المدمج (Timecode LTC / SMPTE):</strong> قفل ومزامنة فورية بالاعتماد على ساعة التايم كود المشتركة المدمجة في الميديا.</li>
                    </ul>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🚀 زري «بدء المزامنة» و «🎬 تصدير تايم لاين XML»</span>
                    <span class="btn-badge tag-green">تصدير مباشر للمونتاج</span>
                </div>
                <div class="btn-desc">
                    يقوم بحساب الفارق الزمني وتصدير تسلسل متعدد الكاميرات جاهز فوراً للعمل في <strong>Adobe Premiere Pro 2026</strong> و<strong>DaVinci Resolve</strong> و<strong>Final Cut Pro</strong>، مع ظهور كافة زوايا الفيديو ومسارات الصوت المستقلة مرتبة ومزامنة تماماً على الخط الزمني!
                </div>
            </div>
        </section>

        <!-- SECTION 10: TAGS & VISION -->
        <section class="doc-section" id="ar-tags">
            <div class="section-header">
                <span class="section-icon">🏷️</span>
                <div>
                    <h2>10. مختبر الذكاء الاصطناعي > الوسوم والتحليل البصري الذكي</h2>
                    <p style="margin:0;">تصنيف المشاهد، التعرف على الإضاءة واللقطات وتوليد سحابة الكلمات المفتاحية.</p>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🤖 زر «استخراج وسوم الذكاء الاصطناعي (Extraire Étiquettes IA)»</span>
                    <span class="btn-badge tag-purple">رؤية حاسوبية</span>
                </div>
                <div class="btn-desc">تشغيل نماذج الرؤية الحاسوبية لاكتشاف وتصنيف طبيعة اللقطات (لقطة عامة، مقربة، درون)، وظروف الإضاءة (ليل، نهار، ساعة ذهبية)، والأشخاص والأماكن.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🏷️ سحابة الوسوم والتحكم في المصطلحات</span>
                    <span class="btn-badge">تنظيم الأرشيف</span>
                </div>
                <div class="btn-desc">انقر نقراً مزدوجاً على أي وسم للانتقال مباشرة إلى كافة المشاهد المرتبطة به في شاشة البحث. تتيح لك أزرار <em>تعديل الاسم</em> و<em>حذف الوسم</em> تنظيم المعجم الوثائقي للمؤسسة.</div>
            </div>
        </section>

        <!-- SECTION 11: DUPLICATES -->
        <section class="doc-section" id="ar-duplicates">
            <div class="section-header">
                <span class="section-icon">👯</span>
                <div>
                    <h2>11. مختبر الذكاء الاصطناعي > كاشف الملفات المكررة والحذف الآمن</h2>
                    <p style="margin:0;">استرجاع مساحات تخزين ضخمة مع أمان تام من الحذف الخاطئ.</p>
                </div>
            </div>

            <h3>أنماط كشف التكرار</h3>
            <ul>
                <li><strong>نمط الملفات المتطابقة:</strong> مطابقة تامة عبر البصمة الرقمية XXHash64 حتى لو تغيرت أسماء الملفات أو اختلفت مساراتها.</li>
                <li><strong>نمط المجلدات المتطابقة:</strong> كشف المجلدات الكاملة المستنسخة بين الأقراص المختلفة (مثل نسخ الحماية المكررة بعد انتهاء التصوير).</li>
            </ul>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">⚖️ جدول خطة التنظيف</span>
                    <span class="btn-badge">مقارنة واضحة</span>
                </div>
                <div class="btn-desc">
                    عرض مجموعات الملفات المكررة مع حساب إجمالي المساحة القابلة للاسترجاع (بالجيجابايت أو التيرابايت).
                    <br>• <strong>إبقاء النسخة الأصلية (الزر الأخضر) :</strong> تثبيت النسخة الأساسية وحمايتها.
                    <br>• <strong>إرسال للسلة (الزر الأحمر) :</strong> تحديد النسخة الفائضة لنقلها إلى سلة المهملات.
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🤖 زر «طلب مشورة الذكاء الاصطناعي (Demander Conseil IA)»</span>
                    <span class="btn-badge tag-cyan">وكيل التنظيف الذكي</span>
                </div>
                <div class="btn-desc">يقوم الوكيل بفحص تواريخ التصوير الأصلية وسرعة الأقراص ليرشح لك بذكاء النسخة التي يُفضل الاحتفاظ بها بكل أمان.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🗑️ زر «النقل إلى سلة المهملات الآمنة (Mettre à la corbeille)»</span>
                    <span class="btn-badge tag-amber">حماية من الضياع</span>
                </div>
                <div class="btn-desc">برنامج ريبيرتوار <strong>لا يقوم أبداً بحذف الملفات نهائياً بشكل غير قابل للاسترجاع</strong>! يتم نقل الملفات المحددة إلى سلة مهملات نظام التشغيل الرسمية (Trash في ماك، Recycle Bin في ويندوز)، مما يتيح لك استعادتها بضغطة زر إن غيرت رأيك لاحقاً.</div>
            </div>
        </section>

        <!-- SECTION 12: PROJECTS -->
        <section class="doc-section" id="ar-projects">
            <div class="section-header">
                <span class="section-icon">📁</span>
                <div>
                    <h2>12. مختبر الذكاء الاصطناعي > إدارة المشاريع وربط الميديا المفقودة</h2>
                    <p style="margin:0;">فهرسة مشاريع Premiere وDaVinci وFinal Cut وإصلاح مشكلة الميديا المفصولة (Media Offline).</p>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔍 دعم شامل لملفات برامج المونتاج</span>
                    <span class="btn-badge">صيغ المشاريع</span>
                </div>
                <div class="btn-desc">فهرسة تلقائية لملفات مشاريع: <code>.prproj</code> (أدوبي بريمير)، <code>.drp</code> (دافينشي ريزولف)، <code>.fcpbundle</code> (فاينل كت)، <code>.aep</code> (أفتر إفكتس) و <code>.logicx</code> (لوجيك برو).</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔗 زر «إعادة ربط الميديا المفقودة (Relink)»</span>
                    <span class="btn-badge tag-green">إصلاح المشاريع</span>
                </div>
                <div class="btn-desc">عند ظهور الشاشة الحمراء الشهيرة (Media Offline) داخل برنامج المونتاج، يقوم ريبيرتوار بمطابقة المشاهد في قاعدة بياناته الشاملة وتحديد القرص والمجلد الذي انتقل إليه المشهد لربطه فوراً!</div>
            </div>
        </section>

        <!-- SECTION 13: SETTINGS -->
        <section class="doc-section" id="ar-settings">
            <div class="section-header">
                <span class="section-icon">⚙️</span>
                <div>
                    <h2>13. الإعدادات، الذكاء الاصطناعي والتحديث الذاتي بنقرة واحدة</h2>
                    <p style="margin:0;">تخصيص المظهر، ربط محركات الذكاء الاصطناعي وتحديث البرنامج دون المساس ببياناتك.</p>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🎨 مظهر التطبيق وأنماط العرض</span>
                    <span class="btn-badge">تخصيص الواجهة</span>
                </div>
                <div class="btn-desc">اختر السمة اللونية المفضلة (Darkly, Cyborg, Cosmo, Flatly...) ونمط خريطة التخزين المرئية (Treemap, Sunburst أو الشجرة).</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🧠 ضبط محرك الذكاء الاصطناعي المحلي (LLM & MCP)</span>
                    <span class="btn-badge tag-purple">ربط النماذج</span>
                </div>
                <div class="btn-desc">ربط البرنامج بخادم الذكاء الاصطناعي المحلي مثل LM Studio (<code>http://localhost:1234/v1</code>) أو Ollama (<code>http://localhost:11434/v1</code>)، واختيار النماذج المفضلة مثل Google Gemma 4 و Qwen 2.5 و Minitron.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">⚡ زر «ضغط وتحسين قاعدة البيانات (VACUUM)»</span>
                    <span class="btn-badge tag-cyan">صيانة SQLite</span>
                </div>
                <div class="btn-desc">إعادة فهرسة وترتيب قاعدة البيانات لضمان بقاء سرعة البحث لحظية وفائقة حتى بعد فهرسة ملايين الملفات.</div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🔄 زر «فحص وتثبيت التحديثات من GitHub»</span>
                    <span class="btn-badge tag-green">تحديث بنقرة واحدة</span>
                </div>
                <div class="btn-desc">يقوم بجلب أحدث الإصلاحات والميزات تلقائياً من GitHub مع <strong>حماية مطلقة لقاعدة بياناتك المحلية حيث تظل سليمة ومحفوظة تماماً</strong>.</div>
            </div>
        </section>

        <!-- SECTION 14: WEB ACCESS -->
        <section class="doc-section" id="ar-web">
            <div class="section-header">
                <span class="section-icon">🌐</span>
                <div>
                    <h2>14. الوصول عبر الويب والأجهزة المحمولة (iPad، الهواتف الذكية)</h2>
                    <p style="margin:0;">تصفح وبحث في أرشيفك من أي هاتف أو جهاز لوحي متصل بشبكة الواي فاي في الاستوديو.</p>
                </div>
            </div>

            <div class="btn-card">
                <div class="btn-header">
                    <span class="btn-title">🌐 زر «تشغيل الوصول عبر الويب والموبايل»</span>
                    <span class="btn-badge tag-green">سيرفر محلي آمن</span>
                </div>
                <div class="btn-desc">تشغيل خادم ويب داخلي مشفر على شبكتك المحلية.
                <br>• يعرض لك التطبيق رابطاً محلياً (مثل: <code>http://192.168.1.45:8080</code>) مصحوباً بـ <strong>رمز أمان سري (PIN Code)</strong>.
                <br>• افتح الرابط على جهاز iPad أو هاتفك الذكي للبحث عن المشاهد واستعراض مواصفاتها وأنت مسترخٍ في غرفة المونتاج أو استوديو الصوت!</div>
            </div>
        </section>

        <!-- SECTION 15: FAQ -->
        <section class="doc-section" id="ar-faq">
            <div class="section-header">
                <span class="section-icon">❓</span>
                <div>
                    <h2>15. حل المشكلات والأسئلة الشائعة (FAQ)</h2>
                    <p style="margin:0;">إرشادات وتوجيهات لأفضل تجربة استخدام يومية.</p>
                </div>
            </div>

            <div class="callout callout-warning">
                <span class="callout-icon">🔒</span>
                <div class="callout-content">
                    <strong>إذن الوصول الكامل للأقراص في نظام ماك (Full Disk Access):</strong><br>
                    إذا تعذر على البرنامج فحص بعض الأقراص الخارجية، توجه إلى <em>إعدادات النظام > الخصوصية والأمن > الوصول الكامل للقرص (Full Disk Access)</em>، وقم بتفعيل تطبيق <strong>Terminal</strong> أو <strong>Repertoir</strong>.
                </div>
            </div>

            <div class="callout callout-info">
                <span class="callout-icon">🎞️</span>
                <div class="callout-content">
                    <strong>هل برامج FFmpeg و FFprobe إلزامية لتشغيل البرنامج؟</strong><br>
                    يمكن للتطبيق فهرسة أسماء الملفات وأحجامها بدونها. ولكن ينصح بها بشدة لاستخراج بيانات الفيديو المتقدمة (ProRes، التايم كود، الدقة والصور المصغرة). ملف التثبيت <code>Installer_Repertoir_Mac.command</code> يثبتها تلقائياً.
                </div>
            </div>

            <div class="callout callout-success">
                <span class="callout-icon">🤝</span>
                <div class="callout-content">
                    <strong>هل يمكنني نقل قاعدة بياناتي ومشاركتها مع زميل يستخدم ويندوز أو لينكس؟</strong><br>
                    نعم بكل تأكيد! ملف الفهرس <code>catalogue.db</code> مبني بمعيار SQLite العالمي المتوافق بين كافة الأنظمة، ويمكنك نقله عبر قرص صلب أو فلاشة USB ليعمل فوراً دون أي تعديل.
                </div>
            </div>
        </section>

    </main>
    '''

print("AR Module ready.")
