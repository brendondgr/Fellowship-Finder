document.addEventListener('DOMContentLoaded', () => {
    const fellowshipCardsContainer = document.getElementById('fellowship-cards-container');

    let currentPage = 1;
    let itemsPerPage = document.getElementById('items-per-page').value;
    let recentlyRemovedId = null;
    let undoTimeout = null;

    // --- Filter and Search Elements ---
    const getResultsBtn = document.getElementById('get-results-btn');
    const minStarsSlider = document.getElementById('min-stars');
    const minStarsValue = document.getElementById('min-stars-value');
    const favoritesFirstCheckbox = document.getElementById('favorites-first');
    const showRemovedCheckbox = document.getElementById('show-removed');
    const searchInput = document.getElementById('search-input');
    const refreshBtn = document.getElementById('refresh-btn');

    minStarsSlider.addEventListener('input', () => {
        minStarsValue.textContent = minStarsSlider.value;
    });

    getResultsBtn.addEventListener('click', () => {
        currentPage = 1;
        fellowshipCardsContainer.innerHTML = '';
        fetchFellowships();
    });

    const itemsPerPageSelector = document.getElementById('items-per-page');
    itemsPerPageSelector.addEventListener('change', () => {
        itemsPerPage = itemsPerPageSelector.value;
        currentPage = 1;
        fellowshipCardsContainer.innerHTML = '';
        fetchFellowships();
    });

    const loadMoreBtn = document.getElementById('load-more-btn');
    loadMoreBtn.addEventListener('click', () => {
        currentPage++;
        fetchFellowships();
    });

    const undoBtn = document.getElementById('undo-btn');
    undoBtn.addEventListener('click', () => {
        if (recentlyRemovedId !== null) {
            undoRemoveFellowship(recentlyRemovedId);
            recentlyRemovedId = null;
            clearTimeout(undoTimeout);
            document.getElementById('undo-container').classList.add('hidden');
        }
    });

    // --- New elements for scrape and process ---
    const scrapeBtn = document.getElementById('scrape-btn');
    const scrapeModal = document.getElementById('scrape-modal');
    const scrapeModalContent = document.getElementById('scrape-modal-content');
    const notificationContainer = document.getElementById('notification-container');
    const notificationMessage = document.getElementById('notification-message');
    
    function showNotification(message, isError = false) {
        notificationMessage.textContent = message;
        notificationContainer.classList.remove('hidden');
        notificationContainer.classList.toggle('bg-red-500', isError);
        notificationContainer.classList.toggle('bg-blue-500', !isError);
        setTimeout(() => {
            notificationContainer.classList.add('hidden');
        }, 5000); // Hide after 5 seconds
    }

    if(refreshBtn) {
        const refreshIcon = refreshBtn.querySelector('img'); // Define refreshIcon here
        refreshBtn.addEventListener('click', (e) => {
            e.preventDefault();
            refreshIcon.classList.add('spin'); // Add spin class on click
            showNotification('Refreshing data...');
            
            fetch('/api/refresh', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if(data.success) {
                        currentPage = 1;
                        fellowshipCardsContainer.innerHTML = '';
                        fetchFellowships(); // Re-fetch with current filters
                        showNotification('Data refreshed successfully!');
                    } else {
                        showNotification(data.error || 'Failed to refresh data.', true);
                    }
                })
                .catch(error => {
                    console.error('Error refreshing data:', error);
                    showNotification('Error refreshing data.', true);
                })
                .finally(() => {
                    refreshIcon.classList.remove('spin'); // Remove spin class after fetch
                });
        });
    }

    if(scrapeBtn) {
        scrapeBtn.addEventListener('click', () => {
            // Load content from scrape.html
            fetch('/scrape')
                .then(response => response.text())
                .then(html => {
                    scrapeModalContent.innerHTML = html;
                    scrapeModal.classList.remove('hidden');
                    scrapeModal.classList.add('flex'); // Use flex to center the modal content
                    
                    // Manually execute the script content from scrape.js
                    const scriptElement = document.createElement('script');
                    scriptElement.textContent = `
                        // --- Browser Button Selection ---
                        const browserButtons = document.querySelectorAll('.browser-btn');
                        browserButtons.forEach(button => {
                            button.addEventListener('click', () => {
                                browserButtons.forEach(btn => {
                                    btn.classList.remove('selected');
                                    btn.classList.add('text-gray-600');
                                });
                                button.classList.add('selected');
                                button.classList.remove('text-gray-600');
                            });
                        });

                        // --- Keyword Logic Sliding Toggle ---
                        const keywordLogicSlider = document.getElementById('keyword-logic-slider');
                        const keywordLogicButtons = document.querySelectorAll('.keyword-logic-btn');
                        if (keywordLogicSlider && keywordLogicButtons.length) {
                            keywordLogicButtons.forEach(button => {
                                button.addEventListener('click', () => {
                                    keywordLogicButtons.forEach(btn => btn.classList.remove('selected'));
                                    button.classList.add('selected');
                                    if (button.dataset.logic === 'OR') {
                                        keywordLogicSlider.style.transform = 'translateX(calc(100% + 2px))';
                                    } else {
                                        keywordLogicSlider.style.transform = 'translateX(0%)';
                                    }
                                });
                            });
                        }

                        // --- Collapsible Section Logic ---
                        const collapsibleSections = document.querySelectorAll('.collapsible-section');
                        collapsibleSections.forEach(section => {
                            const header = section.querySelector('.collapsible-header');
                            const optionsContainer = section.querySelector('.filter-options-container');
                            const options = optionsContainer.querySelector('.space-y-2');
                            const allItems = options.querySelectorAll('label');
                            
                            if (allItems.length > 3) {
                                let initialHeight = 0;
                                for(let i = 0; i < 3; i++) {
                                    initialHeight += allItems[i].offsetHeight;
                                }
                                const style = window.getComputedStyle(options);
                                const gap = parseFloat(style.gap) || (parseFloat(style.getPropertyValue('margin-top')) * 2) || 8;
                                initialHeight += gap * 2;

                                optionsContainer.style.maxHeight = \`\${initialHeight}px\`;

                                header.addEventListener('click', () => {
                                    section.classList.toggle('expanded');
                                    if (section.classList.contains('expanded')) {
                                        optionsContainer.style.maxHeight = \`\${options.scrollHeight}px\`;
                                    } else {
                                        optionsContainer.style.maxHeight = \`\${initialHeight}px\`;
                                    }
                                });
                            } else {
                                const toggleIcon = header.querySelector('.toggle-icon');
                                if (toggleIcon) {
                                    toggleIcon.style.display = 'none';
                                }
                                header.style.cursor = 'default';
                                optionsContainer.style.maxHeight = \`\${options.scrollHeight}px\`;
                            }
                        });

                        // --- Save Filters on Begin Searching ---
                        const modalRoot = document.getElementById('scrape-modal-content');
                        const beginSearchingBtn = modalRoot.querySelector('#begin-searching-btn');
                        if (beginSearchingBtn) {
                            beginSearchingBtn.addEventListener('click', async () => {
                                try {
                                    const selectedBrowserButton = modalRoot.querySelector('.browser-btn.selected');
                                    const browsing = selectedBrowserButton ? selectedBrowserButton.dataset.browser : 'firefox';

                                    const filtersToSave = {
                                        Browsing: browsing,
                                        categories: {},
                                        keywords: {
                                            type: (modalRoot.querySelector('.keyword-logic-btn.selected') || {}).dataset?.logic || 'AND',
                                            words: (modalRoot.querySelector('#keywords-input')?.value || '').split(',').map(s => s.trim()).filter(Boolean)
                                        },
                                        system_instructions: modalRoot.querySelector('#system-instructions-textarea')?.value || ''
                                    };

                                    modalRoot.querySelectorAll('[data-category]').forEach(container => {
                                        const category = container.dataset.category;
                                        if (category === 'keywords' || category === 'system_instructions') return;

                                        if (category === 'Citizenship Requirement' || category === 'Residency Requirement') {
                                            const input = container.querySelector('input');
                                            const value = input ? input.value : '';
                                            filtersToSave.categories[category] = value.split(',').map(s => s.trim()).filter(Boolean);
                                        } else {
                                            const selected = [];
                                            container.querySelectorAll('input[type="checkbox"]:checked').forEach(checkbox => {
                                                selected.push(checkbox.value);
                                            });
                                            filtersToSave.categories[category] = selected;
                                        }
                                    });

                                    const resp = await fetch('/api/filters', {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify(filtersToSave, null, 4)
                                    });

                                    const result = await resp.json();
                                    if (resp.ok && result.success) {
                                        alert('Filters saved successfully!');
                                    } else {
                                        alert('Error saving filters: ' + (result.error || resp.statusText));
                                    }
                                } catch (err) {
                                    console.error('Error saving filters:', err);
                                    alert('An error occurred while saving filters.');
                                }
                            });
                        }
                    `;
                    scrapeModalContent.appendChild(scriptElement);
                })
                .catch(error => {
                    console.error('Error loading scrape page:', error);
                    // Optionally show an error message to the user
                    scrapeModalContent.innerHTML = '<p class="p-8 text-red-500">Could not load scrape options. Please try again later.</p>';
                    scrapeModal.classList.remove('hidden');
                    scrapeModal.classList.add('flex');
                });
        });
    }

    // Close the modal if the background is clicked
    if(scrapeModal){
        scrapeModal.addEventListener('click', (e) => {
            if (e.target === scrapeModal) {
                scrapeModal.classList.add('hidden');
                scrapeModal.classList.remove('flex');
                scrapeModalContent.innerHTML = ''; // Clear content when closing
            }
        });
    }
    
    function fetchFellowships() {
        const minStars = minStarsSlider.value;
        const favoritesFirst = favoritesFirstCheckbox.checked;
        const showRemoved = showRemovedCheckbox.checked;
        const keywords = searchInput.value;

        const queryParams = new URLSearchParams({
            page: currentPage,
            per_page: itemsPerPage,
            min_stars: minStars,
            favorites_first: favoritesFirst,
            show_removed: showRemoved,
            keywords: keywords
        });

        fetch(`/api/fellowships?${queryParams.toString()}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('total-opportunities').textContent = data.total_count;
                data.fellowships.forEach(fellowship => {
                    fellowshipCardsContainer.appendChild(createFellowshipCard(fellowship));
                });

                if (data.has_more) {
                    loadMoreBtn.classList.remove('hidden');
                    document.getElementById('no-more-message').classList.add('hidden');
                } else {
                    loadMoreBtn.classList.add('hidden');
                    document.getElementById('no-more-message').classList.remove('hidden');
                }
            })
            .catch(error => console.error('Error fetching fellowships:', error));
    }

    function createFellowshipCard(fellowship) {
        const card = document.createElement('div');
        card.className = 'bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200 hover:shadow-xl transition-shadow duration-300';
        card.dataset.id = fellowship.id;

        const subjectsHtml = (Array.isArray(fellowship.subjects) ? fellowship.subjects.map(subject => `<span class="px-3 py-1 text-xs font-medium bg-indigo-100 text-indigo-800 rounded-full">${subject}</span>`).join('') : '') || 'N/A';
        const ratingHtml = createRatingStars(fellowship.interest_rating);
        
        const title = fellowship.title || 'No Title Provided';
        const location = fellowship.location || 'N/A';
        const continent = fellowship.continent || 'N/A';
        const deadline = fellowship.deadline || 'N/A';
        const link = fellowship.link || '#';
        const description = fellowship.description || 'No description available.';
        const total_compensation = fellowship.total_compensation || 'N/A';
        const length_in_years = fellowship.length_in_years || 'N/A';

        card.innerHTML = `
            <div class="p-6 md:p-8">
                <!-- First Row -->
                <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
                    <div class="flex-1 min-w-0">
                        <h3 class="text-2xl font-bold text-gray-900 truncate">${title}</h3>
                        <div class="mt-1 flex flex-wrap items-center text-sm text-gray-500 gap-x-4 gap-y-1">
                            <span>${location}</span>
                            <span class="hidden sm:inline">•</span>
                            <span>${continent}</span>
                        </div>
                    </div>
                    <div class="flex items-center gap-4 flex-shrink-0">
                        <div class="text-right">
                            <p class="text-sm text-gray-500">Apply by</p>
                            <p class="font-semibold text-gray-700">${deadline}</p>
                        </div>
                        <a href="${link}" target="_blank" rel="noopener noreferrer" class="p-2 rounded-full bg-gray-100 hover:bg-indigo-100 text-gray-500 hover:text-indigo-600 transition-colors">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                        </a>
                        <button class="favorite-btn p-2 rounded-full bg-gray-100 hover:bg-red-100 text-gray-500 hover:text-red-600 transition-colors ${fellowship.favorited ? 'favorited' : ''}">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                            </svg>
                        </button>
                        <button class="remove-btn p-2 rounded-full bg-gray-100 hover:bg-red-100 text-gray-500 hover:text-red-600 transition-colors">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>
                <!-- Second Row: Description -->
                <div class="mt-6 border-t border-gray-200 pt-6">
                    <h4 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Description</h4>
                    <p class="text-gray-600 leading-relaxed">${description}</p>
                </div>
                <!-- Third Row: Details -->
                <div class="mt-6 border-t border-gray-200 pt-6 grid grid-cols-1 md:grid-cols-3 gap-y-6 gap-x-8">
                    <div class="md:col-span-2">
                        <h4 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Key Features</h4>
                        <div class="flex flex-wrap gap-2">${subjectsHtml}</div>
                    </div>
                    <div class="md:col-span-1 grid grid-cols-3 gap-4 text-center md:text-left">
                        <div>
                            <h4 class="text-sm font-semibold text-gray-500 uppercase tracking-wider truncate">Total</h4>
                            <p class="text-lg font-semibold text-gray-800">${total_compensation}</p>
                        </div>
                        <div>
                            <h4 class="text-sm font-semibold text-gray-500 uppercase tracking-wider">Length</h4>
                            <p class="text-lg font-semibold text-gray-800">${length_in_years} years</p>
                        </div>
                        <div>
                            <h4 class="text-sm font-semibold text-gray-500 uppercase tracking-wider">Rating</h4>
                            <div class="flex items-center justify-center md:justify-start">${ratingHtml}</div>
                        </div>
                    </div>
                </div>
            </div>`;
        
        card.querySelector('.favorite-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            toggleFavorite(fellowship.id, card);
        });

        card.querySelector('.remove-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            removeFellowship(fellowship.id, card);
        });

        return card;
    }

    function createRatingStars(rating) {
        let stars = '';
        const totalStars = 4;
        const normalizedRating = Math.max(0, Math.min(rating || 0, totalStars));

        for (let i = 1; i <= totalStars; i++) {
            if (i <= normalizedRating) {
                stars += '<svg class="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" clip-rule="evenodd" /></svg>';
            } else {
                stars += '<svg class="w-5 h-5 text-gray-300" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" clip-rule="evenodd" /></svg>';
            }
        }
        return stars;
    }

    function toggleFavorite(fellowshipId, card) {
        const isFavorited = card.querySelector('.favorite-btn').classList.toggle('favorited');
        fetch(`/api/fellowships/${fellowshipId}/favorite`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ favorited: isFavorited ? 1 : 0 })
        });
    }

    function removeFellowship(fellowshipId, card) {
        card.classList.add('swipe-out');
        card.addEventListener('animationend', () => {
            card.remove();
        });

        fetch(`/api/fellowships/${fellowshipId}/remove`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const totalElement = document.getElementById('total-opportunities');
                    let currentTotal = parseInt(totalElement.textContent, 10);
                    if (!isNaN(currentTotal)) {
                        totalElement.textContent = currentTotal - 1;
                    }
                }
            })
            .catch(error => console.error('Error removing fellowship:', error));

        recentlyRemovedId = fellowshipId;
        const undoContainer = document.getElementById('undo-container');
        undoContainer.classList.remove('hidden');

        clearTimeout(undoTimeout);
        undoTimeout = setTimeout(() => {
            undoContainer.classList.add('hidden');
            recentlyRemovedId = null;
        }, 5000);
    }

    function undoRemoveFellowship(fellowshipId) {
        fetch(`/api/fellowships/${fellowshipId}/undo`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentPage = 1;
                    fellowshipCardsContainer.innerHTML = '';
                    fetchFellowships();
                }
            });
    }

    // Initial fetch
    fetchFellowships();
});
