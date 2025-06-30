const params = new URLSearchParams(window.location.search);
const rfid = params.get("rfid");
document.getElementById("rfid").value = rfid;

API.getPet(rfid).then(pet => {
  document.getElementById("timeWindow").value = "08:00-20:00";
  document.getElementById("amount").value = "0.5";
});

document.getElementById("edit-form").addEventListener("submit", async e => {
  e.preventDefault();
  const schedule = {
    rfid,
    timeWindow: document.getElementById("timeWindow").value,
    amount: parseFloat(document.getElementById("amount").value),
  };
  await API.updateSchedule(schedule);
  alert("Schedule updated!");
  window.location.href = "/";
});
