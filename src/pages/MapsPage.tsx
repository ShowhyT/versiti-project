import { motion } from 'framer-motion'
import { slideUp } from '../lib/motion'

export default function MapsPage() {
  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <motion.div
        variants={slideUp}
        initial="enter"
        animate="active"
        className="space-y-4"
      >
        <h1 className="text-2xl font-semibold text-text-primary">Карты</h1>
        <div className="bg-surface-2 rounded-xl border border-border p-4">
          <p className="text-sm text-text-secondary">
            Интерактивные схемы корпусов
          </p>
        </div>
      </motion.div>
    </div>
  )
}
