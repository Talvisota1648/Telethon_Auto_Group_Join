from telethon import TelegramClient
import asyncio

# ВАЖНО: Замените на ваши данные
API_ID = '33916449'  # Замените на ваш API ID
API_HASH = '9ec8439ac26f8e1ab2f0796890009f52'  # Замените на ваш API HASH

async def create_session():
    """Создание новой сессии Telegram"""
    print("="*50)
    print("Создание новой Telegram сессии")
    print("="*50)

    session_name = input("\nВведите имя сессии (например: account1): ").strip()

    if not session_name:
        print("Ошибка: Имя сессии не может быть пустым")
        return

    # Опционально: настройка прокси
    use_proxy = input("\nИспользовать прокси? (y/n): ").lower() == 'y'

    proxy = None
    if use_proxy:
        proxy_host = input("IP прокси: ")
        proxy_port = int(input("Порт прокси: "))
        proxy_user = input("Логин (Enter если нет): ")
        proxy_pass = input("Пароль (Enter если нет): ")

        proxy = {
            'proxy_type': 'socks5',
            'addr': proxy_host,
            'port': proxy_port,
            'rdns': True
        }

        if proxy_user:
            proxy['username'] = proxy_user
            proxy['password'] = proxy_pass

    try:
        client = TelegramClient(session_name, API_ID, API_HASH, proxy=proxy)

        print("\nПодключение к Telegram...")
        await client.start()

        me = await client.get_me()
        print(f"\n✓ Успешно авторизован как: {me.first_name}")
        print(f"  Телефон: {me.phone if me.phone else 'Не указан'}")
        print(f"  Username: @{me.username if me.username else 'Не указан'}")
        print(f"\n✓ Файл сессии создан: {session_name}.session")

        await client.disconnect()

    except Exception as e:
        print(f"\n✗ Ошибка: {e}")

if __name__ == '__main__':
    asyncio.run(create_session())
