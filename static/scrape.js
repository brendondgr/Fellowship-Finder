function setupBrowserSelection() {
    const browserButtons = document.querySelectorAll('.browser-btn');
    if (browserButtons.length === 0) return;

    // Ensure a default is selected if none is provided by the server
    const initiallySelected = document.querySelector('.browser-btn.selected');
    if (!initiallySelected) {
        const firefoxButton = document.querySelector('[data-browser="firefox"]');
        if (firefoxButton) firefoxButton.classList.add('selected');
    }

    browserButtons.forEach(button => {
        button.addEventListener('click', function () {
            browserButtons.forEach(btn => btn.classList.remove('selected'));
            this.classList.add('selected');
        });
    });
}

// --- 2. Collapsible Sections ---
function setupCollapsibleSections() {
    setTimeout(() => {
        const collapsibleSections = document.querySelectorAll('.collapsible-section');
        collapsibleSections.forEach(section => {
            const header = section.querySelector('.collapsible-header');
            const container = section.querySelector('.filter-options-container');
            if (!header || !container) return;

            const items = Array.from(container.querySelectorAll('.space-y-2 > *'));
            if (items.length === 0) {
                container.style.maxHeight = '0px'; // Ensure empty sections are collapsed
                return;
            }

            // Get the full height when all items are visible
            const fullHeight = container.scrollHeight + 'px';

            let collapsedHeight = '0px';
            const hasPartialState = items.length > 3;

            if (hasPartialState) {
                // Calculate height of first 3 items by temporarily hiding the rest
                items.slice(3).forEach(item => item.style.display = 'none');
                collapsedHeight = container.scrollHeight + 'px';
                // IMPORTANT: Show them again so they are present for the full expansion
                items.slice(3).forEach(item => item.style.display = '');
            }

            // Set the initial collapsed state
            container.style.maxHeight = collapsedHeight;
            container.style.overflow = 'hidden';

            header.addEventListener('click', function () {
                // Toggle the 'expanded' class and check if it was added
                const isNowExpanded = section.classList.toggle('expanded');
                
                if (isNowExpanded) {
                    // If the section was just expanded, set max-height to its full scroll height
                    container.style.maxHeight = fullHeight;
                } else {
                    // If the section was just collapsed, set max-height back to its collapsed height
                    container.style.maxHeight = collapsedHeight;
                }
            });
        });
    }, 150); // Use a slightly longer delay to ensure DOM is fully ready for height calculations
}

// --- 3. AND/OR Toggle for Keywords ---
function setupKeywordLogicToggle() {
    const keywordLogicSlider = document.getElementById('keyword-logic-slider');
    const keywordLogicButtons = document.querySelectorAll('.keyword-logic-btn');
    if (!keywordLogicSlider || keywordLogicButtons.length === 0) return;

    keywordLogicButtons.forEach(button => {
        button.addEventListener('click', function () {
            const logic = this.getAttribute('data-logic');

            // Update classes for all buttons
            keywordLogicButtons.forEach(btn => {
                btn.classList.remove('selected', 'text-white');
                btn.classList.add('text-gray-500');
            });
            
            // Add selected classes to the clicked button
            this.classList.add('selected', 'text-white');
            this.classList.remove('text-gray-500');

            if (logic === 'OR') {
                keywordLogicSlider.style.transform = 'translateX(calc(100% + 2px))';
            } else {
                keywordLogicSlider.style.transform = 'translateX(0%)';
            }
        });
    });
}

// --- 4. Provider Toggle (Gemini / Perplexity) ---
function setupProviderToggle() {
    const slider = document.getElementById('api-provider-logic-slider');
    const buttons = document.querySelectorAll('.provider-logic-btn');
    if (!slider || buttons.length === 0) return;

    buttons.forEach(button => {
        button.addEventListener('click', function () {
            const provider = this.getAttribute('data-provider');

            buttons.forEach(btn => {
                btn.classList.remove('selected', 'text-white');
                btn.classList.add('text-gray-500');
            });

            this.classList.add('selected', 'text-white');
            this.classList.remove('text-gray-500');

            if (provider && provider.toLowerCase() === 'perplexity') {
                slider.style.transform = 'translateX(calc(100% + 2px))';
            } else {
                slider.style.transform = 'translateX(0%)';
            }
        });
    });
}

// --- 5. Save API Keys (Gemini / Perplexity) ---
function setupSaveGeminiKeyButton() {
    const saveBtn = document.getElementById('save-gemini-api-key-btn');
    const input = document.getElementById('gemini-api-key-input');
    if (!saveBtn || !input) return;

    saveBtn.addEventListener('click', () => {
        const apiKey = input.value.trim();
        if (!apiKey) return;

        saveGeminiApiKey(apiKey)
            .then(() => alert('Gemini API key saved successfully!'))
            .catch(err => alert('Failed to save Gemini API key: ' + err.message));
    });
}

function setupSavePerplexityKeyButton() {
    const saveBtn = document.getElementById('save-perplexity-api-key-btn');
    const input = document.getElementById('perplexity-api-key-input');
    if (!saveBtn || !input) return;

    saveBtn.addEventListener('click', () => {
        const apiKey = input.value.trim();
        if (!apiKey) return;

        savePerplexityApiKey(apiKey)
            .then(() => alert('Perplexity API key saved successfully!'))
            .catch(err => alert('Failed to save Perplexity API key: ' + err.message));
    });
}

// --- 5. Form Submission ---
function setupFormSubmission() {
    const beginSearchingBtn = document.getElementById('begin-searching-btn');
    if (!beginSearchingBtn) return;

    beginSearchingBtn.addEventListener('click', function () {
        // Disable button and show loading state
        beginSearchingBtn.disabled = true;
        beginSearchingBtn.classList.add('loading');
        beginSearchingBtn.innerHTML = 'Processing... <div class="loading-spinner inline-block ml-2"></div>';

        const formData = collectFormData();
        
        saveFiltersAndStartScraping(formData);
    });
}

function collectFormData() {
    const selectedBrowserBtn = document.querySelector('.browser-btn.selected');
    const selectedBrowser = selectedBrowserBtn ? selectedBrowserBtn.getAttribute('data-browser') : 'firefox';
    
    const keywordLogicBtn = document.querySelector('.keyword-logic-btn.selected');
    const keywordLogic = keywordLogicBtn ? keywordLogicBtn.getAttribute('data-logic') : 'AND';

    const providerBtn = document.querySelector('.provider-logic-btn.selected');
    const provider = providerBtn ? providerBtn.getAttribute('data-provider') : 'Gemini';

    const data = {
        "Browsing": selectedBrowser,
        "Filter": provider,
        "categories": {},
        "keywords": {
            "type": keywordLogic,
            "words": []
        },
        "system_instructions": ""
    };

    // Collect checkbox categories
    document.querySelectorAll('.collapsible-section[data-category], div[data-category]:not(.collapsible-section)').forEach(container => {
        const categoryName = container.getAttribute('data-category');
        
        const checkboxes = container.querySelectorAll('input[type="checkbox"]:checked');
        if (checkboxes.length > 0) {
            data.categories[categoryName] = Array.from(checkboxes).map(cb => cb.value);
        }
    });

    // Collect text input categories (Citizenship and Residency)
    const citizenshipInput = document.getElementById('citizenship-input');
    if (citizenshipInput && citizenshipInput.value.trim()) {
        data.categories['Citizenship Requirement'] = citizenshipInput.value.split(',').map(s => s.trim()).filter(Boolean);
    }

    const residencyInput = document.getElementById('residency-input');
    if (residencyInput && residencyInput.value.trim()) {
        data.categories['Residency Requirement'] = residencyInput.value.split(',').map(s => s.trim()).filter(Boolean);
    }

    // Collect keywords
    const keywordsInput = document.getElementById('keywords-input');
    if (keywordsInput && keywordsInput.value.trim()) {
        data.keywords.words = keywordsInput.value.split(',').map(s => s.trim()).filter(Boolean);
    }

    // Collect system instructions
    const systemInstructionsTextarea = document.getElementById('system-instructions-textarea');
    if (systemInstructionsTextarea) {
        data.system_instructions = systemInstructionsTextarea.value.trim();
    }

    return data;
}

function saveFiltersAndStartScraping(formData) {
    const beginSearchingBtn = document.getElementById('begin-searching-btn');

    // First, save any API keys that were provided.
    const geminiInput = document.getElementById('gemini-api-key-input');
    const perplexityInput = document.getElementById('perplexity-api-key-input');
    const keySaves = [];

    if (geminiInput && geminiInput.value.trim()) {
        keySaves.push(saveGeminiApiKey(geminiInput.value.trim()));
    }
    if (perplexityInput && perplexityInput.value.trim()) {
        keySaves.push(savePerplexityApiKey(perplexityInput.value.trim()));
    }

    Promise.all(keySaves)
        .then(() => {
            // Then, save the filters and trigger the scraping process.
            return fetch('/api/filters', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
        })
        .then(response => {
            if (!response.ok) {
                // Try to get a meaningful error from the server
                return response.json().then(err => { throw new Error(err.error || `Server responded with status ${response.status}`) });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert('Scraping process started successfully! You will be redirected to the main page.');
                window.location.href = '/';
            } else {
                throw new Error(data.error || 'Failed to start scraping process.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred: ' + error.message);
            // Re-enable the button on failure
            if(beginSearchingBtn) {
                beginSearchingBtn.disabled = false;
                beginSearchingBtn.classList.remove('loading');
                beginSearchingBtn.innerHTML = 'Begin Searching';
            }
        });
}

function saveGeminiApiKey(apiKey) {
    return fetch('/api/api_key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ "gemini_api_key": apiKey })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || 'Failed to save Gemini API key') });
        }
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            throw new Error(data.error || 'A problem occurred while saving the Gemini API key.');
        }
    });
}

function savePerplexityApiKey(apiKey) {
    return fetch('/api/api_key/perplexity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ "perplexity_api_key": apiKey })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || 'Failed to save Perplexity API key') });
        }
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            throw new Error(data.error || 'A problem occurred while saving the Perplexity API key.');
        }
    });
}

/**
 * Initializes all event listeners and interactive components for the scrape form.
 * This function is designed to be called after the form's HTML has been loaded into the DOM.
 */
window.initializeScrapeForm = function() {
    setupBrowserSelection();
    setupCollapsibleSections();
    setupKeywordLogicToggle();
    setupProviderToggle();
    setupSaveGeminiKeyButton();
    setupSavePerplexityKeyButton();
    setupFormSubmission();
};

document.addEventListener('DOMContentLoaded', function () {
    // This will initialize the form if scrape.html is loaded as a standalone page.
    // It will not run for the modal on index.html, as the content is not yet in the DOM.
    if (document.getElementById('begin-searching-btn')) {
        window.initializeScrapeForm();
    }
}); 