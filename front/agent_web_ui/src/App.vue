<template>
  <div class="app-container">
    <!-- 登录页面 -->
    <div v-if="!isLoggedIn" class="login-container">
      <div class="login-form">
        <div class="its-logo-flat login-logo">
            <img src="/its-logo.svg" alt="ITS Logo" width="60" height="60"/>
          </div>
        <h1 class="login-title">ITS系统登录</h1>
        <div class="login-input-group">
          <label for="username">用户名</label>
          <input 
            id="username"
            v-model="username"
            type="text"
            placeholder="请输入用户名"
            @keyup.enter="handleLogin"
          />
        </div>
        <div class="login-input-group">
          <label for="password">密码</label>
          <input 
            id="password"
            v-model="password"
            type="password"
            placeholder="请输入密码"
            @keyup.enter="handleLogin"
          />
        </div>
        <div v-if="loginError" class="login-error">
          {{ loginError }}
        </div>
        <button class="login-button btn-primary" @click="handleLogin">
          登录
        </button>
        <div class="login-hint">
          <p>测试用户：root1, root2, root3</p>
          <p>密码：123456</p>
        </div>
      </div>
    </div>
    
    <!-- 主界面（登录后显示） -->
    <template v-else>
      <!-- 移除header部分，将用户信息移到结果框右上角 -->
      
      <div class="main-content">
        <!-- 左侧历史会话列表 - 可展开收起 -->
        <div class="sidebar-wrapper">
          <!-- 侧边栏内容 -->
          <div class="sidebar-content" :class="{ 'expanded': isSidebarExpanded }">
            <!-- 扁平化Logo和ITS标题 -->
            <div class="app-branding">
              <!-- 扁平风格的Logo -->
              <div class="its-logo-flat">
                <img src="/its-logo.svg" alt="ITS Logo" width="40" height="40"/>
              </div>
              
              <!-- 标题 - 仅在展开状态显示 -->
              <!-- 已注释掉ITS文本显示 -->
              <!-- <div v-show="isSidebarExpanded" class="sidebar-text-content">
                <h1 class="its-title">ITS</h1>
              </div> -->
              
              <!-- 侧边栏展开/收起按钮 - 与logo水平对齐 -->
              <button 
                class="toggle-sidebar-btn" 
                @click="toggleSidebar"
                :title="isSidebarExpanded ? '收起侧边栏' : '展开侧边栏'"
              >
                {{ isSidebarExpanded ? '‹' : '›' }}
              </button>
            </div>
            
            <!-- 新建会话按钮 - 放到logo下方并左右拉伸 -->
            <div class="session-button-container" v-show="isSidebarExpanded">
              <a href="/" class="new-chat-btn" @click.prevent="createNewSession">
                <span class="icon">
                  <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" role="img" style="" width="20" height="20" viewBox="0 0 1024 1024" name="AddConversation" class="iconify new-icon" data-v-9f34fd85="">
                    <path d="M475.136 561.152v89.74336c0 20.56192 16.50688 37.23264 36.864 37.23264s36.864-16.67072 36.864-37.23264v-89.7024h89.7024c20.60288 0 37.2736-16.54784 37.2736-36.864 0-20.39808-16.67072-36.864-37.2736-36.864H548.864V397.63968A37.0688 37.0688 0 0 0 512 360.448c-20.35712 0-36.864 16.67072-36.864 37.2736v89.7024H385.4336a37.0688 37.0688 0 0 0-37.2736 36.864c0 20.35712 16.67072 36.864 37.2736 36.864h89.7024z" fill="currentColor"></path>
                    <path d="M512 118.784c-223.96928 0-405.504 181.57568-405.504 405.504 0 78.76608 22.44608 152.3712 61.35808 214.6304l-44.27776 105.6768a61.44 61.44 0 0 0 56.68864 85.1968H512c223.92832 0 405.504-181.53472 405.504-405.504 0-223.92832-181.57568-405.504-405.504-405.504z m-331.776 405.504a331.776 331.776 0 1 1 331.73504 331.776H198.656l52.59264-125.5424-11.59168-16.62976A330.09664 330.09664 0 0 1 180.224 524.288z" fill="currentColor"></path>
                  </svg>
                </span>
                <span class="text">新建会话</span>
                <span class="shortcut">
                  <span class="key">Ctrl</span>
                  <span>+</span>
                  <span class="key">K</span>
                </span>
              </a>
            </div>
            
            <!-- 导航栏 -->
            <div class="navigation-container" v-show="isSidebarExpanded">
              <div class="navigation-item" :class="{ 'selected': selectedNavItem === 'knowledge' }" @click="handleKnowledgeBase">
                <svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" fill="none" viewBox="0 0 24 24" class="nav-icon">
                  <path fill="currentColor" fill-rule="evenodd" d="M3.75 7h16.563c0 .48-.007 1.933-.016 3.685.703.172 1.36.458 1.953.837V5.937a2 2 0 0 0-2-2h-6.227a3 3 0 0 1-1.015-.176L9.992 2.677A3 3 0 0 0 8.979 2.5h-5.23a2 2 0 0 0-1.999 2v14.548a2 2 0 0 0 2 2h10.31a6.5 6.5 0 0 1-1.312-2H3.75S3.742 8.5 3.75 7m15.002 14.5a.514.514 0 0 0 .512-.454c.24-1.433.451-2.169.907-2.625.454-.455 1.186-.666 2.611-.907a.513.513 0 0 0-.002-1.026c-1.423-.241-2.155-.453-2.61-.908-.455-.457-.666-1.191-.906-2.622a.514.514 0 0 0-.512-.458.52.52 0 0 0-.515.456c-.24 1.432-.452 2.167-.907 2.624-.454.455-1.185.667-2.607.909a.514.514 0 0 0-.473.513.52.52 0 0 0 .47.512c1.425.24 2.157.447 2.61.9.455.454.666 1.19.907 2.634a.52.52 0 0 0 .515.452" clip-rule="evenodd"></path>
                </svg>
                <span class="nav-text">知识库查询</span>
              </div>
              <div class="navigation-item" :class="{ 'selected': selectedNavItem === 'service' }" @click="handleServiceStation">
                <svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" fill="none" viewBox="0 0 24 24" class="nav-icon">
                  <path fill="currentColor" fill-rule="evenodd" d="M12 20.571a8.5 8.5 0 0 1 2.5-6.08c1.43-1.429 3.5-2.49 6.071-2.491-2.571.002-4.617-1.075-6.05-2.508S12 6 12 3.428C12 6 10.954 8.095 9.517 9.532 8.081 10.968 6 12 3.428 12a8.52 8.52 0 0 1 6.082 2.516c1.43 1.43 2.487 3.484 2.49 6.055m-9.853-7.314c3.485.588 5.053 1.331 6.163 2.44s1.847 2.667 2.435 6.198c.105.627.603 1.105 1.26 1.105.664 0 1.156-.479 1.25-1.11.588-3.502 1.329-5.085 2.441-6.2 1.111-1.114 2.677-1.845 6.16-2.433.638-.075 1.144-.586 1.144-1.253 0-.668-.5-1.188-1.147-1.254-3.481-.59-5.026-1.347-6.137-2.46-1.112-1.115-1.872-2.674-2.46-6.171C13.16 1.482 12.671 1 12.003 1c-.66 0-1.155.481-1.259 1.114-.588 3.5-1.323 5.087-2.435 6.203C7.2 9.43 5.632 10.159 2.156 10.75 1.503 10.816 1 11.333 1 12.004c0 .68.52 1.17 1.147 1.253" clip-rule="evenodd"></path>
                </svg>
                <span class="nav-text">服务站查询</span>
              </div>
              <div class="navigation-item" :class="{ 'selected': selectedNavItem === 'network' }" @click="handleNetworkSearch">
                <svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" fill="none" viewBox="0 0 24 24" class="nav-icon">
                  <path fill="currentColor" fill-rule="evenodd" d="M11 4a7 7 0 1 0 6.993 7.328c-.039-.53-.586-.93-1.131-.891a5.5 5.5 0 1 1-6.203-6.203.75.75 0 0 0-1.317-.63C4.617 5.458 2.75 8.425 2.75 12c0 4.418 3.582 8 8 8s8-3.582 8-8a7.961 7.961 0 0 0-1.996-5.38" clip-rule="evenodd"></path>
                  <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="m21 21-3.5-3.5"></path>
                </svg>
                <span class="nav-text">联网搜索</span>
              </div>
              

            </div>

            <!-- 历史会话列表 - 仅在展开状态显示 -->
            <div v-show="isSidebarExpanded" class="sidebar-main">
              <div class="navigation-item" @click="toggleSessions">
                <svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 1024 1024" class="nav-icon">
                  <path d="M512 81.066667c-233.301333 0-422.4 189.098667-422.4 422.4s189.098667 422.4 422.4 422.4 422.4-189.098667 422.4-422.4-189.098667-422.4-422.4-422.4z m-345.6 422.4a345.6 345.6 0 1 1 691.2 0 345.6 345.6 0 1 1-691.2 0z m379.733333-174.933334a38.4 38.4 0 0 0-76.8 0v187.733334a38.4 38.4 0 0 0 11.264 27.136l93.866667 93.866666a38.4 38.4 0 1 0 54.272-54.272L546.133333 500.352V328.533333z" fill="currentColor"></path>
                </svg>
                <span class="nav-text">历史会话</span>
              </div>
              <div class="sessions-list" v-show="showSessions">
                <div v-if="isLoadingSessions" class="loading-sessions">
                  加载历史对话中...
                </div>
                <div v-else-if="sessions.length === 0" class="no-sessions">
                  暂无历史对话
                </div>
                <div
                  v-for="session in sessions"
                  :key="session.session_id"
                  :class="['session-item', { 'selected': session.session_id === selectedSessionId }]"
                  @click="selectSession(session.session_id)"
                >
                  <div class="session-info">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <img alt="豆包" src="//lf-flow-web-cdn.doubao.com/obj/flow-doubao/doubao/chat/static/image/default.light.2ea4b2b4.png" class="session-icon" style="width: 24px; height: 24px; border-radius: 4px; object-fit: cover;">
                      <div class="session-preview">{{ session.memory[0]?.content || '空对话' }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          

        </div>
        
        <!-- 右侧显示区域 -->
        <div class="main-container">
          <!-- 最终结果显示框 -->
          <div class="result-container" :class="{ 'processing': isProcessing }">
            <!-- 顶部区域，包含用户信息 -->
            <div class="top-user-section">
              <!-- 用户信息和操作按钮 - 放在流程框上方 -->
              <div class="user-avatar-container" ref="avatarContainerRef">
                <!-- 头像，点击时切换用户信息显示状态 -->
                <img 
                  src="https://p3-flow-imagex-sign.byteimg.com/user-avatar/assets/e7b19241fb224cea967dfaea35448102_1080_1080.png~tplv-a9rns2rl98-icon-tiny.png?rcl=202511070904143F9B891FA2E40D7123F0&rk3s=8e244e95&rrcfp=76e58463&x-expires=1765155855&x-signature=nqQBx1W9ABfrm%2FRKkEYZUzsYjE0%3D" 
                  class="user-avatar" 
                  alt="用户头像" 
                  @click="toggleUserInfo"
                  tabindex="0"
                />
                
                <!-- 用户信息下拉框，点击头像时显示/隐藏 -->
                <div class="user-info-dropdown" v-show="showUserInfo">
                  <template v-if="currentUser">
                    <span class="user-name">{{ currentUser }}</span>
                    <button data-testid="setup_logout" class="btn-tertiary" style="width: 100%; justify-content: flex-start;" @click="handleLogout"><span role="img" class="semi-icon semi-icon-default text-16"><svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" fill="none" viewBox="0 0 24 24"><path fill="currentColor" fill-rule="evenodd" d="M14 3H4.5v18H14v-5h2v5a2 2 0 0 1-2 2H4.5a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2H14a2 2 0 0 1 2 2v5h-2zm5.207 4.793a1 1 0 1 0-1.414 1.414L19.586 11H10.5a1 1 0 1 0 0 2h9.086l-1.793 1.793a1 1 0 0 0 1.414 1.414l3.5-3.5a1 1 0 0 0 0-1.414z" clip-rule="evenodd"></path></svg></span>退出登录</button>
                  </template>
                  <template v-else>
                    <span class="user-name">当前未登录</span>
                    <button class="login-button btn-primary" @click="goToLogin">请登录</button>
                  </template>
                </div>
              </div>
            </div>

          
            
            <!-- 统一的消息展示区域 -->
            <div class="chat-message-container" ref="processContent">
              <div v-for="(msg, index) in chatMessages" :key="index" :class="['message-wrapper', msg.type]">
                 <!-- 用户消息 -->
                 <div v-if="msg.type === 'user'" class="user-message-bubble">
                   <div class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
                 </div>

                 <!-- 思考过程 - 带折叠功能的灰色区域 -->
                 <div v-else-if="msg.type === 'THINKING'" class="thinking-section">
                   <div class="thinking-header" @click="toggleThinking(index)">
                     <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="thinking-icon-brain">
                       <path d="M12 2a9 9 0 0 0-9 9v4a9 9 0 0 0 18 0v-4a9 9 0 0 0-9-9z"/>
                       <path d="M12 2v20"/>
                       <path d="M2 11h20"/>
                     </svg>
                     <span class="thinking-label">{{ isProcessing && index === chatMessages.length - 1 ? '🤔 思考中...' : '💭 思考过程' }}</span>
                     <svg
                       xmlns="http://www.w3.org/2000/svg"
                       width="16"
                       height="16"
                       viewBox="0 0 24 24"
                       fill="none"
                       stroke="currentColor"
                       stroke-width="2"
                       stroke-linecap="round"
                       stroke-linejoin="round"
                       class="thinking-toggle-icon"
                       :class="{ 'collapsed': msg.collapsed }"
                     >
                       <polyline points="6 9 12 15 18 9"></polyline>
                     </svg>
                   </div>
                   <div class="thinking-content" v-show="!msg.collapsed">
                     <div class="thinking-text" v-html="renderMarkdown(msg.content)"></div>
                   </div>
                 </div>

                 <!-- 助手回答 - 清晰的白色区域 -->
                 <div v-else-if="msg.type === 'assistant'" class="assistant-answer-section">
                   <div class="assistant-header">
                     <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="assistant-icon">
                       <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                     </svg>
                     <span class="assistant-label">✨ 回答</span>
                   </div>
                   <div class="assistant-content">
                     <div class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
                   </div>
                 </div>
              </div>
            </div>
              
              <!-- 用户输入框 - 移动到最终结果输出框内 -->
              <div class="input-container">
                <div class="textarea-with-button">
                  <textarea
                    v-model="userInput"
                    placeholder="请输入您的请求..."
                    @keyup.enter.exact="handleSend($event)"
                    :disabled="isProcessing"
                  ></textarea>
                  <button 
                    class="send-button btn-primary"
                    :class="{ 'cancel-button': isProcessing, 'disabled': !userInput.trim() && !isProcessing }"
                    :disabled="!userInput.trim() && !isProcessing"
                    @click="isProcessing ? handleCancel() : handleSend()"
                  >
                    {{ isProcessing ? '■' : '发送' }}
                  </button>
                </div>
              </div>
          </div>
        </div>
      </div>
      </template>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick, onUnmounted } from 'vue';
import { marked } from 'marked';

// Configure marked options
marked.setOptions({
  breaks: true, // Enable line breaks
  gfm: true,    // Enable GitHub Flavored Markdown
});

// 使用marked库进行markdown渲染
const renderMarkdown = (text) => {
  if (!text) return '';
  try {
    return marked.parse(text);
  } catch (e) {
    console.error('Markdown parsing error:', e);
    return text;
  }
};

export default {
  name: 'App',
  setup() {
    // 登录相关状态
    const isLoggedIn = ref(true);
    // 侧边栏展开/收起状态
    const isSidebarExpanded = ref(true);
    const username = ref('');
    const password = ref('');
    const currentUser = ref('');
    const loginError = ref('');
    // 用户信息显示状态（用于头像点击显示用户信息）
    const showUserInfo = ref(false);
    // 头像和下拉框的引用
    const avatarContainerRef = ref(null);
    
    // 切换用户信息显示/隐藏
    const toggleUserInfo = () => {
      showUserInfo.value = !showUserInfo.value;
    };

    // 点击外部收起下拉菜单
    const handleClickOutside = (event) => {
      // 关闭用户信息下拉框
      if (showUserInfo.value && avatarContainerRef.value && !avatarContainerRef.value.contains(event.target)) {
        showUserInfo.value = false;
      }
      

    };
    
    // 生命周期钩子：组件挂载后添加事件监听器
    onMounted(() => {
      document.addEventListener('click', handleClickOutside);
    });
    
    // 生命周期钩子：组件卸载前移除事件监听器
    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside);
    });
    
    // 初始化时检查localStorage中的用户信息，恢复currentUser
    const savedUserId = localStorage.getItem('currentUserId');
    if (savedUserId) {
      // 定义测试用户列表，与handleLogin中保持一致
      const validUsers = [
        { username: 'root1', password: '123456', userId: 'root1' },
        { username: 'root2', password: '123456', userId: 'root2' },
        { username: 'root3', password: '123456', userId: 'root3' }
      ];
      
      // 查找对应的用户并设置currentUser
      const savedUser = validUsers.find(u => u.userId === savedUserId);
      if (savedUser) {
        currentUser.value = savedUser.username;
      }
    }
    
    // 主界面相关状态
    const userInput = ref('');
    const chatMessages = ref([]); // Unified chat history: { type: 'user'|'assistant'|'THINKING'|'PROCESS', content: string }
    const processMessages = ref([]); // Deprecated, kept for safety
    const answerText = ref(''); // Deprecated, kept for safety
    const processContent = ref(null);
    const isProcessing = ref(false); // 标记是否正在处理请求
    let reader = null; // 保存读取器引用，用于取消请求
    
    // 当前选中的导航项
    const selectedNavItem = ref('');
    


    // 切换思考过程的折叠状态
    const toggleThinking = (index) => {
      const msg = chatMessages.value[index];
      if (msg && msg.type === 'THINKING') {
        msg.collapsed = !msg.collapsed;
      }
    };
    
    // 暴露给模板
    // return {
    //   toggleThinking,
    //   isLoggedIn,
    //   username,
    //   password,
    //   currentUser,
    

    
    // 处理知识库查询
    const handleKnowledgeBase = () => {
      console.log('打开知识库查询');
      // 清空右侧内容但保持页面结构不变
      processMessages.value = [];
      answerText.value = '';
      processContent.value = null;
      selectedNavItem.value = 'knowledge';
      // 清除历史会话选中状态
      selectedSessionId.value = '';
    };
    
    // 处理服务站查询
    const handleNetworkSearch = () => {
  selectedNavItem.value = 'network';
  selectedSessionId.value = '';
  // 联网搜索功能逻辑可以在这里实现
};

const handleServiceStation = () => {
      console.log('打开服务站查询');
      // 清空右侧内容但保持页面结构不变
      processMessages.value = [];
      answerText.value = '';
      processContent.value = null;
      selectedNavItem.value = 'service';
      // 清除历史会话选中状态
      selectedSessionId.value = '';
    };
    
    // 历史会话相关状态
    const sessions = ref([]);
    const selectedSessionId = ref('');
    const isLoadingSessions = ref(false);
    const showSessions = ref(true); // 控制历史会话的显示/隐藏
    
    // 切换历史会话的显示/隐藏
    const toggleSessions = () => {
      showSessions.value = !showSessions.value;
    };

    // 处理登录
    const handleLogin = () => {
      // 清空错误信息
      loginError.value = '';
      
      // 定义测试用户列表
      const validUsers = [
        { username: 'root1', password: '123456', userId: 'root1' },
        { username: 'root2', password: '123456', userId: 'root2' },
        { username: 'root3', password: '123456', userId: 'root3' }
      ];
      
      // 查找用户
      const user = validUsers.find(u => u.username === username.value && u.password === password.value);
      
      if (user) {
        // 登录成功
        isLoggedIn.value = true;
        currentUser.value = user.username;
        // 保存用户ID（在实际应用中可能会保存token）
        localStorage.setItem('currentUserId', user.userId);
        // 登录成功后执行页面滚动到顶部
        window.scrollTo(0, 0);
        // 清空输入
        username.value = '';
        password.value = '';
      } else {
        // 登录失败
        loginError.value = '用户名或密码错误';
      }
    };

    // 获取历史会话数据
    const fetchUserSessions = async () => {
      if (!currentUser.value) return;
      
      isLoadingSessions.value = true;
      try {
        const response = await fetch('http://127.0.0.1:8000/api/user_sessions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({"user_id": currentUser.value})
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        if (data.success && data.sessions) {
          sessions.value = data.sessions;
          // 默认选择最新的会话
          if (data.sessions.length > 0 && !selectedSessionId.value) {
            selectSession(data.sessions[0].session_id);
          }
        }
      } catch (error) {
        console.error('Error fetching sessions:', error);
      } finally {
        isLoadingSessions.value = false;
        // 刷新会话列表后：确保最终结果框滚动到底部
        scrollToBottom();
      }
    };


    
    // 新建会话
    const createNewSession = () => {
      // 生成新的会话ID (使用时间戳+随机数确保唯一性)
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // 创建新会话对象
      const newSession = {
        session_id: newSessionId,
        create_time: new Date().toISOString(),
        memory: [],
        total_messages: 0
      };
      
      // 将新会话添加到会话列表的最前面
      sessions.value.unshift(newSession);
      
      // 清空当前内容
      processMessages.value = [];
      answerText.value = '';
      userInput.value = '';
      
      // 选中新会话
      selectSession(newSessionId);
    };
    
    // 选择会话
    const selectSession = (sessionId) => {
      selectedSessionId.value = sessionId;
      // 清除导航项选中状态
      selectedNavItem.value = '';
      // 找到选中的会话
      const session = sessions.value.find(s => s.session_id === sessionId);
      
      // 清空当前内容
      chatMessages.value = [];
      processMessages.value = [];
      answerText.value = '';
      
      if (session && session.memory && Array.isArray(session.memory) && session.memory.length > 0) {
        let lastType = null;
        
        session.memory.forEach(msg => {
          if (!msg || !msg.content) return;
          
          // 映射角色类型
          let type = msg.role;
          if (type === 'process') type = 'THINKING';
          
          // 合并连续的思考过程
          if (type === 'THINKING' && lastType === 'THINKING') {
            const lastMsg = chatMessages.value[chatMessages.value.length - 1];
            lastMsg.content += '\n' + msg.content;
          } else {
            chatMessages.value.push({
              type: type, // 'user', 'assistant', 'THINKING'
              content: msg.content
            });
          }
          lastType = type;
        });
        
        // 滚动到底部
        nextTick(() => {
          scrollToBottom();
        });
      }
    };
    
    // 处理登出
    const handleLogout = () => {
      isLoggedIn.value = false;
      currentUser.value = '';
      localStorage.removeItem('currentUserId');
      // 清空聊天内容
      processMessages.value = [];
      answerText.value = '';
      userInput.value = '';
      // 清空会话列表
      sessions.value = [];
      selectedSessionId.value = '';
    };
    
    // 跳转到登录页面
    const goToLogin = () => {
      isLoggedIn.value = false;
      currentUser.value = '';
      localStorage.removeItem('currentUserId');
    };
    
    // 处理发送请求
      const handleSend = async (event) => {
        // 阻止回车键的默认行为（插入换行）
        if (event) {
          event.preventDefault();
        }
        if (!userInput.value.trim()) return;
        
        // 立即强制滚动到页面顶部，防止页面下移
        window.scrollTo(0, 0);
        
        // 检查登录状态，只有点击发送时才检查
        const userId = localStorage.getItem('currentUserId');
        if (!userId) {
          // 如果没有登录凭证，跳转到登录页面
          isLoggedIn.value = false;
          return;
        }
        
        // 设置处理状态
        isProcessing.value = true;
        
        // 自动收起之前的思考过程
        chatMessages.value.forEach(msg => {
          if (msg.type === 'THINKING') {
            msg.collapsed = true;
          }
        });
        
        // 清空中间流程消息，但保留最终结果框中的历史会话内容
        // 注意：请求结束后会保留处理过程中的最后一条消息
        processMessages.value = [];
        
        // 将会话显示逻辑与历史会话保持一致：添加用户消息
        chatMessages.value.push({
          type: 'user',
          content: userInput.value.trim()
        });
        
        // 兼容旧变量（防止其他引用报错）
        const userMessage = `<div class="user-message">${userInput.value.trim()}</div>\n\n`;
        if (selectedSessionId.value && answerText.value) {
          answerText.value += userMessage;
        } else {
          answerText.value = userMessage;
        }
        
        // 确保userId有值，使用currentUser作为备选
        const finalUserId = userId || currentUser.value;
        
        // 请求发起时：添加用户消息后立即滚动到结果框底部
        scrollToBottom();
        
        // 准备请求数据，包含用户ID和选中的会话ID
        const requestData = {
          query: userInput.value.trim(),
          context: { 
            user_id: finalUserId,
            session_id: selectedSessionId.value || ''
          }
        };
        

        
        console.log('发送请求，会话ID:', selectedSessionId.value);
        
        console.log('发送请求，用户ID:', finalUserId);
        
        try {
          // 调用后端API
          const response = await fetch('http://127.0.0.1:8000/api/v2/query', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
          });
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          // 处理流式响应
        reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) {
              // 处理最后一块数据
              if (buffer.trim()) {
                processSSEData(buffer);
                buffer = ''; // 清空缓冲区
              }
              break;
            }
          
          // 解码数据并累积到缓冲区
          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          
          // 按行分割并处理完整的行
          const lines = buffer.split('\n');
          
          // 除了最后一行（可能不完整）外，处理所有行
          for (let i = 0; i < lines.length - 1; i++) {
            const line = lines[i];
            if (line.trim()) {
              processSSEData(line);
            }
          }
          
          // 保留最后一行作为不完整的缓冲区
          buffer = lines[lines.length - 1];
        }
          
        } catch (error) {
          if (!error.name || error.name !== 'AbortError') {
            const errorMsg = `请求失败: ${error.message}`;
            streamTextToProcess(errorMsg + '\n');
            processMessages.value.push({
              type: 'PROCESS',
              text: errorMsg
            });
            console.error('Error:', error);
          }
        } finally {
          isProcessing.value = false;
          reader = null;
          
          // 请求结束时：确保最终结果框滚动到底部
          scrollToBottom();

          // 请求结束后，不自动收起思考过程，保持展开状态以便用户查看
          // const lastMsg = chatMessages.value[chatMessages.value.length - 1];
          // for (let i = chatMessages.value.length - 1; i >= 0; i--) {
          //    if (chatMessages.value[i].type === 'THINKING') {
          //      chatMessages.value[i].collapsed = true;
          //      break; 
          //    }
          // }
          
          // 会话请求结束后刷新历史会话区域
          fetchUserSessions();
        }
        
        // 清空输入框
        userInput.value = '';
      };
      
      // 处理SSE格式的数据
    const processSSEData = (data) => {
      try {
        if (typeof data !== 'string') return;

        if (data.startsWith('data:')) {
          const jsonStr = data.substring(5).trim();

          if (jsonStr) {
            try {
              const parsedData = JSON.parse(jsonStr);

              let kind; // 变量名改为 kind
              let text;

              // -----------------------------------------------------------
              // 适配新的 StreamPacket 结构
              // 结构: { content: { kind: "...", text: "...", ... }, ... }
              // -----------------------------------------------------------
              if (parsedData.content && typeof parsedData.content === 'object') {
                // 1. 获取文本内容
                text = parsedData.content.text;

                // 2. 获取内容分类 (kind)
                if (parsedData.content.kind) {
                  // 新版后端字段名为 kind
                  kind = parsedData.content.kind;
                } else if (parsedData.content.type) {
                  // 兼容旧版字段名 type
                  kind = parsedData.content.type;
                }

                // 3. 处理结束信号 (如果内容是 FinishMessageBody)
                if (parsedData.status === 'FINISHED' || parsedData.content.contentType === 'sagegpt/finish') {
                   // 可以在这里处理结束逻辑，目前前端主要靠流结束自动处理
                   return;
                }
              }

              // -----------------------------------------------------------
              // 降级兼容旧逻辑 (防止后端回滚导致前端挂掉)
              // -----------------------------------------------------------
              else if (parsedData.type && parsedData.content) {
                kind = parsedData.type;
                text = parsedData.content;
              }

              // -----------------------------------------------------------
              // 根据 kind 分发处理逻辑
              // -----------------------------------------------------------
              if (kind && text) {
                console.log('Processing kind:', kind, 'text:', text); // 调试日志

                switch (kind) {
                  case 'ANSWER':
                    stopThinkingAnimation();
                    streamTextToAnswer(text);
                    break;

                  case 'THINKING':
                    streamTextToProcess(text);
                    break;

                  case 'PROCESS':
                    streamTextToProcess(text + '\n');
                    // 兼容旧的 processMessages 数组
                    processMessages.value = [...processMessages.value, {
                      type: 'PROCESS', // 前端内部状态可以暂时保留叫 type，或者你也想改成 kind？建议暂时不动内部状态
                      text: text
                    }];
                    scrollToBottom();
                    break;

                  default:
                    console.log('Unknown content kind:', kind);
                    // 默认作为 PROCESS 处理
                    streamTextToProcess(text + '\n');
                }
              }
            } catch (jsonError) {
              console.error('JSON parse error:', jsonError);
            }
          }
        }
      } catch (error) {
        console.error('Error processing SSE data:', error);
      }
    };
      
      // 处理取消请求
      const handleCancel = () => {
        if (reader) {
          reader.cancel();
          reader = null;
        }
        isProcessing.value = false;
        // 取消请求时停止思考动画
        stopThinkingAnimation();
        
        streamTextToProcess('请求已取消\n');
        processMessages.value.push({
          type: 'PROCESS',
          text: '请求已取消'
        });
      };

    // 移除未使用的handleStreamingResponse函数

    // 流式更新答案文本（使用Markdown渲染）
    const streamTextToAnswer = (text) => {
      // 忽略打断思考过程的纯空白字符
      const lastMsg = chatMessages.value[chatMessages.value.length - 1];
      if ((!text || !text.trim()) && lastMsg && lastMsg.type !== 'assistant') {
        return;
      }

      // 处理文本：将多个空格替换为单个空格，多个换行替换为单个换行
      text = text
      // .replace(/[ \t]+/g, ' ')  // 将多个连续空白字符（包括空格、制表符等）替换为单个空格
      .replace(/ +/g, ' ')  // 将多个连续空白字符（包括空格、制表符等）替换为单个空格
      .replace(/\n+/g, '\n'); // 将多个连续换行符替换为单个换行符
      
      // 更新统一的聊天记录
      // const lastMsg = chatMessages.value[chatMessages.value.length - 1]; // 已在函数开头声明
      if (lastMsg && lastMsg.type === 'assistant') {
        lastMsg.content += text;
      } else {
        chatMessages.value.push({ type: 'assistant', content: text });
      }
      chatMessages.value = [...chatMessages.value]; // Trigger reactivity
      
      // 兼容旧变量
      answerText.value += text;
      
      // 后端返回数据时：确保最终结果框滚动到底部
      scrollToBottom();
    };
    
    // 流式更新处理消息
    const streamTextToProcess = (text) => {
      // 过滤掉纯JSON格式的思考过程（如意图识别结果）
      // 检测是否为JSON对象（包含 l1_intent, l2_intent 等字段）
      try {
        const trimmedText = text.trim();
        // 如果文本看起来像JSON对象，尝试解析
        if (trimmedText.startsWith('{') && trimmedText.includes('"l1_intent"')) {
          const parsed = JSON.parse(trimmedText);
          // 如果成功解析且包含意图识别字段，则跳过显示
          if (parsed.l1_intent || parsed.l2_intent) {
            console.log('过滤掉JSON格式的意图识别结果:', parsed);
            return; // 不显示这类内容
          }
        }
      } catch (e) {
        // 不是有效的JSON，继续正常处理
      }

      // 更新统一的聊天记录
      const lastMsg = chatMessages.value[chatMessages.value.length - 1];
      if (lastMsg && lastMsg.type === 'THINKING') {
        lastMsg.content += text;
        // 如果是新消息且正在处理中，确保展开
        if (isProcessing.value && lastMsg.collapsed === undefined) {
           // 使用 reactive 属性，初始化为 false (展开)
           lastMsg.collapsed = false;
        }
      } else {
        chatMessages.value.push({
          type: 'THINKING',
          content: text,
          collapsed: false // 默认为展开状态
        });
      }
      chatMessages.value = [...chatMessages.value];
      
      // 兼容旧变量
      const lastProcessMsg = processMessages.value[processMessages.value.length - 1];
      if (lastProcessMsg && lastProcessMsg.type === 'THINKING') {
        lastProcessMsg.text += text;
        processMessages.value = [...processMessages.value];
      } else {
        processMessages.value = [...processMessages.value, {
          type: 'THINKING',
          text: text
        }];
      }
      
      scrollToBottom();
    };
    
    // 移除旧的思考动画逻辑，避免覆盖文本内容
    const startThinkingAnimation = () => {
      // 这里的逻辑已移除，由CSS处理动画效果
    };
    
    // 停止思考动画
    const stopThinkingAnimation = () => {
      // 这里的逻辑已移除
    };
    
    // 保留上面的processSSEData函数实现
      
      // 处理响应数据（兼容旧格式）
      const handleResponseData = (data) => {
        if (data.type === 'ANSWER') {
          // 收到答案时停止思考动画
          stopThinkingAnimation();
          streamTextToAnswer(data.content);
        } else if (data.type === 'THINKING') {
          // THINKING内容使用streamTextToProcess函数处理
          streamTextToProcess(data.content);
        } else if (data.type === 'PROCESS') {
          // 收到其他处理消息时停止思考动画
          stopThinkingAnimation();
          processMessages.value.push({ type: 'PROCESS', text: data.content });
          scrollToBottom();
        }
      };

    // 滚动到底部
    const scrollToBottom = () => {
      setTimeout(() => {
        // 滚动新的消息容器
        const chatContainer = document.querySelector('.chat-message-container');
        if (chatContainer) {
          chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // 确保页面不整体滚动，无条件强制滚动到顶部
        window.scrollTo(0, 0);
      }, 0);
    };

    // 监听登录状态变化，登录成功后获取会话列表
    watch(isLoggedIn, (newVal) => {
      if (newVal && currentUser.value) {
        fetchUserSessions();
      }
    });
    
    // 组件挂载时检查登录状态并获取会话列表
    onMounted(() => {
      if (isLoggedIn.value && currentUser.value) {
        fetchUserSessions();

        // 组件挂载默认加载时：确保最终结果框滚动到底部
        nextTick(() => {
          scrollToBottom();
        });
      }
      
      // 添加键盘快捷键监听器
      document.addEventListener('keydown', handleKeyDown);
    });
    
    onUnmounted(() => {
      // 移除键盘快捷键监听器
      document.removeEventListener('keydown', handleKeyDown);
    });
    
    // 处理键盘快捷键
    const handleKeyDown = (event) => {
      // Ctrl+K 快捷键新建会话
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        createNewSession();
      }
    };
    
    // 切换侧边栏展开/收起状态
    const toggleSidebar = () => {
      isSidebarExpanded.value = !isSidebarExpanded.value;
      console.log('侧边栏状态:', isSidebarExpanded.value ? '展开' : '收起');
    };
    
    return {
      // 登录相关状态
      isLoggedIn,
      username,
      password,
      currentUser,
      loginError,
      showUserInfo,
      toggleUserInfo,
      avatarContainerRef,
      handleLogin,
      handleLogout,
      goToLogin,
      // 主界面相关
      userInput,
      chatMessages,
      processMessages,
      answerText,
      processContent,
      isProcessing,
      handleSend,
      handleCancel,
      renderMarkdown,
      // 历史会话相关
      sessions,
      selectedSessionId,
      isLoadingSessions,
      showSessions,
      toggleSessions,
      // 导航栏相关
      selectedNavItem,
      handleKnowledgeBase,
  handleNetworkSearch,
  handleServiceStation,
      selectSession,
      fetchUserSessions,
      createNewSession,

      // 侧边栏相关
      isSidebarExpanded,
      toggleSidebar,
      // 思考过程相关
      toggleThinking
    };
  }
};
</script>

<style scoped>
/* ==================== 消息容器样式 ==================== */
.chat-message-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 20px;
  padding-bottom: 140px; /* 增加底部内边距，避免被输入框遮挡 */
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

.message-wrapper {
  width: 100%;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ==================== 用户消息样式 ==================== */
.user-message-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 18px;
  border-radius: 18px 18px 4px 18px;
  max-width: 70%;
  margin-left: auto;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  word-wrap: break-word;
}

.user-message-bubble .markdown-body {
  color: white;
}

.user-message-bubble .markdown-body * {
  color: white !important;
}

/* ==================== 思考过程样式 ==================== */
.thinking-section {
  background: #fef3c7 !important;
  border: 2px solid #fbbf24 !important;
  border-radius: 12px;
  padding: 14px 18px;
  margin: 8px 0 20px 0;
  box-shadow: 0 2px 8px rgba(251, 191, 36, 0.15) !important;
  position: relative;
}

.thinking-section::after {
  content: '';
  position: absolute;
  bottom: -12px;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  height: 2px;
  background: linear-gradient(to right, transparent, #d1d5db, transparent);
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
  padding: 6px 0;
  transition: all 0.2s ease;
}

.thinking-header:hover {
  opacity: 0.85;
}

.thinking-icon-brain {
  color: #b45309 !important;
  flex-shrink: 0;
}

.thinking-label {
  font-weight: 700 !important;
  font-size: 14px !important;
  color: #92400e !important;
  flex: 1;
}

.thinking-toggle-icon {
  transition: transform 0.3s ease;
  color: #b45309 !important;
  flex-shrink: 0;
}

.thinking-toggle-icon.collapsed {
  transform: rotate(-90deg);
}

.thinking-content {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 2px solid #f59e0b !important;
}

.thinking-text {
  font-size: 14px !important;
  color: #6b7280 !important;
  line-height: 1.7;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  white-space: pre-wrap;
  word-break: break-word;
  font-weight: 500 !important;
  opacity: 0.85;
}

.thinking-text .markdown-body {
  background: transparent !important;
  color: #6b7280 !important;
}

.thinking-text .markdown-body * {
  color: #6b7280 !important;
  font-weight: 500 !important;
}

/* ==================== 助手回答样式 ==================== */
.assistant-answer-section {
  background: white;
  border: 2px solid #e3f2fd;
  border-radius: 12px;
  padding: 16px 20px;
  margin: 20px 0 8px 0;
  box-shadow: 0 2px 12px rgba(33, 150, 243, 0.08);
}

.assistant-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e3f2fd;
}

.assistant-icon {
  color: #2196F3;
  flex-shrink: 0;
}

.assistant-label {
  font-weight: 700;
  font-size: 16px;
  color: #1976D2;
}

.assistant-content {
  font-size: 16px;
  line-height: 1.8;
  color: #000000 !important;
  font-weight: 600 !important;
}

.assistant-content .markdown-body {
  background: transparent;
  color: #000000 !important;
}

.assistant-content .markdown-body p {
  margin: 12px 0;
  color: #000000 !important;
  font-weight: 600 !important;
}

.assistant-content .markdown-body h1,
.assistant-content .markdown-body h2,
.assistant-content .markdown-body h3 {
  color: #000000 !important;
  margin-top: 20px;
  margin-bottom: 12px;
  font-weight: 700 !important;
}

.assistant-content .markdown-body ul,
.assistant-content .markdown-body ol {
  margin: 12px 0;
  padding-left: 28px;
  color: #000000 !important;
}

.assistant-content .markdown-body li {
  margin: 6px 0;
  color: #000000 !important;
  font-weight: 600 !important;
}

.assistant-content .markdown-body code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 14px;
  color: #000000 !important;
  font-weight: 600 !important;
}

.assistant-content .markdown-body pre {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.assistant-content .markdown-body pre code {
  background: transparent;
  padding: 0;
  color: #000000 !important;
  font-weight: 600 !important;
}

/* ==================== 滚动条美化 ==================== */
.chat-message-container::-webkit-scrollbar {
  width: 8px;
}

.chat-message-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.chat-message-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.chat-message-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* ==================== 应用容器样式 ==================== */
.app-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 5px;
  padding-bottom: 10px;
  box-sizing: border-box;
  min-height: 100vh;
  overflow: hidden;
}

/* ==================== 主内容区域布局 ==================== */
.main-content {
  display: flex;
  flex: 1;
  gap: 20px;
  overflow: hidden;
}

/* 左侧历史会话列表样式 */
.sessions-sidebar {
  width: 300px;
  background-color: #fff;
  border: 1px solid #ccc;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.sidebar-header {
  padding: 15px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.refresh-button {
  padding: 6px 12px;
  background-color: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.refresh-button:hover:not(:disabled) {
  background-color: #1976D2;
}

.refresh-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.sessions-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}



/* 登录页面样式 */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  padding: 20px;
}

.login-form {
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  text-align: center;
}

.login-logo {
  margin: 0 auto 20px;
}

.login-title {
  margin: 0 0 30px;
  font-size: 28px;
  font-weight: 700;
  color: #333;
  background: linear-gradient(90deg, #4CAF50, #2196F3);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-input-group {
  margin-bottom: 20px;
  text-align: left;
}

.login-input-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
}

.login-input-group input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.3s ease;
  box-sizing: border-box;
}

.login-input-group input:focus {
  outline: none;
  border-color: #2196F3;
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
}

.login-error {
  color: #f44336;
  margin-bottom: 20px;
  padding: 10px;
  background-color: #ffebee;
  border-radius: 4px;
}

.login-button {
    width: 100%;
    padding: 14px;
    background-color: #2196F3;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }

  .login-button:hover {
    background-color: #1976D2;
  }

.login-hint {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 6px;
  font-size: 14px;
  color: #666;
}

.login-hint p {
  margin: 5px 0;
}

/* 用户信息和登出按钮 */
.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.current-user {
  font-size: 14px;
  color: #666;
  font-weight: 500;
  white-space: nowrap;
}

.logout-button {
  padding: 8px 10.67px;
  background-color: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.logout-button:hover {
  background-color: #d32f2f;
}

/* 顶部标题区域 */
.app-header {
  background-color: white;
  border-radius: 8px;
  padding: 10px 15px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-branding {
  display: flex;
  align-items: center;
  gap: 15px;
}

/* 扁平风格Logo */
.its-logo-flat {
  display: flex;
  align-items: center;
  justify-content: center;
}

.its-logo-flat svg {
  filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.1));
}

/* 扁平风格标题 */
.its-title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 1px;
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  text-transform: uppercase;
  /* 蓝色渐变效果 */
  background: linear-gradient(90deg, #2196F3, #90CAF9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-fill-color: transparent;
}

.display-container {
  display: flex;
  flex: 1;
  overflow: hidden;
  margin-top: 5px;
  margin-bottom: 5px;
  min-height: 500px; /* 设置最小高度确保有足够空间显示 */
}

.result-container {
  flex: 1;
  padding: 15px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  box-sizing: border-box;
  border-radius: 8px;
  border: 1px solid #fff;
}

/* 程序处理中时的渐变闪烁动画 */
.result-container.processing {
  animation: gradient-pulse 1.5s infinite ease-in-out;
}

@keyframes gradient-pulse {
  0% {
    border-color: #fff;
  }
  50% {
    border-color: #2196F3; /* 蓝色边框 */
  }
  100% {
    border-color: #fff;
  }
}


/* 中间流程框样式 */
.process-container {
  width: 100%;
  max-height: 30%; /* 限制最大高度 */
  min-height: 100px;
  margin: 0 0 15px 0; /* 正常的下边距 */
  padding: 10px;
  background-color: #f8f9fa; 
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}

.process-container h3,
.result-container h3 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
}

/* 确保标题前有小图标提示 */
.process-container h3::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 16px;
  background-color: #2196F3;
  margin-right: 8px;
  border-radius: 2px;
}

.process-content {
    flex: 1;
    overflow-y: auto;
    padding: 5px;
    background-color: white;
    border-radius: 4px;
    font-size: 13px;
    border: 1px solid #eee;
  }

.result-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 10px 10px 10px; /* 将上边距减小到0 */
  background-color: white;
  border-radius: 4px;
  white-space: pre-wrap;
  text-align: left;
  font-size: 14px;
  margin-top: 0; /* 确保上边距为0 */
}

.message-item {
    margin-bottom: 8px;
    padding: 5px;
    border-radius: 4px;
    text-align: left;
    line-height: 1.5;
    word-wrap: break-word;
    font-size: 16px !important;
  }

  /* 添加markdown样式 */
  .markdown {
    font-size: 16px !important;
    line-height: 1.6 !important;
  }

  .markdown .paragraph {
    margin-bottom: 16px !important;
    font-size: 16px !important;
    line-height: 1.8 !important;
    color: #333 !important;
  }
  
  /* 确保结果内容中的文本样式 */
  .result-content {
    font-size: 16px !important;
  }
  
  /* 确保段落样式 */
  .result-content p {
    font-size: 16px !important;
    line-height: 1.8 !important;
    margin-bottom: 1px !important;
    margin-top: 1px !important;
    color: #333 !important;
    display: inline-block !important;
  }
  
  /* 添加更多样式以确保匹配用户要求的格式 */
  .result-content > div {
    font-size: 16px !important;
    line-height: 1.8 !important;
  }
  
  /* 确保所有文本元素的样式 */
  .result-content * {
    font-size: 16px !important;
    line-height: 1.8 !important;
    color: #333 !important;
  }
  
  /* 使用深度选择器确保样式穿透组件边界 */
  :deep(.result-content) {
    font-size: 16px !important;
  }
  
  :deep(.result-content) * {
    font-size: 16px !important;
    line-height: 1.8 !important;
    color: #333 !important;
  }
  
  /* 确保段落样式 */
  :deep(.result-content p) {
    font-size: 16px !important;
    line-height: 1.8 !important;
    margin-bottom: 1px !important;
    margin-top: 1px !important;
    color: #333 !important;
    display: inline-block !important;
  }

  /* 用户消息样式 - 右对齐、宽度限制（不超过三分之二）、背景色 */
  /* 在结果框中为用户消息添加样式 */
  :deep(.result-content) {
    position: relative;
  }
  
  :deep(.result-content) [v-pre] {
    white-space: pre-wrap;
    word-break: break-word;
  }
  
  /* 使用CSS伪元素和属性选择器处理标记的用户消息 */
  :deep(.result-content) [v-pre] {
    line-height: 1.6;
  }
  
  /* 用户消息样式 - 使用正则匹配[USER]标记的消息 */
  :deep(.result-content) [v-pre] {
    /* 基础样式 */
    font-size: 14px;
  }
  
  /* 为最终结果框中的用户消息和助手消息添加样式 */
  :deep(.result-content) .user-message {
    background-color: #f5f5f5; /* 浅灰色背景 */
    color: #1565c0;
    display: inline-block; /* 使元素宽度适应内容 */
    text-align: left; /* 默认左对齐 */
    margin-left: auto;
    margin-right: 0;
    max-width: 66.6%; /* 不超过容器的三分之二 */
    border-radius: 8px;
    padding: 10px 15px;
    margin-bottom: 8px;
    word-break: break-word;
    line-height: 1.6;
    white-space: pre-wrap;
  }
  
  /* 使用伪元素技巧实现单行右对齐，多行左对齐 */
  :deep(.result-content) .user-message {
    text-align: left;
  }

  /* 让整个消息块右对齐 */
  :deep(.result-content) {
    text-align: left;
  }
  
  /* 确保助手消息仍然左对齐 */
  :deep(.result-content) .assistant-message {
    text-align: left;
    display: block;
  }
  
  :deep(.result-content) .assistant-message {
    background-color: #ffffff; /* 白色背景 */
    color: #333;
    text-align: left;
    margin-left: 0;
    margin-right: auto;
    max-width: 100%;
    padding: 10px 15px;
    margin-bottom: 8px;
    word-break: break-word;
    line-height: 1.6;
  }
  
  /* 保留.message-item.user样式，以备后续可能的其他用途 */
  .message-item.user {
    background-color: #e3f2fd;
    color: #1565c0;
    text-align: right;
    margin-left: auto;
    max-width: 66.6%; /* 不超过容器的三分之二 */
    border-radius: 8px;
    padding: 10px;
  }

  .message-item.THINKING {
    background-color: #f0f7ff;
    color: #0066cc;
    white-space: pre-wrap; /* 保留空格和换行，但长行依然换行 */
    word-break: break-all; /* 确保超长单词能被截断 */
  }

  .message-item.PROCESS {
    background-color: #f0f7ff;
    color: #0066cc;
    /*background-color: #fff9f0;
    color: #cc6600;
    font-weight: bold; */
  }

  /* Markdown 样式 */
  :deep(h1) {
    font-size: 24px;
    margin: 16px 0 8px;
    color: #333;
  }

  :deep(h2) {
    font-size: 20px;
    margin: 14px 0 7px;
    color: #444;
  }

  :deep(h3) {
    font-size: 18px;
    margin: 12px 0 6px;
    color: #555;
  }

  :deep(p) {
    margin: 8px 0;
    line-height: 1.6;
  }

  :deep(ul), :deep(ol) {
    margin: 8px 0;
    padding-left: 24px;
  }

  :deep(li) {
    margin: 4px 0;
  }

  :deep(pre) {
    background-color: #f5f5f5;
    padding: 12px;
    border-radius: 4px;
    overflow-x: auto;
    font-family: 'Courier New', monospace;
  }

  :deep(code) {
    background-color: #f5f5f5;
    padding: 2px 4px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
  }

  :deep(strong) {
    font-weight: bold;
  }

  :deep(em) {
    font-style: italic;
  }

  :deep(a) {
    color: #2196f3;
    text-decoration: none;
  }

  :deep(a:hover) {
    text-decoration: underline;
  }

.input-container {
  padding: 0;
  margin-top: auto;
}

.textarea-with-button {
  position: relative;
  display: inline-block;
  width: 100%;
  max-width: 50vw;
}

.textarea-with-button textarea {
  width: 100%;
  padding: 12px 48px 12px 12px;
  border: 1px solid #ccc;
  border-radius: 12px;
  resize: none;
  height: 100px;
  font-size: 16px;
  font-family: inherit;
}

.textarea-with-button .send-button {
  position: absolute;
  bottom: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background-color: #4CAF50;
  color: white;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

  .textarea-with-button textarea:focus {
    outline: none;
    border-color: #4CAF50;
    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
  }
  
  /* Send button styles removed from App.vue to use style.css */

  .textarea-with-button textarea:disabled {
    background-color: #f5f5f5;
    cursor: not-allowed;
  }

  .input-container button {
    padding: 12px 24px;
    background-color: #2196F3;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 500;
    transition: background-color 0.3s ease;
  }

  .input-container button:hover {
    background-color: #1976D2;
  }

  .input-container button:active {
    background-color: #1565C0;
  }

  .input-container button.cancel-button {
    background-color: #f44336;
    width: 40px;
    padding: 12px;
    font-size: 16px;
    line-height: 1;
  }

  .input-container button.cancel-button:hover {
    background-color: #d32f2f;
  }

/* 美化滚动条 - 默认隐藏，鼠标悬停时显示 */
.process-content::-webkit-scrollbar {
  width: 0;
  position: absolute;
  right: 0;
  transition: width 0.2s ease;
}

.process-content::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

.process-content::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.process-content::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* 鼠标悬停时显示滚动条 */
.process-content:hover::-webkit-scrollbar {
  width: 8px;
}

/* 最终结果框滚动条样式 - 默认隐藏，鼠标悬停时显示 */
.result-content::-webkit-scrollbar {
  width: 0;
  position: absolute;
  right: 0;
  transition: width 0.2s ease;
}

.result-content:hover::-webkit-scrollbar {
  width: 8px;
}

.result-content::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

.result-content::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.result-content::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-container {
    padding: 8px;
    gap: 8px;
  }
  
  .display-container {
    flex-direction: column;
    gap: 15px;
  }
  
  .process-container,
  .result-container {
    min-height: 180px;
  }
  
  .input-container textarea {
    height: 80px;
    font-size: 14px;
  }
  
  /* 响应式登录页面 */
  .login-form {
    padding: 30px 20px;
  }
  
  .login-title {
    font-size: 24px;
  }
  
  /* 响应式顶部导航 */
  .app-header {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
  
  .user-info {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .app-container {
    padding: 10px;
    gap: 10px;
  }
  
  .process-container h3,
  .result-container h3 {
    font-size: 16px;
  }
  
  .input-container {
    flex-direction: column;
  }
  
  .input-container button {
    align-self: flex-end;
    padding: 10px 20px;
  }
  
  /* 小屏幕登录页面 */
  .login-form {
    padding: 20px 15px;
  }
  
  .login-logo svg {
    width: 50px;
    height: 50px;
  }
}
.model-down {
     padding-left: 50px;
     margin-top: 10px;
}
</style>
