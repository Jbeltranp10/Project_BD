/**
 * main.js - Funcionalidad principal y utilitarios
 */

// Clase principal para manejar la funcionalidad común
class Main {
    constructor() {
        this.apiEndpoints = {
            SEARCH: '/api/search',
            PROVIDENCIA: '/api/providencia',
            SIMILITUDES: '/api/similitudes',
            STATS: '/api/stats'
        };
        
        // Inicializar cuando el DOM esté listo
        document.addEventListener('DOMContentLoaded', () => this.init());
    }

    /**
     * Inicializa la funcionalidad principal
     */
    init() {
        console.log('Inicializando aplicación...');
        this.loadInitialStats();
    }

    /**
     * Carga las estadísticas iniciales
     */
    async loadInitialStats() {
        try {
            const response = await fetch(this.apiEndpoints.STATS);
            const data = await response.json();

            if (data.success) {
                this.displayStats(data.data);
            } else {
                console.error('Error cargando estadísticas:', data.error);
            }
        } catch (error) {
            console.error('Error en loadInitialStats:', error);
        }
    }

    /**
     * Muestra las estadísticas en el contenedor correspondiente
     * @param {Object} stats - Objeto con estadísticas
     */
    displayStats(stats) {
        const statsContainer = document.getElementById('stats');
        if (!statsContainer) return;

        statsContainer.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <h4>Total Providencias</h4>
                    <p class="stat-number">${stats.total}</p>
                </div>
                <div class="stat-card">
                    <h4>Por Tipo</h4>
                    ${Object.entries(stats.por_tipo)
                        .map(([tipo, count]) => `
                            <div class="stat-row">
                                <span>${tipo}</span>
                                <span class="stat-number">${count}</span>
                            </div>
                        `).join('')}
                </div>
                <div class="stat-card">
                    <h4>Por Año</h4>
                    ${Object.entries(stats.por_anio)
                        .map(([anio, count]) => `
                            <div class="stat-row">
                                <span>${anio}</span>
                                <span class="stat-number">${count}</span>
                            </div>
                        `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Utility: Función para debounce de eventos
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Utility: Formatea fechas
     */
    static formatDate(dateString) {
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        return new Date(dateString).toLocaleDateString('es-CO', options);
    }

    /**
     * Utility: Trunca texto
     */
    static truncateText(text, length = 150) {
        return text.length > length ? 
            text.substring(0, length) + '...' : 
            text;
    }

    /**
     * Utility: Muestra mensajes de error
     */
    static showError(message, container) {
        container.innerHTML = `
            <div class="error-message">
                <span class="error-icon">⚠️</span>
                <p>${message}</p>
            </div>
        `;
    }

    /**
     * Utility: Muestra estado de carga
     */
    static showLoading(container) {
        container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>Cargando...</p>
            </div>
        `;
    }
}

// Exportar para uso en otros módulos
window.mainApp = new Main();