import { AnimatePresence, motion } from 'framer-motion'
import {
  QrCode,
  Camera,
  X,
  CheckCircle2,
  XCircle,
  User,
  Users,
  Check,
  Star,
} from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { slideUp, spring } from '../lib/motion'
import type { AttendanceMarkResponse } from '../lib/types'

const SCANNER_ELEMENT_ID = 'qr-scanner-region'

interface FriendItem {
	id: number
	user_id: number
	full_name: string
	email: string | null
	is_favorite: boolean
}

function ScannerModal({
	open,
	onClose,
}: {
	open: boolean
	onClose: () => void
}) {
	const [scanning, setScanning] = useState(false)

	const [zoom, setZoom] = useState(1)
	const [zoomCaps, setZoomCaps] = useState<{
		min: number
		max: number
		step: number
	} | null>(null)

	const [results, setResults] = useState<AttendanceMarkResponse | null>(null)
	const [error, setError] = useState<string | null>(null)
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	const scannerRef = useRef<any>(null)

	// Friends selection
	const [friends, setFriends] = useState<FriendItem[]>([])
	const [selectedFriendIds, setSelectedFriendIds] = useState<Set<number>>(
		new Set(),
	)
	const [showFriendPicker, setShowFriendPicker] = useState(false)

  useEffect(() => {
    if (!open) return
    api<{ success: boolean; friends: FriendItem[] }>('/api/friends')
      .then((res) => {
        if (res.success) {
          setFriends(res.friends)
          // Auto-select favorites
          const favIds = res.friends.filter((f) => f.is_favorite).map((f) => f.user_id)
          if (favIds.length > 0) {
            setSelectedFriendIds(new Set(favIds))
            setShowFriendPicker(true)
          }
        }
      })
      .catch(() => { /* ignore */ })
  }, [open])

	const markAttendance = useCallback(
		async (qrData: string) => {
			setError(null)
			try {
				const body: Record<string, unknown> = { qr_data: qrData }
				if (selectedFriendIds.size > 0) {
					body.friend_ids = [...selectedFriendIds]
				}
				const res = await api<AttendanceMarkResponse>('/api/attendance/mark', {
					method: 'POST',
					body: JSON.stringify(body),
				})
				setResults(res)
			} catch {
				setError('Ошибка отметки посещаемости')
			}
		},
		[selectedFriendIds],
	)

	const handleZoom = useCallback(async (newZoom: number) => {
		setZoom(newZoom)
		if (scannerRef.current) {
			try {
				const caps = scannerRef.current.getRunningTrackCameraCapabilities()
				await caps.zoomFeature().apply(newZoom)
			} catch (err) {
				console.error('Ошибка применения зума:', err)
			}
		}
	}, [])

	const stopScanner = useCallback(async () => {
		if (scannerRef.current) {
			try {
				await scannerRef.current.stop()
				await scannerRef.current.clear()
			} catch {
				/* ignore */
			}
			scannerRef.current = null
		}
		setScanning(false)
	}, [])

	const startScanner = useCallback(async () => {
		setError(null)
		setResults(null)
		try {
			const mod = await import('html5-qrcode')
			const { Html5Qrcode } = mod
			const instance = new Html5Qrcode(SCANNER_ELEMENT_ID)
			scannerRef.current = instance
			await instance.start(
				{ facingMode: 'environment' },
				{
					fps: 10,
					qrbox: (w: number, h: number) => {
						const size = Math.floor(Math.min(w, h) * 0.85)
						return { width: size, height: size }
					},
					aspectRatio: 1,
				},
				async (decodedText: string) => {
					await stopScanner()
					await markAttendance(decodedText)
				},
				() => {
					/* ignore per-frame errors */
				},
			)
			// setting up zoom
			setTimeout(() => {
				try {
					const caps = instance.getRunningTrackCameraCapabilities()
					const zoomFeature = caps.zoomFeature()
					if (zoomFeature.isSupported()) {
						setZoomCaps({
							min: zoomFeature.min(),
							max: zoomFeature.max(),
							step: zoomFeature.step() || 0.1,
						})
						setZoom(zoomFeature.value() ?? zoomFeature.min())
					} else {
						setZoomCaps(null)
					}
				} catch {
					setZoomCaps(null)
				}
			}, 500)

			setScanning(true)
		} catch (e) {
			console.error(e)
			setError('Нет доступа к камере')
		}
	}, [stopScanner, markAttendance])

	useEffect(() => {
		if (!open) {
			stopScanner()
			return
		}
		const t = setTimeout(() => startScanner(), 50)
		return () => {
			clearTimeout(t)
			stopScanner()
		}
	}, [open, startScanner, stopScanner])

	const toggleFriend = (userId: number) => {
		setSelectedFriendIds(prev => {
			const next = new Set(prev)
			if (next.has(userId)) next.delete(userId)
			else next.add(userId)
			return next
		})
	}

	if (!open) return null

          <AnimatePresence>
            {showFriendPicker && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden mt-2"
              >
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {friends.map((f) => {
                    const selected = selectedFriendIds.has(f.user_id)
                    return (
                      <button
                        key={f.user_id}
                        onClick={() => toggleFriend(f.user_id)}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg border transition-colors ${
                          selected
                            ? 'bg-brand/10 border-brand/40'
                            : 'bg-surface-2 border-border'
                        }`}
                      >
                        <div
                          className={`w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 ${
                            selected ? 'bg-brand border-brand' : 'border-border'
                          }`}
                        >
                          {selected && <Check size={12} className="text-white" />}
                        </div>
                        <span className="text-sm text-text-primary text-left truncate flex-1">
                          {f.full_name}
                        </span>
                        {f.is_favorite && (
                          <Star size={12} className="text-warning fill-warning shrink-0" />
                        )}
                      </button>
                    )
                  })}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

			{/* Friends selection toggle */}
			{friends.length > 0 && !results && (
				<div className='px-4 pb-3'>
					<button
						onClick={() => setShowFriendPicker(!showFriendPicker)}
						className='w-full flex items-center justify-between bg-surface-2 border border-border rounded-xl px-4 py-3 hover:border-border-active transition-colors'
					>
						<div className='flex items-center gap-2'>
							<Users size={18} className='text-brand' />
							<span className='text-sm text-text-primary'>
								Отметить с друзьями
							</span>
						</div>
						{selectedFriendIds.size > 0 && (
							<span className='text-xs bg-brand text-white px-2 py-0.5 rounded-full'>
								{selectedFriendIds.size}
							</span>
						)}
					</button>

					<AnimatePresence>
						{showFriendPicker && (
							<motion.div
								initial={{ height: 0, opacity: 0 }}
								animate={{ height: 'auto', opacity: 1 }}
								exit={{ height: 0, opacity: 0 }}
								className='overflow-hidden mt-2'
							>
								<div className='space-y-1 max-h-48 overflow-y-auto'>
									{friends.map(f => {
										const selected = selectedFriendIds.has(f.user_id)
										return (
											<button
												key={f.user_id}
												onClick={() => toggleFriend(f.user_id)}
												className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg border transition-colors ${
													selected
														? 'bg-brand/10 border-brand/40'
														: 'bg-surface-2 border-border'
												}`}
											>
												<div
													className={`w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 ${
														selected ? 'bg-brand border-brand' : 'border-border'
													}`}
												>
													{selected && (
														<Check size={12} className='text-white' />
													)}
												</div>
												<span className='text-sm text-text-primary text-left truncate flex-1'>
													{f.full_name}
												</span>
											</button>
										)
									})}
								</div>
							</motion.div>
						)}
					</AnimatePresence>
				</div>
			)}
			{/* Zoom slider and status */}
			<div className='flex-1 flex flex-col items-center justify-center px-6 gap-6'>
				<p className='text-xs text-text-secondary'>
					Зум: {zoomCaps ? 'Доступен' : 'Недоступен'}
				</p>

				{!results && (
					<div className='relative w-full max-w-xs aspect-square rounded-2xl overflow-hidden border-2 border-brand bg-surface-1'>
						<div id={SCANNER_ELEMENT_ID} className='w-full h-full' />
						{!scanning && !error && (
							<div className='absolute inset-0 flex flex-col items-center justify-center gap-3 bg-surface-1/90 pointer-events-none'>
								<Camera size={32} className='text-text-muted' />
								<p className='text-xs text-text-secondary'>
									Разрешите доступ к камере
								</p>
							</div>
						)}
					</div>
				)}
				{!results && !error && zoomCaps && (
					<div className='w-full max-w-xs flex items-center gap-3 px-2 bg-surface-2 p-3 rounded-xl border border-border'>
						<span className='text-xs font-medium text-text-secondary'>
							{zoom}x
						</span>
						<input
							type='range'
							min={zoomCaps.min}
							max={zoomCaps.max}
							step={zoomCaps.step}
							value={zoom}
							onChange={e => handleZoom(Number(e.target.value))}
							className='flex-1 h-2 bg-border rounded-lg appearance-none cursor-pointer accent-brand'
						/>
					</div>
				)}
				{error && (
					<div className='text-center space-y-4'>
						<XCircle size={48} className='mx-auto text-danger' />
						<p className='text-sm text-danger'>{error}</p>
						<button
							onClick={startScanner}
							className='px-6 py-2 bg-brand text-white rounded-xl text-sm font-medium'
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
						className='w-full max-w-sm space-y-3 max-h-[60vh] overflow-y-auto'
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
									<CheckCircle2 size={20} className='text-success shrink-0' />
								) : (
									<XCircle size={20} className='text-danger shrink-0' />
								)}
								<div className='flex-1 min-w-0'>
									<p className='text-sm font-medium text-text-primary'>
										{r.name}
									</p>
									<p className='text-xs text-text-secondary truncate'>
										{r.message}
									</p>
								</div>
							</div>
						))}

						<div className='flex gap-3 pt-2 sticky bottom-0 bg-surface-0/95 backdrop-blur-sm py-2'>
							<button
								onClick={() => {
									setResults(null)
									startScanner()
								}}
								className='flex-1 py-3 bg-surface-2 border border-border rounded-xl text-sm font-medium text-text-primary'
							>
								Сканировать ещё
							</button>
							<button
								onClick={onClose}
								className='flex-1 py-3 bg-brand text-white rounded-xl text-sm font-medium'
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

export default function HomePage({
	onOpenProfile,
	onOpenFriends,
}: {
	onOpenProfile?: () => void
	onOpenFriends?: () => void
}) {
	const [scannerOpen, setScannerOpen] = useState(false)

	return (
		<div className='flex-1 overflow-y-auto px-4 py-6'>
			<motion.div
				variants={slideUp}
				initial='enter'
				animate='active'
				className='space-y-6'
			>
				<div>
					<h1 className='text-2xl font-semibold text-text-primary'>Привет!</h1>
					<p className='text-sm text-text-secondary mt-1'>
						Добро пожаловать в МИРЭА
					</p>
				</div>

				<motion.button
					onClick={() => setScannerOpen(true)}
					whileTap={{ scale: 0.97 }}
					className='w-full flex items-center gap-4 p-5 bg-brand/10 border border-brand/20 rounded-2xl hover:bg-brand/15 transition-colors'
				>
					<div className='w-14 h-14 bg-brand rounded-xl flex items-center justify-center'>
						<QrCode size={28} className='text-white' />
					</div>
					<div className='text-left'>
						<p className='text-base font-semibold text-text-primary'>
							Отметить посещаемость
						</p>
						<p className='text-xs text-text-secondary mt-0.5'>
							Наведите камеру на QR-код преподавателя
						</p>
					</div>
				</motion.button>

				<div className='grid grid-cols-2 gap-3'>
					<button
						onClick={onOpenFriends}
						className='bg-surface-2 rounded-xl border border-border p-4 flex flex-col items-center gap-2 hover:border-border-active transition-colors'
					>
						<Users size={22} className='text-brand' />
						<span className='text-sm font-medium text-text-primary'>
							Друзья
						</span>
					</button>
					<button
						onClick={onOpenProfile}
						className='bg-surface-2 rounded-xl border border-border p-4 flex flex-col items-center gap-2 hover:border-border-active transition-colors'
					>
						<User size={22} className='text-brand' />
						<span className='text-sm font-medium text-text-primary'>
							Профиль
						</span>
					</button>
				</div>
			</motion.div>

			<AnimatePresence>
				{scannerOpen && (
					<ScannerModal
						open={scannerOpen}
						onClose={() => setScannerOpen(false)}
					/>
				)}
			</AnimatePresence>
		</div>
	)
}
