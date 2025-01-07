import { ChatConstants } from '../constants/chat-constants.js';

export class AudioUtils {
    static formatTime(seconds) {
        if (isNaN(seconds)) return "0:00";
        const minutes = Math.floor(seconds / 60);
        seconds = Math.floor(seconds % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }

    static base64ToBlob(base64, type) {
        const byteCharacters = atob(base64);
        const byteArrays = [];
        
        for (let offset = 0; offset < byteCharacters.length; offset += ChatConstants.AUDIO_CHUNK_SIZE) {
            const slice = byteCharacters.slice(offset, offset + ChatConstants.AUDIO_CHUNK_SIZE);
            const byteNumbers = new Array(slice.length);
            
            for (let i = 0; i < slice.length; i++) {
                byteNumbers[i] = slice.charCodeAt(i);
            }
            
            const byteArray = new Uint8Array(byteNumbers);
            byteArrays.push(byteArray);
        }
        
        return new Blob(byteArrays, { type });
    }
} 