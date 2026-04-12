import { useState, useRef, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { slideUp, spring } from '../lib/motion'
import {
  QrCode,
  Camera,
  X,
  CheckCircle2,
  XCircle,
  User,
  Users,
} from 'lucide-react'
import { api } from '../lib/api'
import type { AttendanceMarkResponse } from '../lib/types'

function ScannerModal({
  open,
  onClose,
}: {
  open: boolean
  onClose: () => void
}) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [scanning, setScanning] = useState(false)
  const [results, setResults] = useState<AttendanceMarkResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    setScanning(false)
  }, [])

  const startCamera = useCallback(async () => {
    setError(null)
    setResults(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setScanning(true)
    } catch {
      setError('Нет доступа к камере')
    }
  }, [])

  useEffect(() => {
    if (!open) {
      stopCamera()
      return
    }
    startCamera()
    return () => stopCamera()
  }, [open, startCamera, stopCamera])

  // Scan loop using BarcodeDetector
  useEffect(() => {
    if (!scanning || !videoRef.current) return

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const BarcodeDetector = (window as any).BarcodeDetector
    if (!BarcodeDetector) {
      setError('Ваш браузер не поддерживает сканирование QR')
      return
    }

    const detector = new BarcodeDetector({ formats: ['qr_code'] })
    let active = true

    const scan = async () => {
      if (!active || !videoRef.current) return
      try {
        const barcodes = await detector.detect(videoRef.current)
        if (barcodes.length > 0) {
          const qrData = barcodes[0].rawValue
          if (qrData) {
            active = false
            stopCamera()
            await markAttendance(qrData)
            return
          }
        }
      } catch {
        /* ignore */
      }
      if (active) requestAnimationFrame(scan)
    }
    requestAnimationFrame(scan)

    return () => {
      active = false
    }
  }, [scanning, stopCamera])

  const markAttendance = async (qrData: string) => {
    setError(null)
    try {
      const res = await api<AttendanceMarkResponse>('/api/attendance/mark', {
        method: 'POST',
        body: JSON.stringify({ qr_data: qrData }),
      })
      setResults(res)
    } catch {
      setError('Ошибка отметки посещаемости')
    }
  }

  if (!open) return null

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-surface-0/95 flex flex-col"
    >
      <div className="flex items-center justify-between px-4 py-3">
        <h2 className="text-lg font-semibold text-text-primary">Сканер QR</h2>
        <button onClick={onClose} className="p-2 text-text-muted hover:text-text-primary">
          <X size={24} />
        </button>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center px-6 gap-6">
        {scanning && (
          <div className="relative w-full max-w-xs aspect-square rounded-2xl overflow-hidden border-2 border-brand">
            <video
              ref={videoRef}
              className="w-full h-full object-cover"
              playsInline
              muted
            />
            <div className="absolute inset-0 border-[3px] border-brand/30 rounded-2xl" />
            <motion.div
              animate={{ y: ['0%', '100%', '0%'] }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute left-4 right-4 h-0.5 bg-brand/60"
            />
          </div>
        )}

        {!scanning && !results && !error && (
          <div className="text-center space-y-4">
            <Camera size={48} className="mx-auto text-text-muted" />
            <p className="text-sm text-text-secondary">Инициализация камеры...</p>
          </div>
        )}

        {error && (
          <div className="text-center space-y-4">
            <XCircle size={48} className="mx-auto text-danger" />
            <p className="text-sm text-danger">{error}</p>
            <button
              onClick={startCamera}
              className="px-6 py-2 bg-brand text-white rounded-xl text-sm font-medium"
            >
              Попробовать снова
            </button>
          </div>
        )}

        {results && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={spring}
            className="w-full max-w-sm space-y-3"
          >
            {results.results?.map((r, i) => (
              <div
                key={i}
                className={`flex items-center gap-3 p-4 rounded-xl border ${
                  r.success
                    ? 'bg-success/10 border-success/20'
                    : 'bg-danger/10 border-danger/20'
                }`}
              >
                {r.success ? (
                  <CheckCircle2 size={20} className="text-success shrink-0" />
                ) : (
                  <XCircle size={20} className="text-danger shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-text-primary">{r.name}</p>
                  <p className="text-xs text-text-secondary truncate">{r.message}</p>
                </div>
              </div>
            ))}

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => {
                  setResults(null)
                  startCamera()
                }}
                className="flex-1 py-3 bg-surface-2 border border-border rounded-xl text-sm font-medium text-text-primary"
              >
                Сканировать ещё
              </button>
              <button
                onClick={onClose}
                className="flex-1 py-3 bg-brand text-white rounded-xl text-sm font-medium"
              >
                Готово
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  )
}

export default function HomePage({ onOpenProfile, onOpenFriends }: { onOpenProfile?: () => void; onOpenFriends?: () => void }) {
  const [scannerOpen, setScannerOpen] = useState(false)

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <motion.div
        variants={slideUp}
        initial="enter"
        animate="active"
        className="space-y-6"
      >
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">Привет!</h1>
          <p className="text-sm text-text-secondary mt-1">
            Добро пожаловать в МИРЭА
          </p>
        </div>

        {/* Scanner button */}
        <motion.button
          onClick={() => setScannerOpen(true)}
          whileTap={{ scale: 0.97 }}
          className="w-full flex items-center gap-4 p-5 bg-brand/10 border border-brand/20 rounded-2xl hover:bg-brand/15 transition-colors"
        >
          <div className="w-14 h-14 bg-brand rounded-xl flex items-center justify-center">
            <QrCode size={28} className="text-white" />
          </div>
          <div className="text-left">
            <p className="text-base font-semibold text-text-primary">Отметить посещаемость</p>
            <p className="text-xs text-text-secondary mt-0.5">
              Наведите камеру на QR-код преподавателя
            </p>
          </div>
        </motion.button>

        {/* Quick links */}
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={onOpenFriends}
            className="bg-surface-2 rounded-xl border border-border p-4 flex flex-col items-center gap-2 hover:border-border-active transition-colors"
          >
            <Users size={22} className="text-brand" />
            <span className="text-sm font-medium text-text-primary">Друзья</span>
          </button>
          <button
            onClick={onOpenProfile}
            className="bg-surface-2 rounded-xl border border-border p-4 flex flex-col items-center gap-2 hover:border-border-active transition-colors"
          >
            <User size={22} className="text-brand" />
            <span className="text-sm font-medium text-text-primary">Профиль</span>
          </button>
        </div>
      </motion.div>

      <AnimatePresence>
        {scannerOpen && (
          <ScannerModal open={scannerOpen} onClose={() => setScannerOpen(false)} />
        )}
      </AnimatePresence>
    </div>
  )
}
