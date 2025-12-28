#!/usr/bin/env python3
"""
Скрипт для получения user_id и списка хостов из Яндекс.Вебмастера.
"""

import os
import json
from dotenv import load_dotenv
from app.ym_webmaster_client import YMWebmasterClient

load_dotenv()

token = os.getenv("YM_WEBMASTER_TOKEN")
if not token:
    print("❌ Ошибка: YM_WEBMASTER_TOKEN не найден в .env")
    exit(1)

print("🔍 Получаю информацию о пользователе и хостах...\n")

try:
    # Шаг 1: Получаем user_id
    user_response = YMWebmasterClient.list_hosts(token)
    user_id = user_response.get("user_id")
    print(f"✅ USER_ID: {user_id}\n")
    
    # Шаг 2: Получаем список хостов
    from app.http_client import get_default_session
    session = get_default_session()
    hosts_url = f"https://api.webmaster.yandex.net/v4/user/{user_id}/hosts"
    hosts_response = session.get(hosts_url, headers={"Authorization": f"OAuth {token}"})
    
    if hosts_response.status_code >= 400:
        print(f"❌ Ошибка получения хостов: {hosts_response.status_code}")
        print(hosts_response.text[:500])
        exit(1)
    
    hosts_data = hosts_response.json()
    hosts = hosts_data.get("hosts", [])
    print(f"📋 Найдено хостов: {len(hosts)}\n")
    
    print("=" * 80)
    print(f"{'HOST_ID':<35} {'URL':<35} {'VERIFIED'}")
    print("=" * 80)
    
    for host in hosts:
        host_id = host.get("host_id", "N/A")
        url = host.get("unicode_host_url", "N/A")
        verified = "✅" if host.get("verified") else "❌"
        print(f"{host_id:<35} {url:<35} {verified}")
    
    print("=" * 80)
    print()
    
    # Ищем makevibe.ru
    makevibe_hosts = [h for h in hosts if "makevibe" in h.get("unicode_host_url", "").lower()]
    
    if makevibe_hosts:
        print("🎯 Найдены хосты для makevibe.ru:")
        print()
        for host in makevibe_hosts:
            host_id = host.get("host_id")
            url = host.get("unicode_host_url")
            verified = "✅ Verified" if host.get("verified") else "❌ Not verified"
            print(f"  Host ID: {host_id}")
            print(f"  URL: {url}")
            print(f"  Status: {verified}")
            print()
        
        # Берем первый verified хост (или любой, если verified нет)
        preferred_host = next((h for h in makevibe_hosts if h.get("verified")), makevibe_hosts[0])
        
        print("📝 Добавьте в clients/makevibe/config.yaml:")
        print()
        print("ym_webmaster:")
        print(f"  user_id: {user_id}")
        print(f"  host_id: \"{preferred_host.get('host_id')}\"")
        print()
    else:
        print("⚠️  makevibe.ru не найден в списке хостов")
        print("   Убедитесь, что сайт добавлен в Яндекс.Вебмастер")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

