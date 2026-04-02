// 数据录入页面专用JavaScript



let currentTab = 'transaction';
let recentTransactions = [];
let recentLoans = [];

// 两级分类数据
const CATEGORIES = {
    "购物消费": ["日常家居", "个护美妆", "手机数码", "虚拟充值", "生活电器", "配饰腕表", "母婴玩具", "服饰运动", "宠物用品", "办公用品", "装修装饰"],
    "食品餐饮": ["早餐", "午餐", "晚餐", "饮料酒水", "休闲零食", "生鲜食品", "请客吃饭", "粮油调味"],
    "出行交通": ["保险", "打车", "公共交通", "停车费", "加油", "火车", "飞机", "保养修车"],
    "休闲娱乐": ["旅游度假", "电影唱歌", "运动健身", "足浴按摩", "棋牌桌游", "酒吧", "演出"],
    "居家生活": ["租金", "话费宽带", "电费", "水费", "燃气费", "物业费", "房租还贷", "车位费", "家政清洁"],
    "文化教育": ["学费", "书报杂志", "培训考试"],
    "送礼人情": ["孝敬长辈", "礼物", "借出", "红包", "打赏"],
    "健康医疗": ["滋补保健", "医院", "买药"],
    "其他": ["罚款赔偿", "理财支出", "慈善捐助"]
};

// 收入分类（单层，无明细）
const INCOME_CATEGORIES = ["工资", "奖金", "兼职外快", "补贴", "报销", "二手闲置", "理财盈利", "礼金人情", "中奖", "借入"];

function initEntryPage() {
    try {
        const today = new Date().toISOString().split('T')[0];
        document.querySelectorAll('input[type="date"]').forEach(input => {
            input.value = today;
        });

        const transactionForm = document.getElementById('transaction-form');
        const loanForm = document.getElementById('loan-form');
        const editForm = document.getElementById('edit-form');
        const transferForm = document.getElementById('transfer-form');
        const batchForm = document.getElementById('batch-form');
        
        if (transactionForm) transactionForm.addEventListener('submit', handleTransactionSubmit);
        if (loanForm) loanForm.addEventListener('submit', handleLoanSubmit);
        if (editForm) editForm.addEventListener('submit', handleEditSubmit);
        if (batchForm) batchForm.addEventListener('submit', handleBatchSubmit);
        if (transferForm) transferForm.addEventListener('submit', handleTransferSubmit);

        // 初始化：设置默认类型并填充下拉选项
        var typeSel = document.getElementById('type-select');
        if (typeSel) { typeSel.value = '支出'; updateCategoryByType(); }
        loadAccountsForSelect();
        loadRecentTransactions();
        if (loanForm) loadRecentLoans();
    } catch (error) {
        console.error('initEntryPage执行错误:', error);
    }
}

async function loadAccountsForSelect() {
    try {
        const resp = await fetch("/finapp/api/accounts", {credentials: "include"});
        const accounts = await resp.json();
        const select = document.getElementById('account-select');
        if (!select) return;
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

function updateSubCategories() {
    const category = document.getElementById('category-select').value;
    const subSelect = document.getElementById('sub-category-select');
    const subGroup = document.getElementById('sub-category-group');
    if (!subSelect) return;
    
    // 收入无明细
    if (!category || category === '收入') {
        if (subGroup) subGroup.style.display = 'none';
        return;
    }
    
    // 支出显示两级联动
    if (CATEGORIES[category]) {
        if (subGroup) subGroup.style.display = '';
        subSelect.innerHTML = '<option value="">请选择明细</option>';
        CATEGORIES[category].forEach(sub => {
            const opt = document.createElement('option');
            opt.value = sub;
            opt.textContent = sub;
            subSelect.appendChild(opt);
        });
    } else {
        if (subGroup) subGroup.style.display = 'none';
    }
}

function updateCategoryByType() {
    const type = document.getElementById('type-select').value;
    const catSelect = document.getElementById('category-select');
    const subSelect = document.getElementById('sub-category-select');
    const subGroup = document.getElementById('sub-category-group');
    if (!catSelect) return;
    
    catSelect.innerHTML = '<option value="">请选择分类</option>';
    if (subSelect) subSelect.innerHTML = '<option value="">请选择明细</option>';
    if (subGroup) subGroup.style.display = 'none';
    
    if (type === '收入') {
        INCOME_CATEGORIES.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            catSelect.appendChild(opt);
        });
    } else if (type === '支出') {
        Object.keys(CATEGORIES).forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            catSelect.appendChild(opt);
        });
    }
}

function updateEditSubCategories(selectedSub) {
    const category = document.getElementById('edit-category-select').value;
    const subSelect = document.getElementById('edit-sub-category-select');
    const subGroup = document.getElementById('edit-sub-category-group');
    if (!subSelect) return;
    
    if (!category || category === '收入' || !CATEGORIES[category]) {
        if (subGroup) subGroup.style.display = 'none';
        return;
    }
    
    if (subGroup) subGroup.style.display = '';
    subSelect.innerHTML = '<option value="">请选择明细</option>';
    CATEGORIES[category].forEach(sub => {
        const opt = document.createElement('option');
        opt.value = sub;
        opt.textContent = sub;
        if (sub === selectedSub) opt.selected = true;
        subSelect.appendChild(opt);
    });
}

function updateEditCategoryByType() {
    const type = document.getElementById('edit-type-select').value;
    const catSelect = document.getElementById('edit-category-select');
    const subSelect = document.getElementById('edit-sub-category-select');
    const subGroup = document.getElementById('edit-sub-category-group');
    if (!catSelect) return;
    
    catSelect.innerHTML = '<option value="">请选择分类</option>';
    if (subSelect) subSelect.innerHTML = '<option value="">请选择明细</option>';
    if (subGroup) subGroup.style.display = 'none';
    
    if (type === '收入') {
        INCOME_CATEGORIES.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            catSelect.appendChild(opt);
        });
    } else if (type === '支出') {
        Object.keys(CATEGORIES).forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            catSelect.appendChild(opt);
        });
    }
}

function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tab + '-tab').classList.add('active');
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast ' + type;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

async function handleTransactionSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    if (data.account_id) data.account_id = parseInt(data.account_id);
    
    if (!data.category) {
        showToast('请选择分类', 'error');
        return;
    }
    if (data.type === '支出' && !data.sub_category) {
        showToast('请选择明细', 'error');
        return;
    }
    
    try {
        const response = await fetch('/finapp/api/transactions', {credentials:"include", 
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast('交易保存成功！');
            e.target.reset();
            document.querySelector('#transaction-form input[name="date"]').value = new Date().toISOString().split('T')[0];
            loadRecentTransactions();
            loadAccountsForSelect();
        } else {
            showToast('保存失败，请重试', 'error');
        }
    } catch (error) {
        console.error('保存交易失败:', error);
        showToast('保存失败，请检查网络连接', 'error');
    }
}

async function handleLoanSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    try {
        const response = await fetch('/finapp/api/loans', {credentials:"include", 
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (response.ok) {
            showToast('借款保存成功！');
            e.target.reset();
            document.querySelector('#loan-form input[name="date"]').value = new Date().toISOString().split('T')[0];
            loadRecentLoans();
        } else {
            showToast('保存失败，请重试', 'error');
        }
    } catch (error) {
        showToast('保存失败，请检查网络连接', 'error');
    }
}

async function loadRecentTransactions() {
    try {
        const response = await fetch('/finapp/api/transactions?page=1&per_page=5', {credentials: "include"});
        const data = await response.json();
        recentTransactions = data.transactions || [];
        renderRecentTransactions();
    } catch (error) {
        console.error('加载交易记录失败:', error);
    }
}

function renderRecentTransactions() {
    const tbody = document.getElementById('recent-transactions');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (recentTransactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999;">暂无记录</td></tr>';
        return;
    }
    recentTransactions.forEach(transaction => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatDateTime(transaction.created_at)}</td>
            <td><span class="type-badge ${transaction.type}">${transaction.type}</span></td>
            <td>${transaction.category || '-'}</td>
            <td>${transaction.description || '-'}</td>
            <td class="amount ${transaction.type}">${formatAmount(transaction.amount)}</td>
            <td>
                <button class="btn-edit" onclick="editTransaction(${transaction.id})">编辑</button>
                <button class="btn-delete" onclick="deleteTransaction(${transaction.id})">删除</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

async function loadRecentLoans() {
        try {
            const response = await fetch('/finapp/api/loans', {credentials:"include", method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data)});
            const loans = await response.json();
            recentLoans = (loans || []).slice(0, 5);
            renderRecentLoans();
        } catch (error) {
            console.error('加载借款记录失败:', error);
        }
    }

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
                ${loan.status !== '已归还' ? `<button class="btn-edit" onclick="returnLoan(${loan.id})">归还</button>` : ''}
                <button class="btn-delete" onclick="deleteLoan(${loan.id})">删除</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

async function editTransaction(id) {
        try {
            const response = await fetch(`/finapp/api/transactions/${id}`, {credentials:"include", method: "DELETE"});
            if (response.ok) {
                const transaction = await response.json();
                openEditModal(transaction);
            }
        } catch (error) {
        showToast('获取交易信息失败', 'error');
    }
}

function openEditModal(transaction) {
    document.querySelector('#edit-form input[name="id"]').value = transaction.id;
    document.querySelector('#edit-form input[name="date"]').value = transaction.date;
    document.querySelector('#edit-form select[name="type"]').value = transaction.type;
    document.querySelector('#edit-form input[name="amount"]').value = transaction.amount;
    document.querySelector('#edit-form textarea[name="description"]').value = transaction.description || '';
    document.querySelector('#edit-form textarea[name="remark"]').value = transaction.remark || '';
    
    // 设置两级分类：先填type触发updateEditCategoryByType，再设category和sub_category
    const typeSelect = document.getElementById('edit-type-select');
    if (typeSelect) {
        typeSelect.value = transaction.type || '';
        updateEditCategoryByType();
        const catSelect = document.getElementById('edit-category-select');
        if (catSelect) {
            catSelect.value = transaction.category || '';
            if (transaction.type === '支出') {
                updateEditSubCategories(transaction.sub_category || '');
            }
        }
    }
    
    // 设置账户
    loadAccountsForEditSelect(transaction.account_id);
    
    document.getElementById('edit-modal').style.display = 'block';
}

async function loadAccountsForEditSelect(selectedId) {
    try {
        const resp = await fetch("/finapp/api/accounts", {credentials: "include"});
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

function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

async function handleEditSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    const id = data.id;
    delete data.id;
    
    if (data.account_id) data.account_id = parseInt(data.account_id);
    else delete data.account_id;
    
    if (!data.category) {
        showToast('请选择分类', 'error');
        return;
    }
    if (data.type === '支出' && !data.sub_category) {
        showToast('请选择明细', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/finapp/api/transactions/${id}`, {credentials:"include", 
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
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
        showToast('修改失败，请检查网络连接', 'error');
    }
}

async function deleteTransaction(id) {
    if (!confirm('确定要删除这条交易记录吗？')) return;
    try {
        const response = await fetch(`/finapp/api/transactions/${id}`, {credentials:"include", method: "DELETE"});
        if (response.ok) {
            showToast('删除成功！');
            loadRecentTransactions();
            loadAccountsForSelect();
        } else {
            showToast('删除失败，请重试', 'error');
        }
    } catch (error) {
        showToast('删除失败，请检查网络连接', 'error');
    }
}

async function returnLoan(id) {
    try {
        await fetch(`/finapp/api/loans/${id}`, {credentials:"include", 
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({status: '已归还', return_date: new Date().toISOString().split('T')[0]})
        });
        showToast('已标记为归还');
        loadRecentLoans();
    } catch (error) {
        showToast('操作失败', 'error');
    }
}

async function deleteLoan(id) {
    if (!confirm('确定删除？')) return;
    try {
        await fetch(`/finapp/api/loans/${id}`, {credentials:"include", method: "DELETE"});
        showToast('删除成功');
        loadRecentLoans();
    } catch (error) {
        showToast('删除失败', 'error');
    }
}

function previewBatch() {
    const textarea = document.querySelector('#batch-form textarea[name="batch-data"]');
    const data = textarea.value.trim();
    if (!data) { showToast('请输入批量数据', 'error'); return; }
    const lines = data.split('\n');
    const previewBody = document.getElementById('preview-body');
    previewBody.innerHTML = '';
    let validCount = 0, errorCount = 0;
    lines.forEach(line => {
        if (!line.trim()) return;
        if (line.includes('日期') && line.includes('收支分类') && line.includes('明细分类') && line.includes('金额')) return;
        let parts = [];
        if (line.includes('\t')) parts = line.split('\t');
        else if (line.includes('|')) parts = line.split('|');
        else if (line.includes(',')) parts = line.replace(/(\d),(?=\d{3}(\D|$))/g, '$1').split(',');
        else parts = line.split(/\s+/);
        const filteredParts = parts.filter(p => p.trim() !== '');
        const row = document.createElement('tr');
        if (filteredParts.length >= 5) {
            let date = filteredParts[0].trim();
            let type = filteredParts[1].trim();
            const category = filteredParts[2].trim();
            const description = filteredParts[3].trim();
            let amountStr = filteredParts[4].replace(/,/g, '').replace(/[^0-9.-]/g, '');
            if (!amountStr) { row.className = 'preview-row error'; row.innerHTML = `<td colspan="6" style="color:#ef4444;">金额无效: ${line.substring(0,30)}...</td>`; errorCount++; previewBody.appendChild(row); return; }
            if (date.includes('/')) { const d = date.split('/'); date = `${d[0]}-${d[1].padStart(2,'0')}-${d[2].padStart(2,'0')}`; }
            const amount = Math.abs(parseFloat(amountStr));
            const isValid = date && type && category && !isNaN(amount) && amount > 0;
            row.className = isValid ? 'preview-row success' : 'preview-row error';
            row.innerHTML = `<td>${date}</td><td>${type}</td><td>${category}</td><td>${description}</td><td>${formatAmount(amount)}</td><td>${isValid ? '✓' : '✗'}</td>`;
            if (isValid) validCount++; else errorCount++;
        } else {
            row.className = 'preview-row error';
            row.innerHTML = `<td colspan="6" style="color:#ef4444;">格式错误</td>`;
            errorCount++;
        }
        previewBody.appendChild(row);
    });
    document.getElementById('batch-preview').style.display = 'block';
    showToast(`预览: ${validCount}条有效, ${errorCount}条无效`, errorCount > 0 ? 'info' : 'success');
}

function clearPreview() {
    document.getElementById('batch-preview').style.display = 'none';
    document.getElementById('preview-body').innerHTML = '';
}

async function handleBatchSubmit(e) {
    e.preventDefault();
    const textarea = document.querySelector('#batch-form textarea[name="batch-data"]');
    const data = textarea.value.trim();
    if (!data) { showToast('请输入批量数据', 'error'); return; }
    const lines = data.split('\n');
    const transactions = [];
    lines.forEach(line => {
        if (!line.trim()) return;
        if (line.includes('日期') && line.includes('收支分类') && line.includes('明细分类') && line.includes('金额')) return;
        let parts = [];
        if (line.includes('\t')) parts = line.split('\t');
        else if (line.includes('|')) parts = line.split('|');
        else if (line.includes(',')) parts = line.replace(/(\d),(?=\d{3}(\D|$))/g, '$1').split(',');
        else parts = line.split(/\s+/);
        const filteredParts = parts.filter(p => p.trim() !== '');
        if (filteredParts.length >= 5) {
            let date = filteredParts[0].trim();
            let type = filteredParts[1].trim();
            const category = filteredParts[2].trim();
            const description = filteredParts[3].trim();
            let amountStr = filteredParts[4].replace(/,/g, '').replace(/[^0-9.-]/g, '');
            if (!amountStr) return;
            if (date.includes('/')) { const d = date.split('/'); date = `${d[0]}-${d[1].padStart(2,'0')}-${d[2].padStart(2,'0')}`; }
            const amount = Math.abs(parseFloat(amountStr));
            if (date && type && category && !isNaN(amount) && amount > 0) {
                transactions.push({date, type, category, amount, description});
            }
        }
    });
    if (transactions.length === 0) { showToast('没有有效数据', 'error'); return; }
    
    let successCount = 0, errorCount = 0;
    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = '导入中...';
    
    for (const t of transactions) {
        try {
            const resp = await fetch('/finapp/api/transactions', {credentials:"include", method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(t)});
            if (resp.ok) successCount++; else errorCount++;
        } catch { errorCount++; }
        await new Promise(r => setTimeout(r, 30));
    }
    
    submitBtn.disabled = false;
    submitBtn.textContent = '批量保存';
    showToast(`完成: ${successCount}条成功, ${errorCount}条失败`, errorCount > 0 ? 'info' : 'success');
    if (successCount > 0) { textarea.value = ''; clearPreview(); loadRecentTransactions(); }

async function handleTransferSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    if (!data.from_account || !data.to_account) {
        showToast('请选择转出和转入账户', 'error');
        return;
    }
    if (!data.amount || parseFloat(data.amount) <= 0) {
        showToast('请输入有效金额', 'error');
        return;
    }
    if (data.from_account === data.to_account) {
        showToast('转出和转入账户不能相同', 'error');
        return;
    }
    
    try {
        const resp = await fetch('/finapp/api/transfer', {
            method: 'POST',
            credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                from_account_id: parseInt(data.from_account),
                to_account_id: parseInt(data.to_account),
                amount: parseFloat(data.amount),
                date: data.date || new Date().toISOString().split('T')[0],
                remark: data.remark || ''
            })
        });
        if (resp.ok) {
            showToast('转账成功');
            e.target.reset();
            if (typeof loadSummaryData === 'function') loadSummaryData();
            if (typeof loadRecentTransactions === 'function') loadRecentTransactions();
        } else {
            const err = await resp.json();
            showToast('转账失败: ' + (err.message || resp.status), 'error');
        }
    } catch (e) {
        console.error('转账失败', e);
        showToast('转账失败: ' + e.message, 'error');
    }
}

}

function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return '-';
    const date = new Date(dateTimeStr);
    return date.toLocaleString('zh-CN', {month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit'});
}

window.onclick = function(event) {
    const modal = document.getElementById('edit-modal');
    if (event.target === modal) closeEditModal();
};

document.addEventListener('DOMContentLoaded', initEntryPage);
