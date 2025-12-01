document.addEventListener('DOMContentLoaded', function () {
    let cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'text-wrap': 'wrap',
                    'font-size': '10px',
                    'width': 'label',
                    'height': 'label',
                    'padding': '10px',
                    'shape': 'round-rectangle'
                }
            },
            {
                selector: 'node[type="policy"]',
                style: {
                    'background-color': '#3b82f6',
                    'color': '#fff'
                }
            },
            {
                selector: 'node[type="condition"]',
                style: {
                    'background-color': '#10b981',
                    'color': '#fff'
                }
            },
            {
                selector: 'node[type="control"]',
                style: {
                    'background-color': '#ef4444',
                    'color': '#fff'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#ccc',
                    'target-arrow-color': '#ccc',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'label': 'data(label)',
                    'font-size': '8px',
                    'text-rotation': 'autorotate'
                }
            },
            {
                selector: '.highlighted',
                style: {
                    'border-width': 4,
                    'border-color': '#10b981', // Green border
                    'opacity': 1
                }
            },
            {
                selector: '.dimmed',
                style: {
                    'opacity': 0.2
                }
            }
        ]
    });

    // Fetch Graph Data
    fetch('/api/graph-data')
        .then(response => {
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            return response.json();
        })
        .then(data => {
            cy.add(data.nodes);
            cy.add(data.edges);

            cy.layout({
                name: 'dagre',
                rankDir: 'LR',
                nodeSep: 50,
                rankSep: 100
            }).run();
        });

    // Search Logic
    const searchInput = document.getElementById('user-search');
    const searchResults = document.getElementById('search-results');
    const selectedUserDiv = document.getElementById('selected-user');
    const userNameSpan = document.getElementById('user-name');
    const clearSelectionBtn = document.getElementById('clear-selection');
    let debounceTimer;

    searchInput.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        const query = this.value;
        if (query.length < 3) {
            searchResults.classList.add('hidden');
            return;
        }

        debounceTimer = setTimeout(() => {
            fetch(`/api/search?q=${query}`)
                .then(res => res.json())
                .then(users => {
                    searchResults.innerHTML = '';
                    if (users.length > 0) {
                        searchResults.classList.remove('hidden');
                        users.forEach(user => {
                            const div = document.createElement('div');
                            div.className = 'p-2 hover:bg-gray-100 cursor-pointer';
                            div.textContent = `${user.displayName} (${user.userPrincipalName})`;
                            div.onclick = () => selectUser(user);
                            searchResults.appendChild(div);
                        });
                    } else {
                        searchResults.classList.add('hidden');
                    }
                });
        }, 300);
    });

    function selectUser(user) {
        searchInput.value = '';
        searchResults.classList.add('hidden');
        selectedUserDiv.classList.remove('hidden');
        userNameSpan.textContent = user.displayName;

        // Fetch Evaluation
        fetch(`/api/evaluate?user_id=${user.id}`)
            .then(res => res.json())
            .then(data => {
                const applicableIds = data.applicable_policy_ids;

                cy.batch(() => {
                    cy.elements().removeClass('highlighted dimmed');

                    // Dim everything first
                    cy.elements().addClass('dimmed');

                    // Highlight applicable policies and their neighbors
                    applicableIds.forEach(policyId => {
                        const policyNode = cy.getElementById(`policy_${policyId}`);
                        if (policyNode.nonempty()) {
                            policyNode.removeClass('dimmed').addClass('highlighted');

                            // Highlight connected edges and nodes (conditions and controls)
                            policyNode.connectedEdges().removeClass('dimmed');
                            policyNode.connectedEdges().connectedNodes().removeClass('dimmed');
                        }
                    });
                });
            });
    }

    clearSelectionBtn.addEventListener('click', function () {
        selectedUserDiv.classList.add('hidden');
        cy.elements().removeClass('highlighted dimmed');
    });

    // Close search results on click outside
    document.addEventListener('click', function (e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.add('hidden');
        }
    });
});
