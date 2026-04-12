import { motion } from 'framer-motion'
import { spring } from '../lib/motion'
import {
  Home,
  Calendar,
  Map,
  CreditCard,
  GraduationCap,
  Gamepad2,
} from 'lucide-react'
import type { TabId } from '../App'

const TABS: { id: TabId; label: string; icon: typeof Home }[] = [
  { id: 'home', label: 'Главная', icon: Home },
  { id: 'schedule', label: 'Пары', icon: Calendar },
  { id: 'maps', label: 'Карты', icon: Map },
  { id: 'passes', label: 'Пропуск', icon: CreditCard },
  { id: 'grades', label: 'БРС', icon: GraduationCap },
  { id: 'esports', label: 'Кибер', icon: Gamepad2 },
]

interface Props {
  active: TabId
  onChange: (id: TabId) => void
}

export default function TabBar({ active, onChange }: Props) {
  const activeIndex = TABS.findIndex((t) => t.id === active)

  return (
    <nav className="relative flex items-center bg-surface-1/80 backdrop-blur-xl border-t border-border px-1 pb-[var(--safe-bottom,0px)]">
      {/* Animated indicator */}
      <motion.div
        className="absolute top-0 left-0 h-[2px] bg-brand rounded-full"
        animate={{
          width: `${100 / TABS.length}%`,
          x: `${activeIndex * 100}%`,
        }}
        transition={spring}
      />

      {TABS.map((tab) => {
        const isActive = tab.id === active
        const Icon = tab.icon
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className="flex-1 flex flex-col items-center gap-0.5 py-2 pt-3 relative"
          >
            <motion.div
              animate={{ scale: isActive ? 1 : 0.9 }}
              transition={spring}
            >
              <Icon
                size={22}
                strokeWidth={isActive ? 2.2 : 1.6}
                className={isActive ? 'text-brand' : 'text-text-muted'}
              />
            </motion.div>
            <span
              className={`text-[10px] font-medium transition-colors duration-200 ${
                isActive ? 'text-brand' : 'text-text-muted'
              }`}
            >
              {tab.label}
            </span>
          </button>
        )
      })}
    </nav>
  )
}
