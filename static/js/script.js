const sendBtn = document.getElementById("sendBtn");
const input = document.getElementById("message");
const messages = document.getElementById("messages");
const historyList = document.getElementById("historyList");
const newChatBtn = document.getElementById("newChatBtn");

let currentConversationId = null;

function addMessage(text, type) {
    const div = document.createElement("div");
    div.classList.add("message");
    div.classList.add(type);
    div.innerHTML = `<p>${text}</p>`;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

function clearMessages() {
    messages.innerHTML = "";
}

function renderHistory(conversations) {
    historyList.innerHTML = "";

    if (!conversations.length) {
        const emptyState = document.createElement("div");
        emptyState.className = "history-empty";
        emptyState.textContent = "No conversations yet";
        historyList.appendChild(emptyState);
        return;
    }

    conversations.forEach((conversation) => {
        const item = document.createElement("button");
        item.className = "chat-item";

        if (conversation.id === currentConversationId) {
            item.classList.add("active");
        }

        item.innerHTML = `
            <div class="chat-header">
                <span class="chat-title">${conversation.title}</span>
                <button class="delete-chat">Delete</button>
            </div>
            <span class="chat-preview">${conversation.preview || "Start chatting"}</span>
        `;

        item.addEventListener("click", () => loadConversation(conversation.id));

        const deleteBtn = item.querySelector(".delete-chat");
        deleteBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            deleteConversation(conversation.id);
        });

        historyList.appendChild(item);
    });
}

async function loadConversations() {
    const response = await fetch("/conversations");
    const data = await response.json();
    renderHistory(data.conversations || []);
}

async function loadConversation(conversationId) {
    currentConversationId = conversationId;
    clearMessages();

    const response = await fetch(`/conversations/${conversationId}`);
    const data = await response.json();

    (data.messages || []).forEach((message) => {
        addMessage(message.content, message.role === "user" ? "user" : "bot");
    });

    loadConversations();
}

async function createConversation() {
    const response = await fetch("/conversations/new", { method: "POST" });
    const data = await response.json();
    currentConversationId = data.conversation_id;
    clearMessages();
    loadConversations();
}

async function deleteConversation(conversationId) {
    await fetch(`/conversations/${conversationId}`, { method: "DELETE" });
    if (currentConversationId === conversationId) {
        currentConversationId = null;
        clearMessages();
    }
    loadConversations();
}

async function sendMessage() {
    const message = input.value.trim();
    if (message === "") return;

    addMessage(message, "user");
    input.value = "";

    const response = await fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: message,
            conversation_id: currentConversationId
        })
    });

    const data = await response.json();

    if (data.response) {
        addMessage(data.response, "bot");
    }

    currentConversationId = data.conversation_id || currentConversationId;
    loadConversations();
}

sendBtn.addEventListener("click", sendMessage);
input.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});
newChatBtn.addEventListener("click", createConversation);

loadConversations();