const params = new URLSearchParams(window.location.search);
const rfid = params.get("rfid");
document.getElementById("rfid").value = rfid;

document.getElementById("register-form").addEventListener("submit", async e => {
  e.preventDefault();
  const pet = {
    rfid,
    name: document.getElementById("name").value,
    silo: document.getElementById("silo").value,
    timeWindow: document.getElementById("timeWindow").value,
    amount: parseFloat(document.getElementById("amount").value),
  };
  await API.registerPet(pet);
  alert("Pet registered!");
  window.location.href = "/";
});