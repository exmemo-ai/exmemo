import { i18n } from '@/main'

export function t(key, params) {
  if (i18n.global) {
    return i18n.global.t(key, params)
  }
  return key
}