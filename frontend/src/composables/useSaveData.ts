import { ref, type Ref } from 'vue'

export function useSaveData(data: Ref<string>, initialFilename: string = 'data.json') {
  const filename = ref<string>(initialFilename)

  const saveToFile = () => {
    // Convert data to JSON
    // const jsonData = JSON.stringify(data.value)

    // Create a blob from the data
    const blob = new Blob([data.value], { type: 'application/json' })

    // Create a link element
    const link = document.createElement('a')

    // Set the download attribute with a filename
    link.download = filename.value

    // Create an object URL and set it as the href attribute
    link.href = window.URL.createObjectURL(blob)

    // Append the link to the body
    document.body.appendChild(link)

    // Programmatically click the link to trigger the download
    link.click()

    // Remove the link from the document
    document.body.removeChild(link)
  }

  return { saveToFile, filename }
}
