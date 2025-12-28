#!/usr/bin/env python3
"""
Скрипт для получения Google Search Console refresh_token через OAuth 2.0.

Использование:
    python3 scripts/get_gsc_refresh_token.py

Требования:
    - Google Cloud Project с включенным Search Console API
    - OAuth 2.0 credentials (Desktop app)
"""

import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import requests

# Конфигурация
CLIENT_ID = input("Введите CLIENT_ID из Google Cloud Console: ").strip()
CLIENT_SECRET = input("Введите CLIENT_SECRET из Google Cloud Console: ").strip()

# OAuth endpoints
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REDIRECT_URI = "http://localhost:8080"
SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"

# Глобальная переменная для хранения authorization code
auth_code = None


class OAuthHandler(BaseHTTPRequestHandler):
    """HTTP handler для получения authorization code"""
    
    def do_GET(self):
        global auth_code
        
        # Парсим query parameters
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'code' in params:
            auth_code = params['code'][0]
            
            # Отправляем успешный ответ в браузер
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b"""
            <html>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: green;">✅ Авторизация успешна!</h1>
                <p>Можете закрыть это окно и вернуться в терминал.</p>
            </body>
            </html>
            """)
        else:
            # Ошибка авторизации
            self.send_response(400)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            error = params.get('error', ['Unknown'])[0]
            self.wfile.write(f"""
            <html>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: red;">❌ Ошибка авторизации</h1>
                <p>Error: {error}</p>
            </body>
            </html>
            """.encode())
    
    def log_message(self, format, *args):
        # Отключаем логи HTTP сервера
        pass


def get_authorization_code():
    """Открывает браузер для OAuth авторизации и получает authorization code"""
    
    # Формируем URL для авторизации
    auth_params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE,
        'response_type': 'code',
        'access_type': 'offline',  # Важно для получения refresh_token
        'prompt': 'consent',  # Форсируем показ consent screen
    }
    
    auth_url_full = f"{AUTH_URL}?" + "&".join(f"{k}={v}" for k, v in auth_params.items())
    
    print("\n📝 ШАГ 1: Авторизация в Google")
    print("=" * 60)
    print(f"Открываю браузер для авторизации...")
    print(f"Если браузер не открылся, скопируйте эту ссылку:")
    print(f"\n{auth_url_full}\n")
    
    # Открываем браузер
    webbrowser.open(auth_url_full)
    
    # Запускаем локальный сервер для получения callback
    print("⏳ Ожидаю авторизации...")
    print("(После авторизации в браузере вернитесь сюда)\n")
    
    server = HTTPServer(('localhost', 8080), OAuthHandler)
    server.handle_request()  # Обрабатываем один запрос
    
    return auth_code


def exchange_code_for_tokens(code):
    """Обменивает authorization code на access_token и refresh_token"""
    
    print("\n🔄 ШАГ 2: Получение токенов")
    print("=" * 60)
    
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
    }
    
    response = requests.post(TOKEN_URL, data=data)
    
    if response.status_code != 200:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text)
        return None
    
    tokens = response.json()
    return tokens


def main():
    print("=" * 60)
    print("🔐 Google Search Console OAuth 2.0 Setup")
    print("=" * 60)
    print()
    print("Этот скрипт поможет получить refresh_token для GSC API.")
    print()
    print("📋 Требования:")
    print("  1. Google Cloud Project с включенным Search Console API")
    print("  2. OAuth 2.0 credentials (тип: Desktop app)")
    print("  3. Redirect URI: http://localhost:8080")
    print()
    print("Если у вас нет credentials, создайте их здесь:")
    print("https://console.cloud.google.com/apis/credentials")
    print()
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ CLIENT_ID и CLIENT_SECRET обязательны!")
        return
    
    # Получаем authorization code
    code = get_authorization_code()
    
    if not code:
        print("❌ Не удалось получить authorization code")
        return
    
    print("✅ Authorization code получен!")
    
    # Обмениваем code на токены
    tokens = exchange_code_for_tokens(code)
    
    if not tokens:
        print("❌ Не удалось получить токены")
        return
    
    # Выводим результаты
    print("\n✅ Токены успешно получены!")
    print("=" * 60)
    print()
    print("📝 Добавьте эти строки в ваш .env файл:")
    print()
    print(f"GSC_CLIENT_ID={CLIENT_ID}")
    print(f"GSC_CLIENT_SECRET={CLIENT_SECRET}")
    print(f"GSC_REFRESH_TOKEN={tokens.get('refresh_token', 'NOT_FOUND')}")
    print()
    print("=" * 60)
    print()
    
    # Сохраняем в файл для удобства
    output_file = "gsc_credentials.txt"
    with open(output_file, 'w') as f:
        f.write(f"GSC_CLIENT_ID={CLIENT_ID}\n")
        f.write(f"GSC_CLIENT_SECRET={CLIENT_SECRET}\n")
        f.write(f"GSC_REFRESH_TOKEN={tokens.get('refresh_token', 'NOT_FOUND')}\n")
    
    print(f"💾 Credentials также сохранены в файл: {output_file}")
    print()
    print("⚠️  ВАЖНО: Не коммитьте этот файл в git!")
    print("          Добавьте его в .gitignore")
    print()
    
    if 'refresh_token' not in tokens:
        print("⚠️  WARNING: refresh_token не был получен!")
        print("   Возможные причины:")
        print("   - Не установлен access_type=offline")
        print("   - Приложение уже было авторизовано ранее")
        print()
        print("   Решение: Отзовите доступ и попробуйте снова:")
        print("   https://myaccount.google.com/permissions")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

