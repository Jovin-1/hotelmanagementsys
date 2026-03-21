from fastapi import FastAPI
from fastapi.responses import FileResponse
from db import get_db_connection
from pydantic import BaseModel
from datetime import date
from pathlib import Path
from fastapi import Query

app = FastAPI()
# app.mount("/static", StaticFiles(directory="static"), name="static")
STATIC_DIR = Path("static")

@app.get("/static/{file_path:path}")
async def static_no_cache(file_path: str):
    file_location = STATIC_DIR / file_path
    if not file_location.exists():
        return {"error": "File not found"}
    return FileResponse(
        file_location,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )
class Booking(BaseModel):
    name: str
    verdoc: str
    dob: date
    room_type: str
    checkin: date
    checkout: date
    payment_mode: str

class Cancel(BaseModel):
    name: str
    dob: date
    reservation_id: int

class UpdateBooking(BaseModel):
    bookingId: str
    room_type: str
    check_in: str
    check_out: str
    payment_mode: str

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/room")
def home():
    return FileResponse("rooms.html")

@app.get("/service")
def home():
    return FileResponse("services.html")

@app.get("/cancel-booking")
def home():
    return FileResponse("cancel.html")

@app.get("/update-booking")
def home():
    return FileResponse("booking.html")

@app.post("/book")
def insertforbooking(data: Booking):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True,buffered=True)

    try:
        # 1️⃣ Insert Guest
        cursor.execute(
            "INSERT INTO guest (gname, verdoc, dob) VALUES (%s, %s, %s)",
            (data.name, data.verdoc, data.dob)
        )
        guest_id = cursor.lastrowid

        # 2️⃣ Reserve Room (ONLY if available)
        cursor.execute("""
            INSERT INTO reservation (check_in, check_out, room_no, floor_no, guest_id)
            SELECT %s, %s, r.room_no, r.floor_no, %s
            FROM rooms r
            WHERE r.room_type = %s
            AND (r.room_no, r.floor_no) NOT IN (
                SELECT res.room_no, res.floor_no
                FROM reservation res
                WHERE NOT (
                    res.check_out <= %s OR res.check_in >= %s
                )
            )
            LIMIT 1;
        """, (
            data.checkin,
            data.checkout,
            guest_id,
            data.room_type,
            data.checkin,
            data.checkout
        ))

        # ❌ No room available
        if cursor.rowcount == 0:
            conn.rollback()
            return {"message": "No rooms available"}

        # 🔥 Get reservation_id
        reservation_id = cursor.lastrowid

        # 3️⃣ Get price
        cursor.execute(
            "SELECT price FROM rooms WHERE room_type = %s LIMIT 1",
            (data.room_type,)
        )
        price = cursor.fetchone()["price"]

        # 4️⃣ Calculate bill
        days = (data.checkout - data.checkin).days
        total_amount = days * price

        # 5️⃣ Insert billing (UPDATED → using reservation_id)
        cursor.execute(
            "INSERT INTO billing (total_bill, mode, reservation_id) VALUES (%s, %s, %s)",
            (total_amount, data.payment_mode, reservation_id)
        )

        bill_id = cursor.lastrowid

        # 🔥 Get full bill details
        cursor.execute("""
            SELECT
                b.bill_id,
                g.guest_id AS guest_id,
                g.gname,
                b.total_bill,
                r.reservation_id,
                r.check_in,
                r.check_out,
                r.room_no,
                r.floor_no,
                rm.room_type
            FROM billing b
            JOIN reservation r ON b.reservation_id = r.reservation_id
            JOIN guest g ON r.guest_id = g.guest_id
            JOIN rooms rm ON rm.room_no = r.room_no
                         AND rm.floor_no = r.floor_no
            WHERE b.bill_id = %s
        """, (bill_id,))

        bill_details = cursor.fetchone()

        # 6️⃣ Commit everything


        return {
            "message": "Booking Successful",
            "bill": bill_details
        }

    except Exception as e:
        conn.rollback()
        return {"message": f"Error: {str(e)}"}

    finally:
        conn.commit()
        cursor.close()
        conn.close()

@app.post("/cancel")
def cancel_booking(data: Cancel):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    try:
        # 1️⃣ Get ALL guest_ids
        cursor.execute(
            "SELECT guest_id FROM guest WHERE gname=%s AND dob=%s",
            (data.name, data.dob)
        )
        guests = cursor.fetchall()

        if not guests:
            return {"message": "Guest not found"}

        # Convert to list
        guest_ids = [g["guest_id"] for g in guests]

        # 2️⃣ Check reservation belongs to ANY of those guest_ids
        format_strings = ','.join(['%s'] * len(guest_ids))

        query = f"""
            SELECT *
            FROM reservation
            WHERE reservation_id = %s
            AND guest_id IN ({format_strings})
        """

        cursor.execute(query, [data.reservation_id] + guest_ids)
        reservation = cursor.fetchone()

        if not reservation:
            return {"message": "Invalid reservation for this guest"}

        # 3️⃣ Get billing
        cursor.execute(
            "SELECT total_bill, mode FROM billing WHERE reservation_id=%s",
            (data.reservation_id,)
        )
        billing = cursor.fetchone()

        if not billing:
            return {"message": "Billing not found"}

        # 4️⃣ Refund logic
        if billing["mode"].lower() != "cash":
            refund_msg = f"Rs {billing['total_bill']} will be refunded shortly."
        else:
            refund_msg = "No refund (Cash payment)."

        # 5️⃣ Delete reservation
        cursor.execute(
            "DELETE FROM reservation WHERE reservation_id=%s",
            (data.reservation_id,)
        )

        return {
            "message": "Booking Cancelled Successfully",
            "refund": refund_msg
        }

    except Exception as e:
        conn.rollback()
        return {"message": f"Error: {str(e)}"}

    finally:
        conn.commit()
        cursor.close()
        conn.close()


class GetBookingForm(BaseModel):
    bookingId: int
    name: str
    dob: date

@app.post("/get-booking")
def get_booking(data: GetBookingForm):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        # 1️⃣ Fetch booking from DB
        cursor.execute("""
            SELECT r.reservation_id, g.gname, g.dob, rm.room_type,
                   r.check_in, r.check_out, b.total_bill, b.mode AS payment_mode
            FROM reservation r
            JOIN guest g ON r.guest_id = g.guest_id
            JOIN rooms rm ON r.room_no = rm.room_no AND r.floor_no = rm.floor_no
            JOIN billing b ON r.reservation_id = b.reservation_id
            WHERE r.reservation_id = %s
              AND g.gname = %s
              AND g.dob = %s
        """, (data.bookingId, data.name, data.dob))

        booking = cursor.fetchone()
        if not booking:
            return {"message": "Booking not found"}

        # 2️⃣ Format dates as string for JSON
        booking['check_in'] = str(booking['check_in'])
        booking['check_out'] = str(booking['check_out'])
        booking['dob'] = str(booking['dob'])

        # 3️⃣ Return directly like /book
        return {
            "message": "Booking found",
            "booking": booking
        }

    except Exception as e:
        return {"message": f"Error: {str(e)}"}

    finally:
        cursor.close()
        conn.close()

# Only allow 'Cash' or 'UPI'
class UpdateBooking(BaseModel):
    bookingId: int
    room_type: str
    check_in: date
    check_out: date
    payment_mode: str  # "Cash" or "UPI"

# Room prices for comparison (fetch from DB in real case)
ROOM_ORDER = {
    "Single Room": 1,
    "Double Room": 2,
    "Deluxe Room": 3,
    "Family Room": 4,
    "Executive Suite": 5,
    "Presidential Suite": 6
}

@app.post("/update-booking")
def update_booking(data: UpdateBooking):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        # 1️⃣ Check if reservation exists
        cursor.execute("""
            SELECT r.reservation_id, r.room_no, r.floor_no, rm.room_type, r.check_in, r.check_out, b.total_bill, b.mode AS payment_mode, g.guest_id, g.gname
            FROM reservation r
            JOIN rooms rm ON r.room_no = rm.room_no AND r.floor_no = rm.floor_no
            JOIN billing b ON r.reservation_id = b.reservation_id
            JOIN guest g ON r.guest_id = g.guest_id
            WHERE r.reservation_id=%s
        """, (data.bookingId,))
        resv = cursor.fetchone()
        if not resv:
            return {"message": "Reservation not found"}

        # 2️⃣ Check room availability if room_type changed
        if data.room_type != resv['room_type']:
            cursor.execute("""
                SELECT r.room_no, r.floor_no, r.price
                FROM rooms r
                WHERE r.room_type=%s
                AND (r.room_no, r.floor_no) NOT IN (
                    SELECT res.room_no, res.floor_no
                    FROM reservation res
                    WHERE NOT (res.check_out <= %s OR res.check_in >= %s)
                    AND res.reservation_id != %s
                )
                LIMIT 1
            """, (data.room_type, data.check_in, data.check_out, data.bookingId))
            new_room = cursor.fetchone()
            if not new_room:
                return {"message": "Selected room type not available for these dates"}
            room_no, floor_no, price = new_room['room_no'], new_room['floor_no'], new_room['price']
        else:
            room_no, floor_no = resv['room_no'], resv['floor_no']
            days_old = (resv['check_out'] - resv['check_in']).days or 1
            price = resv['total_bill'] / days_old

        # 3️⃣ Validate payment mode (Cash → UPI allowed)
        if resv['payment_mode'].lower() == "cash" and data.payment_mode.upper() in ["UPI", "Cash"]:
            payment_mode = data.payment_mode.upper() if data.payment_mode.upper() == "UPI" else "Cash"
        elif resv['payment_mode'].lower() == "upi" and data.payment_mode.upper() == "UPI":
            payment_mode = "UPI"
        else:
            return {"message": "Invalid payment mode change"}

        # 4️⃣ Calculate total bill
        days = (data.check_out - data.check_in).days or 1
        total_bill = days * price

        # 5️⃣ Update reservation
        cursor.execute("""
            UPDATE reservation
            SET room_no=%s, floor_no=%s, check_in=%s, check_out=%s
            WHERE reservation_id=%s
        """, (room_no, floor_no, data.check_in, data.check_out, data.bookingId))

        # 6️⃣ Update billing
        cursor.execute("""
            UPDATE billing
            SET total_bill=%s, mode=%s
            WHERE reservation_id=%s
        """, (total_bill, payment_mode, data.bookingId))

        # 🔥 Fetch updated bill details like new booking
        cursor.execute("""
            SELECT
                b.bill_id,
                g.guest_id,
                g.gname,
                b.total_bill,
                r.reservation_id,
                r.check_in,
                r.check_out,
                r.room_no,
                r.floor_no,
                rm.room_type
            FROM billing b
            JOIN reservation r ON b.reservation_id = r.reservation_id
            JOIN guest g ON r.guest_id = g.guest_id
            JOIN rooms rm ON rm.room_no = r.room_no AND rm.floor_no = r.floor_no
            WHERE b.reservation_id = %s
        """, (data.bookingId,))
        bill_details = cursor.fetchone()

        # 7️⃣ Commit changes
        conn.commit()

        # 8️⃣ Calculate refund if total_bill decreased
        refund_msg = ""
        if total_bill < resv['total_bill']:
            refund_msg = f"Rs {resv['total_bill'] - total_bill} will be refunded."

        return {
            "message": "Booking updated successfully",
            "bill": {**bill_details, "refund": refund_msg}
        }

    except Exception as e:
        conn.rollback()
        return {"message": f"Error: {str(e)}"}

    finally:
        cursor.close()
        conn.close()
