# Fanvue Post Creator

Aplikacja Gradio do uploadowania postow na Fanvue z AI-generowanymi opisami.

## Funkcje

- Upload zdjec i wideo na Fanvue
- Generowanie opisow przez GPT-4o (z analiza obrazu)
- Rozne style opisow (Sexy & Flirty, Casual, Mysterious, Promotional, Custom)
- Wybor odbiorcow (publiczny, obserwujacy, subskrybenci)
- Podglad historii postow
- **AI Content Planner** - generowanie planu tresci na 7-30 dni z tematami sezonowymi
- Eksport planu do CSV
- Przeklikanie pomyslu bezposrednio do nowego posta

## Instalacja

```bash
# Klonuj lub przejdz do folderu
cd "D:\Dropbox\projekty claude\fanvue posty"

# Utworz venv (opcjonalnie)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Zainstaluj zależnosci
pip install -r requirements.txt
```

## Konfiguracja

### OpenAI API Key

Opcja 1 - przez plik .env:
```bash
cp .env.example .env
# Edytuj .env i wpisz klucz
```

Opcja 2 - przez interfejs:
- Uruchom aplikacje
- Przejdz do zakladki "Ustawienia"
- Wpisz klucz OpenAI

### Fanvue Token

Aby uzyskac token:

1. Zaloguj sie na [fanvue.com](https://fanvue.com)
2. Otworz DevTools przegladarki (F12)
3. Przejdz do Application -> Cookies -> fanvue.com
4. Znajdz `access_token` i skopiuj wartosc
5. Wklej w aplikacji w zakladce "Ustawienia"

Token jest zapisywany lokalnie w `.tokens.json`.

## Uruchomienie

```bash
python app.py
```

Aplikacja uruchomi sie na `http://localhost:7860`

## Uzycie

### 1. Zakladka "Ustawienia"
- Wklej Fanvue access token i kliknij "Zaloguj"
- Ustaw klucz OpenAI (jesli nie ma w .env)

### 2. Zakladka "Nowy Post"
1. Wybierz plik (zdjecie lub wideo)
2. Wybierz styl opisu
3. Kliknij "Generuj opis AI" lub wpisz wlasny
4. Wybierz odbiorcow
5. Kliknij "Opublikuj Post"

### 3. Zakladka "Pomysly na posty"
1. Opisz swoja nisze/styl (np. "glamour, lingerie, fitness")
2. Ustaw liczbe dni (7-30)
3. Zaznacz opcje: tematy sezonowe, pomysly PPV
4. Kliknij "Generuj plan tresci"
5. Przejrzyj tabele z pomyslami (typ, opis, caption, godzina, hashtagi)
6. "Eksportuj do CSV" - pobierz plan jako plik
7. "Uzyj tego pomyslu" - przenies caption do zakladki Nowy Post

### Style opisow

| Styl | Opis |
|------|------|
| Sexy & Flirty | Zalotny, kuszacy, ale ze smakiem |
| Casual & Fun | Swobodny, przyjazny |
| Mysterious | Tajemniczy, wzbudzajacy ciekawosc |
| Promotional | Promocyjny, zachecajacy do subskrypcji |
| Custom | Wlasny prompt |

## Struktura projektu

```
fanvue-posty/
├── app.py              # Glowna aplikacja Gradio
├── requirements.txt    # Zaleznosci Python
├── .env.example        # Przyklad konfiguracji
├── .env               # Twoja konfiguracja (nie commituj!)
├── .tokens.json       # Zapisane tokeny (nie commituj!)
├── pomysly/           # Eksportowane plany tresci (CSV)
└── README.md          # Ta dokumentacja
```

## API Fanvue

Aplikacja korzysta z:
- `POST /media/upload/multipart/create` - inicjalizacja uploadu
- `POST /media/upload/multipart/sign` - signed URL do S3
- `POST /media/upload/multipart/complete` - finalizacja
- `POST /creators/{uuid}/posts` - tworzenie posta
- `GET /creators/{uuid}/posts` - historia postow

## Troubleshooting

### "Blad autoryzacji 401"
- Token wygasl - pobierz nowy z przegladarki
- Sprawdz czy skopiowales caly token

### "Blad uploadu"
- Sprawdz polaczenie internetowe
- Plik moze byc za duzy (limit ~100MB)
- Nieobslugiwany format

### "Brak creator UUID"
- Upewnij sie ze masz konto creatora na Fanvue
- Sprawdz czy jestes zalogowany jako creator (nie agencja)

## Bezpieczenstwo

- Tokeny sa zapisywane lokalnie w `.tokens.json`
- NIE commituj `.env` ani `.tokens.json` do git
- Klucz OpenAI jest przechowywany tylko w pamieci lub .env
