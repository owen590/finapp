// 通用分页控件
class Pagination {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.currentPage = options.currentPage || 1;
        this.totalPages = options.totalPages || 1;
        this.pageSize = options.pageSize || 50;
        this.onPageChange = options.onPageChange || function() {};
        
        this.init();
    }
    
    init() {
        this.render();
        this.bindEvents();
    }
    
    render() {
        if (!this.container) return;
        
        const html = `
            <div class="pagination-wrapper">
                <button class="page-btn first-page" ${this.currentPage <= 1 ? 'disabled' : ''}>第一页</button>
                <button class="page-btn prev-page" ${this.currentPage <= 1 ? 'disabled' : ''}>上一页</button>
                <span class="page-numbers"></span>
                <button class="page-btn next-page" ${this.currentPage >= this.totalPages ? 'disabled' : ''}>下一页</button>
                <button class="page-btn last-page" ${this.currentPage >= this.totalPages ? 'disabled' : ''}>最后一页</button>
                <select class="page-jump-select">
                    <option value="">跳转页面</option>
                </select>
            </div>
        `;
        
        this.container.innerHTML = html;
        this.renderPageNumbers();
        this.renderJumpSelect();
    }
    
    renderPageNumbers() {
        const pageNumbersContainer = this.container.querySelector('.page-numbers');
        if (!pageNumbersContainer) return;
        
        pageNumbersContainer.innerHTML = '';
        
        // 计算显示的页码范围（每屏10个）
        let startPage = Math.floor((this.currentPage - 1) / 10) * 10 + 1;
        let endPage = Math.min(startPage + 9, this.totalPages);
        
        // 生成页码按钮
        for (let i = startPage; i <= endPage; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.className = 'page-number-btn' + (i === this.currentPage ? ' active' : '');
            pageBtn.textContent = i;
            pageBtn.dataset.page = i;
            pageNumbersContainer.appendChild(pageBtn);
        }
    }
    
    renderJumpSelect() {
        const select = this.container.querySelector('.page-jump-select');
        if (!select) return;
        
        select.innerHTML = '<option value="">跳转页面</option>';
        
        // 计算有多少个10页区间
        const rangeCount = Math.ceil(this.totalPages / 10);
        
        for (let i = 0; i < rangeCount; i++) {
            const start = i * 10 + 1;
            const end = Math.min((i + 1) * 10, this.totalPages);
            const option = document.createElement('option');
            option.value = start;
            option.textContent = `${start}-${end}`;
            select.appendChild(option);
        }
    }
    
    bindEvents() {
        const self = this;
        
        // 第一页
        this.container.querySelector('.first-page')?.addEventListener('click', function() {
            if (!this.disabled) {
                self.goToPage(1);
            }
        });
        
        // 上一页
        this.container.querySelector('.prev-page')?.addEventListener('click', function() {
            if (!this.disabled) {
                self.goToPage(self.currentPage - 1);
            }
        });
        
        // 下一页
        this.container.querySelector('.next-page')?.addEventListener('click', function() {
            if (!this.disabled) {
                self.goToPage(self.currentPage + 1);
            }
        });
        
        // 最后一页
        this.container.querySelector('.last-page')?.addEventListener('click', function() {
            if (!this.disabled) {
                self.goToPage(self.totalPages);
            }
        });
        
        // 页码按钮
        this.container.querySelector('.page-numbers')?.addEventListener('click', function(e) {
            if (e.target.classList.contains('page-number-btn')) {
                const page = parseInt(e.target.dataset.page);
                self.goToPage(page);
            }
        });
        
        // 跳转下拉框
        this.container.querySelector('.page-jump-select')?.addEventListener('change', function() {
            if (this.value) {
                self.goToPage(parseInt(this.value));
            }
        });
    }
    
    goToPage(page) {
        if (page < 1 || page > this.totalPages || page === this.currentPage) {
            return;
        }
        
        this.currentPage = page;
        this.render();
        this.bindEvents();
        
        if (typeof this.onPageChange === 'function') {
            this.onPageChange(page);
        }
    }
    
    update(currentPage, totalPages) {
        this.currentPage = currentPage;
        this.totalPages = totalPages;
        this.render();
        this.bindEvents();
    }
}

// 导出分页控件
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Pagination;
}
