// PATH: erp-frontend/src/services/predictionService.js

/**
 * NYENZ PREDICTION ENGINE
 * Learns from user input to provide intelligent auto-complete suggestions.
 */

const STORAGE_KEY = 'gs_neural_memory';

// The fields we want to learn patterns for
const LEARNABLE_FIELDS = ['district', 'county', 'blockRoad', 'volume', 'tenure'];

const predictionService = {
    
    /**
     * INGEST: Called on Form Submit.
     * Scans the data and saves unique values to memory.
     */
    learn: (formData) => {
        const currentMemory = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};

        LEARNABLE_FIELDS.forEach(field => {
            const val = formData[field]?.trim().toUpperCase();
            if (!val) return;

            // Initialize array if missing
            if (!currentMemory[field]) currentMemory[field] = [];

            // Add only if unique
            if (!currentMemory[field].includes(val)) {
                currentMemory[field].unshift(val); // Add to top
                // Keep memory lean: max 10 suggestions per field
                if (currentMemory[field].length > 10) currentMemory[field].pop();
            }
        });

        localStorage.setItem(STORAGE_KEY, JSON.stringify(currentMemory));
    },

    /**
     * RECALL: Called when Input gets Focus.
     * Returns list of suggestions for a specific field.
     */
    getSuggestions: (field) => {
        const memory = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
        return memory[field] || [];
    }
};

export default predictionService;