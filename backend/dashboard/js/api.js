const API = {
  async getSilos() {
    return fetch("/silo/list").then(res => res.json());
  },
  async getPets() {
    return fetch("/pet/list").then(res => res.json());
  },
  async getUnknownRFIDs() {
    return fetch("/dashboard/unknown-rfids").then(res => res.json());
  },
  async getPet(rfid) {
    return fetch(`/pet/get/${rfid}`).then(res => res.json());
  },
  async updateSchedule(schedule) {
    return fetch("/schedule/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(schedule),
    }).then(res => res.json());
  },
  async registerPet(pet){
    return fetch("/dashboard/register-pet",{
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pet)
    }).then(res => res.json());
  },
   async dismissRfid(rfid) {
    fetch(`/dashboard/unknown-rfids/dismiss/${rfid}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
        // Add CSRF headers here if needed
      },
      body: JSON.stringify({}) // or null, depending on your backend
    }).then(response => {
      if (response.ok) {
        location.reload();
      } else {
        alert("Failed to dismiss.");
      }
    }).catch(err => {
      console.error("Dismiss error:", err);
      alert("Error occurred.");
    });
  }
};
