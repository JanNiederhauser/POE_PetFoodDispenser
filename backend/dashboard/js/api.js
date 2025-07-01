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
};
