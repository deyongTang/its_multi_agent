import request from './request'

export function uploadFile(data) {
  return request({
    url: '/upload',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function uploadToES(data) {
  return request({
    url: '/upload_es',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function queryKnowledge(data) {
  return request({
    url: '/query',
    method: 'post',
    data
  })
}

export async function queryKnowledgeStream(data, onChunk) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'

  const response = await fetch(`${baseURL}/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()

    if (done) break

    // 解码数据块
    const chunk = decoder.decode(value, { stream: true })

    // SSE 格式: "data: xxx\n\n"
    const lines = chunk.split('\n\n')

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const content = line.slice(6) // 移除 "data: " 前缀
        if (content.trim()) {
          onChunk(content)
        }
      }
    }
  }
}

/**
 * 触发爬虫任务 (Crawler -> OSS)
 * @param {Object} params - 查询参数 { start_id?: number, end_id?: number }
 * @returns {Promise<Object>} - { status, message, task_type }
 */
export function triggerCrawlerTask(params = {}) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'
  
  const queryString = new URLSearchParams(params).toString()
  const url = `/tasks/crawl${queryString ? '?' + queryString : ''}`

  return request({
    url,
    method: 'post',
    baseURL
  })
}

/**
 * 触发入库任务 (OSS -> ES)
 * @param {Object} params - 查询参数 { batch_size?: number, retry?: boolean }
 * @returns {Promise<Object>} - { status, message, task_type }
 */
export function triggerIngestTask(params = {}) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'
  
  const queryString = new URLSearchParams(params).toString()
  const url = `/tasks/ingest${queryString ? '?' + queryString : ''}`

  return request({
    url,
    method: 'post',
    baseURL
  })
}
