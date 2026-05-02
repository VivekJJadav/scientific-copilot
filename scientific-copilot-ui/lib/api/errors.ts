import axios from 'axios'

function extractDetail(detail: unknown): string | null {
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string') {
          return item.msg
        }
        return null
      })
      .filter((item): item is string => Boolean(item))

    if (messages.length > 0) {
      return messages.join(', ')
    }
  }

  return null
}

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data
    const detail = extractDetail(responseData?.detail)
    if (detail) {
      return detail
    }

    if (typeof responseData?.message === 'string' && responseData.message.trim()) {
      return responseData.message
    }
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message
  }

  return 'An unknown error occurred'
}
