# app.py

from google.cloud import firestore
from google.cloud.firestore_v1 import SERVER_TIMESTAMP
import os
from flask import Flask, render_template, request, redirect, url_for,flash
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import DocumentReference


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "hlp1-57071-firebase-adminsdk-ib8b3-56e4af2454.json"
cred = credentials.Certificate("hlp1-57071-firebase-adminsdk-ib8b3-56e4af2454.json")
firebase_admin.initialize_app(cred)
db = firestore.Client()



app = Flask(__name__)
app.secret_key = 'enes'
os.makedirs(os.path.join(app.instance_path, 'uploads'), exist_ok=True)

uploads_dir = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(uploads_dir, exist_ok=True)

def get_user_data_from_reference(user_ref):
    if isinstance(user_ref, DocumentReference):
        user_data = user_ref.get().to_dict()
        return user_data
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png','mp4', 'avi', 'mkv', 'mov'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/kayit', methods=['GET', 'POST'])
def kayit():
    if request.method == 'POST':
        kullanici_tipi = request.form['kullanici_tipi']
        isim = request.form['isim']
        soyisim = request.form['soyisim']
        telefon = request.form['telefon']
        eposta = request.form['eposta']
        sifre = request.form['sifre']
        aktif = True
        if 'profil_fotografi' not in request.files:
            flash('Dosya seçilmedi.')
            return redirect(request.url)

        profil_fotografi = request.files['profil_fotografi']

        if profil_fotografi.filename == '':
            flash('Dosya seçilmedi.')
            return redirect(request.url)

        if profil_fotografi and allowed_file(profil_fotografi.filename):
            # Güvenli dosya adını oluştur
            filename = secure_filename(profil_fotografi.filename)

            # Dosyayı 'uploads' klasörüne kaydet
            profil_fotografi.save(os.path.join(uploads_dir, filename))

            try:
                # Kullanıcı tipine göre belirli bir koleksiyona belge ekleyin
                db.collection("HLP2").document(kullanici_tipi).collection("kullanicilar").add({
                    'isim': isim,
                    'soyisim': soyisim,
                    'telefon': telefon,
                    'eposta': eposta,
                    'sifre': sifre,
                    'profil_fotografi': 'uploads/' + filename,
                    'aktif': aktif
                })

                return f"Kayıt Başarılı! E-posta: {eposta}, Kullanıcı Tipi: {kullanici_tipi}"
            except Exception as e:
                return f"Hata oluştu: {e}"

    return render_template('register.html')


@app.route('/giris', methods=['GET', 'POST'])
def giris():
    if request.method == 'POST':
        eposta = request.form['eposta']
        sifre = request.form['sifre']
        kullanici_tipi = request.form['kullanici_tipi']

        # Kullanıcı tipine göre ilgili koleksiyonu seç
        kullanici_koleksiyonu = db.collection("HLP2").document(kullanici_tipi).collection("kullanicilar")

        # E-posta ve şifre kontrolü
        kullanici_sorgu = kullanici_koleksiyonu.where('eposta', '==', eposta).where('sifre', '==', sifre).where('aktif', '==', True).stream()

        if not kullanici_sorgu:
            return "Hatalı Giriş Bilgileri!"

        # Başarılı giriş durumunda, kullanıcı ile ilgili işlemleri yapabilirsiniz
        # Örneğin, kullanıcının adını ve soyadını almak:
        for doc in kullanici_sorgu:
            kullanici_bilgisi = doc.to_dict()
            isim = kullanici_bilgisi['isim']
            soyisim = kullanici_bilgisi['soyisim']

            # Kullanıcı tipine göre yönlendirme yap
            if kullanici_tipi == 'antrenor':
                return redirect(url_for('antrenor_sayfasi', eposta=eposta))
            elif kullanici_tipi == 'sporcu':
                return redirect(url_for('sporcu_sayfasi', eposta=eposta))
            elif kullanici_tipi == 'yonetici':
                return redirect(url_for('yonetici_sayfasi',eposta=eposta))
            else:
                return "Bilinmeyen Kullanıcı Tipi!"

    return render_template('login.html')

@app.route('/sifremi_unuttum', methods=['GET', 'POST'])
def sifremi_unuttum():
    if request.method == 'POST':
        kullanici_tipi = request.form['kullanici_tipi']
        eposta = request.form['eposta']
        return redirect(url_for('sifremi_goster', kullanici_tipi=kullanici_tipi, eposta=eposta))

    return render_template('sifremi_unuttum.html')

# Şifreyi gösterme veya değiştirme işlemleri için iki ayrı route ekleyin
@app.route('/sifremi_goster', methods=['GET', 'POST'])
def sifremi_goster():
    if request.method == 'POST':
        kullanici_tipi = request.form['kullanici_tipi']
        eposta = request.form['eposta']

        # Kullanıcı tipine göre ilgili koleksiyonu seç
        ana_koleksiyon = 'HLP2'
        alt_koleksiyon = kullanici_tipi  # Kullanıcı tipi ismini alt koleksiyon olarak kullanalım

        # Kullanıcının olduğu koleksiyonu kontrol et
        kullanici_koleksiyonu = db.collection(ana_koleksiyon).document(alt_koleksiyon).collection("kullanicilar")
        kullanici_sorgu = kullanici_koleksiyonu.where('eposta', '==', eposta).stream()

        print(f"Kullanıcı Sorgusu: {kullanici_sorgu}")

        if kullanici_sorgu:
            # Kullanıcı bulunduysa, şifreyi ekrana yazdır
            for doc in kullanici_sorgu:
                kullanici_bilgisi = doc.to_dict()
                girilen_sifre = kullanici_bilgisi['sifre']

                print(f"Girilen Şifre: {girilen_sifre}")

                return render_template('sifremi_goster.html', girilen_sifre=girilen_sifre)
        else:
            flash("Girilen e-posta adresi bulunamadı. Lütfen doğru bilgileri girin.")

    return render_template('sifremi_goster.html')

@app.route('/sifre_degistir', methods=['GET', 'POST'])
def sifre_degistir():
    if request.method == 'POST':
        eposta = request.form['eposta']
        eski_sifre = request.form['eski_sifre']
        yeni_sifre = request.form['yeni_sifre']
        onay_sifre = request.form['onay_sifre']

        # E-posta ve eski şifre kontrolü
        ana_koleksiyon = 'HLP2'
        kullanici_tipi = request.form['kullanici_tipi']  # Kullanıcı tipini formdan al
        alt_koleksiyon = 'kullanicilar'

        kullanici_koleksiyonu = db.collection(ana_koleksiyon).document(kullanici_tipi).collection(alt_koleksiyon)
        kullanici_sorgu = kullanici_koleksiyonu.where('eposta', '==', eposta).where('sifre', '==', eski_sifre).stream()

        if kullanici_sorgu:
            if yeni_sifre == onay_sifre:
                for doc in kullanici_sorgu:
                    kullanici_koleksiyonu.document(doc.id).update({'sifre': yeni_sifre})

                flash("Şifreniz başarıyla değiştirildi.")
                return redirect(url_for('giris'))
            else:
                flash("Yeni şifre ve onay şifresi eşleşmiyor. Lütfen tekrar deneyin.")
        else:
            flash("E-posta veya eski şifre hatalı. Lütfen doğru bilgileri girin.")

    return render_template('sifre_degistir.html')

@app.route('/antrenor_sayfasi', methods=['GET', 'POST'])
def antrenor_sayfasi():
    if request.method == 'POST':
        eposta = request.form['eposta']
        sifre = request.form['sifre']
        kullanici_tipi = 'antrenor'  # Antrenör sayfası olduğu için kullanıcı tipini belirt

        # Kullanıcı tipine göre ilgili koleksiyonu seç
        kullanici_koleksiyonu = db.collection("HLP2").document(kullanici_tipi).collection("kullanicilar")

        # E-posta ve şifre kontrolü
        kullanici_sorgu = kullanici_koleksiyonu.where('eposta', '==', eposta).where('sifre', '==', sifre).where('aktif', '==', True).stream()

        if not kullanici_sorgu:
            return "Hatalı Giriş Bilgileri!"

        # Başarılı giriş durumunda, kullanıcı ile ilgili işlemleri yapabilirsiniz
        # Örneğin, kullanıcının adını ve soyadını almak:
        for doc in kullanici_sorgu:
            kullanici_bilgisi = doc.to_dict()
            isim = kullanici_bilgisi['isim']
            soyisim = kullanici_bilgisi['soyisim']

            # Diğer sayfalara yönlendirme yap
            return render_template('antrenor_sayfasi.html', isim=isim, soyisim=soyisim, eposta=eposta, telefon=kullanici_bilgisi['telefon'], profil_fotografi=kullanici_bilgisi['profil_fotografi'])

        # Mesajlaşma Formu
        if 'antrenor_mesajlasma_form' in request.form:
            return redirect(url_for('antrenor_mesajlasma', eposta=eposta))

        # Gelen Mesajlar Formu
        elif 'antrenor_gelen_mesajlar_form' in request.form:
            return redirect(url_for('antrenor_gelen_mesajlar', eposta=eposta))

    return render_template('login.html')  # Eğer POST isteği değilse, giriş sayfasına yönlendir

@app.route('/antrenor_deneyim', methods=['GET'])
def antrenor_deneyim():
    antrenor_eposta = request.args.get('antrenor_eposta', '')

    # Firestore bağlantısı
    db = firestore.Client()

    # Antrenör referansını al
    antrenor_ref = db.collection("HLP2").document("antrenor").collection("kullanicilar").where("eposta", "==", antrenor_eposta).get()

    # Eğer antrenör bulunamadıysa, hata mesajı döndür
    if not antrenor_ref:
        return "Antrenör Bulunamadı!"

    # Antrenör belgesini al
    antrenor_belgesi = antrenor_ref[0].reference

    # Antrenörün ilerleme kayıtlarını içeren koleksiyonu al
    deneyimler_ref = antrenor_belgesi.collection("deneyimler").stream()

    # Antrenörün deneyimlerini listeleyen bir liste oluştur
    deneyimler = [{'id': doc.id, **doc.to_dict()} for doc in deneyimler_ref]

    # Antrenörün deneyim sayfasını render et
    return render_template('antrenor_deneyim.html', antrenor_eposta=antrenor_eposta, deneyimler=deneyimler)

@app.route('/antrenor_deneyim_ekle', methods=['GET', 'POST'])
def antrenor_deneyim_ekle():
    antrenor_eposta = request.args.get('antrenor_eposta', '')
    if request.method == 'POST':
        tecrube_yili = request.form.get('tecrube_yili', '')
        deneyimler = request.form.get('deneyimler', '')

        # Firestore bağlantısı
        db = firestore.Client()

        # Antrenör referansını al
        antrenor_ref = db.collection("HLP2").document("antrenor").collection("kullanicilar").where("eposta", "==", antrenor_eposta).get()

        # Eğer antrenör bulunamadıysa, hata mesajı döndür
        if not antrenor_ref:
            return "Antrenör Bulunamadı!"

        # Antrenör belgesini al
        antrenor_belgesi = antrenor_ref[0].reference

        # Antrenörün ilerleme kayıtlarını içeren koleksiyonu al
        deneyimler_ref = antrenor_belgesi.collection("deneyimler")

        # Yeni deneyim belgesi oluştur
        yeni_deneyim = {
            'tecrube_yili': tecrube_yili,
            'deneyimler': deneyimler,
            'tarih': firestore.SERVER_TIMESTAMP  # Firestore'da otomatik tarih eklemek için
        }

        # Deneyimleri içeren koleksiyona yeni deneyimi ekle
        deneyimler_ref.add(yeni_deneyim)

        # Deneyim eklendikten sonra antrenörün deneyim sayfasına yönlendir
        return redirect(url_for('antrenor_deneyim', antrenor_eposta=antrenor_eposta))

    # GET isteği durumunda sadece formu göster
    return render_template('antrenor_deneyim_ekle.html', antrenor_eposta=antrenor_eposta)

# Antrenör Mesajlaşma Sayfası
@app.route('/antrenor_mesajlasma', methods=['GET', 'POST'])
def antrenor_mesajlasma():
    gonderen_eposta = None
    antrenor_eposta = request.args.get('antrenor_eposta', '')

    if request.method == 'POST':
        alici_eposta = request.form['alici_eposta']
        icerik = request.form['icerik']
        gonderen_eposta = request.form['gonderen_eposta']  # Hidden input'tan değeri al

        antrenor_ref = db.collection("HLP2").document("antrenor").collection("kullanicilar").where("eposta", "==",gonderen_eposta).limit(1).stream()
        antrenor_ref = list(antrenor_ref)
        if not antrenor_ref:
            return "Antrenör Bulunamadı!"
        antrenor_ref = antrenor_ref[0]

        sporcu_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").where("eposta", "==",alici_eposta).limit(1).stream()

        sporcu_ref = list(sporcu_ref)
        if not sporcu_ref:
            return "Sporcu Bulunamadı!"
        sporcu_ref = sporcu_ref[0]

        mesaj_belgesi = db.collection("HLP2").document("mesajlar").collection("mesajlar").add({
            'gonderen_eposta': antrenor_ref.reference,
            'alici_eposta': sporcu_ref.reference,
            'icerik': icerik,
            'tarih': SERVER_TIMESTAMP
        })
        return redirect(url_for('antrenor_mesajlasma', antrenor_eposta=antrenor_eposta))

    return render_template('antrenor_mesajlasma.html', antrenor_eposta=antrenor_eposta)

@app.route('/antrenor_gelen_mesajlar', methods=['GET', 'POST'])
def antrenor_gelen_mesajlar():
    if request.method == 'POST':
        return redirect(url_for('antrenor_gelen_mesajlar'))

    # Eposta bilgisini al
    antrenor_eposta = request.args.get('antrenor_eposta', '')

    gelen_mesajlar = []
    antrenor_ref = db.collection("HLP2").document("antrenor").collection("kullanicilar").where("eposta", "==", antrenor_eposta).limit(1).stream()
    antrenor_ref = list(antrenor_ref)
    if not antrenor_ref:
        return "Antrenor Bulunamadı!"
    antrenor_ref = antrenor_ref[0]

    antrenor_mesajlar = db.collection("HLP2").document("mesajlar").collection("mesajlar").where('alici_eposta', '==', antrenor_ref.reference).stream()
    for doc in antrenor_mesajlar:
        mesaj = doc.to_dict()

        # Referansları çözme
        gonderen_ref = mesaj.get('gonderen_eposta')
        alici_ref = mesaj.get('alici_eposta')

        # Referanslardan kullanıcı verilerini al
        gonderen_data = get_user_data_from_reference(gonderen_ref)
        alici_data = get_user_data_from_reference(alici_ref)

        # Kullanıcı verilerini mesajlara ekle
        mesaj['gonderen_eposta'] = gonderen_data.get('eposta') if gonderen_data else None
        mesaj['alici_eposta'] = alici_data.get('eposta') if alici_data else None

        gelen_mesajlar.append(mesaj)

    gelen_mesajlar.sort(key=lambda x: x.get('tarih'), reverse=True)

    return render_template('antrenor_gelen_mesajlar.html', gelen_mesajlar=gelen_mesajlar, antrenor_eposta=antrenor_eposta)


@app.route('/antrenor_sporcular', methods=['GET'])
def antrenor_sporcular():
    antrenor_eposta = request.args.get('antrenor_eposta', '')

    # Antrenör epostasına göre antrenör belgesini bul
    antrenor_ref = db.collection("HLP2").document("antrenor").collection("kullanicilar").where("eposta", "==", antrenor_eposta).stream()

    # Eğer antrenör bulunamadıysa, hata mesajı döndür
    if not antrenor_ref:
        return "Antrenör Bulunamadı!"

    # Antrenör belgesini al
    antrenor_belgesi = next(antrenor_ref).reference

    # Antrenöre atanan sporcuların bilgilerini al
    sporcular_ref = antrenor_belgesi.collection("antrenor_sporcular").stream()
    sporcular = []
    # Antrenör sporcularını yazdır
    for sporcu in sporcular_ref:
        sporcu_dict = sporcu.to_dict()
        # Anahtar kontrolü yaparak sporcu_eposta ekleyelim
        if 'sporcu_eposta' in sporcu_dict:
            sporcular.append({'sporcu_eposta': sporcu_dict['sporcu_eposta']})
        else:
            print("sporcu_eposta anahtarı bulunamadı.")
    return render_template('antrenor_sporcular.html', antrenor_eposta=antrenor_eposta, sporcular=sporcular)

@app.route('/egzersiz_plan_hazirla', methods=['GET', 'POST'])
def egzersiz_plan_hazirla():
    if request.method == 'POST':
        # Formdan gelen verileri al
        sporcu_eposta = request.form.get('sporcu_eposta')
        egzersiz_adi = request.form.get('egzersiz_adi')
        set_sayisi = request.form.get('set_sayisi')
        tekrar_sayisi = request.form.get('tekrar_sayisi')
        hedef = request.form.get('hedef')

        # Egzersiz videosunu işle
        video = request.files['video']
        if video and allowed_file(video.filename):
            # Güvenli dosya adı oluştur
            filename = secure_filename(video.filename)

            video.save(os.path.join(uploads_dir, filename))

            # Firestore'a kaydet
            sporcu_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").where("eposta", "==", sporcu_eposta).get()

            for sporcu in sporcu_ref:
                sporcu_id = sporcu.id
                egzersiz_plan_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").document(sporcu_id).collection("egzersiz_plan").add({
                    'egzersiz_adi': egzersiz_adi,
                    'set_sayisi': set_sayisi,
                    'tekrar_sayisi': tekrar_sayisi,
                    'hedef': hedef,
                    'video_path': 'uploads/' + filename,
                })

            return "Egzersiz planı başarıyla kaydedildi."

    # GET request'i ise egzersiz_plan_hazirla sayfasını render et
    return render_template('egzersiz_plan_hazirla.html')

@app.route('/beslenme_plan_hazirla', methods=['GET', 'POST'])
def beslenme_plan_hazirla():
    if request.method == 'POST':
        # Formdan gelen verileri al
        sporcu_eposta = request.form.get('sporcu_eposta')
        hedef = request.form.get('hedef')
        gunluk_ogunler = request.form.get('gunluk_ogunler')
        kalori_hedefi = request.form.get('kalori_hedefi')

        # Beslenme planını Firestore'a kaydet
        sporcu_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").where("eposta", "==", sporcu_eposta).get()

        for sporcu in sporcu_ref:
            sporcu_id = sporcu.id
            beslenme_plan_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").document(sporcu_id).collection("beslenme_plan").add({
                'hedef': hedef,
                'gunluk_ogunler': gunluk_ogunler,
                'kalori_hedefi': kalori_hedefi,
            })

        return "Beslenme planı başarıyla kaydedildi."

    # GET request'i ise beslenme_plan_hazirla sayfasını render et
    return render_template('beslenme_plan_hazirla.html')

@app.route('/antrenor_ilerleme_kayitlari', methods=['GET', 'POST'])
def antrenor_ilerleme_kayitlari():
    if request.method == 'POST':
        sporcu_eposta = request.form.get('sporcu_eposta', '')
        return redirect(url_for('ilerleme_kayitlari', sporcu_eposta=sporcu_eposta))

    # Eğer başka bir HTTP methodu kullanıldıysa burada ilgili işlemleri yapabilirsin.
    return render_template('antrenor_ilerleme_kayitlari.html')

@app.route('/ilerleme_kayitlari/<sporcu_eposta>', methods=['GET'])
def ilerleme_kayitlari(sporcu_eposta):
    # HLP2 koleksiyonunda bulunan sporcular dokümanındaki kullanıcılar koleksiyonundan sporcunun bilgilerini çek
    sporcu_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").where("eposta", "==", sporcu_eposta).get()
    # Eğer sporcu bulunamadıysa, hata mesajı döndür
    if not sporcu_ref:
        return "Sporcu Bulunamadı!"

    # Sporcu belgesini al
    sporcu_belgesi = sporcu_ref[0].reference

    # Sporcunun ilerleme kayıtlarını içeren koleksiyonu al
    ilerleme_kayitlari_ref = sporcu_belgesi.collection("ilerleme").stream()

    # İlerleme kayıtlarını bir liste olarak hazırla
    ilerleme_kayitlari = [kayit.to_dict() for kayit in ilerleme_kayitlari_ref]

    return render_template('ilerleme_kayitlari.html', sporcu_eposta=sporcu_eposta, ilerleme_kayitlari=ilerleme_kayitlari)

@app.route('/sporcu_sayfasi', methods=['GET', 'POST'])
def sporcu_sayfasi():
    # E-posta adresini al
    eposta = request.args.get('eposta', '')
    # Kullanıcı bilgilerini veritabanından çek
    kullanici_koleksiyonu = db.collection("HLP2").document("sporcu").collection("kullanicilar")
    kullanici_sorgu = kullanici_koleksiyonu.where('eposta', '==', eposta).stream()

    if not kullanici_sorgu:
        return "Sporcu Bulunamadı!"

    # Sporcu bilgilerini al
    for doc in kullanici_sorgu:
        kullanici_bilgisi = doc.to_dict()
        isim = kullanici_bilgisi['isim']
        soyisim = kullanici_bilgisi['soyisim']
        telefon = kullanici_bilgisi['telefon']
        profil_fotografi = kullanici_bilgisi['profil_fotografi']

    if request.method == 'POST':
        if 'antrenor_sec_form' in request.form:
            return redirect(url_for('sporcu_antrenor_sec', eposta=eposta))

        # Egzersiz Planları Formu
        elif 'egzersiz_planlari_form' in request.form:
            # Egzersiz planları işlemleri buraya gelecek
            return redirect(url_for('sporcu_egzersiz_planlar', eposta=eposta))

        # Beslenme Planları Formu
        elif 'beslenme_planlari_form' in request.form:
            # Beslenme planları işlemleri buraya gelecek
            return redirect(url_for('sporcu_beslenme_planlar', eposta=eposta))

        # İlerleme Kayıt Formu
        elif 'ilerleme_kayit_form' in request.form:
            return redirect(url_for('ilerleme_kayit', eposta=eposta))

        # Mesajlaşma Formu
        elif 'sporcu_mesajlasma_form' in request.form:
            return redirect(url_for('sporcu_mesajlasma', eposta=eposta))

        # Gelen Mesajlar Formu
        elif 'sporcu_gelen_mesajlar_form' in request.form:
            return redirect(url_for('sporcu_gelen_mesajlar', eposta=eposta))



    # Kullanıcı bilgilerini template'e geçir
    return render_template('sporcu_sayfasi.html', isim=isim, soyisim=soyisim, eposta=eposta, telefon=telefon, profil_fotografi=profil_fotografi)

@app.route('/ilerleme_kayit', methods=['GET', 'POST'])
def ilerleme_kayit():
    sporcu_eposta = request.args.get('eposta', '')

    if request.method == 'POST':
        kilo = request.form.get('kilo')
        boy = request.form.get('boy')
        kas_orani = request.form.get('kas_orani')
        yag_orani = request.form.get('yag_orani')
        bki = request.form.get('bki')
        resim = request.files['resim']

        # Sporcunun belgesini bul
        sporcu_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").where("eposta", "==", sporcu_eposta).stream()
        # Eğer sporcu bulunamadıysa, hata mesajı döndür
        if not sporcu_ref:
            return "Sporcu Bulunamadı!"
        if resim and allowed_file(resim.filename):
            # Güvenli dosya adını oluştur
            filename = secure_filename(resim.filename)
            resim.save(os.path.join(uploads_dir, filename))

        # Sporcunun belgesini al
        sporcu_belgesi = next(sporcu_ref).reference
        # İlerleme kaydını sporcunun belgesinin içine ekle
        ilerleme_kayit_ref = sporcu_belgesi.collection("ilerleme").add({
            'kilo': kilo,
            'boy': boy,
            'kas_orani': kas_orani,
            'yag_orani': yag_orani,
            'bki': bki,
            'resim': 'uploads/' + filename,
            'tarih': firestore.SERVER_TIMESTAMP
        })

        return f"Ilerleme kaydedildi: {ilerleme_kayit_ref[1].id}"

    return render_template('ilerleme_kayit.html', sporcu_eposta=sporcu_eposta)


@app.route('/sporcu_egzersiz_planlar', methods=['GET', 'POST'])
def sporcu_egzersiz_planlar():
    sporcu_eposta = request.args.get('eposta', '')
    if request.method == 'GET':
        # Firestore'dan sporcu bilgilerini çek
        sporcu_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").where("eposta", "==", sporcu_eposta).get()

        for sporcu in sporcu_ref:
            sporcu_id = sporcu.id
            egzersiz_planlari_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").document(sporcu_id).collection("egzersiz_plan").stream()

            # Egzersiz planlarını liste olarak al
            egzersiz_planlari = [egzersiz.to_dict() for egzersiz in egzersiz_planlari_ref]

        return render_template('sporcu_egzersiz_planlar.html', egzersiz_planlari=egzersiz_planlari)


@app.route('/sporcu_beslenme_planlar', methods=['GET'])
def sporcu_beslenme_planlar():
    sporcu_eposta = request.args.get('eposta', '')

    if request.method == 'GET':
        # Firestore'dan sporcu bilgilerini çek
        sporcu_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").where("eposta", "==", sporcu_eposta).get()

        for sporcu in sporcu_ref:
            sporcu_id = sporcu.id
            beslenme_planlari_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").document(sporcu_id).collection("beslenme_plan").stream()

            # Beslenme planlarını liste olarak al
            beslenme_planlari = [beslenme_plan.to_dict() for beslenme_plan in beslenme_planlari_ref]

        return render_template('sporcu_beslenme_planlar.html', beslenme_planlari=beslenme_planlari)


@app.route('/sporcu_antrenor_sec', methods=['GET', 'POST'])
def sporcu_antrenor_sec():
    antrenor_listesi = []
    antrenor_id = request.form.get('antrenor_sec', '')
    sporcu_eposta = request.args.get('eposta', '')
    if request.method == 'POST':
        # Antrenor seçildikten sonra antrenor_sporcular koleksiyonuna doc ekle
        antrenor_ref = db.collection("HLP2").document("antrenor").collection("kullanicilar").document(antrenor_id)
        antrenor_sporcular_ref = antrenor_ref.collection("antrenor_sporcular").add({
            'sporcu_eposta': sporcu_eposta,
        })

        return f"Antrenör seçildi: {antrenor_ref.get().to_dict()['isim']} {antrenor_ref.get().to_dict()['soyisim']}"

    else:
        # Tüm antrenörleri getir
        antrenorler = db.collection("HLP2").document("antrenor").collection("kullanicilar").stream()
        for antrenor in antrenorler:
            antrenor_data = antrenor.to_dict()
            antrenor_listesi.append({
                'id': antrenor.id,
                'isim': antrenor_data.get('isim'),
                'soyisim': antrenor_data.get('soyisim'),
            })

        return render_template('sporcu_antrenor_sec.html', antrenor_listesi=antrenor_listesi,eposta=sporcu_eposta)


@app.route('/sporcu_mesajlasma', methods=['GET', 'POST'])
def sporcu_mesajlasma():
    gonderen_eposta = None
    eposta = request.args.get('eposta', '')

    if request.method == 'POST':
        alici_eposta = request.form['alici_eposta']
        icerik = request.form['icerik']
        gonderen_eposta = request.form['gonderen_eposta']  # Hidden input'tan değeri al

        antrenor_ref = db.collection("HLP2").document("antrenor").collection("kullanicilar").where("eposta", "==",alici_eposta).limit(1).stream()
        antrenor_ref = list(antrenor_ref)
        if not antrenor_ref:
            return "Antrenör Bulunamadı!"
        antrenor_ref = antrenor_ref[0]

        sporcu_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").where("eposta", "==",gonderen_eposta).limit(1).stream()

        sporcu_ref = list(sporcu_ref)
        if not sporcu_ref:
            return "Sporcu Bulunamadı!"
        sporcu_ref = sporcu_ref[0]

        mesaj_belgesi = db.collection("HLP2").document("mesajlar").collection("mesajlar").add({
            'gonderen_eposta': sporcu_ref.reference,
            'alici_eposta': antrenor_ref.reference,
            'icerik': icerik,
            'tarih': SERVER_TIMESTAMP
        })
        return redirect(url_for('sporcu_mesajlasma', eposta=eposta))

    return render_template('sporcu_mesajlasma.html', eposta=eposta)



@app.route('/sporcu_gelen_mesajlar', methods=['GET', 'POST'])
def sporcu_gelen_mesajlar():
    if request.method == 'POST':
        return redirect(url_for('sporcu_gelen_mesajlar'))

    # Eposta bilgisini al
    eposta = request.args.get('eposta', '')

    gelen_mesajlar = []
    sporcu_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").where("eposta", "==", eposta).limit(1).stream()
    sporcu_ref = list(sporcu_ref)
    if not sporcu_ref:
        return "Sporcu Bulunamadı!"
    sporcu_ref = sporcu_ref[0]

    sporcu_mesajlar = db.collection("HLP2").document("mesajlar").collection("mesajlar").where('alici_eposta', '==', sporcu_ref.reference).stream()
    for doc in sporcu_mesajlar:
        mesaj = doc.to_dict()

        # Referansları çözme
        gonderen_ref = mesaj.get('gonderen_eposta')
        alici_ref = mesaj.get('alici_eposta')

        # Referanslardan kullanıcı verilerini al
        gonderen_data = get_user_data_from_reference(gonderen_ref)
        alici_data = get_user_data_from_reference(alici_ref)

        # Kullanıcı verilerini mesajlara ekle
        mesaj['gonderen_eposta'] = gonderen_data.get('eposta') if gonderen_data else None
        mesaj['alici_eposta'] = alici_data.get('eposta') if alici_data else None

        gelen_mesajlar.append(mesaj)

    gelen_mesajlar.sort(key=lambda x: x.get('tarih'), reverse=True)

    return render_template('sporcu_gelen_mesajlar.html', gelen_mesajlar=gelen_mesajlar, eposta=eposta)


@app.route('/yonetici_sayfasi', methods=['GET', 'POST'])
def yonetici_sayfasi():
    # E-posta adresini al
    eposta = request.args.get('eposta', '')

    # Yönetici bilgilerini veritabanından çek
    kullanici_koleksiyonu = db.collection("HLP2").document("yonetici").collection("kullanicilar")
    kullanici_sorgu = kullanici_koleksiyonu.where('eposta', '==', eposta).stream()

    if not kullanici_sorgu:
        return "Yönetici Bulunamadı!"

    # Yönetici bilgilerini al
    for doc in kullanici_sorgu:
        kullanici_bilgisi = doc.to_dict()
        isim = kullanici_bilgisi['isim']
        soyisim = kullanici_bilgisi['soyisim']
        telefon = kullanici_bilgisi['telefon']
        profil_fotografi = kullanici_bilgisi['profil_fotografi']

    if request.method == 'POST':
        # Yönlendirme yapılacak butonlara göre
        if 'yonetici_antrenor_hesaplari_form' in request.form:
            return redirect(url_for('yonetici_antrenor_hesaplari'))

        elif 'yonetici_sporcu_hesaplari_form' in request.form:
            return redirect(url_for('yonetici_sporcu_hesaplari'))

        elif 'hesap_durumu_form' in request.form:
            return redirect(url_for('yonetici_hesaplar'))


    return render_template('yonetici_sayfasi.html', isim=isim, soyisim=soyisim, telefon=telefon, eposta=eposta, profil_fotografi=profil_fotografi)


@app.route('/yonetici_hesaplar', methods=['GET', 'POST'])
def yonetici_hesaplar():
    antrenor_bilgileri = []
    antrenorler_ref = db.collection("HLP2").document("antrenor").collection("kullanicilar").stream()

    sporcu_bilgileri = []
    sporcular_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").stream()

    for antrenor in antrenorler_ref:
        antrenor_data = antrenor.to_dict()
        antrenor_bilgileri.append({
            'isim': antrenor_data['isim'],
            'soyisim': antrenor_data['soyisim'],
            'aktif': antrenor_data['aktif']
        })

    for sporcu in sporcular_ref:
        sporcu_data = sporcu.to_dict()
        sporcu_bilgileri.append({
            'isim': sporcu_data['isim'],
            'soyisim': sporcu_data['soyisim'],
            'aktif': sporcu_data['aktif']
        })

    if request.method == 'POST':
        for antrenor in antrenor_bilgileri:
            antrenor_isim = antrenor['isim']
            antrenor_soyisim = antrenor['soyisim']
            antrenor_aktif = request.form.get(f'antrenor_{antrenor_isim}')

            # Antrenör belgesini güncelle
            antrenor_ref = db.collection("HLP2").document("antrenor").collection("kullanicilar").where('isim', '==',
                                                                                                       antrenor_isim).where(
                'soyisim', '==', antrenor_soyisim)

            for doc in antrenor_ref.stream():
                doc.reference.update({'aktif': antrenor_aktif == 'on'})

        for sporcu in sporcu_bilgileri:
            sporcu_isim = sporcu['isim']
            sporcu_soyisim = sporcu['soyisim']
            sporcu_aktif = request.form.get(f'sporcu_{sporcu_isim}')

            # Sporcu belgesini güncelle
            sporcu_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").where('isim', '==',
                                                                                                   sporcu_isim).where(
                'soyisim', '==', sporcu_soyisim)

            for doc in sporcu_ref.stream():
                doc.reference.update({'aktif': sporcu_aktif == 'on'})

    return render_template('yonetici_hesaplar.html', antrenor_bilgileri=antrenor_bilgileri,
                           sporcu_bilgileri=sporcu_bilgileri)


@app.route('/yonetici_antrenor_hesaplari', methods=['GET', 'POST'])
def yonetici_antrenor_hesaplari():
    # Firestore bağlantısını oluştur
    db = firestore.Client()

    # Antrenörlerin bilgilerini Firestore'dan al
    antrenor_bilgileri = []
    antrenorler_ref = db.collection("HLP2").document("antrenor").collection("kullanicilar").stream()

    for antrenor in antrenorler_ref:
        antrenor_data = antrenor.to_dict()

        # Antrenörün deneyimlerini Firestore'dan al
        deneyimler_ref = antrenor.reference.collection("deneyimler").stream()
        antrenor_data['deneyimler'] = [{'tecrube_yili': deneyim.get('tecrube_yili'), 'deneyimler': deneyim.get('deneyimler'), 'tarih': deneyim.get('tarih')} for deneyim in deneyimler_ref]

        # Antrenöre atanmış sporcuların epostalarını Firestore'dan al
        sporcular_ref = antrenor.reference.collection("antrenor_sporcular").stream()
        antrenor_data['sporcular'] = [{'sporcu_eposta': sporcu.get('sporcu_eposta')} for sporcu in sporcular_ref]

        antrenor_bilgileri.append(antrenor_data)

    return render_template('yonetici_antrenor_hesaplari.html', antrenor_bilgileri=antrenor_bilgileri)

@app.route('/yonetici_sporcu_hesaplari', methods=['GET', 'POST'])
def yonetici_sporcu_hesaplari():
    # Firestore bağlantısını oluştur
    db = firestore.Client()

    # Sporcuların bilgilerini Firestore'dan al
    sporcu_bilgileri = []
    sporcular_ref = db.collection("HLP2").document("sporcu").collection("kullanicilar").stream()

    for sporcu in sporcular_ref:
        sporcu_data = sporcu.to_dict()

        # Sporcunun beslenme planını Firestore'dan al
        beslenme_plan_ref = sporcu.reference.collection("beslenme_plan").stream()
        sporcu_data['beslenme_plan'] = [{'gunluk_ogunler': beslenme_plan.get('gunluk_ogunler'), 'hedef': beslenme_plan.get('hedef'), 'kalori_hedefi': beslenme_plan.get('kalori_hedefi')} for beslenme_plan in beslenme_plan_ref]

        # Sporcunun egzersiz planını Firestore'dan al
        egzersiz_plan_ref = sporcu.reference.collection("egzersiz_plan").stream()
        sporcu_data['egzersiz_plan'] = [{'egzersiz_adi': egzersiz_plan.get('egzersiz_adi'), 'hedef': egzersiz_plan.get('hedef'), 'set_sayisi': egzersiz_plan.get('set_sayisi'), 'tekrar_sayisi': egzersiz_plan.get('tekrar_sayisi'), 'video_path': egzersiz_plan.get('video_path')} for egzersiz_plan in egzersiz_plan_ref]

        # Sporcunun ilerleme kayıtlarını Firestore'dan al
        ilerleme_ref = sporcu.reference.collection("ilerleme").stream()
        sporcu_data['ilerleme'] = [{'bki': ilerleme.get('bki'), 'boy': ilerleme.get('boy'), 'kas_orani': ilerleme.get('kas_orani'), 'kilo': ilerleme.get('kilo'), 'resim': ilerleme.get('resim'), 'tarih': ilerleme.get('tarih'), 'yag_orani': ilerleme.get('yag_orani')} for ilerleme in ilerleme_ref]

        sporcu_bilgileri.append(sporcu_data)

    return render_template('yonetici_sporcu_hesaplari.html', sporcu_bilgileri=sporcu_bilgileri)


if __name__ == '__main__':
    app.run(debug=True)
