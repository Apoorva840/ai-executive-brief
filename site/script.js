fetch("./data/daily_brief.json")
  .then(response => {
    if (!response.ok) {
      throw new Error("Failed to load daily_brief.json");
    }
    return response.json();
  })
  .then(data => {
    const container = document.getElementById("stories");
    const meta = document.getElementById("meta");

    meta.textContent = `Updated on ${data.date}`;

    container.innerHTML = "";

    data.top_stories.forEach(story => {
      const card = document.createElement("div");
      card.className = "story";

      let html = `
        <h2>${story.rank}. ${story.title}</h2>

        <h3>Summary</h3>
        <p>${story.summary}</p>
      `;

      if (story.technical_takeaway && story.technical_takeaway !== "null") {
        html += `
          <h3>Technical takeaway</h3>
          <p>${story.technical_takeaway}</p>
        `;
      }

      if (story.primary_risk && story.primary_risk !== "null") {
        html += `
          <h3>Primary risk</h3>
          <p>${story.primary_risk}</p>
        `;
      }

      if (story.primary_opportunity && story.primary_opportunity !== "null") {
        html += `
          <h3>Primary opportunity</h3>
          <p>${story.primary_opportunity}</p>
        `;
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
      "<p>Failed to load daily brief.</p>";
    console.error(error);
  });
