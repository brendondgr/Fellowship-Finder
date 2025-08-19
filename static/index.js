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
    const processBtn = document.getElementById('process-btn');
    const scrapeModalCleanup = document.getElementById('scrape-modal-cleanup');
    const scrapeModalBrowser = document.getElementById('scrape-modal-browser');
    const cleanupYes = document.getElementById('cleanup-yes');
    const cleanupNo = document.getElementById('cleanup-no');
    const browserChrome = document.getElementById('browser-chrome');
    const browserFirefox = document.getElementById('browser-firefox');
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
        refreshBtn.addEventListener('click', (e) => {
            e.preventDefault();
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
                });
        });
    }

    // --- Scrape and Process Button Event Listeners ---
    if(scrapeBtn) {
        scrapeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            scrapeModalCleanup.classList.remove('hidden');
        });
    }

    if(processBtn) {
        processBtn.addEventListener('click', (e) => {
            e.preventDefault();
            showNotification('Processing data...');
            fetch('/process', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if(data.success) {
                        showNotification('Data processed successfully! Reloading...');
                        setTimeout(() => window.location.reload(), 2000);
                    } else {
                        showNotification(data.error || 'An unknown error occurred.', true);
                    }
                })
                .catch(error => {
                    console.error('Error processing data:', error);
                    showNotification('Error processing data.', true);
                });
        });
    }

    // --- Modal Handling ---
    if(cleanupYes) {
        cleanupYes.addEventListener('click', () => {
            scrapeModalCleanup.classList.add('hidden');
            scrapeModalBrowser.classList.remove('hidden');
            startScrape(true);
        });
    }

    if(cleanupNo) {
        cleanupNo.addEventListener('click', () => {
            scrapeModalCleanup.classList.add('hidden');
            scrapeModalBrowser.classList.remove('hidden');
            startScrape(false);
        });
    }

    if(browserChrome) {
        browserChrome.addEventListener('click', () => {
            scrapeModalBrowser.classList.add('hidden');
            runScrape(true, 'chrome');
        });
    }
    
    if(browserFirefox) {
        browserFirefox.addEventListener('click', () => {
            scrapeModalBrowser.classList.add('hidden');
            runScrape(true, 'firefox');
        });
    }

    let scrapeCleanup = false;

    function startScrape(cleanup) {
        scrapeCleanup = cleanup;
    }

    function runScrape(cleanup, browser) {
        showNotification(`Starting scrape with ${browser}...`);
        fetch('/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cleanup: cleanup, browser: browser })
        })
        .then(response => response.json())
        .then(data => {
            if(data.success) {
                showNotification('Scraping process started successfully.');
            } else {
                showNotification(data.error || 'Failed to start scraping.', true);
            }
        })
        .catch(error => {
            console.error('Error starting scrape:', error);
            showNotification('Error starting scrape.', true);
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
