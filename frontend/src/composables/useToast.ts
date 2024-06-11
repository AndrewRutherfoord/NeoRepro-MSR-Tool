import { useToast as usePrimeToast } from 'primevue/usetoast'

type severity = 'success' | 'info' | 'warn' | 'error' | 'secondary' | 'contrast'

export function useToast() {
  const toast = usePrimeToast()

  function add(severity: severity, summary: string, detail: string | undefined = undefined, life : number = 3000) {
    toast.add({ severity: severity, summary: summary, detail: detail, life: life })
  }

  function success(summary: string, detail: string | undefined = undefined) {
    add('success', summary, detail)
  }
  function info(summary: string, detail: string | undefined = undefined) {
    add('info', summary, detail)
  }
  function warn(summary: string, detail: string | undefined = undefined) {
    add('warn', summary, detail)
  }
  function error(summary: string, detail: string | undefined = undefined) {
    add('error', summary, detail, 7000)
  }
  function secondary(summary: string, detail: string | undefined = undefined) {
    add('secondary', summary, detail)
  }

  return {
    success,
    info,
    warn,
    error,
    secondary
  }
}
