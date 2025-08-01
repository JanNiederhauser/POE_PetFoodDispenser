async function renderDashboard() {
  const [silos, pets, unknownRFIDs] = await Promise.all([
    API.getSilos(),
    API.getPets(),
    API.getUnknownRFIDs()
  ]);

  const siloContainer = document.getElementById("silo-container");
  siloContainer.innerHTML = "";

  console.log(silos, pets, unknownRFIDs);

  silos.forEach(silo => {
    const pet = pets.find(p => p.silo === silo.id);
    const fill = silo.percentage;

    const div = document.createElement("div");
    div.className = "bg-gray-800 rounded-xl p-4 shadow";

    div.innerHTML = `
  <h2 class="text-lg font-semibold mb-2">Silo ${silo.id}</h2>

  <!-- Fill bar container -->
  <div class="w-full h-32 bg-gray-700 rounded mb-4 overflow-hidden flex flex-col-reverse">
    <div class="bg-teal-500 transition-all duration-500" style="height: ${fill}%;"></div>
  </div>
  
  <p class="text-sm">Fill: ${fill.toFixed(0)}%</p>
  <p class="text-sm mb-2">Assigned to: <strong>${pet?.name || 'None'}</strong></p>
  ${pet ? `<button onclick="editSchedule('${pet.rfid}')" class="bg-teal-600 px-4 py-2 rounded text-sm">Edit Schedule</button>` : ""}
`;


    siloContainer.appendChild(div);
  });

  const unknownDiv = document.getElementById("unknown-rfids");
  unknownDiv.innerHTML = unknownRFIDs.map(e => `
    <div class="bg-gray-800 p-4 rounded flex justify-between items-center">
      <span>RFID: ${e.rfid}</span>
      <div class="flex space-x-2">
        <a href="#" onclick="event.preventDefault(); API.dismissRfid('${e.rfid}')" class="text-sm text-teal-400">
          Dismiss
        </a>
        <a href="/register-pet.html?rfid=${e.rfid}" class="text-sm text-teal-400">
          Register
        </a>
      </div>
    </div>
  `).join('');
}

function editSchedule(rfid) {
  window.location.href = `/edit-schedule.html?rfid=${rfid}`;
}

renderDashboard();
