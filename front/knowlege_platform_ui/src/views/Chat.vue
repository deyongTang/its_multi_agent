<template>
  <div class="chat-container">
    <div class="chat-box">
      <div class="messages" ref="messagesRef">
        <div v-if="messages.length === 0" class="empty-state">
          <el-icon :size="60" color="#30363d"><ChatDotRound /></el-icon>
          <p>开始您的提问，我将基于知识库为您解答。</p>
        </div>
        
        <div 
          v-for="(msg, index) in messages" 
          :key="index" 
          class="message-item"
          :class="msg.role"
        >
          <div class="avatar">
            <el-avatar :icon="msg.role === 'user' ? 'User' : 'Service'" :style="{ backgroundColor: msg.role === 'user' ? '#409EFF' : '#00f260' }" />
          </div>
          <div class="content">
            <div class="bubble">
              <div v-if="msg.loading" class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
              <div v-else v-html="formatContent(msg.content)"></div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="input-area">
        <el-input
          v-model="input"
          placeholder="请输入您的问题..."
          :rows="3"
          type="textarea"
          resize="none"
          @keydown.enter.prevent="handleSend"
        />
        <el-button type="primary" class="send-btn" @click="handleSend" :loading="loading" :disabled="!input.trim()">
          <el-icon><Position /></el-icon> 发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { queryKnowledgeStream } from '@/api/knowledge'
import { User, Service, Position, ChatDotRound } from '@element-plus/icons-vue'
import { marked } from 'marked'

const input = ref('')
const loading = ref(false)
const messages = ref([])
const messagesRef = ref(null)

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

const formatContent = (text) => {
  // Use marked to parse markdown content into HTML
  return marked(text)
}

const handleSend = async () => {
  if (!input.value.trim() || loading.value) return

  const question = input.value
  input.value = ''

  // Add user message
  messages.value.push({
    role: 'user',
    content: question
  })
  scrollToBottom()

  // Add bot placeholder
  loading.value = true
  messages.value.push({
    role: 'assistant',
    content: '',
    loading: true
  })
  scrollToBottom()

  try {
    const botMsg = messages.value[messages.value.length - 1]

    // 使用流式查询
    await queryKnowledgeStream({ question }, (chunk) => {
      // 第一次收到数据时，移除 loading 状态
      if (botMsg.loading) {
        botMsg.loading = false
      }

      // 逐字追加内容
      botMsg.content += chunk

      // 滚动到底部
      scrollToBottom()
    })

  } catch (error) {
    console.error('查询出错:', error)
    const botMsg = messages.value[messages.value.length - 1]
    botMsg.loading = false
    botMsg.content = '抱歉，查询出错，请稍后重试。'
  } finally {
    loading.value = false
    scrollToBottom()
  }
}
</script>

<style lang="scss" scoped>
.chat-container {
  height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
}

.chat-box {
  flex: 1;
  background-color: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  
  .empty-state {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: #8b949e;
    
    p {
      margin-top: 20px;
    }
  }
}

.message-item {
  display: flex;
  margin-bottom: 20px;
  
  &.user {
    flex-direction: row-reverse;
    
    .content {
      align-items: flex-end;
      
      .bubble {
        background-color: #409EFF;
        color: #fff;
        border-top-right-radius: 0;
      }
    }
    
    .avatar {
      margin-left: 10px;
      margin-right: 0;
    }
  }
  
  &.assistant {
    .content {
      align-items: flex-start;
      
      .bubble {
        background-color: #1f242d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-top-left-radius: 0;
      }
    }
    
    .avatar {
      margin-right: 10px;
    }
  }
}

.content {
  display: flex;
  flex-direction: column;
  max-width: 70%;
  
  .bubble {
    padding: 10px 15px;
    border-radius: 12px;
    line-height: 1.5;
    font-size: 14px;
    word-break: break-word;

    /* Markdown 样式适配 */
    :deep(p) {
      margin: 0 0 10px 0;
      &:last-child {
        margin-bottom: 0;
      }
    }

    :deep(a) {
      color: #58a6ff;
      text-decoration: none;
      &:hover {
        text-decoration: underline;
      }
    }
    
    :deep(ul), :deep(ol) {
      padding-left: 20px;
      margin: 5px 0;
    }
    
    :deep(code) {
      background-color: rgba(110, 118, 129, 0.4);
      padding: 0.2em 0.4em;
      border-radius: 6px;
      font-family: monospace;
    }
    
    :deep(pre) {
      background-color: #161b22;
      padding: 10px;
      border-radius: 6px;
      overflow-x: auto;
      
      code {
        background-color: transparent;
        padding: 0;
      }
    }
    
    :deep(img) {
      max-width: 100%;
      border-radius: 6px;
      margin: 10px 0;
    }
  }
}

.input-area {
  padding: 20px;
  background-color: #0d1117;
  border-top: 1px solid #30363d;
  display: flex;
  gap: 10px;
  align-items: flex-end;
  
  :deep(.el-textarea__inner) {
    background-color: #161b22;
    border-color: #30363d;
    color: #c9d1d9;
    box-shadow: none;
    
    &:focus {
      border-color: #409EFF;
    }
  }
  
  .send-btn {
    height: auto;
    padding: 10px 20px;
  }
}

.typing-indicator {
  span {
    display: inline-block;
    width: 6px;
    height: 6px;
    background-color: #8b949e;
    border-radius: 50%;
    margin: 0 2px;
    animation: bounce 1.4s infinite ease-in-out both;
    
    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
  }
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>
