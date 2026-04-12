import { motion } from 'framer-motion'
import { slideUp } from '../lib/motion'
import { ChevronLeft } from 'lucide-react'

interface Props {
  onClose: () => void
}

export default function PrivacyPage({ onClose }: Props) {
  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <motion.div variants={slideUp} initial="enter" animate="active" className="space-y-6">
        <div className="flex items-center gap-3">
          <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors">
            <ChevronLeft size={24} />
          </button>
          <h1 className="text-2xl font-semibold text-text-primary">Политика конфиденциальности</h1>
        </div>

        <div className="space-y-4 text-sm text-text-secondary leading-relaxed">
          <p className="text-xs text-text-muted">Дата вступления в силу: 12 апреля 2026 г.</p>

          <section className="space-y-2">
            <h2 className="text-base font-medium text-text-primary">1. Общие положения</h2>
            <p>
              Versiti (далее — «Сервис») — веб-приложение для студентов, предоставляющее
              доступ к расписанию, оценкам, посещаемости и другим сервисам МИРЭА.
              Настоящая политика описывает, какие данные мы собираем и как их используем.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-medium text-text-primary">2. Какие данные мы собираем</h2>
            <ul className="list-disc pl-5 space-y-1">
              <li>
                <strong>Учётные данные МИРЭА</strong> — логин и пароль передаются напрямую
                серверам lk.mirea.ru для получения сессии авторизации. Пароль не сохраняется
                на наших серверах.
              </li>
              <li>
                <strong>Сессия МИРЭА</strong> — полученные cookies хранятся в зашифрованном
                виде (AES-256) для выполнения запросов от вашего имени.
              </li>
              <li>
                <strong>Имя и email</strong> — извлекаются из токена МИРЭА при авторизации
                для отображения в профиле и поиска друзей.
              </li>
              <li>
                <strong>Логи посещаемости</strong> — записи об отметках (без данных QR-кода)
                для отображения истории.
              </li>
            </ul>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-medium text-text-primary">3. Как мы используем данные</h2>
            <ul className="list-disc pl-5 space-y-1">
              <li>Отображение расписания, оценок и посещаемости</li>
              <li>Отметка посещаемости по QR-коду</li>
              <li>Отображение событий прохода через турникеты</li>
              <li>Поиск друзей для совместной отметки</li>
              <li>Бронирование мест в киберзоне</li>
            </ul>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-medium text-text-primary">4. Хранение и защита</h2>
            <p>
              Сессии МИРЭА шифруются с использованием AES-256 (Fernet) с поддержкой
              ротации ключей. JWT-токены авторизации действуют 7 дней. Данные хранятся
              на сервере в России.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-medium text-text-primary">5. Передача третьим лицам</h2>
            <p>
              Мы не передаём ваши данные третьим лицам. Запросы отправляются только
              на серверы МИРЭА (lk.mirea.ru, university-app.mirea.ru) от вашего имени.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-medium text-text-primary">6. Ваши права</h2>
            <ul className="list-disc pl-5 space-y-1">
              <li>Отвязать аккаунт МИРЭА в настройках профиля</li>
              <li>Удалить аккаунт — все данные будут безвозвратно удалены</li>
              <li>Выйти из аккаунта — все активные сессии будут аннулированы</li>
            </ul>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-medium text-text-primary">7. Открытый исходный код</h2>
            <p>
              Исходный код Versiti открыт и доступен на{' '}
              <a
                href="https://github.com/silverhans/versiti-project"
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand hover:underline"
              >
                GitHub
              </a>
              . Вы можете самостоятельно проверить, как обрабатываются ваши данные.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-medium text-text-primary">8. Контакты</h2>
            <p>
              По вопросам конфиденциальности:{' '}
              <a
                href="https://github.com/silverhans/versiti-project/issues"
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand hover:underline"
              >
                GitHub Issues
              </a>
            </p>
          </section>
        </div>
      </motion.div>
    </div>
  )
}
