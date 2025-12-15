/**
 * Front-end helpers for the interaction module.
 */

(function (window, document) {
    'use strict';

    const csrfToken = (function () {
        const name = 'csrftoken';
        const cookies = document.cookie ? document.cookie.split('; ') : [];
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i];
            if (cookie.startsWith(name + '=')) {
                return decodeURIComponent(cookie.split('=').pop());
            }
        }
        return window.csrfToken || '';
    })();

    function post(url, data) {
        const formData = new FormData();
        Object.keys(data).forEach(key => {
            if (data[key] !== undefined && data[key] !== null) {
                formData.append(key, data[key]);
            }
        });
        return fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
            body: formData
        }).then(response => response.json());
    }

    function toggleLike(button) {
        const articleId = button.dataset.articleId;
        if (!articleId) {
            return;
        }
        post('/interaction/like/', {article_id: articleId}).then(data => {
            button.classList.toggle('liked', data.liked);
            const counter = document.querySelector('[data-like-counter="' + articleId + '"]');
            if (counter) {
                counter.textContent = data.like_count;
            }
        });
    }

    function fetchFolders() {
        return fetch('/interaction/folders/', {
            credentials: 'same-origin',
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        }).then(response => response.json());
    }

    function QuickSaveModal() {
        this.modal = document.getElementById('quickSaveModal');
        if (!this.modal) {
            return;
        }
        this.form = document.getElementById('quickSaveForm');
        this.folderSelect = document.getElementById('quickSaveFolderSelect');
        this.newFields = document.getElementById('quickSaveNewFolderFields');
        this.errorBox = document.getElementById('quickSaveError');
        this.successBox = document.getElementById('quickSaveSuccess');
        this.backdrop = null;
        this.registerEvents();
    }

    QuickSaveModal.prototype.open = function (articleId) {
        const self = this;
        if (!this.modal) {
            return;
        }
        this.form.reset();
        this.form.article_id.value = articleId;
        this.toggleNewFields(true);
        this.errorBox.classList.add('d-none');
        this.successBox.classList.add('d-none');
        fetchFolders().then(data => {
            if (!self.folderSelect) {
                return;
            }
            while (self.folderSelect.options.length > 1) {
                self.folderSelect.remove(1);
            }
            data.folders.forEach(folder => {
                const option = document.createElement('option');
                option.value = folder.id;
                option.textContent = folder.name;
                option.dataset.shareUrl = folder.share_url;
                self.folderSelect.appendChild(option);
            });
        });
        this.showModal();
    };

    QuickSaveModal.prototype.showModal = function () {
        if (!this.modal) {
            return;
        }
        this.modal.classList.add('show');
        this.modal.style.display = 'block';
        document.body.classList.add('modal-open');
        if (!this.backdrop) {
            this.backdrop = document.createElement('div');
            this.backdrop.className = 'modal-backdrop fade show';
            document.body.appendChild(this.backdrop);
        }
    };

    QuickSaveModal.prototype.close = function () {
        if (!this.modal) {
            return;
        }
        this.modal.classList.remove('show');
        this.modal.style.display = 'none';
        document.body.classList.remove('modal-open');
        if (this.backdrop) {
            document.body.removeChild(this.backdrop);
            this.backdrop = null;
        }
    };

    QuickSaveModal.prototype.toggleNewFields = function (shouldShow) {
        if (!this.newFields) {
            return;
        }
        if (shouldShow) {
            this.newFields.classList.remove('d-none');
        } else {
            this.newFields.classList.add('d-none');
        }
    };

    QuickSaveModal.prototype.registerEvents = function () {
        const self = this;
        if (!this.modal) {
            return;
        }
        this.modal.addEventListener('click', function (event) {
            if (event.target.matches('[data-bs-dismiss="modal"]') || event.target === self.modal) {
                event.preventDefault();
                self.close();
            }
        });
        if (this.folderSelect) {
            this.folderSelect.addEventListener('change', function () {
                self.toggleNewFields(!self.folderSelect.value);
            });
        }
        if (this.form) {
            this.form.addEventListener('submit', function (event) {
                event.preventDefault();
                self.errorBox.classList.add('d-none');
                self.successBox.classList.add('d-none');
                const formData = new FormData(self.form);
                fetch(self.form.action, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken
                    },
                    body: formData
                }).then(response => response.json().then(data => ({status: response.status, data})))
                    .then(result => {
                        if (result.status >= 400) {
                            self.errorBox.textContent = JSON.stringify(result.data.errors || result.data);
                            self.errorBox.classList.remove('d-none');
                        } else {
                            self.successBox.textContent = '保存成功！';
                            self.successBox.classList.remove('d-none');
                            setTimeout(function () {
                                self.close();
                            }, 800);
                        }
                    })
                    .catch(() => {
                        self.errorBox.textContent = '网络错误，请重试。';
                        self.errorBox.classList.remove('d-none');
                    });
            });
        }
    };

    const quickSaveModal = new QuickSaveModal();

    document.addEventListener('click', function (event) {
        const likeBtn = event.target.closest('[data-like-button]');
        if (likeBtn) {
            event.preventDefault();
            toggleLike(likeBtn);
        }
        const saveBtn = event.target.closest('[data-save-button]');
        if (saveBtn && quickSaveModal) {
            event.preventDefault();
            quickSaveModal.open(saveBtn.dataset.articleId);
        }
    });

})(window, document);

