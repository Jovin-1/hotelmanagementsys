const fetchForm = document.getElementById("ub-fetchBookingForm");
const updateForm = document.getElementById("ub-bookingForm");
const notFoundMsg = document.getElementById("ub-notfound");

const billPopup = document.getElementById("billPopup");
const billResId = document.getElementById("billResId");
const billRoomType = document.getElementById("billRoomType");
const billCheckIn = document.getElementById("billCheckIn");
const billCheckOut = document.getElementById("billCheckOut");
const billPayment = document.getElementById("billPayment");
const billTotal = document.getElementById("billTotal");
const billRefund = document.getElementById("billRefund");

let currentBookingId = null;

// Fetch booking
fetchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const bookingId = parseInt(document.getElementById("ub-bookingIdFetch").value);
  const guestName = document.getElementById("ub-guestNameFetch").value;
  const dob = document.getElementById("ub-dobFetch").value;

  try {
    const res = await fetch("/get-booking", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({bookingId, name: guestName, dob})
    });
    const data = await res.json();

    if (!data.booking) {
      updateForm.style.display = "none";
      notFoundMsg.style.display = "block";
      return;
    }

    currentBookingId = data.booking.reservation_id;

    document.getElementById("ub-roomType").value = data.booking.room_type;
    document.getElementById("ub-check_in").value = data.booking.check_in;
    document.getElementById("ub-check_out").value = data.booking.check_out;
    document.getElementById("ub-payment_mode").value = data.booking.payment_mode;

    updateForm.style.display = "block";
    notFoundMsg.style.display = "none";

  } catch (err) {
    alert("Error fetching booking");
    console.error(err);
  }
});

// Update booking
updateForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    bookingId: currentBookingId,
    room_type: document.getElementById("ub-roomType").value,
    check_in: document.getElementById("ub-check_in").value,
    check_out: document.getElementById("ub-check_out").value,
    payment_mode: document.getElementById("ub-payment_mode").value
  };

  try {
    const res = await fetch("/update-booking", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.bill) {
      // Populate popup
     billId.textContent = data.bill.bill_id;
guestId.textContent = data.bill.guest_id;
guestName.textContent = data.bill.gname;
billResId.textContent = data.bill.reservation_id;
billRoomNo.textContent = data.bill.room_no;
billFloorNo.textContent = data.bill.floor_no;
billRoomType.textContent = data.bill.room_type;
billCheckIn.textContent = data.bill.check_in;
billCheckOut.textContent = data.bill.check_out;
billPayment.textContent = data.bill.payment_mode;
billTotal.textContent = data.bill.total_bill;
billRefund.textContent = data.bill.refund || "";

      billPopup.style.display = "flex"; // show popup
    } else {
      alert(data.message);
    }

  } catch (err) {
    alert("Error updating booking");
    console.error(err);
  }
});

function closeBillPopup() {
  billPopup.style.display = "none";
}
