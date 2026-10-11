const form = document.getElementById('chat-form');
const input = document.getElementById('question');
const messages = document.getElementById('messages');
const welcome = document.getElementById('welcome');
const scroller = document.getElementById('chat-scroll');
const send = form.querySelector('button');
let history = [], controller = null;
function addMessage(text, role) {
	const row = document.createElement('div');
	row.className = 'message ' + role;
	const avatar = document.createElement('span');
	avatar.className = 'avatar';
	avatar.textContent = role === 'user' ? 'You' : '🌶️';
	const bubble = document.createElement('div');
	bubble.className = 'bubble';
	bubble.textContent = text;
	row.append(avatar, bubble);
	messages.append(row);
	scroller.scrollTop = scroller.scrollHeight;
	return bubble;
}
form.addEventListener('submit', async event => {
	event.preventDefault();
	const question = input.value.trim();
	if (!question || controller) return;
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
		if (!response.ok) throw new Error('Request failed');
		const data = await response.json();
		if (typeof data.reply !== 'string' || !data.reply.trim()) throw new Error('Invalid reply');
		pending.textContent = data.reply;
		history.push({ role:'assistant', content:data.reply });
	} catch (error) {
		if (error.name !== 'AbortError') {
			pending.textContent = 'Unable to reach ChillBot. Please try again. If you’re setting up this app, connect /api/chat to your AI service.';
			history.pop();
		}
	} finally {
		if (controller === request) { controller = null; send.disabled = false; input.focus(); }
		scroller.scrollTop = scroller.scrollHeight;
	}
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
	messages.replaceChildren();
	welcome.hidden = false;
	send.disabled = false;
	input.value = '';
	input.focus();
});