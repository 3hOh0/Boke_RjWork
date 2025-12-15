/**
 * Manage favorite dashboard interactions.
 */

(function (window, document) {
    'use strict';

    function getCsrfToken() {
        const name = 'csrftoken';
        const cookies = document.cookie ? document.cookie.split('; ') : [];
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i];
            if (cookie.startsWith(name + '=')) {
                return decodeURIComponent(cookie.split('=').pop());
            }
        }
        return window.csrfToken || '';
    }

    const csrfToken = getCsrfToken();

    function ajax(method, url, formData) {
        return fetch(url, {
            method: method,
            body: formData,
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            }
        }).then(res => res.json());
    }

    const folderForm = document.getElementById('folderForm');
    if (folderForm) {
        folderForm.addEventListener('submit', function (event) {
            event.preventDefault();
            const data = new FormData(folderForm);
            ajax('POST', folderForm.getAttribute('action'), data).then(() => window.location.reload());
        });
    }

    function selectedItemIds(scope) {
        return Array.from(scope.querySelectorAll('[data-batch-item]:checked')).map(input => input.value);
    }

    function selectedFolderIds() {
        return Array.from(document.querySelectorAll('[data-folder-select]:checked')).map(input => input.value);
    }

    document.addEventListener('click', function (event) {
        const deleteForm = event.target.closest('form[data-method="delete"]');
        if (deleteForm) {
            event.preventDefault();
            const data = new FormData(deleteForm);
            data.append('_method', 'delete');
            ajax('POST', deleteForm.getAttribute('action'), data)
                .then(() => window.location.reload());
        }
        const copyBtn = event.target.closest('[data-copy-share]');
        if (copyBtn) {
            event.preventDefault();
            const url = copyBtn.dataset.copyShare;
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(url).then(() => {
                    copyBtn.textContent = '已复制！';
                    setTimeout(() => copyBtn.textContent = '复制链接', 1200);
                }).catch(() => {
                    window.prompt('复制失败，请手动复制链接：', url);
                });
            } else {
                window.prompt('请手动复制链接：', url);
            }
        }

        const pinBtn = event.target.closest('[data-folder-pin]');
        if (pinBtn) {
            event.preventDefault();
            const folderId = pinBtn.dataset.folderPin;
            const formData = new FormData();
            formData.append('action', pinBtn.textContent.includes('取消') ? 'unpin_folders' : 'pin_folders');
            formData.append('folder_ids', folderId);
            ajax('POST', '/interaction/batch/', formData).then(() => window.location.reload());
        }

        const deleteSelectedBtn = event.target.closest('[data-batch-delete]');
        if (deleteSelectedBtn) {
            event.preventDefault();
            const folderId = deleteSelectedBtn.dataset.batchDelete;
            const card = deleteSelectedBtn.closest('[data-folder-card]');
            const ids = selectedItemIds(card);
            if (!ids.length) {
                alert('请选择要删除的文章');
                return;
            }
            const formData = new FormData();
            formData.append('action', 'delete_items');
            ids.forEach(id => formData.append('item_ids', id));
            ajax('POST', '/interaction/batch/', formData).then(() => window.location.reload());
        }

        const moveBtn = event.target.closest('[data-batch-move]');
        if (moveBtn) {
            event.preventDefault();
            const card = moveBtn.closest('[data-folder-card]');
            const ids = selectedItemIds(card);
            if (!ids.length) {
                alert('请选择要移动的文章');
                return;
            }
            const select = card.querySelector('[data-move-target]');
            const targetId = select ? select.value : '';
            if (!targetId) {
                alert('请选择目标收藏夹');
                return;
            }
            const formData = new FormData();
            formData.append('action', 'move_items');
            formData.append('target_folder_id', targetId);
            ids.forEach(id => formData.append('item_ids', id));
            ajax('POST', '/interaction/batch/', formData).then(() => window.location.reload());
        }
    });

    const searchInput = document.getElementById('folderSearchInput');
    const tagFilter = document.getElementById('folderTagFilter');
    const sortSelect = document.getElementById('folderSortSelect');
    const cards = document.querySelectorAll('[data-folder-card]');

    function applyFilters() {
        const keyword = (searchInput && searchInput.value.toLowerCase()) || '';
        const tag = (tagFilter && tagFilter.value.toLowerCase()) || '';
        cards.forEach(card => {
            const title = card.getAttribute('data-folder-name').toLowerCase();
            const desc = card.getAttribute('data-folder-desc').toLowerCase();
            const tags = (card.getAttribute('data-folder-tags') || '').toLowerCase();
            const matchText = !keyword || title.includes(keyword) || desc.includes(keyword);
            const matchTag = !tag || tags.includes(tag);
            if (matchText && matchTag) {
                card.classList.remove('d-none');
            } else {
                card.classList.add('d-none');
            }
        });
        applySort();
    }

    function applySort() {
        if (!sortSelect) return;
        const value = sortSelect.value;
        const container = document.querySelector('.row');
        if (!container) return;
        const visibleCards = Array.from(cards).filter(c => !c.classList.contains('d-none'));
        visibleCards.sort((a, b) => {
            const aPinned = Number(a.getAttribute('data-pinned') || '0');
            const bPinned = Number(b.getAttribute('data-pinned') || '0');
            const aOrder = Number(a.getAttribute('data-sort-order') || '0');
            const bOrder = Number(b.getAttribute('data-sort-order') || '0');
            const aUpdated = Number(a.getAttribute('data-updated') || '0');
            const bUpdated = Number(b.getAttribute('data-updated') || '0');
            const aCount = Number(a.getAttribute('data-item-count') || '0');
            const bCount = Number(b.getAttribute('data-item-count') || '0');
            if (value === 'pinned') {
                if (aPinned !== bPinned) return bPinned - aPinned;
                return aOrder - bOrder;
            }
            if (value === 'recent') {
                return bUpdated - aUpdated;
            }
            if (value === 'count') {
                return bCount - aCount;
            }
            // default: pinned + sort_order
            if (aPinned !== bPinned) return bPinned - aPinned;
            return aOrder - bOrder;
        });
        visibleCards.forEach(card => container.appendChild(card));
    }

    if (searchInput) {
        searchInput.addEventListener('input', applyFilters);
    }
    if (tagFilter) {
        tagFilter.addEventListener('input', applyFilters);
    }
    if (sortSelect) {
        sortSelect.addEventListener('change', applySort);
    }

    applyFilters();

})(window, document);

