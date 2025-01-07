import { WebSocketHandler } from './websocket-handler.js';

export class ChatApp {
    constructor() {
        this.messageInput = document.getElementById('messageInput');
        this.wsHandler = new WebSocketHandler();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Send button click handler
        document.querySelector('button[onclick="sendMessage()"]').onclick = () => this.sendMessage();
        
        // Enter key handler
        this.messageInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                this.sendMessage();
            }
        });
    }

    sendMessage() {
        const message = this.messageInput.value;
        if (message) {
            this.wsHandler.sendMessage(message);
            this.messageInput.value = '';
        }
    }
}

// Initialize the chat application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
}); 