import type { Transition, Variants } from 'framer-motion'

export const spring: Transition = {
  type: 'spring',
  damping: 26,
  stiffness: 400,
}

export const springLight: Transition = {
  type: 'spring',
  damping: 20,
  stiffness: 300,
}

export const pageVariants: Variants = {
  enter: { opacity: 0, y: 12 },
  active: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -12 },
}

export const fadeVariants: Variants = {
  enter: { opacity: 0 },
  active: { opacity: 1 },
  exit: { opacity: 0 },
}

export const scaleIn: Variants = {
  enter: { opacity: 0, scale: 0.95 },
  active: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
}

export const slideUp: Variants = {
  enter: { opacity: 0, y: 20 },
  active: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 20 },
}
