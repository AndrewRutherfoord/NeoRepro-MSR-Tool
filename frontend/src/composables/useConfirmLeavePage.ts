import { onBeforeUnmount, onMounted, type Ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

/**
 * Composable that shows a confirm leave or confirm reload dialog there are unsaved changes on a page.
 *
 * @param confirmLeaveMessage Message to show in the dialog.
 * @param leavable Boolean that indicates whether the page can be left without showing the dialog.
 */
export function useConfirmLeavePage(confirmLeaveMessage: string, leavable: Ref<boolean>) {
  /**
   * Before reloading the page, checks if there are unsaved changes and shows a confirm leave dialog.
   */
  function beforeReload(event: { returnValue: string }) {
    // To show confirm leave dialog.
    if (!leavable.value) {
      event.returnValue = confirmLeaveMessage // Needed for some browsers
      return confirmLeaveMessage
    }
    return null
  }

  onMounted(() => {
    // Add confirm leave event listener.
    window.addEventListener('beforeunload', beforeReload)
  })

  onBeforeUnmount(() => {
    // Remove confirm leave event listener.
    window.removeEventListener('beforeunload', beforeReload)
  })

  /**
   * Before a route change, checks if there are unsaved changes and shows a confirm leave dialog.
   */
  onBeforeRouteLeave(() => {
    if (!leavable.value && !confirm(confirmLeaveMessage)) {
      return false
    }
    return true
  })
}
