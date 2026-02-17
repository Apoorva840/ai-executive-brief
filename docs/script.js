document.addEventListener("DOMContentLoaded", () => {
    const historySelect = document.getElementById("history-select");

    loadBriefData("./data/daily_brief.json");
    loadJargonData("./data/jargon_buster.json");

    fetch("./data/manifest.json")
        .then(response => response.ok ? response.json() : [])
        .then(dates => {
            const sortedDates = dates.sort().reverse();
            const pastDates = sortedDates.slice(1);
            if (pastDates.length > 0) {
                pastDates.forEach(date => {
                    const option = document.createElement("option");
                    option.value = `./data/archive/brief_${date}.json`;
                    option.textContent = date; 
                    historySelect.appendChild(option);
                });
            }
        });

    historySelect.addEventListener("change", (event) => {
        const selectedPath = event.target.value === "latest" ? "./data/daily_brief.json" : event.target.value;
        loadBriefData(selectedPath);
    });
});

function loadJargonData(path) {
    fetch(path)
        .then(response => response.ok ? response.json() : null)
        .then(data => {
            const section = document.getElementById("jargon-decoder");
            const container = document.getElementById("jargon-container");

            if (data && data.is_weekly_active === true) {
                section.style.display = "block";
                
                // Add the "Last Updated" timestamp to the section title
                const titleElement = section.querySelector(".section-title");
                titleElement.innerHTML = `🎓 Jargon Decoder <span class="update-tag">Updated: ${data.last_updated}</span>`;

                container.innerHTML = "";
                data.terms.forEach(item => {
                    const box = document.createElement("div");
                    box.className = "jargon-card";
                    box.innerHTML = `
                        <h4>${item.term}</h4>
                        <p><strong>Definition:</strong> ${item.definition}</p>
                        <p><em>Analogy: ${item.analogy}</em></p>
                    `;
                    container.appendChild(box);
                });
            } else {
                section.style.display = "none";
            }
        });
}

function loadBriefData(path) {
    fetch(path)
        .then(response => response.ok ? response.json() : null)
        .then(data => {
            if(!data) return;
            const container = document.getElementById("stories");
            const meta = document.getElementById("meta");
            meta.textContent = `Updated on ${data.date}`;
            container.innerHTML = "";
            data.top_stories.forEach(story => {
                const card = document.createElement("div");
                card.className = "story";
                card.innerHTML = `
                    <h2>${story.rank}. ${story.title}</h2>
                    <h3>Summary</h3>
                    <p>${story.summary}</p>
                    <p class="source">Source: <a href="${story.url}" target="_blank">${story.source}</a></p>
                `;
                container.appendChild(card);
            });
        });
}