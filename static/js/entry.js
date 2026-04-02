// 数据录入页面专用JavaScript

let currentTab = 'transaction';
let recentTransactions = [];
let recentLoans = [];

function initEntryPage() {
    try {
        // 设置默认日期为今天
        const today = new Date().toISOString().split('T')[0];
        document.querySelectorAll('input[type="date"]').forEach(input => {
            input.value = today;
        });

        // 绑定表单提交事件 - 检查表单是否存在
        const transactionForm = document.getElementById('transaction-form');
        const loanForm = document.getElementById('loan-form');
        const editForm = document.getElementById('edit-form');
        const batchForm = document.getElementById('batch-form');
        
        if (transactionForm) transactionForm.addEventListener('submit', handleTransactionSubmit);
        if (loanForm) loanForm.addEventListener('submit', handleLoanSubmit);
        if (editForm) editForm.addEventListener('submit', handleEditSubmit);
        if (batchForm) batchForm.addEventListener('submit', handleBatchSubmit);

        // 加载账户列表
        loadAccountsForSelect();

        // 加载最近记录
        loadRecentTransactions();
        if (loanForm) loadRecentLoans();
        
        // 不再自动检查URL中的edit参数，编辑交易只通过点击按钮触发
    } catch (error) {
        console.error('initEntryPage执行错误:', error);
    }
}

// 加载账户下拉选择
async function loadAccountsForSelect() {
    try {
        const resp = await fetch('/api/accounts');
        const accounts = await resp.json();
        const select = document.getElementById('account-select');
        if (!select) return;
        
        // 保留"请选择账户"选项
        select.innerHTML = '<option value="">请选择账户</option>';
        accounts.forEach(a => {
            const opt = document.createElement('option');
            opt.value = a.id;
            opt.textContent = `${a.name}（余额: ¥${a.current_balance.toFixed(2)}）`;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error('加载账户失败', e);
    }
}

async function loadTransactionForEdit(id) {
    try {
        const response = await fetch('/api/transactions/' + id);
        if (response.ok) {
            const transaction = await response.json();
            openEditModal(transaction);
        }
    } catch (error) {
        console.error('加载交易失败:', error);
    }
}

// 切换标签页
function switchTab(tab) {
    currentTab = tab;
    
    // 更新按钮状态
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // 更新内容显示
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tab + '-tab').classList.add('active');
}

// 显示提示消息
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast ' + type;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// 处理交易表单提交
async function handleTransactionSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    // 转换account_id为整数
    if (data.account_id) {
        data.account_id = parseInt(data.account_id);
    }
    
    try {
        const response = await fetch('/api/transactions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast('交易保存成功！');
            e.target.reset();
            
            // 重置日期为今天
            document.querySelector('#transaction-form input[name="date"]').value = 
                new Date().toISOString().split('T')[0];
            
            // 刷新最近记录
            loadRecentTransactions();
            
            // 添加到最近记录列表
            recentTransactions.unshift(result);
            renderRecentTransactions();
        } else {
            showToast('保存失败，请重试', 'error');
        }
    } catch (error) {
        console.error('保存交易失败:', error);
        showToast('保存失败，请检查网络连接', 'error');
    }
}

// 处理借款表单提交
async function handleLoanSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch('/api/loans', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast('借款保存成功！');
            e.target.reset();
            
            // 重置日期为今天
            document.querySelector('#loan-form input[name="date"]').value = 
                new Date().toISOString().split('T')[0];
            
            // 刷新最近记录
            loadRecentLoans();
        } else {
            showToast('保存失败，请重试', 'error');
        }
    } catch (error) {
        console.error('保存借款失败:', error);
        showToast('保存失败，请检查网络连接', 'error');
    }
}

// 加载最近的交易记录
async function loadRecentTransactions() {
    try {
        const response = await fetch('/api/transactions?page=1&per_page=5');
        const data = await response.json();
        recentTransactions = data.transactions;
        renderRecentTransactions();
    } catch (error) {
        console.error('加载交易记录失败:', error);
    }
}

// 渲染最近交易记录
function renderRecentTransactions() {
    const tbody = document.getElementById('recent-transactions');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    recentTransactions.forEach(transaction => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatDateTime(transaction.created_at)}</td>
            <td><span class="type-badge ${transaction.type}">${transaction.type}</span></td>
            <td>${transaction.category || '-'}</td>
            <td>${transaction.description || '-'}</td>
            <td class="amount ${transaction.type}">${formatAmount(transaction.amount)}</td>
            <td>
                <div class="action-btns">
                    <button class="btn-edit" onclick="editTransaction(${transaction.id})">编辑</button>
                    <button class="btn-delete" onclick="deleteTransaction(${transaction.id})">删除</button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 加载最近的借款记录
async function loadRecentLoans() {
    try {
        const response = await fetch('/api/loans');
        const loans = await response.json();
        recentLoans = loans.slice(0, 5);
        renderRecentLoans();
    } catch (error) {
        console.error('加载借款记录失败:', error);
    }
}

// 渲染最近借款记录
function renderRecentLoans() {
    const tbody = document.getElementById('recent-loans');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    recentLoans.forEach(loan => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatDateTime(loan.created_at)}</td>
            <td>${loan.lender}</td>
            <td class="amount">${formatAmount(loan.amount)}</td>
            <td><span class="status-badge ${loan.status === '已归还' ? 'returned' : 'unreturned'}">${loan.status}</span></td>
            <td>
                <div class="action-btns">
                    ${loan.status !== '已归还' ? `<button class="btn-edit" onclick="returnLoan(${loan.id})">归还</button>` : ''}
                    <button class="btn-delete" onclick="deleteLoan(${loan.id})">删除</button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 编辑交易
async function editTransaction(id) {
    const transaction = recentTransactions.find(t => t.id === id);
    if (!transaction) {
        // 从服务器获取
        try {
            const response = await fetch(`/api/transactions?page=1&per_page=1000`);
            const data = await response.json();
            transaction = data.transactions.find(t => t.id === id);
        } catch (error) {
            showToast('获取交易信息失败', 'error');
            return;
        }
    }
    
    if (transaction) {
        openEditModal(transaction);
    }
}

function openEditModal(transaction) {
    document.querySelector('#edit-form input[name="id"]').value = transaction.id;
    document.querySelector('#edit-form input[name="date"]').value = transaction.date;
    document.querySelector('#edit-form select[name="type"]').value = transaction.type;
    document.querySelector('#edit-form input[name="category"]').value = transaction.category || '';
    document.querySelector('#edit-form input[name="amount"]').value = transaction.amount;
    document.querySelector('#edit-form textarea[name="description"]').value = transaction.description || '';
    document.querySelector('#edit-form textarea[name="remark"]').value = transaction.remark || '';
    
    // 设置账户
    loadAccountsForEditSelect(transaction.account_id);
    
    document.getElementById('edit-modal').style.display = 'block';
}

async function loadAccountsForEditSelect(selectedId) {
    try {
        const resp = await fetch('/api/accounts');
        const accounts = await resp.json();
        const select = document.getElementById('edit-account-select');
        if (!select) return;
        
        select.innerHTML = '<option value="">请选择账户</option>';
        accounts.forEach(a => {
            const opt = document.createElement('option');
            opt.value = a.id;
            opt.textContent = `${a.name}（余额: ¥${a.current_balance.toFixed(2)}）`;
            if (a.id == selectedId) opt.selected = true;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error('加载账户失败', e);
    }
}

// 关闭编辑弹窗
function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

// 处理编辑表单提交
async function handleEditSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    const id = data.id;
    delete data.id;
    
    // 转换account_id为整数
    if (data.account_id) {
        data.account_id = parseInt(data.account_id);
    } else {
        delete data.account_id;
    }
    
    try {
        const response = await fetch(`/api/transactions/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('修改成功！');
            closeEditModal();
            loadRecentTransactions();
        } else {
            showToast('修改失败，请重试', 'error');
        }
    } catch (error) {
        console.error('修改交易失败:', error);
        showToast('修改失败，请检查网络连接', 'error');
    }
}

// 删除交易
async function deleteTransaction(id) {
    if (!confirm('确定要删除这条交易记录吗？')) return;
    
    try {
        const response = await fetch(`/api/transactions/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('删除成功！');
            loadRecentTransactions();
        } else {
            showToast('删除失败，请重试', 'error');
        }
    } catch (error) {
        console.error('删除交易失败:', error);
        showToast('删除失败，请检查网络连接', 'error');
    }
}

// 批量录入预览
function previewBatch() {
    const textarea = document.querySelector('#batch-form textarea[name="batch-data"]');
    const data = textarea.value.trim();
    
    if (!data) {
        showToast('请输入批量数据', 'error');
        return;
    }
    
    const lines = data.split('\n');
    const previewBody = document.getElementById('preview-body');
    previewBody.innerHTML = '';
    
    let validCount = 0;
    let errorCount = 0;
    
    lines.forEach((line, index) => {
        if (!line.trim()) return;
        
        // 跳过表头行
        if (line.includes('日期') && line.includes('收支分类') && line.includes('明细分类') && line.includes('金额')) {
            return;
        }
        
        // 改进解析逻辑：先识别字段分隔符，再处理千分位
        let parts = [];
        
        // 尝试按制表符分割（最可靠）
        if (line.includes('\t')) {
            parts = line.split('\t');
        }
        // 尝试按竖线分割
        else if (line.includes('|')) {
            parts = line.split('|');
        }
        // 如果是逗号分隔，需要更复杂的逻辑来区分千分位
        else if (line.includes(',')) {
            // 使用正则表达式匹配：逗号前后都是数字的视为千分位，否则视为分隔符
            const tempLine = line.replace(/(\d),(?=\d{3}(\D|$))/g, '$1'); // 先移除千分位逗号
            parts = tempLine.split(',');
        }
        // 如果没有明显分隔符，尝试按空格分割
        else {
            parts = line.split(/\s+/);
        }
        
        // 过滤掉空字符串
        const filteredParts = parts.filter(part => part.trim() !== '');
        
        const row = document.createElement('tr');
        row.className = 'preview-row';
        
        if (filteredParts.length >= 5) {
            let date = filteredParts[0].trim();
            let type = filteredParts[1].trim();
            const category = filteredParts[2].trim();
            const description = filteredParts[3].trim();
            let amountStr = filteredParts[4].trim();
            
            // 处理金额格式
            // 1. 移除所有逗号（千分位）
            amountStr = amountStr.replace(/,/g, '');
            // 2. 移除¥符号和其他非数字字符，保留负号
            amountStr = amountStr.replace(/[^0-9.-]/g, '');
            
            // 确保金额字符串不为空
            if (!amountStr) {
                row.className = 'preview-row error';
                row.innerHTML = `
                    <td colspan="6" style="text-align: center; color: #ef4444;">金额为空: ${line}</td>
                `;
                errorCount++;
                previewBody.appendChild(row);
                return;
            }
            
            // 转换日期格式：2025/1/9 -> 2025-01-09
            if (date.includes('/')) {
                const dateParts = date.split('/');
                if (dateParts.length === 3) {
                    const year = dateParts[0];
                    const month = dateParts[1].padStart(2, '0');
                    const day = dateParts[2].padStart(2, '0');
                    date = `${year}-${month}-${day}`;
                }
            }
            
            // 转换收支分类：保持原分类不变
            if (type === '出账') {
                type = '出账';
            } else if (type === '入账') {
                type = '入账';
            }
            
            // 解析金额
            const amount = parseFloat(amountStr);
            
            // 根据收支分类处理金额
            let finalAmount = amount;
            if (type === '出账' && amount > 0) {
                // 出账部分：如果金额是正数，转换为负数
                finalAmount = -Math.abs(amount);
            } else if (type === '入账' && amount < 0) {
                // 入账部分：如果金额是负数，转换为正数
                finalAmount = Math.abs(amount);
            }
            
            // 确保金额有效
            const positiveAmount = Math.abs(finalAmount);
            
            const isValid = date && type && category && !isNaN(positiveAmount) && positiveAmount > 0;
            
            row.className = isValid ? 'preview-row success' : 'preview-row error';
            row.innerHTML = `
                <td>${date}</td>
                <td>${type}</td>
                <td>${category}</td>
                <td>${description}</td>
                <td>${isNaN(positiveAmount) ? '无效' : formatAmount(positiveAmount)}</td>
                <td>${isValid ? '✓ 有效' : '✗ 无效'}</td>
            `;
            
            if (isValid) validCount++;
            else errorCount++;
        } else {
            row.className = 'preview-row error';
            row.innerHTML = `
                <td colspan="6" style="text-align: center; color: #ef4444;">格式错误: ${line}</td>
            `;
            errorCount++;
        }
        
        previewBody.appendChild(row);
    });
    
    document.getElementById('batch-preview').style.display = 'block';
    
    if (errorCount > 0) {
        showToast(`预览完成: ${validCount}条有效, ${errorCount}条无效`, 'info');
    } else {
        showToast(`预览完成: ${validCount}条数据待导入`, 'success');
    }
}

// 清空预览
function clearPreview() {
    document.getElementById('batch-preview').style.display = 'none';
    document.getElementById('preview-body').innerHTML = '';
}

// 处理批量提交
async function handleBatchSubmit(e) {
    console.log('handleBatchSubmit called');
    e.preventDefault();
    
    const textarea = document.querySelector('#batch-form textarea[name="batch-data"]');
    const data = textarea.value.trim();
    
    console.log('Batch data:', data);
    
    if (!data) {
        showToast('请输入批量数据', 'error');
        return;
    }
    
    const lines = data.split('\n');
    const transactions = [];
    
    lines.forEach(line => {
        if (!line.trim()) return;
        
        // 跳过表头行
        if (line.includes('日期') && line.includes('收支分类') && line.includes('明细分类') && line.includes('金额')) {
            return;
        }
        
        // 改进解析逻辑：先识别字段分隔符，再处理千分位
        let parts = [];
        
        // 尝试按制表符分割（最可靠）
        if (line.includes('\t')) {
            parts = line.split('\t');
        }
        // 尝试按竖线分割
        else if (line.includes('|')) {
            parts = line.split('|');
        }
        // 如果是逗号分隔，需要更复杂的逻辑来区分千分位
        else if (line.includes(',')) {
            // 使用正则表达式匹配：逗号前后都是数字的视为千分位，否则视为分隔符
            const tempLine = line.replace(/(\d),(?=\d{3}(\D|$))/g, '$1'); // 先移除千分位逗号
            parts = tempLine.split(',');
        }
        // 如果没有明显分隔符，尝试按空格分割
        else {
            parts = line.split(/\s+/);
        }
        
        // 过滤掉空字符串
        const filteredParts = parts.filter(part => part.trim() !== '');
        
        if (filteredParts.length >= 5) {
            let date = filteredParts[0].trim();
            let type = filteredParts[1].trim();
            const category = filteredParts[2].trim();
            const description = filteredParts[3].trim();
            let amountStr = filteredParts[4].trim();
            
            // 处理金额格式
            // 1. 移除所有逗号（千分位）
            amountStr = amountStr.replace(/,/g, '');
            // 2. 移除¥符号和其他非数字字符，保留负号
            amountStr = amountStr.replace(/[^0-9.-]/g, '');
            
            // 确保金额字符串不为空
            if (!amountStr) return;
            
            // 转换日期格式：2025/1/9 -> 2025-01-09
            if (date.includes('/')) {
                const dateParts = date.split('/');
                if (dateParts.length === 3) {
                    const year = dateParts[0];
                    const month = dateParts[1].padStart(2, '0');
                    const day = dateParts[2].padStart(2, '0');
                    date = `${year}-${month}-${day}`;
                }
            }
            
            // 转换收支分类：保持原分类不变
            if (type === '出账') {
                type = '出账';
            } else if (type === '入账') {
                type = '入账';
            }
            
            // 解析金额
            const amount = parseFloat(amountStr);
            
            // 根据收支分类处理金额
            let finalAmount = amount;
            if (type === '出账' && amount > 0) {
                // 出账部分：如果金额是正数，转换为负数
                finalAmount = -Math.abs(amount);
            } else if (type === '入账' && amount < 0) {
                // 入账部分：如果金额是负数，转换为正数
                finalAmount = Math.abs(amount);
            }
            
            // 确保金额有效
            const positiveAmount = Math.abs(finalAmount);
            
            if (date && type && category && !isNaN(positiveAmount) && positiveAmount > 0) {
                transactions.push({
                    date,
                    type,
                    category,
                    amount: positiveAmount,
                    description
                });
            }
        }
    });
    
    if (transactions.length === 0) {
        showToast('没有有效的数据可以导入', 'error');
        return;
    }
    
    // 显示导入进度
    const progressToast = document.createElement('div');
    progressToast.className = 'toast info';
    progressToast.style.position = 'fixed';
    progressToast.style.top = '50%';
    progressToast.style.left = '50%';
    progressToast.style.transform = 'translate(-50%, -50%)';
    progressToast.style.zIndex = '10000';
    progressToast.style.padding = '20px';
    progressToast.style.background = 'rgba(102, 126, 234, 0.9)';
    progressToast.style.color = 'white';
    progressToast.style.borderRadius = '10px';
    progressToast.style.textAlign = 'center';
    progressToast.style.minWidth = '200px';
    
    let successCount = 0;
    let errorCount = 0;
    
    // 禁用批量保存按钮，防止重复提交
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>导入中...</span>';
    
    // 显示进度弹窗
    progressToast.innerHTML = `
        <div style="font-size: 16px; font-weight: bold; margin-bottom: 10px;">批量导入中</div>
        <div style="font-size: 14px;">进度: 0/${transactions.length}</div>
        <div style="margin-top: 10px; width: 100%; height: 4px; background: rgba(255,255,255,0.3); border-radius: 2px;">
            <div style="width: 0%; height: 100%; background: white; border-radius: 2px; transition: width 0.3s;"></div>
        </div>
    `;
    document.body.appendChild(progressToast);
    
    for (let i = 0; i < transactions.length; i++) {
        const transaction = transactions[i];
        
        // 更新进度
        const progress = ((i + 1) / transactions.length) * 100;
        const progressBar = progressToast.querySelector('div:last-child > div');
        const progressText = progressToast.querySelector('div:nth-child(2)');
        
        if (progressBar) progressBar.style.width = progress + '%';
        if (progressText) progressText.textContent = `进度: ${i + 1}/${transactions.length}`;
        
        try {
            const response = await fetch('/api/transactions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(transaction)
            });
            
            if (response.ok) {
                successCount++;
            } else {
                errorCount++;
            }
        } catch (error) {
            errorCount++;
        }
        
        // 添加小延迟，避免请求过于密集
        await new Promise(resolve => setTimeout(resolve, 50));
    }
    
    // 移除进度弹窗
    document.body.removeChild(progressToast);
    
    // 恢复按钮状态
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
    
    if (errorCount === 0) {
        showToast(`成功导入 ${successCount} 条记录！`);
        textarea.value = '';
        clearPreview();
        loadRecentTransactions();
    } else {
        showToast(`导入完成: ${successCount}条成功, ${errorCount}条失败`, 'info');
    }
}

// 格式化日期时间
function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return '-';
    const date = new Date(dateTimeStr);
    return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 点击弹窗外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('edit-modal');
    if (event.target === modal) {
        closeEditModal();
    }
}
