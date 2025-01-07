document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');

    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadDetails = document.getElementById('uploadDetails');
    const contentTitle = document.getElementById('contentTitle');
    const submitUpload = document.getElementById('submitUpload');
    const verifyBtn = document.getElementById('verifyBtn');
    const detectBtn = document.getElementById('detectBtn');
    const resultDiv = document.getElementById('result');
    const loadingDiv = document.getElementById('loading');

    // Log elements to make sure they're found
    console.log('Elements found:', {
        fileInput: !!fileInput,
        uploadBtn: !!uploadBtn,
        uploadDetails: !!uploadDetails,
        contentTitle: !!contentTitle,
        submitUpload: !!submitUpload,
        verifyBtn: !!verifyBtn,
        detectBtn: !!detectBtn,
        resultDiv: !!resultDiv,
        loadingDiv: !!loadingDiv
    });

    let currentOperation = null;
    let selectedFile = null;

    function showLoading() {
        console.log('Showing loading...');
        loadingDiv.classList.remove('hidden');
    }

    function hideLoading() {
        console.log('Hiding loading...');
        loadingDiv.classList.add('hidden');
    }

    function showResult(message, isError = false) {
        console.log('Showing result:', message, 'isError:', isError);
        resultDiv.innerHTML = `
            <div class="${isError ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'} p-4 rounded-md">
                ${message}
            </div>
        `;
        resultDiv.classList.remove('hidden');
    }

    function handleFileSelect(operation) {
        console.log('Handling file select for operation:', operation);
        currentOperation = operation;
        fileInput.click();
    }

    uploadBtn.addEventListener('click', () => {
        console.log('Upload button clicked');
        uploadDetails.classList.remove('hidden');
        resultDiv.classList.add('hidden');
    });

    submitUpload.addEventListener('click', async () => {
        console.log('Submit upload clicked');
        if (!fileInput.files[0]) {
            handleFileSelect('upload');
            return;
        }

        const title = contentTitle.value.trim();
        if (!title) {
            showResult('Please enter a title for the content', true);
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('title', title);

        try {
            showLoading();
            console.log('Sending upload request...');
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            console.log('Upload response:', data);
            
            if (data.success) {
                showResult(`
                    <div class="space-y-2">
                        <p class="font-semibold">✓ Content Protected Successfully</p>
                        <p>Content ID: ${data.content_id}</p>
                    </div>
                `);
                uploadDetails.classList.add('hidden');
                fileInput.value = '';
                contentTitle.value = '';
            } else {
                showResult(data.message, true);
            }
        } catch (error) {
            console.error('Upload error:', error);
            showResult('Error uploading content: ' + error.message, true);
        } finally {
            hideLoading();
        }
    });

    verifyBtn.addEventListener('click', () => {
        console.log('Verify button clicked');
        handleFileSelect('verify');
    });

    detectBtn.addEventListener('click', () => {
        console.log('Detect button clicked');
        handleFileSelect('detect');
    });

    fileInput.addEventListener('change', async () => {
        console.log('File input changed');
        const file = fileInput.files[0];
        if (!file) return;

        console.log('Selected file:', file.name);

        if (currentOperation === 'upload') {
            // File selected for upload, wait for title and submit
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            showLoading();
            console.log('Sending', currentOperation, 'request...');
            const response = await fetch(`/api/${currentOperation}`, {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            console.log(currentOperation, 'response:', data);

            if (data.success) {
                let resultMessage = '';
                if (currentOperation === 'verify') {
                    resultMessage = `
                        <div class="space-y-2">
                            <p class="font-semibold">✓ Content Verification Result</p>
                            <p>Status: ${data.verified ? 'Verified' : 'Not Verified'}</p>
                            <p>Owner: ${data.owner}</p>
                            <p>Timestamp: ${new Date(data.timestamp).toLocaleString()}</p>
                        </div>
                    `;
                } else if (currentOperation === 'detect') {
                    resultMessage = `
                        <div class="space-y-2">
                            <p class="font-semibold">✓ Piracy Detection Result</p>
                            <p>Status: ${data.matches.length > 0 ? 'Potential Match Found' : 'No Matches Found'}</p>
                            <p>Similarity Score: ${(data.similarity_score * 100).toFixed(2)}%</p>
                        </div>
                    `;
                }
                showResult(resultMessage);
            } else {
                showResult(data.message, true);
            }
        } catch (error) {
            console.error(currentOperation, 'error:', error);
            showResult(`Error during ${currentOperation}: ` + error.message, true);
        } finally {
            hideLoading();
            fileInput.value = '';
        }
    });
});
