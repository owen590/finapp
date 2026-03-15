let currentPage = 1;
const perPage = 20;

function formatAmount(amount) {
    return '¥' + parseFloat(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN');
}

async function loadStatistics() {
    const year = document.getElementById('year-filter')?.value || '';
    const month = document.getElementById('month-filter')?.value || '';
    
    let url = '/api/statistics';
    const params = new URLSearchParams();
    if (year) params.append('year', year);
    if (month) params.append('month', month);
    if (params.toString()) url += '?' + params.toString();
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (document.getElementById('total-income')) {
            document.getElementById('total-income').textContent = formatAmount(data.total_income);
            document.getElementById('total-expense').textContent = formatAmount(data.total_expense);
            document.getElementById('balance').textContent = formatAmount(data.balance);
        }
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}

async function loadTransactions(page = 1) {
    const type = document.getElementById('type-filter')?.value || '';
    const year = document.getElementById('year-filter')?.value || '';
    const month = document.getElementById('month-filter')?.value || '';
    
    let url = `/api/transactions?page=${page}&per_page=${perPage}`;
    if (type) url += `&type=${type}`;
    if (year) url += `&year=${year}`;
    if (month) url += `&month=${month}`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        const tableBody = document.getElementById('transactions-table');
        if (tableBody) {
            tableBody.innerHTML = '';
            
            data.transactions.forEach(transaction => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${formatDate(transaction.date)}</td>
                    <td><span class="type-badge ${transaction.type}">${transaction.type}</span></td>
                    <td>${transaction.category || '-'}</td>
                    <td>${transaction.description || '-'}</td>
                    <td class="amount ${transaction.type}">${formatAmount(transaction.amount)}</td>
                    <td>${transaction.remark || '-'}</td>
                    <td>
                        <button class="btn-primary btn-sm" onclick="editTransaction(${transaction.id})">编辑</button>
                        <button class="btn-danger btn-sm" onclick="deleteTransaction(${transaction.id})">删除</button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        }
        
        renderPagination(data.total, data.pages, data.current_page);
    } catch (error) {
        console.error('加载交易记录失败:', error);
    }
}

async function loadLoans() {
    try {
        const response = await fetch('/api/loans');
        const loans = await response.json();
        
        const tableBody = document.getElementById('loans-table');
        if (tableBody) {
            tableBody.innerHTML = '';
            
            let totalLoans = 0;
            let returnedLoans = 0;
            let unreturnedLoans = 0;
            
            loans.forEach(loan => {
                totalLoans += loan.amount;
                if (loan.status === '已归还') {
                    returnedLoans += loan.amount;
                } else {
                    unreturnedLoans += loan.amount;
                }
                
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${formatDate(loan.date)}</td>
                    <td>${loan.lender}</td>
                    <td class="amount">${formatAmount(loan.amount)}</td>
                    <td><span class="status-badge ${loan.status === '已归还' ? 'returned' : 'unreturned'}">${loan.status}</span></td>
                    <td>${loan.return_date ? formatDate(loan.return_date) : '-'}</td>
                    <td>
                        <button class="btn-success" onclick="returnLoan(${loan.id})" ${loan.status === '已归还' ? 'disabled' : ''}>归还</button>
                        <button class="btn-danger" onclick="deleteLoan(${loan.id})">删除</button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
            
            if (document.getElementById('total-loans')) {
                document.getElementById('total-loans').textContent = formatAmount(totalLoans);
                document.getElementById('returned-loans').textContent = formatAmount(returnedLoans);
                document.getElementById('unreturned-loans').textContent = formatAmount(unreturnedLoans);
            }
        }
    } catch (error) {
        console.error('加载借款记录失败:', error);
    }
}

async function loadCapital() {
    try {
        const response = await fetch('/api/capital');
        const capitalList = await response.json();
        
        const tableBody = document.getElementById('capital-table');
        if (tableBody) {
            tableBody.innerHTML = '';
            let totalCapital = 0;
            
            capitalList.forEach(capital => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${formatDate(capital.date)}</td>
                    <td>${capital.investor}</td>
                    <td class="amount income">${formatAmount(capital.amount)}</td>
                    <td>${capital.description || '-'}</td>
                    <td>
                        <button class="btn-primary" onclick="editCapital(${capital.id})">编辑</button>
                        <button class="btn-danger" onclick="deleteCapital(${capital.id})">删除</button>
                    </td>
                `;
                tableBody.appendChild(row);
                
                totalCapital += capital.amount;
            });
            
            if (document.getElementById('total-capital')) {
                document.getElementById('total-capital').textContent = formatAmount(totalCapital);
            }
        }
    } catch (error) {
        console.error('加载资本投入失败:', error);
    }
}

function showAddModal() {
    document.getElementById('modal-title').textContent = '添加资本投入';
    document.getElementById('capital-id').value = '';
    document.getElementById('capital-form').reset();
    document.getElementById('add-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('add-modal').style.display = 'none';
}

async function editCapital(id) {
    try {
        const response = await fetch(`/api/capital/${id}`);
        const capital = await response.json();
        
        document.getElementById('modal-title').textContent = '编辑资本投入';
        document.getElementById('capital-id').value = capital.id;
        document.getElementById('capital-form').elements.date.value = capital.date;
        document.getElementById('capital-form').elements.investor.value = capital.investor;
        document.getElementById('capital-form').elements.amount.value = capital.amount;
        document.getElementById('capital-form').elements.description.value = capital.description || '';
        document.getElementById('add-modal').style.display = 'block';
    } catch (error) {
        console.error('加载资本投入详情失败:', error);
    }
}

async function deleteCapital(id) {
    if (confirm('确定要删除这条资本投入记录吗？')) {
        try {
            const response = await fetch(`/api/capital/${id}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            alert(data.message);
            loadCapital();
        } catch (error) {
            console.error('删除资本投入失败:', error);
        }
    }
}

// 表单提交处理
document.getElementById('capital-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const id = document.getElementById('capital-id').value;
    const data = {
        date: this.elements.date.value,
        investor: this.elements.investor.value,
        amount: this.elements.amount.value,
        description: this.elements.description.value
    };
    
    try {
        const url = id ? `/api/capital/${id}` : '/api/capital';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal();
            loadCapital();
        } else {
            const error = await response.json();
            alert('保存失败: ' + (error.error || '未知错误'));
        }
    } catch (error) {
        console.error('保存资本投入失败:', error);
        alert('保存失败，请稍后重试');
    }
});

async function loadMonthlyData() {
    const year = document.getElementById('year-select')?.value || '2025';
    const month = document.getElementById('month-select')?.value || '1';
    
    try {
        const response = await fetch(`/api/statistics?year=${year}&month=${month}`);
        const data = await response.json();
        
        if (document.getElementById('monthly-income')) {
            document.getElementById('monthly-income').textContent = formatAmount(data.total_income);
            document.getElementById('monthly-expense').textContent = formatAmount(data.total_expense);
            document.getElementById('monthly-balance').textContent = formatAmount(data.balance);
        }
        
        const transactionsResponse = await fetch(`/api/transactions?year=${year}&month=${month}&per_page=1000`);
        const transactionsData = await transactionsResponse.json();
        
        const expenseTable = document.getElementById('expense-table');
        const incomeTable = document.getElementById('income-table');
        
        if (expenseTable) {
            expenseTable.innerHTML = '';
            transactionsData.transactions.filter(t => t.type === '支出').forEach(t => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${formatDate(t.date)}</td>
                    <td>${t.category || '-'}</td>
                    <td class="amount expense">${formatAmount(t.amount)}</td>
                    <td>${t.description || '-'}</td>
                    <td>${t.remark || '-'}</td>
                    <td>
                        <button class="btn-primary btn-sm" onclick="editTransaction(${t.id})">编辑</button>
                        <button class="btn-danger btn-sm" onclick="deleteTransaction(${t.id})">删除</button>
                    </td>
                `;
                expenseTable.appendChild(row);
            });
        }
        
        if (incomeTable) {
            incomeTable.innerHTML = '';
            transactionsData.transactions.filter(t => t.type === '入账').forEach(t => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${formatDate(t.date)}</td>
                    <td>${t.category || '-'}</td>
                    <td class="amount income">${formatAmount(t.amount)}</td>
                    <td>${t.description || '-'}</td>
                    <td>${t.remark || '-'}</td>
                    <td>
                        <button class="btn-primary btn-sm" onclick="editTransaction(${t.id})">编辑</button>
                        <button class="btn-danger btn-sm" onclick="deleteTransaction(${t.id})">删除</button>
                    </td>
                `;
                incomeTable.appendChild(row);
            });
        }
    } catch (error) {
        console.error('加载月度数据失败:', error);
    }
}

function switchTab(tabId) {
    // 隐藏所有标签内容
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // 移除所有标签按钮的激活状态
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 显示选中的标签内容
    document.getElementById(tabId + '-tab').classList.add('active');
    
    // 激活选中的标签按钮
    event.currentTarget.classList.add('active');
}

function renderPagination(total, pages, current) {
    const pagination = document.getElementById('pagination');
    if (!pagination) return;
    
    pagination.innerHTML = '';
    
    if (pages <= 1) return;
    
    const prevButton = document.createElement('button');
    prevButton.textContent = '上一页';
    prevButton.disabled = current === 1;
    prevButton.onclick = () => loadTransactions(current - 1);
    pagination.appendChild(prevButton);
    
    for (let i = 1; i <= pages; i++) {
        const button = document.createElement('button');
        button.textContent = i;
        button.className = i === current ? 'active' : '';
        button.onclick = () => loadTransactions(i);
        pagination.appendChild(button);
    }
    
    const nextButton = document.createElement('button');
    nextButton.textContent = '下一页';
    nextButton.disabled = current === pages;
    nextButton.onclick = () => loadTransactions(current + 1);
    pagination.appendChild(nextButton);
}

function applyFilter() {
    currentPage = 1;
    loadStatistics();
    loadTransactions(currentPage);
}

function resetFilter() {
    // 重置所有筛选条件
    const yearFilter = document.getElementById('year-filter');
    const monthFilter = document.getElementById('month-filter');
    const typeFilter = document.getElementById('type-filter');
    
    if (yearFilter) yearFilter.value = '';
    if (monthFilter) monthFilter.value = '';
    if (typeFilter) typeFilter.value = '';
    
    currentPage = 1;
    loadStatistics();
    loadTransactions(currentPage);
}

function showAddModal() {
    const modal = document.getElementById('add-modal');
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeModal() {
    const modal = document.getElementById('add-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // 加载统计数据和交易记录
    if (document.getElementById('total-income') || document.getElementById('transactions-table')) {
        loadStatistics();
        loadTransactions();
    }
    
    const addForm = document.getElementById('add-form');
    if (addForm) {
        addForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(addForm);
            const data = Object.fromEntries(formData);
            
            try {
                const response = await fetch('/api/transactions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                if (response.ok) {
                    closeModal();
                    addForm.reset();
                    loadTransactions(currentPage);
                    loadStatistics();
                    alert('添加成功！');
                } else {
                    alert('添加失败，请重试');
                }
            } catch (error) {
                console.error('添加交易失败:', error);
                alert('添加失败，请重试');
            }
        });
    }
});

async function returnLoan(id) {
    if (!confirm('确认标记为已归还？')) return;
    
    try {
        const response = await fetch(`/api/loans/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: '已归还' })
        });
        
        if (response.ok) {
            loadLoans();
            alert('归还成功！');
        } else {
            alert('操作失败，请重试');
        }
    } catch (error) {
        console.error('归还借款失败:', error);
        alert('操作失败，请重试');
    }
}

async function deleteLoan(id) {
    if (!confirm('确认删除这条借款记录？')) return;
    
    try {
        const response = await fetch(`/api/loans/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadLoans();
            alert('删除成功！');
        } else {
            alert('删除失败，请重试');
        }
    } catch (error) {
        console.error('删除借款失败:', error);
        alert('删除失败，请重试');
    }
}

function setupFileUpload() {
    const fileInput = document.getElementById('file-input');
    const uploadBox = document.querySelector('.upload-box');
    
    if (uploadBox && fileInput) {
        uploadBox.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadBox.style.borderColor = '#667eea';
            uploadBox.style.background = '#f0f4ff';
        });
        
        uploadBox.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadBox.style.borderColor = '#ddd';
            uploadBox.style.background = '#f8f9fa';
        });
        
        uploadBox.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadBox.style.borderColor = '#ddd';
            uploadBox.style.background = '#f8f9fa';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload(files[0]);
            }
        });
        
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
            }
        });
    }
}

async function handleFileUpload(file) {
    if (!file.name.match(/\.(xlsx|xls)$/)) {
        alert('请上传Excel文件（.xlsx或.xls格式）');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/import', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            const resultDiv = document.getElementById('import-result');
            const resultContent = document.getElementById('result-content');
            
            if (resultDiv && resultContent) {
                resultContent.innerHTML = `
                    <p>✓ 交易记录: ${result.transactions_count} 条</p>
                    <p>✓ 借款记录: ${result.loans_count} 条</p>
                    <p>✓ 分配记录: ${result.distributions_count} 条</p>
                `;
                resultDiv.style.display = 'block';
                document.querySelector('.upload-area').style.display = 'none';
            }
        } else {
            alert('导入失败: ' + (result.error || '未知错误'));
        }
    } catch (error) {
        console.error('导入失败:', error);
        alert('导入失败，请重试');
    }
}

function resetImport() {
    document.getElementById('import-result').style.display = 'none';
    document.querySelector('.upload-area').style.display = 'block';
    document.getElementById('file-input').value = '';
}
