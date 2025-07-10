/**
 * Simple toast notification system
 */

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastOptions {
  duration?: number
  icon?: string
}

class ToastManager {
  private container: HTMLDivElement | null = null

  private ensureContainer() {
    if (!this.container) {
      this.container = document.createElement('div')
      this.container.className = 'fixed top-4 right-4 z-50 space-y-2'
      document.body.appendChild(this.container)
    }
  }

  show(message: string, type: ToastType, options: ToastOptions = {}) {
    this.ensureContainer()
    
    const toast = document.createElement('div')
    const duration = options.duration || 5000
    
    // Set classes based on type
    const baseClasses = 'px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 text-white transition-all transform translate-x-0'
    const typeClasses = {
      success: 'bg-green-600',
      error: 'bg-red-600',
      warning: 'bg-yellow-600',
      info: 'bg-blue-600'
    }
    
    toast.className = `${baseClasses} ${typeClasses[type]}`
    
    // Add icon if provided
    if (options.icon) {
      toast.innerHTML = `<span>${options.icon}</span><span>${message}</span>`
    } else {
      toast.textContent = message
    }
    
    // Add close button
    const closeBtn = document.createElement('button')
    closeBtn.innerHTML = '×'
    closeBtn.className = 'ml-2 text-2xl leading-none hover:opacity-80'
    closeBtn.onclick = () => this.remove(toast)
    toast.appendChild(closeBtn)
    
    // Add to container
    this.container!.appendChild(toast)
    
    // Animate in
    setTimeout(() => {
      toast.style.transform = 'translateX(0)'
    }, 10)
    
    // Auto remove after duration
    setTimeout(() => {
      this.remove(toast)
    }, duration)
  }

  private remove(toast: HTMLElement) {
    toast.style.transform = 'translateX(400px)'
    toast.style.opacity = '0'
    setTimeout(() => {
      toast.remove()
    }, 300)
  }

  success(message: string, options?: ToastOptions) {
    this.show(message, 'success', { icon: '✓', ...options })
  }

  error(message: string, options?: ToastOptions) {
    this.show(message, 'error', { icon: '✕', ...options })
  }

  warning(message: string, options?: ToastOptions) {
    this.show(message, 'warning', { icon: '⚠', ...options })
  }

  info(message: string, options?: ToastOptions) {
    this.show(message, 'info', { icon: 'ℹ', ...options })
  }
}

export const toast = new ToastManager()