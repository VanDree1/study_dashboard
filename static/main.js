const formatChangesText = (numChanges) => {
  const numeric = Number(numChanges);
  if (!Number.isFinite(numeric) || numeric === 0) {
    return "Direkt";
  }
  return `${numeric} byten`;
};
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

const getModeIcon = (mode = "") => {
  const label = mode.toLowerCase();
  if (label.includes("metro") || label.includes("t-bana") || label.includes("subway")) return "🚇";
  if (label.includes("train") || label.includes("tåg") || label.includes("jny")) return "🚆";
  if (label.includes("bus") || label.includes("buss")) return "🚌";
  if (label.includes("tram") || label.includes("spårvagn")) return "🚊";
  if (label.includes("ship") || label.includes("ferry")) return "⛴️";
  if (label.includes("walk") || label.includes("gång")) return "🚶";
  return "•";
};

const ORIGIN_ID = "740021704"; // Skärmarbrink T-bana
const DEST_ID = "740007480"; // Ekonomikum, Uppsala

window.addEventListener("DOMContentLoaded", () => {
  const now = new Date();
  const dateInput =
    document.querySelector('input[name="date"]') ||
    document.querySelector('input[name="travel-date"]');
  if (dateInput && !dateInput.value) {
    dateInput.value = now.toISOString().slice(0, 10);
  }
  const timeInput =
    document.getElementById("travel-time-input") ||
    document.querySelector('input[name="time"]') ||
    document.querySelector('input[name="travel-time"]');
  if (timeInput && !timeInput.value) {
    timeInput.value = now.toTimeString().slice(0, 5);
  }
  const nowButton = document.getElementById("travel-now-button");
  if (timeInput && nowButton) {
    nowButton.addEventListener("click", () => {
      const t = new Date();
      timeInput.value = t.toTimeString().slice(0, 5);
      timeInput.focus();
    });
  }
});

const getTodayDate = () => new Date().toISOString().slice(0, 10);

const getCurrentTime = () => {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
};

const applyInitialDateTime = () => {
  document.querySelectorAll('input[name="date"], input[name="travel-date"]').forEach((input) => {
    if (!input.value) input.value = getTodayDate();
  });
  document.querySelectorAll('input[name="time"], input[name="travel-time"]').forEach((input) => {
    if (!input.value) input.value = getCurrentTime();
  });
};

const attachNowButtons = () => {
  document.querySelectorAll("#time-now-btn, #travel-time-now").forEach((button) => {
    button.addEventListener("click", () => {
      const target = button.closest("label")?.querySelector('input[type="time"]') || document.querySelector('input[name="time"]');
      if (target) {
        target.value = getCurrentTime();
        target.focus();
      }
    });
  });
};

document.addEventListener("DOMContentLoaded", () => {
  applyInitialDateTime();
  attachNowButtons();
});

const getTodayDate = () => {
  const now = new Date();
  return now.toISOString().slice(0, 10);
};

const getCurrentTime = () => {
  const now = new Date();
  return `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
};

const setInitialDateTime = () => {
  const dateField = document.querySelector('input[name="date"]');
  const timeField = document.querySelector('input[name="time"]');
  if (dateField && !dateField.value) {
    dateField.value = getTodayDate();
  }
  if (timeField && !timeField.value) {
    timeField.value = getCurrentTime();
  }
};

const attachNowButtons = () => {
  const timeField = document.querySelector('input[name="time"]');
  const buttons = document.querySelectorAll("#time-now-btn, #travel-time-now");
  buttons.forEach((btn) =>
    btn.addEventListener("click", () => {
      if (timeField) {
        timeField.value = getCurrentTime();
      }
    })
  );
};

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
  if (wrapper) {
    wrapper.remove();
  }
};

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
  hideSkeleton();
  resetResult();
  showStatus(message, true);
};

document.addEventListener("DOMContentLoaded", () => {
  setInitialDateTime();
  attachNowButtons();
});

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
  showSkeleton();

  const params = new URLSearchParams({
    originId: ORIGIN_ID,
    destId: DEST_ID,
    date,
    time,
  });

  try {const response = await fetch(`/api/travel?${params.toString()}`);
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

    hideSkeleton();

    const trips = Array.isArray(payload.trips) ? payload.trips : [];
    if (!trips.length) {
      handleTravelError({ error: "Ingen resa hittades." });
      return;
    }

    resultSection.innerHTML = "";
    const list = document.createElement("div");
    list.className = "trip-list";

    (trips || []).slice(0, 3).forEach((trip) => {
      const card = document.createElement("article");
      card.className = "trip-card";

      // header: tid + restid + byten
      const header = document.createElement("div");
      header.className = "trip-header";

      const title = document.createElement("div");
      title.className = "trip-title";
      title.textContent = `${stripSeconds(trip.departureTime)} → ${stripSeconds(
        trip.arrivalTime
      )}`;

      // hämta antal byten från backend
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

      // rad under: från–till
      const summary = document.createElement("div");
      summary.className = "trip-summary";
      const origin = cleanStopName(
        trip.originName || ROUTE_LABEL.split(" → ")[0]
      );
      const dest = cleanStopName(
        trip.destinationName || ROUTE_LABEL.split(" → ")[1]
      );
      summary.textContent = `${origin} → ${dest}`;

      // knapp + detaljer (delresor)
      const toggleButton = document.createElement("button");
      toggleButton.type = "button";
      toggleButton.className = "trip-toggle";
      toggleButton.textContent = "Visa detaljer";

      const details = document.createElement("div");
      details.classList.add("trip-details", "hidden");

      (trip.legs || []).forEach((leg) => {
        const row = document.createElement("div");
        row.className = "leg-row";

        const time = document.createElement("div");
        time.className = "leg-time";
        time.textContent = `${stripSeconds(
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

        row.appendChild(time);
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
