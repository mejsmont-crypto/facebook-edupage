# Automatyczne aktualności Facebook → EduPage

Szkoła: https://www.facebook.com/zsdygowo

## Co robi system

GitHub Actions co godzinę odczytuje do 15 opublikowanych wpisów strony przez Meta Graph API, generuje `posts.json` i publikuje responsywną stronę na GitHub Pages. EduPage wyświetla ją przez **jeden stały IFRAME**. Żadnych tokenów w publicznym HTML.

**Ważne:** do działania konieczne są uprawnienia Meta i token strony. Nie da się zagwarantować dostępu do API bez właściwej konfiguracji konta/aplikacji. Zdjęcia pobierane z adresów Meta mogą wygasać; ponowna synchronizacja je odświeża. Filmy otwierają się przez link do oryginalnego posta.

## Krok 1. GitHub

1. Zaloguj się na https://github.com i utwórz **publiczne** repozytorium np. `facebook-edupage`.
2. Prześlij **zawartość** folderu z paczki, zachowując strukturę `.github/workflows/sync.yml`, `scripts/fetch.py`, `site/index.html` i `site/posts.json`. Najłatwiej przez `Add file → Upload files`, ale sprawdź, czy ukryty folder `.github` również trafił do repozytorium; w razie potrzeby utwórz go przez `Add file → Create new file` i wpisz ścieżkę `.github/workflows/sync.yml`.
3. W `Settings → Pages → Build and deployment → Source` wybierz **GitHub Actions**.

## Krok 2. Meta

1. Na https://developers.facebook.com/apps/ utwórz aplikację umożliwiającą dostęp do Pages API / Facebook Login (interfejs Meta może się zmieniać).
2. Jako administrator strony `zsdygowo` uzyskaj w Graph API Explorer token użytkownika z uprawnieniami `pages_show_list` i `pages_read_engagement`. Dla odczytu niektórych endpointów Meta może wymagać dodatkowo `pages_read_user_content`. Nie proś o uprawnienia do publikowania, jeśli nie są potrzebne.
3. W Graph API Explorer wywołaj `GET /me/accounts?fields=id,name,access_token` i znajdź szkołę. Zapisz jej **numeryczne ID** i **Page access token**. Nie kopiuj tokenu do plików repozytorium ani do EduPage.
4. Sprawdź `GET /{PAGE_ID}/published_posts?fields=id,message,created_time,permalink_url,full_picture&limit=3` z tokenem strony. Jeżeli zwraca błąd uprawnień, trzeba najpierw rozwiązać kwestię dostępu w Meta; GitHub nie ominie tej blokady.
5. Dla długotrwałego działania uzyskaj Page token na podstawie długoterminowego tokenu użytkownika lub prawidłowo skonfigurowanego system user, jeśli Meta udostępnia go dla tej strony. Token może zostać unieważniony; kontroluj błędy synchronizacji. Nie publikuj App Secret.

## Krok 3. GitHub Secrets i Variables

W repozytorium: `Settings → Secrets and variables → Actions`.

- `Secrets → New repository secret`: nazwa `FB_PAGE_TOKEN`, wartość: **Page access token**.
- `Variables → New repository variable`: nazwa `FB_PAGE_ID`, wartość: **numeryczne ID strony**.

Nie wklejaj tokenu do wiadomości, zgłoszeń, zrzutów ekranu ani publicznego kodu.

## Krok 4. Uruchom

W `Actions → Facebook – synchronizacja i publikacja → Run workflow` uruchom ręcznie. Poczekaj na zielony status. Potem `Settings → Pages` pokaże adres, zwykle `https://TWOJ_LOGIN.github.io/facebook-edupage/`.

Jeśli akcja zgłasza błąd Meta API, wejdź w log kroku „Pobierz wpisy z Meta Graph API”. **Nie przesyłaj tokenu**. Harmonogram działa co godzinę, ale GitHub może opóźnić zaplanowane uruchomienia. Nie jest to aktualizacja w czasie rzeczywistym.

## Krok 5. EduPage

Dodaj **osobny widżet tekstowy** pod istniejącym granatowym nagłówkiem. Wstaw **tylko jeden IFRAME** z pliku `EDUPAGE-IFRAME.txt`, po podmianie `TWOJ_LOGIN` na login GitHub (i ewentualnie nazwy repozytorium). Nie wklejaj HTML całego panelu. Jeśli edytor rozbije kod, użyj „Wstaw IFRAME” i wpisz sam adres strony GitHub Pages w polu URL. Szerokość: `100%` jeśli edytor akceptuje; w przeciwnym razie szerokość obszaru widżetu. Wysokość: 900 px na początek.

**Uwaga o wysokości:** IFRAME osadzony na innej domenie nie może automatycznie dopasować wysokości bez współpracy JavaScript po obu stronach. Dla wielu postów wybierz odpowiednio większą wysokość albo włącz przewijanie w IFRAME. W pliku przykładowym przewijanie jest włączone, aby nie ucinać wpisów.

## Bezpieczeństwo i ograniczenia

- Repozytorium i dane publikowane na Pages są publiczne. Publikuj wyłącznie treści przeznaczone do publicznego wyświetlania, zwłaszcza zdjęcia uczniów.
- Token tylko w GitHub Actions Secrets; Graph API jest wywoływany po stronie workflow, nie w przeglądarce.
- Niektóre typy postów i galerie mogą mieć ograniczone dane w API. Odnośnik „Zobacz pełny post” pozostaje dostępny.
- Jeśli aplikacja Meta jest w trybie developerskim, dostęp jest zwykle ograniczony do użytkowników z rolą w aplikacji. Uprawnienia i ewentualny App Review zależą od konfiguracji i zasad Meta.
- Przy błędzie pobierania workflow nie publikuje pustego panelu; poprzednia wersja GitHub Pages pozostaje dostępna.
- Nie ma opłat za typowe wykorzystanie publicznego repozytorium GitHub Pages i standardowych GitHub-hosted Actions w publicznym repo, z zastrzeżeniem aktualnych limitów usług.
