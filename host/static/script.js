const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const loading = document.getElementById('loading');

function addMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = text;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function setInput(text) {
    userInput.value = text;
    userInput.focus();
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // Add user message
    addMessage(message, 'user');
    userInput.value = '';

    // Show loading
    sendBtn.disabled = true;
    loading.classList.add('active');

    try {
        // Send to backend
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        if (data.success) {
            addMessage(data.response, 'assistant');
        } else {
            addMessage('Error: ' + data.error, 'system');
        }
    } catch (error) {
        addMessage('Error connecting to server: ' + error.message, 'system');
    } finally {
        sendBtn.disabled = false;
        loading.classList.remove('active');
    }
}

// Add initial system message
setTimeout(() => {
    addMessage('I can help you send emails through Gmail. Just tell me who to email and what to say!', 'assistant');
}, 500);