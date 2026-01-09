import asyncio
import os
import glob
from pathlib import Path
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import GetDiscussionMessageRequest
import random
from datetime import datetime

# Конфигурация
API_ID = '33916449'  # Замените на ваш API ID
API_HASH = '9ec8439ac26f8e1ab2f0796890009f52'  # Замените на ваш API HASH

# Параметры
JOINS_PER_HOUR = 2
DELAY_BETWEEN_JOINS = 3600 / JOINS_PER_HOUR  # секунды


def load_proxies(filename='proxy.txt'):
    """Загрузка прокси из файла"""
    proxies = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Формат: login:password@ip:port
                try:
                    auth, address = line.split('@')
                    username, password = auth.split(':')
                    ip, port = address.split(':')
                    proxies.append({
                        'proxy_type': 'socks5',
                        'addr': ip,
                        'port': int(port),
                        'username': username,
                        'password': password,
                        'rdns': True
                    })
                except Exception as e:
                    print(f"Ошибка парсинга прокси {line}: {e}")
        print(f"Загружено {len(proxies)} прокси")
    except FileNotFoundError:
        print(f"Файл {filename} не найден")
    return proxies


def load_groups(filename='groups.txt'):
    """Загрузка ссылок на группы из файла"""
    groups = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and 't.me/' in line:
                    groups.append(line)
        print(f"Загружено {len(groups)} групп для вступления")
    except FileNotFoundError:
        print(f"Файл {filename} не найден")
    return groups


def get_session_files():
    """Получение всех .session файлов в текущей директории"""
    session_files = glob.glob('*.session')
    session_names = [os.path.splitext(f)[0] for f in session_files]
    print(f"Найдено {len(session_names)} сессий: {session_names}")
    return session_names


async def join_channel_with_discussion(client, channel_link, session_name):
    """Вступление в канал и его обсуждение"""
    try:
        # Извлекаем username канала из ссылки
        if 't.me/' in channel_link:
            channel_username = channel_link.split('t.me/')[-1].strip('/')
        else:
            channel_username = channel_link

        print(f"[{session_name}] Попытка вступить в: {channel_username}")

        # Получаем entity канала
        try:
            entity = await client.get_entity(channel_username)
        except Exception as e:
            print(f"[{session_name}] Ошибка получения entity для {channel_username}: {e}")
            return False

        # Вступаем в канал
        try:
            await client(JoinChannelRequest(entity))
            print(f"[{session_name}] ✓ Вступил в {channel_username}")
            await asyncio.sleep(random.uniform(2, 5))  # Случайная задержка
        except errors.ChannelsTooMuchError:
            print(f"[{session_name}] ✗ Превышен лимит каналов")
            return False
        except errors.ChannelPrivateError:
            print(f"[{session_name}] ✗ Канал приватный: {channel_username}")
            return False
        except errors.InviteRequestSentError:
            print(f"[{session_name}] ⚠ Отправлен запрос на вступление: {channel_username}")
        except errors.UserAlreadyParticipantError:
            print(f"[{session_name}] ⚠ Уже в канале: {channel_username}")
        except Exception as e:
            print(f"[{session_name}] Ошибка вступления в {channel_username}: {e}")
            return False

        # Попытка вступить в обсуждение (discussion group)
        try:
            full_channel = await client.get_entity(entity)
            if hasattr(full_channel, 'linked_chat_id') and full_channel.linked_chat_id:
                discussion_entity = await client.get_entity(full_channel.linked_chat_id)
                await client(JoinChannelRequest(discussion_entity))
                print(f"[{session_name}] ✓ Вступил в обсуждение канала {channel_username}")
        except Exception as e:
            print(f"[{session_name}] Обсуждение недоступно или ошибка: {e}")

        return True

    except Exception as e:
        print(f"[{session_name}] Общая ошибка для {channel_link}: {e}")
        return False


async def process_session(session_name, proxy, groups):
    """Обработка одной сессии"""
    try:
        # Создаем клиента с прокси
        if proxy:
            print(f"[{session_name}] Подключение через прокси: {proxy['addr']}:{proxy['port']}")
            client = TelegramClient(session_name, API_ID, API_HASH, proxy=proxy)
        else:
            print(f"[{session_name}] Подключение без прокси")
            client = TelegramClient(session_name, API_ID, API_HASH)

        await client.connect()

        if not await client.is_user_authorized():
            print(f"[{session_name}] ✗ Сессия не авторизована")
            await client.disconnect()
            return

        me = await client.get_me()
        print(f"[{session_name}] ✓ Подключен: {me.first_name} ({me.phone if me.phone else 'No phone'})")

        # Обрабатываем группы с ограничением скорости
        groups_joined = 0
        for i, group in enumerate(groups):
            if groups_joined >= len(groups):
                break

            success = await join_channel_with_discussion(client, group, session_name)

            if success:
                groups_joined += 1

            # Задержка между вступлениями (2 в час)
            if groups_joined < len(groups):
                delay = DELAY_BETWEEN_JOINS + random.uniform(-60, 60)  # Добавляем случайность
                print(f"[{session_name}] Ожидание {delay/60:.1f} минут до следующего вступления...")
                await asyncio.sleep(delay)

        print(f"[{session_name}] Завершено. Вступил в {groups_joined} групп(ы)")
        await client.disconnect()

    except Exception as e:
        print(f"[{session_name}] Критическая ошибка: {e}")
        try:
            await client.disconnect()
        except:
            pass


async def main():
    """Главная функция"""
    print("="*60)
    print("Telegram Auto-Joiner")
    print("="*60)

    # Загружаем данные
    proxies = load_proxies('proxy.txt')
    groups = load_groups('groups.txt')
    sessions = get_session_files()

    if not sessions:
        print("\n✗ Не найдено .session файлов!")
        return

    if not groups:
        print("\n✗ Не найдено групп в groups.txt!")
        return

    # Распределяем прокси по сессиям
    tasks = []
    for i, session_name in enumerate(sessions):
        proxy = proxies[i % len(proxies)] if proxies else None
        tasks.append(process_session(session_name, proxy, groups))

    # Запускаем все сессии параллельно
    print(f"\n{'='*60}")
    print(f"Запуск {len(tasks)} сессий параллельно...")
    print(f"{'='*60}\n")

    await asyncio.gather(*tasks)

    print(f"\n{'='*60}")
    print("Все сессии завершены!")
    print(f"{'='*60}")


if __name__ == '__main__':
    # Запуск программы
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nПрограмма остановлена пользователем")
