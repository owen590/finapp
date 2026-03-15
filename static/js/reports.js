// 报表页面功能

let currentReportType = 'daily';
let currentReportData = null;

// 初始化报表页面
document.addEventListener('DOMContentLoaded', function() {
    initializeReportTabs();
    setupDateDefaults();
});

// 初始化报表标签页
function initializeReportTabs() {
    const tabs = document.querySelectorAll('.report-tab');
    const panels = document.querySelectorAll('.report-panel');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const reportType = this.getAttribute('data-type');
            
            // 更新标签状态
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // 更新面板显示
            panels.forEach(panel => panel.classList.remove('active'));
            document.getElementById(`${reportType}-report`).classList.add('active');
            
            currentReportType = reportType;
            updateFilterVisibility(reportType);
            
            // 清除之前的数据
            clearReportData();
        });
    });
}

// 根据报表类型更新筛选条件显示
function updateFilterVisibility(reportType) {
    const dateInput = document.getElementById('report-date');
    const monthSelect = document.getElementById('report-month');
    const yearSelect = document.getElementById('report-year');
    
    // 重置所有筛选条件
    dateInput.style.display = 'none';
    monthSelect.style.display = 'none';
    yearSelect.style.display = 'none';
    
    // 根据报表类型显示相应的筛选条件
    switch(reportType) {
        case 'daily':
            dateInput.style.display = 'block';
            break;
        case 'monthly':
            monthSelect.style.display = 'block';
            yearSelect.style.display = 'block';
            break;
        case 'yearly':
            yearSelect.style.display = 'block';
            break;
    }
}

// 设置默认日期
function setupDateDefaults() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    
    // 设置默认日期
    document.getElementById('report-date').value = `${year}-${month}-${day}`;
    document.getElementById('report-month').value = month;
    document.getElementById('report-year').value = year;
    
    updateFilterVisibility('daily');
}

// 生成报表
async function generateReport() {
    const reportType = currentReportType;
    let url = '/api/reports';
    let params = [];
    
    // 根据报表类型构建参数
    switch(reportType) {
        case 'daily':
            const date = document.getElementById('report-date').value;
            if (!date) {
                showToast('请选择日期', 'error');
                return;
            }
            params.push(`type=daily`);
            params.push(`date=${date}`);
            break;
            
        case 'monthly':
            const month = document.getElementById('report-month').value;
            const year = document.getElementById('report-year').value;
            if (!month || !year) {
                showToast('请选择年份和月份', 'error');
                return;
            }
            params.push(`type=monthly`);
            params.push(`year=${year}`);
            params.push(`month=${month}`);
            break;
            
        case 'yearly':
            const yearOnly = document.getElementById('report-year').value;
            if (!yearOnly) {
                showToast('请选择年份', 'error');
                return;
            }
            params.push(`type=yearly`);
            params.push(`year=${yearOnly}`);
            break;
    }
    
    if (params.length > 0) {
        url += '?' + params.join('&');
    }
    
    // 显示加载状态
    showLoading(true);
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (response.ok) {
            currentReportData = data;
            renderReport(data, reportType);
            document.getElementById('export-pdf-btn').disabled = false;
            // 直接展示结果，不显示成功提示
        } else {
            throw new Error(data.error || '生成报表失败');
        }
    } catch (error) {
        console.error('生成报表失败:', error);
        showToast('生成报表失败: ' + error.message, 'error');
        clearReportData();
    } finally {
        showLoading(false);
    }
}

// 渲染报表数据
function renderReport(data, reportType) {
    switch(reportType) {
        case 'daily':
            renderDailyReport(data);
            break;
        case 'monthly':
            renderMonthlyReport(data);
            break;
        case 'yearly':
            renderYearlyReport(data);
            break;
    }
}

// 渲染日报表
function renderDailyReport(data) {
    const tbody = document.getElementById('daily-tbody');
    const dateRange = document.getElementById('daily-date-range');
    
    dateRange.textContent = `日期: ${data.date}`;
    
    tbody.innerHTML = '';
    
    // 从上期结余开始
    let runningBalance = data.opening_balance || 0;
    
    // 如果有上期结余，显示上期结余行
    if (runningBalance !== 0) {
        const openingRow = document.createElement('tr');
        openingRow.className = 'opening-balance-row';
        openingRow.innerHTML = `
            <td>-</td>
            <td>上期结余</td>
            <td>-</td>
            <td>上期结余转入</td>
            <td style="text-align: right;">-</td>
            <td style="text-align: right;">-</td>
            <td style="text-align: right;">¥${formatAmount(runningBalance)}</td>
        `;
        tbody.appendChild(openingRow);
    }
    
    if (data.transactions && data.transactions.length > 0) {
        // 按时间顺序排序
        const sortedTransactions = data.transactions.sort((a, b) => {
            return new Date(a.created_at) - new Date(b.created_at);
        });
        
        sortedTransactions.forEach(transaction => {
            const row = document.createElement('tr');
            row.className = transaction.type === '入账' ? 'income-row' : 'expense-row';
            
            const time = new Date(transaction.created_at).toLocaleTimeString('zh-CN', {
                hour: '2-digit',
                minute: '2-digit'
            });
            
            const income = transaction.type === '入账' ? transaction.amount : 0;
            const expense = transaction.type === '出账' ? transaction.amount : 0;
            runningBalance = runningBalance + income - expense;
            
            const incomeStr = transaction.type === '入账' ? `¥${formatAmount(transaction.amount)}` : '';
            const expenseStr = transaction.type === '出账' ? `¥${formatAmount(transaction.amount)}` : '';
            const balanceStr = `¥${formatAmount(runningBalance)}`;
            
            row.innerHTML = `
                <td>${time}</td>
                <td>${transaction.type}</td>
                <td>${transaction.category}</td>
                <td>${transaction.description}</td>
                <td style="color: #10b981; text-align: right;">${incomeStr}</td>
                <td style="color: #ef4444; text-align: right;">${expenseStr}</td>
                <td style="text-align: right;">${balanceStr}</td>
            `;
            
            tbody.appendChild(row);
        });
        
        // 添加汇总行
        const totalRow = document.createElement('tr');
        totalRow.className = 'total-row';
        totalRow.innerHTML = `
            <td colspan="4"><strong>当日汇总</strong></td>
            <td style="color: #10b981; text-align: right;"><strong>¥${formatAmount(data.total_income)}</strong></td>
            <td style="color: #ef4444; text-align: right;"><strong>¥${formatAmount(data.total_expense)}</strong></td>
            <td style="text-align: right;"><strong>¥${formatAmount(runningBalance)}</strong></td>
        `;
        tbody.appendChild(totalRow);
        
    } else if (runningBalance === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #6b7280;">当日无交易记录</td></tr>';
    }
}

// 渲染月报表
function renderMonthlyReport(data) {
    const tbody = document.getElementById('monthly-tbody');
    const dateRange = document.getElementById('monthly-date-range');
    
    dateRange.textContent = `月份: ${data.month}月${data.year}年`;
    
    tbody.innerHTML = '';
    
    // 从上期结余开始
    let runningBalance = data.opening_balance || 0;
    
    // 如果有上期结余，显示上期结余行
    if (runningBalance !== 0) {
        const openingRow = document.createElement('tr');
        openingRow.className = 'opening-balance-row';
        const startDate = `${data.year}-${String(data.month).padStart(2, '0')}-01`;
        openingRow.innerHTML = `
            <td>${startDate}</td>
            <td>上期结余</td>
            <td>-</td>
            <td>上期结余转入</td>
            <td style="text-align: right;">-</td>
            <td style="text-align: right;">-</td>
            <td style="text-align: right;">¥${formatAmount(runningBalance)}</td>
        `;
        tbody.appendChild(openingRow);
    }
    
    if (data.daily_data && Object.keys(data.daily_data).length > 0) {
        // 按日期分组，同一天收入在前
        Object.keys(data.daily_data).sort().forEach(date => {
            const dayData = data.daily_data[date];
            
            // 先显示收入记录
            dayData.income.forEach(transaction => {
                runningBalance = runningBalance + transaction.amount;
                const row = document.createElement('tr');
                row.className = 'income-row';
                
                const income = `¥${formatAmount(transaction.amount)}`;
                const expense = '';
                const balance = `¥${formatAmount(runningBalance)}`;
                
                row.innerHTML = `
                    <td>${date}</td>
                    <td>入账</td>
                    <td>${transaction.category}</td>
                    <td>${transaction.description}</td>
                    <td style="color: #10b981; text-align: right;">${income}</td>
                    <td style="color: #ef4444; text-align: right;">${expense}</td>
                    <td style="text-align: right;">${balance}</td>
                `;
                
                tbody.appendChild(row);
            });
            
            // 再显示支出记录
            dayData.expense.forEach(transaction => {
                runningBalance = runningBalance - transaction.amount;
                const row = document.createElement('tr');
                row.className = 'expense-row';
                
                const income = '';
                const expense = `¥${formatAmount(transaction.amount)}`;
                const balance = `¥${formatAmount(runningBalance)}`;
                
                row.innerHTML = `
                    <td>${date}</td>
                    <td>出账</td>
                    <td>${transaction.category}</td>
                    <td>${transaction.description}</td>
                    <td style="color: #10b981; text-align: right;">${income}</td>
                    <td style="color: #ef4444; text-align: right;">${expense}</td>
                    <td style="text-align: right;">${balance}</td>
                `;
                
                tbody.appendChild(row);
            });
        });
        
        // 添加汇总行
        const totalRow = document.createElement('tr');
        totalRow.className = 'total-row';
        totalRow.innerHTML = `
            <td colspan="4"><strong>月度汇总</strong></td>
            <td style="color: #10b981; text-align: right;"><strong>¥${formatAmount(data.total_income)}</strong></td>
            <td style="color: #ef4444; text-align: right;"><strong>¥${formatAmount(data.total_expense)}</strong></td>
            <td style="text-align: right;"><strong>¥${formatAmount(runningBalance)}</strong></td>
        `;
        tbody.appendChild(totalRow);
        
    } else if (runningBalance === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #6b7280;">该月份无交易记录</td></tr>';
    }
}

// 渲染年度报表
function renderYearlyReport(data) {
    const tbody = document.getElementById('yearly-tbody');
    const dateRange = document.getElementById('yearly-date-range');
    
    dateRange.textContent = `年份: ${data.year}年`;
    
    tbody.innerHTML = '';
    
    // 从上期结余开始
    let runningBalance = data.opening_balance || 0;
    
    // 如果有上期结余，显示上期结余行
        if (runningBalance !== 0) {
            const openingRow = document.createElement('tr');
            openingRow.className = 'opening-balance-row';
            openingRow.innerHTML = `
                <td style="text-align: center;">年初</td>
                <td style="text-align: right;">-</td>
                <td style="text-align: right;">-</td>
                <td style="text-align: right;">¥${formatAmount(runningBalance)}</td>
                <td style="text-align: right;">-</td>
            `;
            tbody.appendChild(openingRow);
        }
        
        if (data.monthly_data && Object.keys(data.monthly_data).length > 0) {
            // 按数字排序月份
            Object.keys(data.monthly_data).sort((a, b) => parseInt(a) - parseInt(b)).forEach(month => {
                const monthData = data.monthly_data[month];
                const monthBalance = monthData.total_income - monthData.total_expense;
                runningBalance = runningBalance + monthBalance;
                
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td style="text-align: center;">${month}月</td>
                    <td style="color: #10b981; text-align: right;">¥${formatAmount(monthData.total_income)}</td>
                    <td style="color: #ef4444; text-align: right;">¥${formatAmount(monthData.total_expense)}</td>
                    <td style="text-align: right;">¥${formatAmount(runningBalance)}</td>
                    <td style="text-align: right;">${monthData.transaction_count}</td>
                `;
                
                tbody.appendChild(row);
            });
            
            // 添加汇总行
            const totalRow = document.createElement('tr');
            totalRow.className = 'total-row';
            totalRow.innerHTML = `
                <td style="text-align: center;"><strong>年度汇总</strong></td>
                <td style="color: #10b981; text-align: right;"><strong>¥${formatAmount(data.total_income)}</strong></td>
                <td style="color: #ef4444; text-align: right;"><strong>¥${formatAmount(data.total_expense)}</strong></td>
                <td style="text-align: right;"><strong>¥${formatAmount(runningBalance)}</strong></td>
                <td style="text-align: right;"><strong>${data.total_count}</strong></td>
            `;
            tbody.appendChild(totalRow);
        
    } else if (runningBalance === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #6b7280;">该年份无交易记录</td></tr>';
    }
}

// 导出PDF
async function exportToPDF() {
    if (!currentReportData) {
        showToast('请先生成报表', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/export-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: currentReportType,
                data: currentReportData
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `财务报表_${currentReportType}_${new Date().toISOString().split('T')[0]}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            // 直接下载，不显示成功提示
        } else {
            throw new Error('导出PDF失败');
        }
    } catch (error) {
        console.error('导出PDF失败:', error);
        showToast('导出PDF失败', 'error');
    }
}

// 清除报表数据
function clearReportData() {
    const tbodies = document.querySelectorAll('#daily-tbody, #monthly-tbody, #yearly-tbody');
    const dateRanges = document.querySelectorAll('#daily-date-range, #monthly-date-range, #yearly-date-range');
    
    tbodies.forEach(tbody => {
        // 日报表和月报表使用7列，年度报表使用5列
        if (tbody.id === 'daily-tbody' || tbody.id === 'monthly-tbody') {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #6b7280;">请生成报表</td></tr>';
        } else {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #6b7280;">请生成报表</td></tr>';
        }
    });
    
    dateRanges.forEach(range => {
        range.textContent = '请选择日期生成报表';
    });
    
    document.getElementById('export-pdf-btn').disabled = true;
    currentReportData = null;
}

// 显示/隐藏加载状态
function showLoading(show) {
    // 这里可以添加加载动画
    const buttons = document.querySelectorAll('.filter-controls button');
    buttons.forEach(btn => {
        btn.disabled = show;
    });
}

// 金额格式化
function formatAmount(amount) {
    return parseFloat(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// 显示提示信息
function showToast(message, type = 'info') {
    // 简单的提示实现
    alert(`${type.toUpperCase()}: ${message}`);
}