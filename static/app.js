document.addEventListener('DOMContentLoaded', function() {
    const uploadBtn = document.getElementById('uploadBtn');
    const verifyBtn = document.getElementById('verifyBtn');
    const detectBtn = document.getElementById('detectBtn');
    const resultDiv = document.getElementById('result');

    function showResult(message, isError = false) {
        resultDiv.textContent = message;
        resultDiv.className = `mt-4 p-4 rounded-md ${isError ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`;
        resultDiv.classList.remove('hidden');
    }

    uploadBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            showResult('API Status: ' + data.status);
        } catch (error) {
            showResult('Error connecting to API: ' + error.message, true);
        }
    });

    verifyBtn.addEventListener('click', () => {
        showResult('Content verification feature coming soon');
    });

    detectBtn.addEventListener('click', () => {
        showResult('Piracy detection feature coming soon');
    });
});
