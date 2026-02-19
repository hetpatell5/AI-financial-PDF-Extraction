document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const userId = decodeURIComponent(urlParams.get('userId') || 'user123');

    // Set userId in title if element exists
    const userTitle = document.getElementById('userTitle');
    if (userTitle) userTitle.textContent = `Welcome, ${userId}`;

    let currentPage = 0;
    const limit = 50;
    let currentFilters = {};
    let charts = {}; // Store chart instances

    // Initial Load
    loadCategories();
    loadTransactions();
    loadSummary();

    // Event Listeners
    document.getElementById('applyFilters')?.addEventListener('click', applyFilters);
    document.getElementById('prevBtn')?.addEventListener('click', prevPage);
    document.getElementById('nextBtn')?.addEventListener('click', nextPage);

    document.getElementById('backBtn')?.addEventListener('click', () => {
        window.location.href = '/';
    });

    // Clear Data Functionality
    const clearDataBtn = document.getElementById('clearDataBtn');
    if (clearDataBtn) {
        clearDataBtn.addEventListener('click', async () => {
            if (confirm('Are you sure you want to clear all your transaction data? This cannot be undone.')) {
                try {
                    const response = await fetch(`/api/transactions/${userId}`, { method: 'DELETE' });
                    const result = await response.json();

                    if (result.success) {
                        alert('Data cleared successfully. Redirecting to home...');
                        window.location.href = '/';
                    } else {
                        alert('Failed to clear data: ' + result.message);
                    }
                } catch (error) {
                    console.error('Error clearing data:', error);
                    alert('Error clearing data. Please try again.');
                }
            }
        });
    }

    async function loadCategories() {
        try {
            const response = await fetch(`/api/transactions/${userId}/categories`);
            const result = await response.json();

            if (result.success) {
                const categorySelect = document.getElementById('category');
                if (categorySelect) {
                    result.data.forEach(cat => {
                        const option = document.createElement('option');
                        option.value = cat;
                        option.textContent = cat;
                        categorySelect.appendChild(option);
                    });
                }
            }
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    async function loadTransactions() {
        showLoading(true);

        try {
            const params = new URLSearchParams({
                limit: limit,
                skip: currentPage * limit,
                ...currentFilters
            });

            const response = await fetch(`/api/transactions/${userId}?${params}`);
            const result = await response.json();

            if (result.success) {
                displayTransactions(result.data);
                updatePagination(result.pagination);

                if (result.data.length === 0) {
                    showNoData(true);
                } else {
                    showNoData(false);
                }
            }
        } catch (error) {
            console.error('Error loading transactions:', error);
            showNoData(true);
        } finally {
            showLoading(false);
        }
    }

    async function loadSummary() {
        try {
            const params = new URLSearchParams(currentFilters);
            const response = await fetch(`/api/transactions/${userId}/summary?${params}`);
            const result = await response.json();

            if (result.success && result.data) {
                updateStats(result.data.overview);
                updateCharts(result.data); // Future implementation for charts
            }
        } catch (error) {
            console.error('Error loading summary:', error);
        }
    }

    // Format Toggle - Removed as per request, default to Indian
    const currentLocale = 'en-IN';



    function updateStats(stats) {
        setTextContent('totalCount', (stats.debitCount + stats.creditCount).toLocaleString(currentLocale));
        setTextContent('totalDebit', formatCurrency(stats.totalDebit));
        setTextContent('totalCredit', formatCurrency(stats.totalCredit));
        setTextContent('netAmount', formatCurrency(stats.netAmount));
    }

    function formatCurrency(amount) {
        return '₹' + Math.abs(amount).toLocaleString(currentLocale, {
            minimumFractionDigits: 1,
            maximumFractionDigits: 2
        });
    }

    function setTextContent(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }

    function displayTransactions(transactions) {
        const tbody = document.getElementById('transactionsBody');
        if (!tbody) return;

        if (transactions.length === 0) {
            tbody.innerHTML = '';
            return;
        }

        tbody.innerHTML = transactions.map(t => `
            <tr>
                <td data-label="Date"><span>${new Date(t.date).toLocaleDateString(currentLocale)}</span></td>
                <td data-label="Description"><span>${escapeHtml(t.description)}</span></td>
                <td data-label="Category"><span class="badge" style="background: rgba(255,255,255,0.1);">${t.category}</span></td>
                <td data-label="Type"><span class="badge badge-${t.type.toLowerCase()}">${t.type}</span></td>
                <td data-label="Amount" style="font-weight: 600;"><span>₹${t.amount.toLocaleString(currentLocale, { minimumFractionDigits: 2 })}</span></td>
                <td data-label="Balance"><span>${t.balance ? '₹' + t.balance.toLocaleString(currentLocale, { minimumFractionDigits: 2 }) : '-'}</span></td>
            </tr>
        `).join('');
    }

    function updatePagination(pagination) {
        const pageInfo = document.getElementById('pageInfo');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');

        if (pageInfo) {
            const totalPages = Math.ceil(pagination.total / limit);
            pageInfo.textContent = `Page ${currentPage + 1} of ${totalPages || 1}`;
        }

        if (prevBtn) prevBtn.disabled = currentPage === 0;
        if (nextBtn) nextBtn.disabled = !pagination.hasMore;
    }

    function prevPage() {
        if (currentPage > 0) {
            currentPage--;
            loadTransactions();
        }
    }

    function nextPage() {
        currentPage++;
        loadTransactions();
    }

    function applyFilters() {
        const startDate = document.getElementById('startDate')?.value;
        const endDate = document.getElementById('endDate')?.value;
        const category = document.getElementById('category')?.value;
        const type = document.getElementById('type')?.value;

        currentFilters = {};
        if (startDate) currentFilters.startDate = startDate;
        if (endDate) currentFilters.endDate = endDate;
        if (category) currentFilters.category = category;
        if (type) currentFilters.type = type;

        currentPage = 0;
        loadTransactions();
        loadSummary();
    }

    function showLoading(show) {
        const loading = document.getElementById('loading');
        const tableContainer = document.getElementById('tableContainer');
        if (loading) loading.style.display = show ? 'block' : 'none';
        if (tableContainer) tableContainer.style.display = show ? 'none' : 'block';
    }

    function showNoData(show) {
        const noData = document.getElementById('noData');
        const tableContainer = document.getElementById('tableContainer');
        if (noData) noData.style.display = show ? 'block' : 'none';
        if (tableContainer) tableContainer.style.display = show ? 'none' : 'block';
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Chart.js Implementation
    function updateCharts(data) {
        if (typeof Chart === 'undefined') return;

        // 1. Balance Chart (Doughnut) - only if overview data is present
        const balanceCtx = document.getElementById('balanceChart');
        if (balanceCtx && data.overview) {
            // Destroy existing balance chart only when we're updating it
            if (charts.balance) charts.balance.destroy();

            charts.balance = new Chart(balanceCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Income', 'Expense'],
                    datasets: [{
                        data: [data.overview.totalCredit, data.overview.totalDebit],
                        backgroundColor: ['#10b981', '#ef4444'],
                        borderWidth: 0,
                        hoverOffset: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { color: '#fff', font: { family: 'Outfit' } } }
                    }
                }
            });
        }

        // 2. Category Table - Populate from server-side aggregated categories
        const tableBody = document.getElementById('categoryTableBody');
        if (tableBody && data.categories && Array.isArray(data.categories)) {
            // Sort by total activity (debit + credit)
            const sortedCats = [...data.categories].sort((a, b) =>
                (b.debit + b.credit) - (a.debit + a.credit)
            );

            if (sortedCats.length > 0) {
                tableBody.innerHTML = sortedCats.map(cat => `
                    <tr>
                        <td>
                            <span class="category-name">
                                <span class="category-badge"></span>
                                ${cat._id || 'Other'}
                            </span>
                        </td>
                        <td>${cat.count.toLocaleString('en-IN')}</td>
                        <td class="text-danger">₹${cat.debit.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                        <td class="text-success">₹${cat.credit.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    </tr>
                `).join('');
            } else {
                tableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-secondary);">No category data available</td></tr>';
            }
        }
    }
});
