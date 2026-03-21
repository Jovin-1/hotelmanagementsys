async function cancelBooking() {
    const resultDiv = document.getElementById("result");

    resultDiv.innerText = "Processing...";
    resultDiv.className = "";

    const name = document.getElementById("name").value;
    const dob = document.getElementById("dob").value;
    const reservation_id = document.getElementById("reservation_id").value;

    try {
        const response = await fetch("http://127.0.0.1:8000/cancel", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: name,
                dob: dob,
                reservation_id: parseInt(reservation_id)
            })
        });

        const data = await response.json();

        if (response.ok) {
            resultDiv.className = "success";
        } else {
            resultDiv.className = "error";
        }

        resultDiv.innerText =
            data.message + (data.refund ? " | " + data.refund : "");

    } catch (err) {
        resultDiv.className = "error";
        resultDiv.innerText = "Server error. Try again.";
    }
}
