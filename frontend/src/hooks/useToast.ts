import { useUiStore, ToastType } from '../store/ui'

export function useToast() {
  const addToast = useUiStore((state) => state.addToast)
  const removeToast = useUiStore((state) => state.removeToast)
  const clearToasts = useUiStore((state) => state.clearToasts)

  return {
    toast: (message: string, type?: ToastType, duration?: number) =>
      addToast(message, type, duration),
    success: (message: string, duration?: number) =>
      addToast(message, 'success', duration),
    error: (message: string, duration?: number) =>
      addToast(message, 'error', duration),
    info: (message: string, duration?: number) =>
      addToast(message, 'info', duration),
    warning: (message: string, duration?: number) =>
      addToast(message, 'warning', duration),
    remove: removeToast,
    clear: clearToasts,
  }
}
