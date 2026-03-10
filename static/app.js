const grid = document.getElementById("grid");
const checkboxMap = new Map();

async function loadCheckboxes() {
  const response = await fetch("/api/checkboxes");
  const data = await response.json();

  grid.innerHTML = "";

  data.forEach((item) => {
    const wrapper = document.createElement("label");
    wrapper.className = "box";

    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = item.checked;
    input.dataset.id = item.id;

    input.addEventListener("change", async () => {
      const id = Number(input.dataset.id);
      const checked = input.checked;

      try {
        const response = await fetch(`/api/checkboxes/${id}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ checked }),
        });

        const result = await response.json();

        if (!response.ok || result.error) {
          input.checked = !checked;
          console.error(result.error || "Update failed");
        }
      } catch (error) {
        input.checked = !checked;
        console.error("Network error:", error);
      }
    });

    const text = document.createElement("span");
    text.textContent = `Box ${item.id}`;

    wrapper.appendChild(input);
    wrapper.appendChild(text);
    grid.appendChild(wrapper);

    checkboxMap.set(item.id, input);
  });
}

function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);

  socket.onopen = () => {
    console.log("WebSocket connected");
    socket.send("connected");
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const checkbox = checkboxMap.get(data.id);

    if (checkbox) {
      checkbox.checked = data.checked;
    }
  };

  socket.onclose = () => {
    console.log("WebSocket disconnected, retrying in 1 second...");
    setTimeout(connectWebSocket, 1000);
  };

  socket.onerror = (error) => {
    console.error("WebSocket error:", error);
    socket.close();
  };
}

loadCheckboxes();
connectWebSocket();