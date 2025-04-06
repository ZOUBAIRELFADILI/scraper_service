// Main JavaScript for the scraper service
document.addEventListener('DOMContentLoaded', function() {
    const scrapeForm = document.getElementById('scrapeForm');
    const urlInput = document.getElementById('urlInput');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const resultsContainer = document.getElementById('resultsContainer');
    const articlesContainer = document.getElementById('articlesContainer');
    const errorContainer = document.getElementById('errorContainer');
    const statsContainer = document.getElementById('statsContainer');

    scrapeForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get URLs from textarea
        const urlsText = urlInput.value.trim();
        if (!urlsText) {
            showError('Please enter at least one URL');
            return;
        }

        // Parse URLs (one per line)
        const urls = urlsText.split('\n')
            .map(url => url.trim())
            .filter(url => url.length > 0);

        if (urls.length === 0) {
            showError('Please enter at least one valid URL');
            return;
        }

        // Show loading overlay
        loadingOverlay.style.display = 'flex';
        errorContainer.style.display = 'none';
        articlesContainer.innerHTML = '';
        statsContainer.innerHTML = '';

        try {
            // Call the API
            const response = await fetch('/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ urls })
            });

            // Hide loading overlay
            loadingOverlay.style.display = 'none';

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to scrape articles');
            }

            const data = await response.json();
            
            // Display results
            displayResults(data);
            
            // Scroll to results
            resultsContainer.scrollIntoView({ behavior: 'smooth' });
        } catch (error) {
            // Hide loading overlay
            loadingOverlay.style.display = 'none';
            
            // Show error
            showError(error.message || 'An error occurred while scraping articles');
        }
    });

    function displayResults(data) {
        articlesContainer.innerHTML = '';
        statsContainer.innerHTML = '';
        
        if (data.articles.length === 0 && data.errors.length === 0) {
            showError('No articles found and no errors reported. Try different URLs.');
            return;
        }

        // Display statistics
        const statsHtml = `
            <div class="alert alert-info">
                <h4>Scraping Results</h4>
                <p>Found ${data.articles.length} articles from ${data.articles.length + data.errors.length} URLs</p>
                ${data.errors.length > 0 ? `<p>Failed to scrape ${data.errors.length} URLs</p>` : ''}
            </div>
        `;
        statsContainer.innerHTML = statsHtml;

        // Display errors if any
        if (data.errors.length > 0) {
            let errorHtml = `
                <div class="card error-container mb-4">
                    <div class="card-header bg-danger text-white">
                        <h5 class="mb-0">Errors (${data.errors.length})</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
            `;
            
            data.errors.forEach(error => {
                errorHtml += `
                    <li class="list-group-item">
                        <strong>${error.url}</strong>: ${error.error}
                    </li>
                `;
            });
            
            errorHtml += `
                        </ul>
                    </div>
                </div>
            `;
            
            errorContainer.innerHTML = errorHtml;
            errorContainer.style.display = 'block';
        } else {
            errorContainer.style.display = 'none';
        }

        // Display articles
        if (data.articles.length > 0) {
            const resultsHeader = document.createElement('div');
            resultsHeader.className = 'row mb-4';
            resultsHeader.innerHTML = `
                <div class="col-12">
                    <h3>Articles (${data.articles.length})</h3>
                    <hr>
                </div>
            `;
            articlesContainer.appendChild(resultsHeader);

            // Create row for articles
            const articlesRow = document.createElement('div');
            articlesRow.className = 'row';
            articlesContainer.appendChild(articlesRow);

            // Group articles by domain for better organization
            const articlesByDomain = groupArticlesByDomain(data.articles);
            
            // Display articles by domain
            Object.keys(articlesByDomain).forEach(domain => {
                const domainArticles = articlesByDomain[domain];
                
                // Create domain header
                const domainHeader = document.createElement('div');
                domainHeader.className = 'col-12 mb-3';
                domainHeader.innerHTML = `
                    <h4 class="domain-header">
                        <i class="bi bi-globe"></i> ${domain} 
                        <span class="badge bg-primary">${domainArticles.length}</span>
                    </h4>
                `;
                articlesRow.appendChild(domainHeader);
                
                // Display articles for this domain
                domainArticles.forEach(article => {
                    const articleElement = document.createElement('div');
                    articleElement.className = 'col-md-6 col-lg-4 mb-4';
                    
                    // Format publication date
                    const pubDate = article.publication_date ? 
                        new Date(article.publication_date).toLocaleDateString() : 
                        'Unknown';
                    
                    // Truncate content for display
                    const truncatedContent = article.content.length > 300 ? 
                        article.content.substring(0, 300) + '...' : 
                        article.content;
                    
                    // Create URL object to get hostname
                    const urlObj = new URL(article.url);
                    
                    articleElement.innerHTML = `
                        <div class="card article-card h-100">
                            <div class="article-header d-flex justify-content-between align-items-center">
                                <span class="badge language-badge">${article.language.toUpperCase()}</span>
                                <small class="text-muted">${pubDate}</small>
                            </div>
                            <div class="article-content">
                                <h5 class="card-title">${article.title}</h5>
                                <p class="card-text text-muted small mb-2">
                                    <a href="${article.url}" target="_blank" class="text-truncate d-inline-block" style="max-width: 100%;">
                                        ${article.url}
                                    </a>
                                </p>
                                <p class="card-text">${truncatedContent}</p>
                            </div>
                            <div class="article-footer">
                                <div class="d-flex justify-content-between">
                                    <a href="${article.url}" target="_blank" class="btn btn-sm btn-primary">
                                        <i class="bi bi-box-arrow-up-right"></i> View Original
                                    </a>
                                    <button class="btn btn-sm btn-outline-secondary copy-content" 
                                            data-content="${encodeURIComponent(article.content)}"
                                            data-bs-toggle="tooltip" 
                                            title="Copy full content to clipboard">
                                        <i class="bi bi-clipboard"></i> Copy
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    articlesRow.appendChild(articleElement);
                });
            });

            // Initialize tooltips
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });

            // Add event listeners for copy buttons
            document.querySelectorAll('.copy-content').forEach(button => {
                button.addEventListener('click', function() {
                    const content = decodeURIComponent(this.getAttribute('data-content'));
                    navigator.clipboard.writeText(content).then(() => {
                        // Update button text and style temporarily
                        const icon = this.querySelector('i');
                        icon.className = 'bi bi-check-lg';
                        this.classList.add('btn-success');
                        this.classList.remove('btn-outline-secondary');
                        
                        setTimeout(() => {
                            icon.className = 'bi bi-clipboard';
                            this.classList.remove('btn-success');
                            this.classList.add('btn-outline-secondary');
                        }, 2000);
                    });
                });
            });
        }
    }

    function groupArticlesByDomain(articles) {
        const articlesByDomain = {};
        
        articles.forEach(article => {
            try {
                const urlObj = new URL(article.url);
                const domain = urlObj.hostname.replace('www.', '');
                
                if (!articlesByDomain[domain]) {
                    articlesByDomain[domain] = [];
                }
                
                articlesByDomain[domain].push(article);
            } catch (e) {
                // If URL parsing fails, use "Other" as domain
                if (!articlesByDomain['Other']) {
                    articlesByDomain['Other'] = [];
                }
                articlesByDomain['Other'].push(article);
            }
        });
        
        return articlesByDomain;
    }

    function showError(message) {
        errorContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle-fill"></i> ${message}
            </div>
        `;
        errorContainer.style.display = 'block';
    }
});
