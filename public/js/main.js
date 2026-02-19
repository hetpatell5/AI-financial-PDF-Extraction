document.addEventListener('DOMContentLoaded', () => {
    let selectedFiles = [];
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const uploadBtn = document.getElementById('uploadBtn');
    const userIdInput = document.getElementById('userId');

    // Drag and drop handlers
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.pdf'));
        addFiles(files);
    });

    uploadArea.addEventListener('click', (e) => {
        if (e.target === uploadArea || e.target.closest('.upload-icon, h3, p')) {
            fileInput.click();
        }
    });

    fileInput.addEventListener('change', (e) => {
        addFiles(Array.from(e.target.files));
    });

    // Make functions available globally or attach to elements
    window.addFiles = function (files) {
        files.forEach(file => {
            if (!selectedFiles.find(f => f.name === file.name)) {
                selectedFiles.push(file);
            }
        });
        renderFileList();
        uploadBtn.disabled = selectedFiles.length === 0;
    };

    window.removeFile = function (index) {
        selectedFiles.splice(index, 1);
        renderFileList();
        uploadBtn.disabled = selectedFiles.length === 0;
    };

    function renderFileList() {
        if (selectedFiles.length === 0) {
            fileList.innerHTML = '';
            return;
        }

        fileList.innerHTML = selectedFiles.map((file, index) => `
            <div class="file-item">
                <div>
                    <span class="file-name">📄 ${file.name}</span>
                    <span class="file-size" style="margin-left: 10px; opacity: 0.7;">${(file.size / 1024 / 1024).toFixed(2)} MB</span>
                </div>
                <button class="remove-btn" onclick="removeFile(${index})">Remove</button>
            </div>
        `).join('');
    }

    uploadBtn.addEventListener('click', uploadFiles);

    async function uploadFiles() {
        const userId = userIdInput.value.trim();

        if (!userId) {
            showError('Please enter a User ID');
            return;
        }

        if (selectedFiles.length === 0) {
            showError('Please select at least one PDF file');
            return;
        }

        // Show processing indicator
        const processingDiv = document.getElementById('processing');
        const resultsDiv = document.getElementById('results');
        const errorDiv = document.getElementById('error');

        if (processingDiv) processingDiv.classList.add('active');
        if (resultsDiv) resultsDiv.classList.remove('active');
        if (errorDiv) errorDiv.classList.remove('active');

        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<span class="spinner" style="width: 20px; height: 20px; border-width: 2px; margin: 0; display: inline-block; vertical-align: middle;"></span> Processing...';

        try {
            const formData = new FormData();
            let response;

            if (selectedFiles.length === 1) {
                formData.append('pdf', selectedFiles[0]);
                formData.append('userId', userId);
                response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
            } else {
                selectedFiles.forEach(file => {
                    formData.append('pdfs', file);
                });
                formData.append('userId', userId);
                response = await fetch('/api/upload/batch', {
                    method: 'POST',
                    body: formData
                });
            }

            const result = await response.json();

            if (result.success) {
                // Success - redirect to dashboard with user ID
                console.log(`Upload success: ${result.message}`, result.data);
                window.location.href = `/dashboard.html?userId=${encodeURIComponent(userId)}`;
            } else {
                showError(result.message || 'Processing failed. Please check the file and try again.');
            }
        } catch (error) {
            showError('Upload failed: ' + error.message);
        } finally {
            if (processingDiv) processingDiv.classList.remove('active');
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Process PDFs';
        }
    }

    function showError(message) {
        const errorDiv = document.getElementById('error');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.classList.add('active');
            setTimeout(() => {
                errorDiv.classList.remove('active');
            }, 5000);
        } else {
            alert(message);
        }
    }
});
