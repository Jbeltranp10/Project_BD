class GraphViewer {
    constructor() {
        console.log('Inicializando GraphViewer...');
        this.network = null;
        this.initializeElements();
        this.setupEventListeners();
        this.loadInitialGraph();
    }

    initializeElements() {
        this.elements = {
            container: document.getElementById('graph-container'),
            searchInput: document.getElementById('providencia-search'),
            scoreSlider: document.getElementById('score-slider'),
            scoreValue: document.getElementById('score-value'),
            statsContainer: document.getElementById('graph-stats')
        };
    }

    setupEventListeners() {
        if (this.elements.searchInput) {
            this.elements.searchInput.addEventListener('input', () => {
                this.updateGraph();
            });
        }

        if (this.elements.scoreSlider) {
            this.elements.scoreSlider.addEventListener('input', (e) => {
                const value = e.target.value;
                if (this.elements.scoreValue) {
                    this.elements.scoreValue.textContent = `${value}%`;
                }
                this.updateGraph();
            });
        }
    }

    showNoResultsMessage() {
        if (this.network) {
            this.network.destroy();
            this.network = null;
        }

        this.elements.container.innerHTML = `
            <div class="no-results-container" style="
                height: 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                background: white;
                padding: 2rem;
            ">
                <img src="/static/assets/images/cr7.jpg" 
                     alt="No se encontraron resultados" 
                     style="
                        max-width: 300px;
                        margin-bottom: 1rem;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                     ">
                <h3 style="
                    color: #374151;
                    margin: 1rem 0;
                    font-size: 1.25rem;
                ">No se encontraron relaciones para los criterios especificados</h3>
                <p style="
                    color: #6B7280;
                    font-size: 0.875rem;
                ">Intenta ajustar el porcentaje mínimo de similitud</p>
            </div>
        `;

        // Actualizar estadísticas
        if (this.elements.statsContainer) {
            this.elements.statsContainer.innerHTML = `
                <div class="graph-stats">
                    <p>Total de relaciones: 0</p>
                </div>
            `;
        }
    }

    async loadInitialGraph() {
        try {
            const response = await fetch('/api/graph/ ?min_score=0');
            const data = await response.json();
            if (data.success) {
                if (data.data.relationships.length > 0) {
                    this.renderGraph(data.data);
                    this.updateStats(data.data.stats);
                } else {
                    this.showNoResultsMessage();
                }
            }
        } catch (error) {
            console.error('Error cargando grafo inicial:', error);
            this.showNoResultsMessage();
        }
    }

    updateGraph() {
        const providencia = this.elements.searchInput?.value.trim() || ' ';
        const minScore = parseInt(this.elements.scoreSlider?.value || 0);
        
        try {
            console.log(`Actualizando grafo - Providencia: "${providencia}", Score mínimo: ${minScore}`);
            fetch(`/api/graph/${providencia}?min_score=${minScore}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        if (data.data.relationships.length > 0) {
                            console.log(`Datos recibidos: ${data.data.relationships.length} relaciones encontradas`);
                            this.renderGraph(data.data);
                            this.updateStats(data.data.stats);
                        } else {
                            console.log('No se encontraron resultados');
                            this.showNoResultsMessage();
                        }
                    } else {
                        console.error('Error en respuesta:', data.error);
                        this.showNoResultsMessage();
                    }
                })
                .catch(error => {
                    console.error('Error actualizando grafo:', error);
                    this.showNoResultsMessage();
                });
        } catch (error) {
            console.error('Error en updateGraph:', error);
            this.showNoResultsMessage();
        }
    }

    renderGraph(graphData) {
        if (!this.elements.container) return;
    
        // Configuración de nodos
        const nodes = new vis.DataSet(graphData.nodes.map(node => ({
            id: node.id,
            label: node.nombre,
            color: {
                background: '#FFB5D9',
                border: '#FF69B4',
                highlight: {
                    background: '#FF69B4',
                    border: '#FF1493'
                },
                hover: {
                    background: '#FF69B4',
                    border: '#FF1493'
                }
            },
            shape: 'dot',
            size: 25,
            font: {
                color: '#333333',
                size: 12,
                face: 'Arial'
            },
            borderWidth: 2,
            shadow: true
        })));
    
        // Configuración de relaciones
        const edges = new vis.DataSet(graphData.relationships.map(rel => ({
            from: rel.source,
            to: rel.target,
            label: `${(rel.score).toFixed(1)}%`,
            color: {
                color: '#a5abb6',
                highlight: '#858c99',
                hover: '#858c99'
            },
            width: 1,
            arrows: {
                to: false,
                from: false
            },
            font: {
                align: 'horizontal',
                size: 10,
                color: '#666666'
            },
            smooth: {
                type: 'continuous',
                roundness: 0.5
            }
        })));
    
        // Opciones de visualización
        const options = {
            nodes: {
                scaling: {
                    min: 20,
                    max: 30
                }
            },
            edges: {
                smooth: {
                    type: 'continuous',
                    forceDirection: 'none'
                }
            },
            physics: {
                solver: 'forceAtlas2Based',
                forceAtlas2Based: {
                    gravitationalConstant: -50,
                    centralGravity: 0.01,
                    springLength: 100,
                    springConstant: 0.08,
                    damping: 0.4,
                    avoidOverlap: 1
                },
                stabilization: {
                    enabled: true,
                    iterations: 1000,
                    updateInterval: 25
                }
            },
            interaction: {
                hover: true,
                zoomView: true,
                dragView: true,
                navigationButtons: false,
                keyboard: {
                    enabled: false
                }
            },
            manipulation: {
                enabled: false
            },
            layout: {
                improvedLayout: true,
                hierarchical: false
            }
        };
    
        try {
            if (this.network) {
                this.network.destroy();
            }
    
            this.network = new vis.Network(
                this.elements.container,
                { nodes, edges },
                options
            );
    
            this.network.on("stabilizationIterationsDone", function() {
                console.log('Estabilización completada');
            });
            
        } catch (error) {
            console.error('Error renderizando grafo:', error);
        }
    }
    
    updateStats(stats) {
        if (!this.elements.statsContainer) return;

        this.elements.statsContainer.innerHTML = `
            <div class="graph-stats">
                <p>Total de relaciones: ${stats.totalRelations}</p>
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.graphViewer = new GraphViewer();
});