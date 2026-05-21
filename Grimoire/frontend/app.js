document.getElementById('search-btn').addEventListener('click', () => {
    const username = document.getElementById('username-input').value.trim();
    if (!username) return;
    fetchRecommendations(username);
});

document.getElementById('username-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const username = e.target.value.trim();
        if (username) fetchRecommendations(username);
    }
});

async function fetchRecommendations(username) {
    document.getElementById('results').classList.add('hidden');
    document.getElementById('error').classList.add('hidden');
    document.getElementById('loading').classList.remove('hidden');

    try {
        const res = await fetch(`http://127.0.0.1:8000/recommend/${username}`);
        const data = await res.json();

        if (res.status === 202) {
            document.getElementById('loading').classList.add('hidden');
            document.getElementById('error').classList.remove('hidden');
            document.getElementById('error-msg').innerText = "Processing your shelf in the background. Please click discover again in a few seconds.";
            return;
        }

        if (!res.ok) {
            document.getElementById('loading').classList.add('hidden');
            document.getElementById('error').classList.remove('hidden');
            document.getElementById('error-msg').innerText = data.message || "Profile not found.";
            return;
        }

        renderResults(username, data);

    } catch (err) {
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('error').classList.remove('hidden');
        document.getElementById('error-msg').innerText = "Could not connect to the API. Make sure uvicorn is running!";
    }
}

function renderResults(username, data) {
    document.getElementById('loading').classList.add('hidden');
    document.getElementById('results').classList.remove('hidden');

    document.getElementById('display-name').innerText = username;

    const usersList = document.getElementById('similar-users-list');
    usersList.innerHTML = '';
    if (data.top_similar_users && data.top_similar_users.length > 0) {
        data.top_similar_users.forEach(u => {
            const li = document.createElement('li');
            li.innerHTML = `<a href="https://hardcover.app/@${u.username}" target="_blank" class="user-link">${u.username}</a> <span class="sim">${u.similarity.toFixed(2)}</span>`;
            usersList.appendChild(li);
        });
    } else {
        usersList.innerHTML = '<li>No similar users found yet.</li>';
    }

    const grid = document.getElementById('books-grid');
    grid.innerHTML = '';

    if (data.books && data.books.length > 0) {
        data.books.forEach(b => {
            const card = document.createElement('div');
            card.className = 'book-card';
            const coverStyle = b.cover_url ? `url('${b.cover_url}')` : "url('placeholder_cover.png')";
            const truncatedDesc = b.description && b.description.length > 250 ? b.description.substring(0, 250) + "..." : (b.description || "No description available.");
            const fullDesc = b.description || "No description available.";

            card.innerHTML = `
                <div class="cover" style="background-image: ${coverStyle}"></div>
                <div class="title-container">
                    <a href="https://hardcover.app/books/${b.slug}" target="_blank" class="book-title">${b.title}</a>
                    <div class="tooltip">${fullDesc}</div>
                </div>
                <div class="book-author">${b.authors}</div>
                <div class="book-meta">${b.rating.toFixed(1)} ★ • ${b.pages || '?'} pages</div>
            `;
            grid.appendChild(card);
        });
    } else {
        grid.innerHTML = '<p>No book recommendations found.</p>';
    }
}
