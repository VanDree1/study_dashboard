document.addEventListener("DOMContentLoaded", () => {
  const panel = document.getElementById("ai-panel");
  const button = document.getElementById("ai-button");
  const closeBtn = document.getElementById("ai-close");
  const sendBtn = document.getElementById("ai-send");
  const input = document.getElementById("ai-input");
  const messages = document.getElementById("ai-messages");

  function togglePanel(show) {
    if (show) {
      panel.classList.add("visible");
      panel.classList.remove("hidden");
      input.focus();
    } else {
      panel.classList.remove("visible");
      setTimeout(() => panel.classList.add("hidden"), 250);
    }
  }

  function appendMessage(role, text) {
    const bubble = document.createElement("div");
    bubble.className = `ai-bubble ${role}`;
    bubble.textContent = text;
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
  }

  async function sendMessage() {
    const value = input.value.trim();
    if (!value) return;
    appendMessage("user", value);
    input.value = "";

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: value })
      });
      const data = await response.json();
      appendMessage("assistant", data.reply || "(No reply)");
    } catch (err) {
      appendMessage("assistant", "Sorry, I ran into a problem.");
    }
  }

  button?.addEventListener("click", () => togglePanel(true));
  closeBtn?.addEventListener("click", () => togglePanel(false));
  sendBtn?.addEventListener("click", sendMessage);
  input?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      sendMessage();
    }
  });
});
