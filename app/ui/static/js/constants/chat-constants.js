export const ChatConstants = {
    WEBSOCKET_URL: `ws://${window.location.host}/ws`,
    DEFAULT_BUDGET: 25.00,
    LOW_BUDGET_THRESHOLD: 5.00,
    AUDIO_CHUNK_SIZE: 512,
    MESSAGE_TYPES: {
        USER: 'user',
        BOT: 'bot',
        ERROR: 'error'
    },
    ERROR_TYPES: {
        PROMPT_TOO_LONG: 'Prompt Too Long',
        BUDGET_EXCEEDED: 'Budget Exceeded',
        GENERIC: 'Error'
    },
    MIME_TYPES: {
        AUDIO: 'audio/mp3',
        IMAGE: 'image/png'
    }
}; 