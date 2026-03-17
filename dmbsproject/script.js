function bookRoom(){

    let name=document.getElementById("name").value;
    let room=document.getElementById("room").value;
    let payment=document.getElementById("payment").value;

    if(name=="" ){
        alert("Please enter name");
        return;
    }

    let booking={
        name:name,
        room:room,
        payment:payment
    };

    localStorage.setItem("booking",JSON.stringify(booking));

    alert("Room Booked Successfully!");
}

function cancelBooking(){

    let data=localStorage.getItem("booking");

    if(data==null){
        alert("No booking found");
        return;
    }

    localStorage.removeItem("booking");

    alert("Booking Cancelled");
}
