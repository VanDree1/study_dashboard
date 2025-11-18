// ----- Helpers för texten "Direkt" / "X byten" -----
const formatChangesText = (numChanges) => {
  const numeric = Number(numChanges);
  if (!Number.isFinite(numeric) || numeric === 0) {
    return "Direkt";
  }
  return `${numeric} byten`;
};

// ----- Grundreferenser i DOMen -----
const form = document.getElementById("tripForm");
const statusBox = document.getElementById("status");
const resultSection = document.getElementById("result");
const ROUTE_LABEL = "Skärmarbrink T-bana → Ekonomikum, Uppsala";
const departureEl = document.getElementById("travel-departure");
const arrivalEl = document.getElementById("travel-arrival");
const durationEl = document.getElementById("travel-duration");

// ----- Små helpers -----
const stripSeconds = (value) => {
  if (!value) return "-";
  const match = String(value).match(/^\d{2}:\d{2}/);
  return match ? match[0] : value;
};

const cleanStopName = (name) => {
  if (!name) return "-";
  return String(name).replace(/\s*\([^)]*\)\s*$/, "").trim();
};

const getModeIcon = (mode = "") => {
  const label = String(mode).toLowerCase();
  if (label.includes("metro") || label.includes("t-bana") || label.includes("subway")) return "🚇";
  if (label.includes("train") || label.includes("tåg") || label.includes("jny")) return "🚆";
  if (label.includes("bus") || label.includes("buss")) return "🚌";
  if (label.includes("tram") || label.includes("spårvagn")) return "🚊";
  if (label.includes("ship") || label.includes("ferry")) return "⛴️";
  if (label.includes("walk") || label.includes("gång")) return "🚶";
  return "•";
};

// ----- Origin / destination -----
const ORIGIN_ID = "740021704"; // Skärmarbrink T-bana
const DEST_ID = "740007480";   // Ekonomikum, Uppsala

// ----- Datum / tid helpers -----
const getTodayDate = () => new Date().toISOString().slice(0, 10);

const getCurrentTime = () => {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
};

const applyInitialDateTime = () => {
  document
    .querySelectorAll('input[name="date"], input[name="travel-date"]')
    .forEach((input) => {
      if (!input.value) input.value = getTodayDate();
    });

  document
    .querySelectorAll('input[name="time"], input[name="travel-time"]')
    .forEach((input) => {
      if (!input.value) input.value = getCurrentTime();
    });
};

const attachNowButtons = () => {
  const buttons = document.querySelectorAll(".time-now-btn");

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const value = getCurrentTime();
      document.querySelectorAll('input[type="time"]').forEach((input) => {
        input.value = value;
      });
    });
  });
};

// Körs EN gång när sidan laddas
document.addEventListener("DOMContentLoaded", () => {
  applyInitialDateTime();
  attachNowButtons();
});

// ----- Skeleton loader -----
const showSkeleton = () => {
  if (!resultSection) return;
  const skeletonCards = Array.from({ length: 3 })
    .map(
      () => `
      <article class="skeleton-card">
        <div class="skeleton-line wide"></div>
        <div class="skeleton-line medium"></div>
        <div class="skeleton-line short"></div>
      </article>`
    )
    .join("");
  resultSection.classList.remove("hidden");
  resultSection.innerHTML = `<div class="skeleton-wrapper">${skeletonCards}</div>`;
};

const hideSkeleton = () => {
  if (!resultSection) return;
  const wrapper = resultSection.querySelector(".skeleton-wrapper");
  if (wrapper) wrapper.remove();
};

// ----- Status / reset / fel -----
const showStatus = (message, isError = false) => {
  if (!statusBox) return;
  statusBox.textContent = message;
  statusBox.classList.toggle("error", isError);
};

const resetResult = () => {
  if (!resultSection) return;
  resultSection.classList.add("hidden");
  resultSection.innerHTML = "";
  if (departureEl) departureEl.textContent = "-";
  if (arrivalEl) arrivalEl.textContent = "-";
  if (durationEl) durationEl.textContent = "-";
};

const handleTravelError = (payload) => {
  console.error("Travel API error:", payload);
  let message = "Ett fel uppstod vid hämtning av resa.";
  if (payload && typeof payload === "object") {
    if (payload.error) message = payload.error;
    if (payload.details) message += ` (${payload.details})`;
  }
  hideSkeleton();
  resetResult();
  showStatus(message, true);
};

// ----- Submit-handler -----
if (form) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const date = formData.get("date") || formData.get("travel-date");
    const time = formData.get("time") || formData.get("travel-time");

    if (!date || !time) {
      showStatus("Fyll i både datum och tid.", true);
      return;
    }

    resetResult();
    showStatus("Söker resa...", false);
    showSkeleton();

    const params = new URLSearchParams({
      originId: ORIGIN_ID,
      destId: DEST_ID,
      date,
      time,
    });

    try {
      const response = await fetch(`/api/travel?${params.toString()}`);
      const payload = await response.json();
      console.log("Travel payload:", payload);

      const trips = Array.isArray(payload.trips) ? payload.trips : [];
      if (!trips.length) {
        handleTravelError({ error: "Ingen resa hittades." });
        return;
      }

      const firstTrip = trips[0];
      if (departureEl) departureEl.textContent = firstTrip.departureTime || "-";
      if (arrivalEl) arrivalEl.textContent = firstTrip.arrivalTime || "-";
      if (durationEl) durationEl.textContent = firstTrip.totalTravelTime || "-";

      if (!response.ok) {
        handleTravelError(payload);
        return;
      }

      hideSkeleton();

      resultSection.innerHTML = "";
      const list = document.createElement("div");
      list.className = "trip-list";

      trips.slice(0, 3).forEach((trip) => {
        const card = document.createElement("article");
        card.className = "trip-card";

        const header = document.createElement("div");
        header.className = "trip-header";

        const title = document.createElement("div");
        title.className = "trip-title";
        title.textContent = `${stripSeconds(trip.departureTime)} → ${stripSeconds(
          trip.arrivalTime
        )}`;

        const changesCount = Number.isFinite(Number(trip.numberOfChanges))
          ? Number(trip.numberOfChanges)
          : 0;

        const meta = document.createElement("div");
        meta.className = "trip-meta";
        meta.textContent = `${trip.totalTravelTime || "-"} • ${formatChangesText(
          changesCount
        )}`;

        header.appendChild(title);
        header.appendChild(meta);

        const summary = document.createElement("div");
        summary.className = "trip-summary";
        const origin = cleanStopName(
          trip.originName || ROUTE_LABEL.split(" → ")[0]
        );
        const dest = cleanStopName(
          trip.destinationName || ROUTE_LABEL.split(" → ")[1]
        );
        summary.textContent = `${origin} → ${dest}`;

        const toggleButton = document.createElement("button");
        toggleButton.type = "button";
        toggleButton.className = "trip-toggle";
        toggleButton.textContent = "Visa detaljer";

        const details = document.createElement("div");
        details.classList.add("trip-details", "hidden");

        (trip.legs || []).forEach((leg) => {
          const row = document.createElement("div");
          row.className = "leg-row";

          const timeEl = document.createElement("div");
          timeEl.className = "leg-time";
          timeEl.textContent = `${stripSeconds(
            leg.departureTime
          )} → ${stripSeconds(leg.arrivalTime)}`;

          const info = document.createElement("div");
          info.className = "leg-info";
          info.textContent = `${cleanStopName(leg.origin)} → ${cleanStopName(
            leg.destination
          )}`;

          const mode = document.createElement("div");
          mode.className = "leg-mode";
          const icon = getModeIcon(leg.mode || "");
          mode.textContent = `${icon} ${leg.mode || ""}`.trim();

          row.appendChild(timeEl);
          row.appendChild(info);
          row.appendChild(mode);
          details.appendChild(row);
        });

        toggleButton.addEventListener("click", () => {
          const isHidden = details.classList.contains("hidden");
          details.classList.toggle("hidden", !isHidden);
          toggleButton.textContent = isHidden ? "Dölj detaljer" : "Visa detaljer";
        });

        card.appendChild(header);
        card.appendChild(summary);
        card.appendChild(toggleButton);
        card.appendChild(details);

        list.appendChild(card);
      });

      resultSection.appendChild(list);
      resultSection.classList.remove("hidden");
      showStatus("Resa hittad ✨");
    } catch (error) {
      console.error(error);
      handleTravelError({ error: error.message || "Kunde inte hämta resa." });
    }
  });
}