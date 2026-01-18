// Repertoire Web UI JavaScript

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('stat-recordings').textContent = stats.total_recordings;
        document.getElementById('stat-library').textContent = stats.in_library;
        document.getElementById('stat-composers').textContent = stats.unique_composers;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function searchRecordings() {
    const composer = document.getElementById('composer-filter').value;
    const work = document.getElementById('work-filter').value;
    const label = document.getElementById('label-filter').value;

    try {
        const params = new URLSearchParams();
        if (composer) params.append('composer', composer);
        if (work) params.append('work', work);
        if (label) params.append('label', label);

        const response = await fetch(`/api/recordings?${params}`);
        const recordings = await response.json();

        displayRecordings(recordings);
    } catch (error) {
        console.error('Error searching recordings:', error);
    }
}

function displayRecordings(recordings) {
    const container = document.getElementById('recordings-list');
    
    if (recordings.length === 0) {
        container.innerHTML = '<p class="empty-state">No recordings found.</p>';
        return;
    }

    container.innerHTML = recordings.map(recording => `
        <div class="recording-item">
            <h3>${recording.title}</h3>
            <div class="recording-info">
                ${recording.catalog_number ? `
                    <div>
                        <span class="recording-label">Catalog:</span> ${recording.catalog_number}
                    </div>
                ` : ''}
                ${recording.release_year ? `
                    <div>
                        <span class="recording-label">Year:</span> ${recording.release_year}
                    </div>
                ` : ''}
                ${recording.recording_type ? `
                    <div>
                        <span class="recording-label">Type:</span> ${recording.recording_type}
                    </div>
                ` : ''}
                <div>
                    <span class="recording-label">Library:</span> ${recording.in_library ? '✓' : '✗'}
                </div>
            </div>
        </div>
    `).join('');
}

// Event listeners
document.getElementById('search-btn').addEventListener('click', searchRecordings);
document.querySelectorAll('.filter-input').forEach(input => {
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchRecordings();
    });
});

// Load initial data
document.addEventListener('DOMContentLoaded', loadStats);
