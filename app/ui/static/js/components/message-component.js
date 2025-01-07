import { ChatConstants } from '../constants/chat-constants.js';
import { AudioUtils } from '../utils/audio-utils.js';

export class MessageComponent {
    constructor(messagesContainer) {
        this.messagesContainer = messagesContainer;
        this.currentAudio = null;
    }

    appendMessage(message, isUser = false, costInfo = null, agentFlow = null) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${isUser ? ChatConstants.MESSAGE_TYPES.USER : ChatConstants.MESSAGE_TYPES.BOT}`;
        
        const messageContent = this._createMessageContent(message, isUser);
        messageDiv.appendChild(messageContent);
        
        if (!isUser && (costInfo || agentFlow)) {
            const chipsContainer = this._createChipsContainer(costInfo, agentFlow);
            messageDiv.appendChild(chipsContainer);
        }
        
        this.messagesContainer.appendChild(messageDiv);
        this._scrollToBottom();
    }

    appendError(title, message) {
        const errorDiv = document.createElement("div");
        errorDiv.className = "error-card";
        
        const titleDiv = document.createElement("div");
        titleDiv.className = "error-title";
        titleDiv.textContent = title;
        
        const messageDiv = document.createElement("p");
        messageDiv.className = "error-message";
        messageDiv.textContent = message;
        
        errorDiv.appendChild(titleDiv);
        errorDiv.appendChild(messageDiv);
        this.messagesContainer.appendChild(errorDiv);
        this._scrollToBottom();
    }

    createAudioPlayer(base64Audio) {
        const audioContainer = document.createElement("div");
        audioContainer.className = `message ${ChatConstants.MESSAGE_TYPES.BOT}`;

        const audioPlayerDiv = document.createElement("div");
        audioPlayerDiv.className = "audio-container";

        const audio = document.createElement("audio");
        audio.src = `data:${ChatConstants.MIME_TYPES.AUDIO};base64,${base64Audio}`;

        const controls = this._createAudioControls(audio, base64Audio);
        audioPlayerDiv.appendChild(controls);
        audioContainer.appendChild(audioPlayerDiv);

        return audioContainer;
    }

    _createMessageContent(message, isUser) {
        const messageContent = document.createElement("div");
        messageContent.className = "message-content";
        messageContent.innerHTML = `<strong>${isUser ? "You" : "Bot"}:</strong> ${message}`;
        return messageContent;
    }

    _createChipsContainer(costInfo, agentFlow) {
        const chipsContainer = document.createElement("div");
        chipsContainer.className = "message-chips";
        
        if (costInfo?.request_cost) {
            chipsContainer.appendChild(this._createCostChip(costInfo.request_cost));
        }
        
        if (agentFlow) {
            chipsContainer.appendChild(this._createAgentFlowChip(agentFlow));
        }
        
        return chipsContainer;
    }

    _createCostChip(cost) {
        const costChip = document.createElement("div");
        costChip.className = "message-cost-chip";
        costChip.innerHTML = `<i class="fas fa-coins"></i> $${cost.toFixed(3)}`;
        return costChip;
    }

    _createAgentFlowChip(agentFlow) {
        const flowChip = document.createElement("div");
        flowChip.className = "agent-flow-chip collapsed";
        
        const flowHeader = this._createFlowHeader();
        const flowContent = this._createFlowContent(agentFlow);
        
        flowChip.appendChild(flowHeader);
        flowChip.appendChild(flowContent);
        
        flowHeader.addEventListener("click", () => {
            flowChip.classList.toggle("collapsed");
        });
        
        return flowChip;
    }

    _createFlowHeader() {
        const flowHeader = document.createElement("div");
        flowHeader.className = "agent-flow-header";
        flowHeader.innerHTML = `<i class="fas fa-code-branch"></i> Agent Flow <i class="fas fa-chevron-down"></i>`;
        return flowHeader;
    }

    _createFlowContent(agentFlow) {
        const flowContent = document.createElement("div");
        flowContent.className = "agent-flow-content";
        
        let formattedFlow = '';
        if (agentFlow.tool_calls) {
            formattedFlow += this._formatToolCalls(agentFlow.tool_calls);
        }
        
        if (agentFlow.internal_messages) {
            formattedFlow += this._formatInternalMessages(agentFlow.internal_messages);
        }
        
        flowContent.innerHTML = formattedFlow || JSON.stringify(agentFlow, null, 2);
        return flowContent;
    }

    _formatToolCalls(toolCalls) {
        return toolCalls.map(call => `
            <div class="tool-call">
                <div class="tool-call-name">${call.name}</div>
                <pre>${JSON.stringify(call.parameters, null, 2)}</pre>
                ${call.result ? `<div class="tool-result">Result: ${call.result}</div>` : ''}
            </div>
        `).join('');
    }

    _formatInternalMessages(messages) {
        return messages.map(msg => `<div class="internal-message">${msg}</div>`).join('');
    }

    _createAudioControls(audio, base64Audio) {
        const controls = document.createElement("div");
        controls.className = "audio-controls";

        const playButton = this._createPlayButton(audio);
        const progressContainer = this._createProgressContainer(audio);
        const timeDisplay = this._createTimeDisplay();
        const downloadButton = this._createDownloadButton(base64Audio);

        controls.appendChild(playButton);
        controls.appendChild(progressContainer);
        controls.appendChild(timeDisplay);
        controls.appendChild(downloadButton);

        this._setupAudioEventListeners(audio, playButton, progressContainer.querySelector('.audio-progress-bar'), timeDisplay);

        return controls;
    }

    _createPlayButton(audio) {
        const playButton = document.createElement("button");
        playButton.innerHTML = '<i class="fas fa-play"></i> Play';
        
        playButton.addEventListener("click", () => {
            if (this.currentAudio && this.currentAudio !== audio) {
                this._resetCurrentAudio();
            }
            
            if (audio.paused) {
                this._playAudio(audio, playButton);
            } else {
                this._pauseAudio(audio, playButton);
            }
        });
        
        return playButton;
    }

    _createProgressContainer(audio) {
        const progressContainer = document.createElement("div");
        progressContainer.className = "audio-progress";
        
        const progressBar = document.createElement("div");
        progressBar.className = "audio-progress-bar";
        progressContainer.appendChild(progressBar);
        
        progressContainer.addEventListener("click", (e) => {
            const rect = progressContainer.getBoundingClientRect();
            const pos = (e.clientX - rect.left) / rect.width;
            audio.currentTime = pos * audio.duration;
        });
        
        return progressContainer;
    }

    _createTimeDisplay() {
        const timeDisplay = document.createElement("div");
        timeDisplay.className = "audio-time";
        timeDisplay.textContent = "0:00 / 0:00";
        return timeDisplay;
    }

    _createDownloadButton(base64Audio) {
        const downloadButton = document.createElement("button");
        downloadButton.innerHTML = '<i class="fas fa-download"></i> Download';
        
        downloadButton.addEventListener("click", () => {
            const blob = AudioUtils.base64ToBlob(base64Audio, ChatConstants.MIME_TYPES.AUDIO);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.style.display = "none";
            a.href = url;
            a.download = `audio_${new Date().toISOString().slice(0,19).replace(/[-:]/g, "")}.mp3`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        });
        
        return downloadButton;
    }

    _setupAudioEventListeners(audio, playButton, progressBar, timeDisplay) {
        audio.addEventListener("timeupdate", () => {
            const progress = (audio.currentTime / audio.duration) * 100;
            progressBar.style.width = progress + "%";
            timeDisplay.textContent = `${AudioUtils.formatTime(audio.currentTime)} / ${AudioUtils.formatTime(audio.duration)}`;
        });

        audio.addEventListener("ended", () => {
            this._resetAudioButton(playButton);
            this.currentAudio = null;
        });
    }

    _resetCurrentAudio() {
        this.currentAudio.pause();
        this.currentAudio.currentTime = 0;
        const button = this.currentAudio.parentElement.querySelector("button");
        this._resetAudioButton(button);
    }

    _playAudio(audio, button) {
        audio.play();
        button.innerHTML = '<i class="fas fa-pause"></i> Pause';
        button.classList.add("playing");
        this.currentAudio = audio;
    }

    _pauseAudio(audio, button) {
        audio.pause();
        this._resetAudioButton(button);
    }

    _resetAudioButton(button) {
        button.innerHTML = '<i class="fas fa-play"></i> Play';
        button.classList.remove("playing");
    }

    _scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
} 