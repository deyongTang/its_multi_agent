<template>
  <div class="knowledge-container">
    <div class="page-header">
      <h2>知识库管理</h2>
      <p class="subtitle">Upload and manage your knowledge base documents</p>
    </div>

    <el-tabs v-model="activeTab" class="tabs-container">
      <!-- 上传到向量库标签 -->
      <el-tab-pane label="上传到向量库" name="vector">
        <el-card class="upload-card">
          <template #header>
            <div class="card-header">
              <span>文件上传（向量库）</span>
            </div>
          </template>
          <div class="upload-area">
            <el-upload
              class="upload-demo"
              drag
              action=""
              :http-request="handleUpload"
              multiple
              :show-file-list="false"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                Drop file here or <em>click to upload</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  Supported files: .txt, .md, .pdf (if supported by backend)
                </div>
              </template>
            </el-upload>
          </div>
        </el-card>

        <div v-if="vectorUploadHistory.length > 0" class="history-section">
          <h3>上传记录</h3>
          <el-table :data="vectorUploadHistory" style="width: 100%" :row-class-name="tableRowClassName">
            <el-table-column prop="fileName" label="文件名" width="280" />
            <el-table-column prop="chunks" label="新增切片数" width="150" align="center" />
            <el-table-column prop="status" label="状态" width="120">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="信息" />
            <el-table-column prop="time" label="时间" width="180" />
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 上传到Elasticsearch标签 -->
      <el-tab-pane label="上传到 Elasticsearch" name="es">
        <el-card class="upload-card">
          <template #header>
            <div class="card-header">
              <span>文件上传（Elasticsearch）</span>
            </div>
          </template>
          <div class="upload-area">
            <el-upload
              class="upload-demo"
              drag
              action=""
              :http-request="handleUploadES"
              multiple
              :show-file-list="false"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                Drop file here or <em>click to upload</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  Supported files: .txt, .md, .pdf (if supported by backend)
                </div>
              </template>
            </el-upload>
          </div>
        </el-card>

        <div v-if="esUploadHistory.length > 0" class="history-section">
          <h3>上传记录</h3>
          <el-table :data="esUploadHistory" style="width: 100%" :row-class-name="tableRowClassName">
            <el-table-column prop="fileName" label="文件名" width="280" />
            <el-table-column prop="status" label="状态" width="120">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="信息" />
            <el-table-column prop="time" label="时间" width="180" />
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 知识库同步标签 -->
      <el-tab-pane label="知识库同步" name="sync">
        <el-card class="sync-card">
          <template #header>
            <div class="card-header">
              <span>知识库同步任务</span>
            </div>
          </template>
          
          <!-- 爬虫任务区域 -->
          <div class="sync-section">
            <h3>1. 开始爬取数据</h3>
            <p class="section-desc">从源站抓取指定范围的文档，清洗并上传到 MinIO 对象存储</p>
            <div class="form-group">
              <div class="form-row">
                <div class="form-item">
                  <label>起始 ID</label>
                  <el-input-number v-model="crawlParams.start_id" :min="1" />
                </div>
                <div class="form-item">
                  <label>结束 ID</label>
                  <el-input-number v-model="crawlParams.end_id" :min="1" />
                </div>
              </div>
              <el-button 
                type="primary" 
                @click="handleTriggerCrawl"
                :loading="crawlLoading"
                :disabled="crawlLoading"
              >
                {{ crawlLoading ? '爬取中...' : '开始爬取数据' }}
              </el-button>
            </div>
          </div>

          <el-divider />

          <!-- 入库任务区域 -->
          <div class="sync-section">
            <h3>2. 执行同步索引</h3>
            <p class="section-desc">扫描数据库中状态为 NEW 的文档，下载并向量化写入 Elasticsearch</p>
            <div class="form-group">
              <div class="form-row">
                <div class="form-item">
                  <label>批处理数量</label>
                  <el-input-number v-model="ingestParams.batch_size" :min="1" />
                </div>
                <div class="form-item">
                  <label>重试失败文档</label>
                  <el-switch v-model="ingestParams.retry" />
                </div>
              </div>
              <el-button 
                type="success" 
                @click="handleTriggerIngest"
                :loading="ingestLoading"
                :disabled="ingestLoading"
              >
                {{ ingestLoading ? '执行中...' : '执行同步索引' }}
              </el-button>
            </div>
          </div>
        </el-card>

        <div v-if="syncTaskHistory.length > 0" class="history-section">
          <h3>任务历史</h3>
          <el-table :data="syncTaskHistory" style="width: 100%" :row-class-name="tableRowClassName">
            <el-table-column prop="taskType" label="任务类型" width="120" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'accepted' ? 'success' : 'danger'">
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="消息" />
            <el-table-column prop="time" label="提交时间" width="180" />
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { uploadFile, uploadToES, triggerCrawlerTask, triggerIngestTask } from '@/api/knowledge'
import { ElMessage } from 'element-plus'

const activeTab = ref('vector')
const vectorUploadHistory = ref([])
const esUploadHistory = ref([])
const syncTaskHistory = ref([])

// 爬虫任务参数
const crawlParams = ref({
  start_id: 1,
  end_id: 100
})
const crawlLoading = ref(false)

// 入库任务参数
const ingestParams = ref({
  batch_size: 100,
  retry: false
})
const ingestLoading = ref(false)

const handleUpload = async (options) => {
  const { file } = options
  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await uploadFile(formData)
    vectorUploadHistory.value.unshift({
      fileName: res.file_name,
      chunks: res.chunks_added,
      status: res.status,
      message: res.message,
      time: new Date().toLocaleString()
    })
    ElMessage.success(`File ${file.name} uploaded successfully`)
  } catch (error) {
    vectorUploadHistory.value.unshift({
      fileName: file.name,
      chunks: 0,
      status: 'error',
      message: error.message || 'Upload failed',
      time: new Date().toLocaleString()
    })
    ElMessage.error(`Upload failed for ${file.name}`)
  }
}

const handleUploadES = async (options) => {
  const { file } = options
  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await uploadToES(formData)
    esUploadHistory.value.unshift({
      fileName: res.file_name || file.name,
      status: res.status,
      message: res.message,
      time: new Date().toLocaleString()
    })
    ElMessage.success(`File ${file.name} uploaded to Elasticsearch successfully`)
  } catch (error) {
    esUploadHistory.value.unshift({
      fileName: file.name,
      status: 'error',
      message: error.message || 'Upload failed',
      time: new Date().toLocaleString()
    })
    ElMessage.error(`Upload to Elasticsearch failed for ${file.name}`)
  }
}

const handleTriggerCrawl = async () => {
  crawlLoading.value = true
  try {
    const res = await triggerCrawlerTask({
      start_id: crawlParams.value.start_id,
      end_id: crawlParams.value.end_id
    })
    
    syncTaskHistory.value.unshift({
      taskType: '爬虫任务',
      status: res.status,
      message: res.message,
      time: new Date().toLocaleString()
    })
    
    ElMessage.success('爬虫任务已提交到后台队列')
    
    // 禁用按钮3秒防止重复点击
    setTimeout(() => {
      crawlLoading.value = false
    }, 3000)
  } catch (error) {
    syncTaskHistory.value.unshift({
      taskType: '爬虫任务',
      status: 'error',
      message: error.message || 'Task submission failed',
      time: new Date().toLocaleString()
    })
    ElMessage.error(`爬虫任务提交失败: ${error.message}`)
    crawlLoading.value = false
  }
}

const handleTriggerIngest = async () => {
  ingestLoading.value = true
  try {
    const res = await triggerIngestTask({
      batch_size: ingestParams.value.batch_size,
      retry: ingestParams.value.retry
    })
    
    syncTaskHistory.value.unshift({
      taskType: '入库任务',
      status: res.status,
      message: res.message,
      time: new Date().toLocaleString()
    })
    
    ElMessage.success('入库任务已提交到后台队列')
    
    // 禁用按钮3秒防止重复点击
    setTimeout(() => {
      ingestLoading.value = false
    }, 3000)
  } catch (error) {
    syncTaskHistory.value.unshift({
      taskType: '入库任务',
      status: 'error',
      message: error.message || 'Task submission failed',
      time: new Date().toLocaleString()
    })
    ElMessage.error(`入库任务提交失败: ${error.message}`)
    ingestLoading.value = false
  }
}

const tableRowClassName = ({ rowIndex }) => {
  if (rowIndex === 0) {
    return 'success-row'
  }
  return ''
}
</script>

<style lang="scss" scoped>
.knowledge-container {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
  h2 {
    color: #fff;
    margin-bottom: 10px;
  }
  .subtitle {
    color: #8b949e;
    font-size: 14px;
  }
}

.tabs-container {
  margin-bottom: 20px;
  
  :deep(.el-tabs__header) {
    margin: 0;
    border-bottom: 1px solid #30363d;
  }
  
  :deep(.el-tabs__nav-wrap::after) {
    background-color: #30363d;
  }
  
  :deep(.el-tabs__item) {
    color: #8b949e;
    
    &:hover {
      color: #c9d1d9;
    }
    
    &.is-active {
      color: #58a6ff;
    }
  }
  
  :deep(.el-tabs__active-bar) {
    background-color: #58a6ff;
  }
}

.upload-card {
  background-color: #161b22;
  border: 1px solid #30363d;
  color: #c9d1d9;
  margin-bottom: 30px;

  :deep(.el-card__header) {
    border-bottom: 1px solid #30363d;
  }
}

.sync-card {
  background-color: #161b22;
  border: 1px solid #30363d;
  color: #c9d1d9;
  margin-bottom: 30px;

  :deep(.el-card__header) {
    border-bottom: 1px solid #30363d;
  }
}

.sync-section {
  margin-bottom: 20px;

  h3 {
    color: #fff;
    font-size: 16px;
    margin-bottom: 8px;
  }

  .section-desc {
    color: #8b949e;
    font-size: 13px;
    margin-bottom: 15px;
  }

  .form-group {
    display: flex;
    gap: 20px;
    align-items: flex-end;

    .form-row {
      display: flex;
      gap: 15px;
      flex: 1;
    }

    .form-item {
      display: flex;
      flex-direction: column;
      gap: 8px;
      flex: 1;

      label {
        color: #c9d1d9;
        font-size: 13px;
      }

      :deep(.el-input-number) {
        width: 100%;

        .el-input__wrapper {
          background-color: #0d1117;
          border-color: #30363d;
        }

        input {
          color: #c9d1d9;
        }
      }

      :deep(.el-switch) {
        --el-switch-on-color: #58a6ff;
      }
    }
  }
}

.upload-area {
  padding: 20px;
  
  :deep(.el-upload-dragger) {
    background-color: #0d1117;
    border-color: #30363d;
    
    &:hover {
      border-color: #409EFF;
      background-color: #161b22;
    }
    
    .el-icon--upload {
      color: #58a6ff;
    }
    
    .el-upload__text {
      color: #8b949e;
      em {
        color: #58a6ff;
      }
    }
  }
}

.history-section {
  h3 {
    color: #fff;
    margin-bottom: 20px;
  }
  
  :deep(.el-table) {
    background-color: #161b22;
    color: #c9d1d9;
    --el-table-border-color: #30363d;
    --el-table-header-bg-color: #0d1117;
    --el-table-row-hover-bg-color: #1f242d;
    
    th, tr {
      background-color: #161b22;
    }
    
    .success-row {
      background-color: #1c2518;
    }
  }
}
</style>
