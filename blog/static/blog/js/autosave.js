/* Simple autosave helper
   Usage:
   autosaveInit(selector, { saveUrl: '/autosave/', interval: 5000 })
*/
(function(window){
  function getCookie(name) {
    var v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
    return v ? v[2] : null;
  }

  function postJSON(url, data){
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(data),
      credentials: 'same-origin'
    }).then(function(r){ return r.json(); });
  }

  function autosaveInit(selector, opts){
    opts = opts || {};
    var el = document.querySelector(selector);
    if(!el) return;
    var saveUrl = opts.saveUrl || '/autosave/';
    var interval = opts.interval || 5000;
    var version = 1;
    var timer = null;

    function doSave(){
      var content = el.value || '';
      var titleEl = document.querySelector(opts.titleSelector || '#id_title');
      var title = titleEl ? titleEl.value : '';
      postJSON(saveUrl, { title: title, content: content, version: version }).then(function(resp){
        if(resp && resp.version) version = resp.version + 1;
      }).catch(function(){ /* ignore */ });
    }

    timer = setInterval(doSave, interval);
    // also save on page unload
    window.addEventListener('beforeunload', function(){ doSave(); });
    return { stop: function(){ clearInterval(timer); } };
  }

  window.autosaveInit = autosaveInit;
})(window);
/**
 * 文章自动保存功能
 */

class ArticleAutosave {
    constructor(options = {}) {
        // 默认配置
        this.config = {
            autoSaveInterval: 30000, // 30秒自动保存
            saveUrl: '/api/autosave/draft/',
            versionsUrl: '/api/autosave/versions/',
            restoreUrl: '/api/autosave/restore/',
            publishUrl: '/api/autosave/publish/',
            statusUrl: '/api/autosave/status/',
            articleId: null,
            csrfToken: this.getCsrfToken(),
            ...options
        };
        
        // 状态变量
        this.timer = null;
        this.isSaving = false;
        this.lastContent = '';
        this.lastTitle = '';
        this.hasUnsavedChanges = false;
        this.saveCount = 0;
        
        // DOM元素
        this.titleInput = null;
        this.contentInput = null;
        this.indicator = null;
        
        // 初始化
        this.init();
    }
    
    init() {
        console.log('文章自动保存功能初始化...');
        
        // 获取输入元素
        this.titleInput = document.querySelector('input[name="title"], #id_title');
        this.contentInput = document.querySelector('textarea[name="body"], #id_body');
        
        // 如果使用富文本编辑器（mdeditor）
        if (!this.contentInput) {
            // 尝试获取mdeditor的textarea
            this.contentInput = document.querySelector('.mdeditor-textarea');
        }
        
        if (!this.titleInput || !this.contentInput) {
            console.warn('未找到文章标题或内容输入框，自动保存功能未启用');
            return;
        }
        
        console.log('找到输入框，自动保存功能已启用');
        
        // 创建保存提示元素
        this.createIndicator();
        
        // 初始化内容
        this.lastContent = this.getContent();
        this.lastTitle = this.getTitle();
        
        // 绑定事件
        this.bindEvents();
        
        // 开始自动保存
        this.startAutoSave();
    }
    
    createIndicator() {
        // 创建保存状态提示元素
        this.indicator = document.createElement('div');
        this.indicator.id = 'autosave-indicator';
        this.indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 6px;
            background: white;
            border: 1px solid #ddd;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 9999;
            opacity: 0;
            transition: all 0.3s ease;
            font-size: 14px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            pointer-events: none;
            max-width: 300px;
        `;
        
        document.body.appendChild(this.indicator);
    }
    
    showIndicator(message, type = 'info') {
        const colors = {
            success: { bg: '#d4edda', border: '#c3e6cb', text: '#155724' },
            error: { bg: '#f8d7da', border: '#f5c6cb', text: '#721c24' },
            info: { bg: '#d1ecf1', border: '#bee5eb', text: '#0c5460' },
            warning: { bg: '#fff3cd', border: '#ffeaa7', text: '#856404' }
        };
        
        const color = colors[type] || colors.info;
        
        this.indicator.textContent = message;
        this.indicator.style.background = color.bg;
        this.indicator.style.borderColor = color.border;
        this.indicator.style.color = color.text;
        this.indicator.style.opacity = 1;
        
        // 3秒后淡出
        clearTimeout(this.indicatorTimeout);
        this.indicatorTimeout = setTimeout(() => {
            this.indicator.style.opacity = 0;
        }, 3000);
    }
    
    getTitle() {
        return this.titleInput.value || '';
    }
    
    getContent() {
        // 检查是否是富文本编辑器
        if (this.contentInput.classList && this.contentInput.classList.contains('mdeditor-textarea')) {
            // 对于mdeditor，直接获取值
            return this.contentInput.value || '';
        }
        return this.contentInput.value || '';
    }
    
    async saveDraft(saveType = 'auto') {
        // 防止重复保存
        if (this.isSaving) {
            return false;
        }
        
        const title = this.getTitle();
        const content = this.getContent();
        
        // 如果内容为空，不保存
        if (!title.trim() && !content.trim()) {
            return false;
        }
        
        // 检查内容是否有变化
        const currentContent = title + content;
        if (currentContent === this.lastContent) {
            return false;
        }
        
        this.isSaving = true;
        this.showIndicator('正在保存...', 'info');
        
        try {
            const data = {
                title: title,
                body: content,  // 注意：原Article模型使用body字段
                save_type: saveType
            };
            
            // 获取分类信息
            const categorySelect = document.querySelector('select[name="category"]');
            if (categorySelect && categorySelect.value) {
                data.category_id = categorySelect.value;
            }
            
            // 获取其他表单字段
            const showTocCheckbox = document.querySelector('input[name="show_toc"]');
            if (showTocCheckbox) {
                data.show_toc = showTocCheckbox.checked;
            }
            
            const orderInput = document.querySelector('input[name="article_order"]');
            if (orderInput) {
                data.article_order = parseInt(orderInput.value) || 0;
            }
            
            let url = this.config.saveUrl;
            if (this.config.articleId) {
                url = url + this.config.articleId + '/';
            }
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.config.csrfToken
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // 更新状态
                this.lastContent = currentContent;
                this.lastTitle = title;
                this.saveCount++;
                this.hasUnsavedChanges = false;
                
                // 如果是新文章，更新articleId
                if (result.data && result.data.article_id && !this.config.articleId) {
                    this.config.articleId = result.data.article_id;
                    console.log('新文章ID:', this.config.articleId);
                    
                    // 更新URL（如果是在编辑新文章）
                    if (window.history && window.history.replaceState) {
                        const newUrl = window.location.pathname.replace('/new/', `/${this.config.articleId}/edit/`);
                        window.history.replaceState({}, '', newUrl);
                    }
                }
                
                // 显示成功提示
                const time = result.data.human_time || '刚刚';
                const typeText = saveType === 'auto' ? '自动保存' : '手动保存';
                this.showIndicator(`${typeText}成功 (${time})`, 'success');
                
                // 更新页面状态显示
                this.updateStatusDisplay(result.data);
                
                return true;
            } else {
                throw new Error(result.message || '保存失败');
            }
            
        } catch (error) {
            console.error('保存草稿失败:', error);
            this.showIndicator(`保存失败: ${error.message}`, 'error');
            return false;
        } finally {
            this.isSaving = false;
        }
    }
    
    updateStatusDisplay(data) {
        // 更新页面上的状态显示
        let statusDiv = document.getElementById('draft-status-display');
        if (!statusDiv) {
            statusDiv = document.createElement('div');
            statusDiv.id = 'draft-status-display';
            statusDiv.style.cssText = `
                padding: 10px 15px;
                margin: 10px 0;
                border-radius: 5px;
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                font-size: 14px;
            `;
            
            // 添加到表单顶部
            const form = document.querySelector('form');
            if (form) {
                form.insertBefore(statusDiv, form.firstChild);
            }
        }
        
        const statusText = data.is_draft ? '草稿' : '已发布';
        const saveTypeText = data.save_type === 'auto' ? '自动' : '手动';
        statusDiv.innerHTML = `
            <strong>状态: ${statusText}</strong> | 
            最后${saveTypeText}保存: ${data.human_time} | 
            版本: ${data.version}
            ${this.config.articleId ? `<a href="#" class="view-versions" style="margin-left: 10px; color: #007bff;">查看版本历史</a>` : ''}
        `;
        
        // 绑定查看版本历史事件
        const viewLink = statusDiv.querySelector('.view-versions');
        if (viewLink) {
            viewLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.showVersionHistory();
            });
        }
    }
    
    startAutoSave() {
        // 清除现有定时器
        if (this.timer) {
            clearInterval(this.timer);
        }
        
        // 设置自动保存定时器
        this.timer = setInterval(() => {
            this.saveDraft('auto');
        }, this.config.autoSaveInterval);
        
        console.log(`自动保存已启动，间隔: ${this.config.autoSaveInterval/1000}秒`);
        
        // 页面加载后立即保存一次
        setTimeout(() => this.saveDraft('auto'), 5000);
    }
    
    stopAutoSave() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }
    
    bindEvents() {
        // 输入变化监听
        const inputHandler = () => {
            this.hasUnsavedChanges = true;
        };
        
        this.titleInput.addEventListener('input', inputHandler);
        this.titleInput.addEventListener('change', inputHandler);
        
        this.contentInput.addEventListener('input', inputHandler);
        this.contentInput.addEventListener('change', inputHandler);
        
        // 创建手动保存按钮
        this.createSaveButton();
        
        // 创建版本历史按钮
        this.createHistoryButton();
        
        // 页面离开提示
        window.addEventListener('beforeunload', (e) => {
            if (this.hasUnsavedChanges) {
                e.preventDefault();
                e.returnValue = '您有未保存的更改，确定要离开吗？';
                return e.returnValue;
            }
        });
        
        // 表单提交时标记为已保存
        const form = this.titleInput.closest('form');
        if (form) {
            form.addEventListener('submit', () => {
                this.hasUnsavedChanges = false;
            });
        }
    }
    
    createSaveButton() {
        // 查找现有的保存按钮
        let saveButton = document.querySelector('#save-draft-btn, .save-draft-btn');
        
        if (!saveButton) {
            // 创建手动保存按钮
            saveButton = document.createElement('button');
            saveButton.id = 'save-draft-btn';
            saveButton.type = 'button';
            saveButton.innerHTML = '💾 保存草稿';
            saveButton.style.cssText = `
                padding: 8px 16px;
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin: 10px 5px;
                font-size: 14px;
            `;
            
            // 添加到页面合适位置
            const form = this.titleInput.closest('form');
            if (form) {
                const submitButtons = form.querySelector('button[type="submit"], input[type="submit"]');
                if (submitButtons) {
                    submitButtons.parentNode.insertBefore(saveButton, submitButtons);
                } else {
                    form.appendChild(saveButton);
                }
            }
        }
        
        saveButton.addEventListener('click', (e) => {
            e.preventDefault();
            this.saveDraft('manual');
        });
    }
    
    createHistoryButton() {
        // 创建版本历史按钮
        const historyButton = document.createElement('button');
        historyButton.id = 'version-history-btn';
        historyButton.type = 'button';
        historyButton.innerHTML = '📜 版本历史';
        historyButton.style.cssText = `
            padding: 8px 16px;
            background: #17a2b8;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin: 10px 5px;
            font-size: 14px;
        `;
        
        // 添加到页面
        const saveButton = document.querySelector('#save-draft-btn');
        if (saveButton) {
            saveButton.parentNode.insertBefore(historyButton, saveButton.nextSibling);
        }
        
        historyButton.addEventListener('click', (e) => {
            e.preventDefault();
            this.showVersionHistory();
        });
    }
    
    getCsrfToken() {
        // 从cookie获取CSRF token
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        
        // 或者从meta标签获取
        if (!cookieValue) {
            const metaToken = document.querySelector('meta[name="csrf-token"]');
            if (metaToken) {
                cookieValue = metaToken.getAttribute('content');
            }
        }
        
        return cookieValue;
    }
    
    async showVersionHistory() {
        if (!this.config.articleId) {
            this.showIndicator('请先保存文章以查看版本历史', 'warning');
            return;
        }
        
        try {
            const response = await fetch(`${this.config.versionsUrl}${this.config.articleId}/`);
            const result = await response.json();
            
            if (result.success) {
                this.renderVersionHistory(result.versions, result.article_title);
            } else {
                throw new Error(result.message || '获取版本失败');
            }
        } catch (error) {
            console.error('获取版本历史失败:', error);
            this.showIndicator(`获取版本历史失败: ${error.message}`, 'error');
        }
    }
    
    renderVersionHistory(versions, articleTitle = '') {
        // 创建模态框
        const modal = document.createElement('div');
        modal.id = 'version-history-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        `;
        
        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: white;
            border-radius: 10px;
            padding: 25px;
            max-width: 800px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        `;
        
        let html = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #eee; padding-bottom: 10px;">
                <h3 style="margin: 0; color: #333;">${articleTitle || '文章'} - 版本历史</h3>
                <button id="close-modal" style="
                    background: none;
                    border: none;
                    font-size: 24px;
                    cursor: pointer;
                    color: #999;
                    padding: 0;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">×</button>
            </div>
            <div style="margin-bottom: 20px; color: #666; font-size: 14px;">
                最多显示最近10个版本，点击版本可查看详情
            </div>
            <div class="version-list">
        `;
        
        if (versions.length === 0) {
            html += `
                <div style="text-align: center; padding: 40px; color: #999; font-size: 16px;">
                    <div style="font-size: 48px; margin-bottom: 20px;">📝</div>
                    暂无版本历史
                </div>
            `;
        } else {
            versions.forEach((version, index) => {
                const isLatest = index === 0;
                const typeClass = version.save_type === 'manual' ? 'manual-save' : 'auto-save';
                const typeText = version.save_type === 'manual' ? '手动保存' : '自动保存';
                const statusText = version.status_display || '草稿';
                
                html += `
                    <div class="version-item" data-id="${version.id}" style="
                        padding: 15px;
                        border: 1px solid ${isLatest ? '#4CAF50' : '#eee'};
                        border-left: 4px solid ${version.save_type === 'manual' ? '#2196F3' : '#9C27B0'};
                        border-radius: 4px;
                        margin-bottom: 10px;
                        cursor: pointer;
                        transition: all 0.2s ease;
                        background: ${isLatest ? '#f8fff8' : 'white'};
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                            <div style="flex: 1;">
                                <div style="font-weight: bold; color: #333; margin-bottom: 5px;">
                                    ${version.title || '无标题'}
                                    ${isLatest ? '<span style="color: #4CAF50; font-size: 12px; margin-left: 8px;">(当前)</span>' : ''}
                                </div>
                                <div style="font-size: 13px; color: #666; margin-bottom: 8px;">
                                    ${version.body_preview}
                                </div>
                            </div>
                            <div>
                                <span class="save-type ${typeClass}" style="
                                    padding: 3px 10px;
                                    border-radius: 12px;
                                    font-size: 12px;
                                    font-weight: 500;
                                    background: ${version.save_type === 'manual' ? '#e3f2fd' : '#f3e5f5'};
                                    color: ${version.save_type === 'manual' ? '#1976d2' : '#7b1fa2'};
                                    white-space: nowrap;
                                    margin-left: 10px;
                                    display: block;
                                    margin-bottom: 5px;
                                ">
                                    ${typeText}
                                </span>
                                <span style="
                                    padding: 3px 10px;
                                    border-radius: 12px;
                                    font-size: 12px;
                                    font-weight: 500;
                                    background: #f8f9fa;
                                    color: #6c757d;
                                    white-space: nowrap;
                                    margin-left: 10px;
                                    display: block;
                                ">
                                    ${statusText}
                                </span>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 12px; color: #888;">
                            <span>版本 ${version.version}</span>
                            <span>${version.human_time} (${version.saved_at})</span>
                        </div>
                    </div>
                `;
            });
        }
        
        html += `
            </div>
            <div style="margin-top: 25px; text-align: center;">
                <button id="restore-btn" style="
                    padding: 10px 30px;
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 15px;
                    font-weight: 500;
                    transition: background 0.2s;
                    opacity: 0.5;
                    pointer-events: none;
                " disabled>恢复选中版本</button>
                <button id="close-btn" style="
                    padding: 10px 20px;
                    background: #f5f5f5;
                    color: #666;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 15px;
                    font-weight: 500;
                    transition: background 0.2s;
                    margin-left: 10px;
                ">关闭</button>
            </div>
        `;
        
        modalContent.innerHTML = html;
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        // 绑定事件
        let selectedVersionId = null;
        
        // 关闭按钮
        const closeModal = () => {
            document.body.removeChild(modal);
        };
        
        modal.querySelector('#close-modal').addEventListener('click', closeModal);
        modal.querySelector('#close-btn').addEventListener('click', closeModal);
        
        // 点击外部关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
        
        // 选择版本
        modal.querySelectorAll('.version-item').forEach(item => {
            item.addEventListener('click', (e) => {
                // 移除其他选中状态
                modal.querySelectorAll('.version-item').forEach(i => {
                    i.style.background = '';
                    i.style.boxShadow = 'none';
                });
                
                // 设置选中状态
                item.style.background = '#f0f7ff';
                item.style.boxShadow = '0 2px 8px rgba(33, 150, 243, 0.2)';
                selectedVersionId = item.dataset.id;
                
                // 启用恢复按钮
                const restoreBtn = modal.querySelector('#restore-btn');
                restoreBtn.disabled = false;
                restoreBtn.style.opacity = 1;
                restoreBtn.style.pointerEvents = 'auto';
            });
        });
        
        // 恢复按钮
        modal.querySelector('#restore-btn').addEventListener('click', async () => {
            if (!selectedVersionId) return;
            
            if (confirm('确定要恢复到这个版本吗？当前编辑的内容将会被替换。')) {
                try {
                    const response = await fetch(`${this.config.restoreUrl}${selectedVersionId}/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': this.config.csrfToken
                        }
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        // 更新编辑器内容
                        this.titleInput.value = result.data.title;
                        this.contentInput.value = result.data.body;
                        
                        // 更新最后保存的内容
                        this.lastContent = result.data.title + result.data.body;
                        this.lastTitle = result.data.title;
                        
                        this.showIndicator('已恢复到指定版本', 'success');
                        closeModal();
                        
                        // 保存当前状态
                        setTimeout(() => this.saveDraft('manual'), 500);
                    } else {
                        throw new Error(result.message);
                    }
                } catch (error) {
                    console.error('恢复版本失败:', error);
                    this.showIndicator(`恢复失败: ${error.message}`, 'error');
                }
            }
        });
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 检查当前页面是否是文章编辑页面
    const isEditPage = document.querySelector('input[name="title"], textarea[name="body"]');
    
    if (isEditPage) {
        // 获取文章ID
        let articleId = null;
        
        // 从URL中提取文章ID
        const pathMatch = window.location.pathname.match(/\/(\d+)\//);
        if (pathMatch) {
            articleId = pathMatch[1];
        }
        
        // 从隐藏字段获取
        if (!articleId) {
            const articleIdInput = document.querySelector('input[name="id"]');
            if (articleIdInput) {
                articleId = articleIdInput.value;
            }
        }
        
        // 初始化自动保存
        const autosave = new ArticleAutosave({
            articleId: articleId,
            csrfToken: document.querySelector('[name=csrfmiddlewaretoken]')?.value,
            autoSaveInterval: 30000,
        });
        
        // 如果是编辑已有文章，获取状态信息
        if (articleId) {
            fetch(`/api/autosave/status/${articleId}/`)
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        autosave.updateStatusDisplay(result.data);
                    }
                })
                .catch(error => console.error('获取状态失败:', error));
        }
    }
});