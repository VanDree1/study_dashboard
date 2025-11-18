const form = document.getElementById("tripForm");
const statusBox = document.getElementById("status");
const resultSection = document.getElementById("result");
const ROUTE_LABEL = "Skärmarbrink T-bana → Ekonomikum, Uppsala";
const departureEl = document.getElementById("travel-departure");
const arrivalEl = document.getElementById("travel-arrival");
const durationEl = document.getElementById("travel-duration");
const stripSeconds = (value) => {
  if (!value) return "-";
  const match = String(value).match(/^\d{2}:\d{2}/);
  return match ? match[0] : value;
};

const cleanStopName = (name) => {
  if (!name) return "-";
  return String(name).replace(/\s*\([^)]*\)\s*$/, "").trim();
};

const formatChangesText = (numChanges) => {
  const numeric = Number(numChanges);
  if (!Number.isFinite(numeric) || numeric === 0) {
    return "Direkt";
  }
  return `${numeric} byten`;
};

const getModeIcon = (leg) => {
  const label = (leg.modeLabel || leg.mode || "").toLowerCase();
  if (label.includes("tunnelbana") || label.includes("subway") || label.includes("t-bana")) {
    return "🚇";
  }
  if (label.includes("pendeltåg") || label.includes("tåg") || label.includes("train")) {
    return "🚆";
  }
  if (label.includes("buss") || label.includes("bus")) {
    return "🚌";
  }
  if (label.includes("gång") || label.includes("walk")) {
    return "🚶";
  }
  return "🚈";
};

const ORIGIN_ID = "740021704"; // Skärmarbrink T-bana
const DEST_ID = "740007480"; // Ekonomikum, Uppsala

const showStatus = (message, isError = false) => {
  statusBox.textContent = message;
  statusBox.classList.toggle("error", isError);
};

const resetResult = () => {
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
    if (payload.error) {
      message = payload.error;
    }
    if (payload.details) {
      message += ` (${payload.details})`;
    }
  }
  resetResult();
  showStatus(message, true);
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const date = formData.get("date");
  const time = formData.get("time");

  if (!date || !time) {
    showStatus("Fyll i både datum och tid.", true);
    return;
  }

  resetResult();
  showStatus("Söker resa...", false);

  const params = new URLSearchParams({
    originId: ORIGIN_ID,
    destId: DEST_ID,
    date,
    time,
  });

  try {
    const response = await fetch(`/api/trip?${params.toString()}`);
    const payload = await response.json();
    console.log("Travel payload:", payload);

    {
      const trips = payload.trips || [];
      if (!trips.length) {
        handleTravelError({ error: "Ingen resa hittades." });
        return;
      }

      const firstTrip = trips[0];
      if (departureEl) {
        departureEl.textContent = firstTrip.departureTime || "-";
      }
      if (arrivalEl) {
        arrivalEl.textContent = firstTrip.arrivalTime || "-";
      }
      if (durationEl) {
        durationEl.textContent = firstTrip.totalTravelTime || "-";
      }
    }

    if (!response.ok) {
      handleTravelError(payload);
      return;
    }

    const trips = Array.isArray(payload.trips) ? payload.trips : [];
    if (!trips.length) {
      handleTravelError({ error: "Ingen resa hittades." });
      return;
    }

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
      title.textContent = `${stripSeconds(trip.departureTime)} → ${stripSeconds(trip.arrivalTime)}`;
      const changesCount =
        typeof trip.numberOfChanges === "number"
          ? trip.numberOfChanges
          : Number.isFinite(trip.changes)
          ? trip.changes
          : Number.isFinite(trip.numChanges)
          ? trip.numChanges
          : 0;
      const meta = document.createElement("div");
      meta.className = "trip-meta";
      meta.textContent = `${trip.totalTravelTime || "-"} • ${formatChangesText(changesCount)}`;
      header.appendChild(title);
      header.appendChild(meta);

      const summary = document.createElement("div");
      summary.className = "trip-summary";
      const origin = cleanStopName(trip.originName || ROUTE_LABEL.split(" → ")[0]);
      const dest = cleanStopName(trip.destinationName || ROUTE_LABEL.split(" → ")[1]);
      summary.textContent = `${origin} → ${dest}`;

      const toggleButton = document.createElement("button");
      toggleButton.type = "button";
      toggleButton.className = "trip-toggle";
      toggleButton.textContent = "Visa detaljer";

      const details = document.createElement("div");
      details.classList.add("trip-details", "hidden");

      (trip.legs || []).forEach((leg) => {
        const legRow = document.createElement("div");
        legRow.className = "leg-row";

        const legTime = document.createElement("div");
        legTime.className = "leg-time";
        legTime.textContent = `${stripSeconds(leg.departureTime)} → ${stripSeconds(leg.arrivalTime)}`;

        const legInfo = document.createElement("div");
        legInfo.className = "leg-info";
        legInfo.textContent = `${cleanStopName(leg.origin)} → ${cleanStopName(leg.destination)}`;

        const legMode = document.createElement("div");
        legMode.className = "leg-mode";
        legMode.textContent = leg.mode || "";

        legRow.appendChild(legTime);
        legRow.appendChild(legInfo);
        legRow.appendChild(legMode);
        details.appendChild(legRow);
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
    showStatus("Resan hittades!");
  } catch (error) {
    console.error(error);
    handleTravelError({ error: error.message || "Kunde inte hämta resa." });
  }
});
