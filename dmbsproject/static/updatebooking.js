document.addEventListener("DOMContentLoaded", () => {
    const bookingForm = document.getElementById("ub-bookingForm");
    const mess = document.getElementById("ub-mess");
    const billStatsEl = document.getElementById("ub-billstats");
    const billTextEl = document.getElementById("ub-billText");
    const billDetails = document.getElementById("ub-billDetails");

    bookingForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData(bookingForm);
        const data = Object.fromEntries(formData.entries());

        try {
            const res = await fetch("/update-booking", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            });
            const result = await res.json();

            if (!result.success) {
                mess.textContent = result.message || "Update Failed ❌";
                mess.style.display = "block";
                billStatsEl.textContent = "";
                billTextEl.textContent = "";
                billDetails.style.display = "block";
                return;
            }

            const newBill = result.new_bill;
            let billMessage = "Booking Updated Successfully ✅";

            if (newBill < result.old_bill) {
                billMessage += `\nRefund: ₹${result.old_bill - newBill}`;
            }

            billStatsEl.textContent = billMessage;
            mess.style.display = "none";

            const bills = result.updated_booking;
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
                billDetails.style.display = "block";
            }
        } catch (err) {
            console.error("Update request failed:", err);
            mess.textContent = "Error: Could not update booking";
            mess.style.display = "block";
            billDetails.style.display = "block";
        }
    });
});
