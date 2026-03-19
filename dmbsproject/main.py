from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from db import get_db_connection
from pydantic import BaseModel
from datetime import date

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

class Booking(BaseModel):
    name: str
    verdoc: str
    dob: date
    room_type: str
    checkin: date
    checkout: date
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

