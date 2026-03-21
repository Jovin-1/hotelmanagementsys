// popup.js

// Open popup when room card button is clicked
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".room-card button").forEach((btn) => {
    btn.addEventListener("click", () => {
      const popup = document.getElementById("popup");
      const roomTypeInput = document.getElementById("roomType");

      popup.style.display = "flex";

      // Auto-fill room type based on clicked card
      const roomName = btn.closest(".room-card").querySelector("h3").innerText;
      roomTypeInput.value = roomName;
    });
  });

  // Close popup function
  window.closePopup = function () {
    document.getElementById("popup").style.display = "none";
    document.getElementById("bookingForm").style.display = "block";
    document.getElementById("billDetails").style.display = "none";
  };

  // Handle booking form submission
  const bookingForm = document.getElementById("bookingForm");
  bookingForm.addEventListener("submit", async (e) => {
    e.preventDefault(); // Stop page reload

    const formData = new FormData(bookingForm);
    const data = Object.fromEntries(formData.entries());

    console.log(data); // Debug

    try {
      const response = await fetch("/book", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      const result = await response.json();
      const billStat = result.message;
      const bills = result.bill;

      // Hide form and show results
      bookingForm.style.display = "none";

      const mess = document.getElementById("mess");
      const billStatsEl = document.getElementById("billstats");
      const billTextEl = document.getElementById("billText");
      const billDetails = document.getElementById("billDetails");

      if (!billStat.includes("Booking Successful")) {
        billStatsEl.textContent = "Booking Failed";
        billTextEl.style.display = "none";
        mess.textContent = billStat;
        mess.style.display = "block";
        billDetails.style.display = "block";
      } else {
        mess.style.display = "none";
        billStatsEl.textContent = billStat;
      }

      if (bills) {
        const billString = `
Bill ID: ${bills.bill_id}
Guest ID: ${bills.guest_id}
Name: ${bills.gname}
Reservation ID: ${bills.reservation_id}
Room: ${bills.room_type}
Room No: ${bills.room_no}
Floor: ${bills.floor_no}
Check-in: ${bills.check_in}
Check-out: ${bills.check_out}
Total: ₹${bills.total_bill}
        `;
        billTextEl.textContent = billString;
        billTextEl.style.display = "block";
        billDetails.style.display = "block";
      }
    } catch (error) {
      console.error("Booking request failed:", error);
    }
  });
});
