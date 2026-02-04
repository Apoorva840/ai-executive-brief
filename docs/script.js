document.addEventListener("DOMContentLoaded", () => {
    const historySelect = document.getElementById("history-select");

    // --- STEP 1: INITIAL FETCH ---
    // Always load the absolute latest brief on startup
    loadBriefData("./data/daily_brief.json");

    // --- STEP 2: FETCH THE MANIFEST ---
    fetch("./data/manifest.json")
        .then(response => response.ok ? response.json() : [])
        .then(dates => {
            // Sort dates to ensure newest is first
            const sortedDates = dates.sort().reverse();

            // STEP 2b: HIDE TODAY FROM DROPDOWN
            // Since 'Today' is already loaded via daily_brief.json, 
            // we skip the first entry in the manifest to show only actual history.
            const pastDates = sortedDates.slice(1);

            if (pastDates.length > 0) {
                pastDates.forEach(date => {
                    const option = document.createElement("option");
                    option.value = `./data/archive/brief_${date}.json`;
                    
                    // Format date for a better look (e.g., 2026-02-02)
                    option.textContent = date; 
                    historySelect.appendChild(option);
                });
            } else {
                const infoOpt = document.createElement("option");
                infoOpt.textContent = "Archive starts tomorrow";
                infoOpt.disabled = true;
                historySelect.appendChild(infoOpt);
            }
        })
        .catch(err => console.error("Manifest not found yet. It will be created on the next run."));

    // --- STEP 3: HANDLE DROPDOWN CHANGES ---
    historySelect.addEventListener("change", (event) => {
        const selectedPath = event.target.value === "latest" 
            ? "./data/daily_brief.json" 
            : event.target.value;
        
        loadBriefData(selectedPath);
    });
});

/**
 * CORE FETCH FUNCTION
 */
function loadBriefData(path) {
    console.log("Fetching data from:", path);

    fetch(path)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load ${path}`);
            }
            return response.json();
        })
        .then(data => {
            const container = document.getElementById("stories");
            const meta = document.getElementById("meta");

            // Update the "Updated on" text
            meta.textContent = `Updated on ${data.date}`;

            // Clear current stories
            container.innerHTML = "";

            // Build the cards
            data.top_stories.forEach(story => {
                const card = document.createElement("div");
                card.className = "story";

                let html = `
                    <h2>${story.rank}. ${story.title}</h2>
                    <h3>Summary</h3>
                    <p>${story.summary}</p>
                `;

                if (story.technical_takeaway && story.technical_takeaway !== "null") {
                    html += `<h3>Technical takeaway</h3><p>${story.technical_takeaway}</p>`;
                }

                if (story.primary_risk && story.primary_risk !== "null") {
                    html += `<h3>Primary risk</h3><p>${story.primary_risk}</p>`;
                }

                if (story.primary_opportunity && story.primary_opportunity !== "null") {
                    html += `<h3>Primary opportunity</h3><p>${story.primary_opportunity}</p>`;
                }

                html += `
                    <p class="source">
                        Source: <a href="${story.url}" target="_blank">${story.source}</a>
                    </p>
                `;

                card.innerHTML = html;
                container.appendChild(card);
            });
        })
        .catch(error => {
            document.getElementById("stories").innerHTML =
                `<p>Error: Could not load the brief. (${error.message})</p>`;
            console.error(error);
        });
}