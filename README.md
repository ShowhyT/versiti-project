# Versiti

Веб-приложение для студентов МИРЭА — расписание, БРС, посещаемость, сканер QR, киберзона.

**Прод:** [versiti.ru](https://versiti.ru)

## Возможности

- **Сканер QR** — отметка посещаемости за себя и до 30 друзей
- **Расписание** — поиск по группе, преподавателю, аудитории
- **БРС** — баллы по дисциплинам, детальная посещаемость
- **Пропуск** — события входа/выхода через турникеты (ACS)
- **Киберзона** — бронирование места в компьютерном зале
- **Друзья** — поиск по университетскому email, совместная отметка

## Стек

- **Frontend:** React 19 + TypeScript + Vite + Tailwind CSS + Framer Motion
- **Backend:** Python 3.12, aiohttp, SQLAlchemy (async)
- **Database:** SQLite (по умолчанию) или PostgreSQL
- **Auth:** JWT (7 дней) + МИРЭА Keycloak SSO

## Структура

```
backend/           — Python API
├── api/           — endpoints (auth, grades, schedule, friends, acs, esports)
├── services/      — МИРЭА API, crypto, JWT
├── database/      — models, migrations
└── main.py

src/               — React frontend
├── pages/         — Login, Home, Schedule, Grades, Passes, Profile, Friends
├── components/    — TabBar
├── hooks/         — useSchedule
└── lib/           — api client, motion presets
```

---

## Self-hosting

### Требования

- Python 3.12+
- Node.js 20+
- Публичный HTTPS домен

### 1. Клонирование

```bash
git clone https://github.com/silverhans/versiti-project.git
cd versiti-project

python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
pip install aiosqlite
```

### 2. Конфигурация

```bash
cp .env.example .env
```

Минимальный `.env`:

```env
JWT_SECRET=$(openssl rand -hex 32)
WEBAPP_URL=https://your-domain.com
SESSION_KEYS=$(openssl rand -hex 32)
DATABASE_URL=sqlite+aiosqlite:///./data/versiti.db
API_PORT=8095
```

### 3. Инициализация БД

```bash
python -c "from backend.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 4. Сборка фронтенда

```bash
npm install
npm run build
```

Собранные файлы окажутся в `dist/`.

### 5. Запуск

```bash
python -m backend.main
```

API поднимется на `http://0.0.0.0:8095`.

---

## Nginx + SSL

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        root /path/to/versiti-project/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8095;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

SSL через Certbot:

```bash
certbot --nginx -d your-domain.com
```

---

## Systemd

```ini
# /etc/systemd/system/versiti.service
[Unit]
Description=Versiti API
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/versiti
ExecStart=/opt/versiti/venv/bin/python -m backend.main
EnvironmentFile=/opt/versiti/.env
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now versiti
```

---

## Безопасность

- Сессии МИРЭА хранятся в БД **в зашифрованном виде** (AES-256 Fernet)
- Пароль МИРЭА **не хранится** — используется только для получения cookies
- JWT токены действуют 7 дней, с поддержкой ревокации через `sessions_revoked_at`
- Поддержка ротации ключей шифрования

---

## Контрибьютинг

PR приветствуются. Перед отправкой:

1. Форкни репозиторий
2. Создай ветку: `git checkout -b feat/описание`
3. Убедись что билд проходит: `npm run build`
4. Убедись что TypeScript не ругается: `npx tsc --noEmit`
5. Отправь PR

### Соглашения

- **Коммиты:** `feat:`, `fix:`, `chore:`, `docs:` префиксы
- **Frontend:** компоненты в `src/components/`, страницы в `src/pages/`, хуки в `src/hooks/`
- **Backend:** следуй существующему стилю (async/await, SQLAlchemy ORM)
- **Секреты:** никогда не коммить `.env`, токены, пароли

## Уязвимости

Нашёл уязвимость? Создай issue с тегом `security` или напиши напрямую на email в профиле GitHub.

---

## Лицензия

[MIT](LICENSE) © silverhans
