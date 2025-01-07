import { ChatConstants } from '../constants/chat-constants.js';
import { MessageComponent } from '../components/message-component.js';

export class WebSocketHandler {
    constructor() {
        this.ws = new WebSocket(ChatConstants.WEBSOCKET_URL);
        this.messageComponent = new MessageComponent(document.getElementById('messages'));
        this.setupWebSocket();
    }

    setupWebSocket() {
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
    }

    handleWebSocketMessage(data) {
        // Update cost information if available
        if (data.cost_info) {
            this.updateCostDisplay(data.cost_info);
        }
        
        // Handle error messages
        if (data.message?.startsWith("Error:")) {
            this.handleErrorMessage(data);
            return;
        }
        
        // Handle normal messages with cost and agent flow
        if (data.message) {
            this.messageComponent.appendMessage(data.message, false, data.cost_info, data.agent_flow);
        }
        
        // Handle images
        if (data.base64_image) {
            this.handleImageMessage(data.base64_image);
        }

        // Handle audio
        if (data.base64_audio) {
            this.handleAudioMessage(data.base64_audio);
        }

        // Handle research results
        if (data.research_result) {
            this.handleResearchMessage(data.research_result);
        }
    }

    handleErrorMessage(data) {
        const errorMessage = data.message.substring(7).trim();
        let title = ChatConstants.ERROR_TYPES.GENERIC;
        
        if (errorMessage.includes("Prompt must be length")) {
            title = ChatConstants.ERROR_TYPES.PROMPT_TOO_LONG;
        } else if (errorMessage.includes("budget exceeded")) {
            title = ChatConstants.ERROR_TYPES.BUDGET_EXCEEDED;
        }
        
        this.messageComponent.appendError(title, errorMessage);
    }

    handleImageMessage(base64Image) {
        const imgDiv = document.createElement("div");
        imgDiv.className = `message ${ChatConstants.MESSAGE_TYPES.BOT}`;
        
        const img = document.createElement("img");
        img.src = `data:${ChatConstants.MIME_TYPES.IMAGE};base64,${base64Image}`;
        img.className = "generated-image";
        
        imgDiv.appendChild(img);
        this.messageComponent.messagesContainer.appendChild(imgDiv);
        this.messageComponent._scrollToBottom();
    }

    handleAudioMessage(base64Audio) {
        const audioPlayer = this.messageComponent.createAudioPlayer(base64Audio);
        this.messageComponent.messagesContainer.appendChild(audioPlayer);
        this.messageComponent._scrollToBottom();
    }

    handleResearchMessage(researchResult) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${ChatConstants.MESSAGE_TYPES.BOT}`;
        
        const messageContent = document.createElement("div");
        messageContent.className = "message-content";
        messageContent.innerHTML = "<strong>Bot:</strong>";
        messageDiv.appendChild(messageContent);
        
        const researchDiv = document.createElement("div");
        researchDiv.className = "research-container";
        
        const researchHeader = document.createElement("div");
        researchHeader.className = "research-header";
        researchHeader.innerHTML = '<i class="fas fa-search"></i> Research Results';
        researchDiv.appendChild(researchHeader);
        
        const researchContent = document.createElement("div");
        researchContent.className = "markdown-content";
        researchContent.innerHTML = DOMPurify.sanitize(marked.parse(researchResult));
        
        researchDiv.appendChild(researchContent);
        messageDiv.appendChild(researchDiv);
        this.messageComponent.messagesContainer.appendChild(messageDiv);
        this.messageComponent._scrollToBottom();
    }

    updateCostDisplay(costInfo) {
        if (!costInfo) return;
        
        const totalCostElement = document.getElementById('totalCost');
        const remainingBudgetElement = document.getElementById('remainingBudget');
        
        if (typeof costInfo.total_cost === 'number') {
            totalCostElement.textContent = costInfo.total_cost.toFixed(3);
        }
        
        if (typeof costInfo.remaining_budget === 'number') {
            remainingBudgetElement.textContent = costInfo.remaining_budget.toFixed(2);
            
            const parentElement = remainingBudgetElement.parentElement;
            if (costInfo.remaining_budget < ChatConstants.LOW_BUDGET_THRESHOLD) {
                parentElement.classList.add('cost-warning');
            } else {
                parentElement.classList.remove('cost-warning');
            }
        }
    }

    sendMessage(message) {
        if (message) {
            this.messageComponent.appendMessage(message, true);
            this.ws.send(message);
        }
    }
} 