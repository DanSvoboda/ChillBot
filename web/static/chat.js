const form = document.getElementById('chat-form');
const input = document.getElementById('question');
const messages = document.getElementById('messages');
const welcome = document.getElementById('welcome');
const scroller = document.getElementById('chat-scroll');
const send = form.querySelector('button');
let history = [], controller = null, retryQuestion = null;

function responseText(data) {
	const content = data.response?.choices?.[0]?.message?.content;
	return typeof content === 'string' ? content : '';
}

function renderMessage(bubble, text, role) {
	if (role !== 'assistant' || !window.marked || !window.DOMPurify) {
		bubble.textContent = text;
		return;
	}

	const html = window.marked.parse(text, { breaks: true });
	bubble.innerHTML = window.DOMPurify.sanitize(html);
}

function addMessage(text, role) {
	const row = document.createElement('div');
	row.className = 'message ' + role;
	const avatar = document.createElement('span');
	avatar.className = 'avatar';
	avatar.textContent = role === 'user' ? 'You' : '🌶️';
	const bubble = document.createElement('div');
	bubble.className = 'bubble';
	renderMessage(bubble, text, role);
	row.append(avatar, bubble);
	messages.append(row);
	scroller.scrollTop = scroller.scrollHeight;
	return bubble;
}
async function sendQuestion(question) {
	if (!question || controller) return;
	retryQuestion = null;
	welcome.hidden = true;
	addMessage(question, 'user');
	history.push({ role:'user', content:question });
	input.value = '';
	send.disabled = true;
	const pending = addMessage('Thinking about chillies…', 'assistant');
	const request = new AbortController();
	controller = request;
	try {
		// Connect this endpoint to your server-side AI provider; never expose API keys here.
		const csrf = document.cookie.split('; ').find(cookie => cookie.startsWith('csrftoken='));
		const headers = { 'Content-Type':'application/json' };
		if (csrf) headers['X-CSRFToken'] = decodeURIComponent(csrf.slice(10));
		const response = await fetch('/api/chat', { method:'POST', headers, credentials:'same-origin', body:JSON.stringify({ message:question, messages:history }), signal:request.signal });
		const contentType = response.headers.get('content-type') || '';
		const data = contentType.includes('application/json')
			? await response.json()
			: { error: `The server returned an unexpected response (${response.status}). Please try again.` };
		if (!response.ok) {
			const error = new Error(data.error || 'Request failed');
			error.code = response.status;
			throw error;
		}
		const reply = responseText(data);
		if (!reply.trim()) throw new Error('Invalid reply');
		renderMessage(pending, reply, 'assistant');
		history.push({ role:'assistant', content:reply });
	} catch (error) {
		if (error.name !== 'AbortError') {
			pending.textContent = error.message;
			if (error.code === 403) {
				retryQuestion = question;
				apiKeyNotice.hidden = false;
				settingsPanel.hidden = false;
				apiKey.focus();
			}
			history.pop();
		}
	} finally {
		if (controller === request) { controller = null; send.disabled = false; input.focus(); }
		scroller.scrollTop = scroller.scrollHeight;
	}
}

form.addEventListener('submit', event => {
	event.preventDefault();
	void sendQuestion(input.value.trim());
});
document.querySelectorAll('[data-prompt]').forEach(button => button.addEventListener('click', () => {
	if (controller) return;
	input.value = button.dataset.prompt;
	form.requestSubmit();
}));
document.getElementById('new-chat').addEventListener('click', () => {
	if (controller) controller.abort();
	controller = null;
	history = [];
	retryQuestion = null;
	messages.replaceChildren();
	welcome.hidden = false;
	send.disabled = false;
	input.value = '';
	input.focus();
});

const settingsToggle = document.getElementById('settings-toggle');
const settingsPanel = document.getElementById('settings-panel');
const settingsForm = document.getElementById('settings-form');
const apiKey = document.getElementById('api-key');
const settingsMessage = document.getElementById('settings-message');
const apiKeyNotice = document.getElementById('api-key-notice');
const apiKeyNoticeAction = document.getElementById('api-key-notice-action');

settingsToggle.addEventListener('click', () => {
	settingsPanel.hidden = !settingsPanel.hidden;
	if (!settingsPanel.hidden) apiKey.focus();
});

apiKeyNoticeAction.addEventListener('click', () => {
	settingsPanel.hidden = false;
	apiKey.focus();
});

settingsForm.addEventListener('submit', async event => {
	event.preventDefault();
	const key = apiKey.value.trim();
	if (!key) return;

	const button = settingsForm.querySelector('button');
	button.disabled = true;
	settingsMessage.textContent = '';
	try {
		const response = await fetch('/api/update_client', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			credentials: 'same-origin',
			body: JSON.stringify({ api_key: key })
		});
		if (!response.ok) throw new Error('Request failed');
		apiKey.value = '';
		settingsMessage.textContent = 'API key updated.';
		apiKeyNotice.hidden = true;
		settingsPanel.hidden = true;
		if (retryQuestion) {
			const question = retryQuestion;
			retryQuestion = null;
			void sendQuestion(question);
		} else {
			input.focus();
		}
	} catch {
		settingsMessage.textContent = 'Unable to update the API key.';
	} finally {
		button.disabled = false;
	}
});

apiKeyNotice.hidden = false;
settingsPanel.hidden = false;
apiKey.focus();