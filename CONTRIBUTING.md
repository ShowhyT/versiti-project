# Contributing to Versiti

## Быстрый старт

### 1. Fork и клонирование

```bash
git clone https://github.com/YOUR_USERNAME/versiti-project.git
cd versiti-project
```

### 2. Локальный запуск

```bash
# Backend
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
pip install aiosqlite

cp .env.example .env
# Заполни JWT_SECRET, SESSION_KEYS в .env

python -c "from backend.database import init_db; import asyncio; asyncio.run(init_db())"
python -m backend.main
```

```bash
# Frontend (отдельный терминал)
npm install
npm run dev
```

## Pull Request

1. Создай ветку от `main`:
   ```bash
   git checkout -b fix/description
   # или
   git checkout -b feat/description
   ```
2. Внеси изменения
3. Убедись что фронтенд собирается: `npm run build`
4. Убедись что нет TypeScript ошибок: `npx tsc --noEmit`
5. Запушь ветку и открой PR на GitHub

## Соглашения

- **Коммиты:** `feat:`, `fix:`, `chore:`, `docs:` префиксы
- **Python:** async/await, SQLAlchemy ORM, следуй существующему стилю
- **TypeScript:** strict mode, функциональные компоненты, хуки
- **Стили:** Tailwind CSS, без inline-стилей
- **Секреты:** никогда не коммить `.env`, токены, пароли

## Структура фронтенда

```
src/
├── App.tsx                    — корневой компонент с роутингом
├── main.tsx                   — entry point
├── index.css                  — Tailwind theme
├── components/
│   └── TabBar.tsx             — нижняя навигация
├── pages/                     — экраны приложения
│   ├── LoginPage.tsx
│   ├── HomePage.tsx
│   ├── SchedulePage.tsx
│   ├── GradesPage.tsx
│   ├── PassesPage.tsx
│   ├── EsportsPage.tsx
│   ├── MapsPage.tsx
│   ├── ProfilePage.tsx
│   ├── FriendsPage.tsx
│   └── PrivacyPage.tsx
├── hooks/                     — кастомные хуки
│   └── useSchedule.ts
└── lib/
    ├── api.ts                 — HTTP клиент с JWT
    ├── motion.ts              — Framer Motion пресеты
    └── types.ts               — TypeScript типы
```

## Структура бэкенда

```
backend/
├── main.py                    — aiohttp entry point
├── config.py                  — pydantic settings
├── api/
│   ├── routes.py              — регистрация роутов
│   ├── auth.py                — логин/2FA/MIREA connect
│   ├── friends.py             — система друзей
│   ├── schedule.py            — расписание
│   ├── grades.py              — БРС
│   ├── acs.py                 — события турникетов
│   ├── esports.py             — киберзона
│   ├── attendance.py          — отметка посещаемости
│   └── common.py              — require_user, общие утилиты
├── services/
│   ├── mirea_auth.py          — Keycloak SSO
│   ├── mirea_api.py           — pulse API
│   ├── mirea_grades.py        — парсинг БРС
│   ├── mirea_acs.py           — парсинг ACS
│   ├── crypto.py              — шифрование сессий (Fernet)
│   ├── jwt_auth.py            — JWT creation/verification
│   └── api_middlewares.py     — rate limiting, error handling
└── database/
    ├── models.py              — SQLAlchemy модели
    └── migrations.py          — версии схемы БД
```

## Что можно улучшить

- Поддержка других университетов (не только МИРЭА)
- Интерактивные карты корпусов
- Push-уведомления (PWA)
- Темы оформления
- Docker Compose для локальной разработки
- Тесты для frontend (Vitest + Testing Library)

## Безопасность

Не создавай публичный issue для уязвимостей — напиши напрямую на email в профиле GitHub.
