import { i18n } from '@/main'

export function t(key) {
  if (i18n.global) {
    return i18n.global.t(key)
  }
  return key
}