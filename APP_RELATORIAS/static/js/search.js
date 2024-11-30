/**
 * search.js - Manejo específico de la funcionalidad de búsqueda
 */

class Search {
    constructor() {
        this.initializeElements();
        this.setupEventListeners();
        this.currentSearch = null;
        this.availableYears = new Set();
        this.loadAvailableYears();
    }

    async loadAvailableYears() {
        try {
            const response = await fetch(`${mainApp.apiEndpoints.STATS}`);
            const data = await response.json();
            if (data.success && data.data.por_anio) {
                this.availableYears = new Set(Object.keys(data.data.por_anio));
            }
        } catch (error) {
            console.error('Error cargando años disponibles:', error);
        }
    }

    initializeElements() {
        this.filters = {
            tipo: document.getElementById('tipo'),
            anio: document.getElementById('anio'),
            providencia: document.getElementById('providencia'),
            texto: document.getElementById('searchText')
        };

        this.containers = {
            results: document.getElementById('results'),
            similarities: document.getElementById('similarities'),
        };
        
        Object.entries(this.filters).forEach(([key, element]) => {
            if (!element) console.error(`Elemento no encontrado: ${key}`);
        });
    }

    setupEventListeners() {
        this.filters.tipo.addEventListener('change', () => {
            this.handleSearch();
        });

        this.filters.anio.addEventListener('input', () => {
            const year = parseInt(this.filters.anio.value);
            if (year > 2024) {
                this.displayResults([], 'future');
                return;
            }
            if (year && !this.availableYears.has(year.toString())) {
                this.displayResults([], 'unavailable');
                return;
            }
            Main.debounce(() => this.handleSearch(), 500)();
        });

        this.filters.providencia.addEventListener('input',
            Main.debounce(() => this.handleProvidenciaSearch(), 500)
        );

        this.filters.texto.addEventListener('input',
            Main.debounce(() => this.handleSearch(), 500)
        );
    }

    async handleSearch() {
        try {
            Main.showLoading(this.containers.results);

            const year = parseInt(this.filters.anio.value);
            if (year > 2024) {
                this.displayResults([], 'future');
                return;
            }
            if (year && !this.availableYears.has(year.toString())) {
                this.displayResults([], 'unavailable');
                return;
            }

            const params = new URLSearchParams();

            if (this.filters.tipo.value) {
                params.append('tipo', this.filters.tipo.value);
            }
            if (this.filters.anio.value) {
                params.append('anio', this.filters.anio.value);
            }
            if (this.filters.texto.value) {
                params.append('texto', this.filters.texto.value);
            }

            const response = await fetch(`${mainApp.apiEndpoints.SEARCH}?${params}`);
            const data = await response.json();

            if (data.success) {
                console.log(data.data);
                this.displayResults(data.data);
            } else {
                Main.showError(data.error, this.containers.results);
            }
        } catch (error) {
            console.error('Error en búsqueda:', error);
            Main.showError('Error al realizar la búsqueda', this.containers.results);
        }
    }

    async handleProvidenciaSearch() {
        const id = this.filters.providencia.value;
        if (!id) {
            console.log('ID vacío, realizando búsqueda general...');
            this.handleSearch();
            return;
        }

        try {
            Main.showLoading(this.containers.results);

            const response = await fetch(`${mainApp.apiEndpoints.PROVIDENCIA}/${id}`);
            const data = await response.json();
            if (data.success) {
                this.displayResults([data.data]);
                console.log(data.data);
            } else {
                Main.showError(data.error, this.containers.results);
            }
        } catch (error) {
            console.error('Error en búsqueda por ID:', error);
            Main.showError('Error al buscar providencia', this.containers.results);
        }
    }

    async loadSimilarities(providenciaId) {
        try {
            Main.showLoading(this.containers.similarities);

            const response = await fetch(
                `${mainApp.apiEndpoints.SIMILITUDES}/${providenciaId}`
            );
            const data = await response.json();

            if (data.success) {
                this.displaySimilarities(data.data);
            } else {
                Main.showError(data.error, this.containers.similarities);
            }
        } catch (error) {
            console.error('Error cargando similitudes:', error);
            Main.showError(
                'Error al cargar providencias similares',
                this.containers.similarities
            );
        }
    }

    displayResults(results, errorType = null) {
        if (!results.length || errorType) {
            let message = '';
            let subMessage = '';

            switch (errorType) {
                case 'future':
                    message = 'No es posible buscar providencias posteriores al año 2024';
                    subMessage = 'Por favor, selecciona un año válido';
                    break;
                case 'unavailable':
                    message = `No existen providencias para el año ${this.filters.anio.value}`;
                    subMessage = 'Por favor, selecciona un año diferente';
                    break;
                default:
                    message = 'No se encontraron resultados';
                    subMessage = 'Intenta ajustar los filtros de búsqueda';
            }

            this.containers.results.innerHTML = `
            <h3>No se encontraron resultados</h3>
                <div class="no-results" style="
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    text-align: center;
                    margin-top: 1rem;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                ">
                    <p style="color: #374151; font-weight: 500; margin-bottom: 0.5rem;">
                        ${message}
                    </p>
                    <p style="color: #6B7280; font-size: 0.875rem;">
                        ${subMessage}
                    </p>
                </div>
            `;
            return;
        }

        this.containers.results.innerHTML = `
        <h3 style="margin-bottom:12px">Se encontraron ${results.length} documentos</h3>
        ${results.map(result => `
            <div class="result-card">
                <div class="result-header">
                    <h3>${result.providencia}</h3>
                    <div class="metadata">
                        <span class="metadata-tag">${result.tipo}</span>
                        <span class="metadata-tag">Año: ${result.anio}</span>
                    </div>
                </div>
                <p class="result-text">
                    ${Main.truncateText(result.texto, 200)}
                </p>
            </div>
        `).join('')}`;
    }

    displaySimilarities(similarities) {
        if (!similarities.length) {
            this.containers.similarities.innerHTML = `
                <div class="no-similarities">
                    <p>No se encontraron providencias similares</p>
                </div>
            `;
            return;
        }

        this.containers.similarities.innerHTML = `
            <h3>Providencias Similares</h3>
            <div class="similarities-grid">
                ${similarities.map(sim => `
                    <div class="similarity-card">
                        <h4>${sim.providencia}</h4>
                        <p class="similarity-score">
                            Score: ${(sim.similitud * 100).toFixed(2)}%
                        </p>
                        <button onclick="searchApp.handleProvidenciaSearch('${sim.providencia}')"
                                class="btn-view">
                            Ver Detalles
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
    }
}

window.searchApp = new Search();