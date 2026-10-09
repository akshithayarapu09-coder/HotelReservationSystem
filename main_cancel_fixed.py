# Grand Palace Hotel - Hotel Reservation System
# Complete project code with a visible startup-error window.
import tkinter as _error_tk
from tkinter import ttk as _error_ttk
import traceback as _error_traceback

def _show_startup_error(exc_text):
    root = _error_tk.Tk()
    root.title("Grand Palace Hotel - Startup Error")
    root.geometry("900x600")
    root.minsize(700, 450)
    frame = _error_ttk.Frame(root, padding=15)
    frame.pack(fill="both", expand=True)
    _error_ttk.Label(frame, text="Grand Palace Hotel Reservation System", font=("Segoe UI", 16, "bold")).pack(anchor="w")
    _error_ttk.Label(frame, text="The project could not start. The full error is shown below.", font=("Segoe UI", 10)).pack(anchor="w", pady=(6, 10))
    box_frame = _error_ttk.Frame(frame)
    box_frame.pack(fill="both", expand=True)
    box = _error_tk.Text(box_frame, wrap="word", font=("Consolas", 10))
    box.pack(side="left", fill="both", expand=True)
    scroll = _error_ttk.Scrollbar(box_frame, orient="vertical", command=box.yview)
    scroll.pack(side="right", fill="y")
    box.configure(yscrollcommand=scroll.set)
    box.insert("1.0", exc_text)
    box.configure(state="disabled")
    _error_ttk.Button(frame, text="Close", command=root.destroy).pack(anchor="e", pady=(10, 0))
    root.mainloop()

try:
    import sqlite3
    import os
    import hashlib
    import secrets
    import tkinter as tk
    from tkinter import ttk, messagebox
    from datetime import datetime

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_NAME = os.path.join(BASE_DIR, "hotel.db")
    SUMMARY_TXT_NAME = os.path.join(BASE_DIR, "hotel_customer_summary.txt")

    BG = "#0B1220"
    SIDEBAR = "#101A2E"
    CARD = "#162238"
    CARD2 = "#1B2A42"
    GOLD = "#D4AF37"
    GOLD_LIGHT = "#F0D77A"
    CREAM = "#F5EEDC"
    WHITE = "#FFFFFF"
    TEXT = "#DCE4F2"
    MUTED = "#91A0B8"
    GREEN = "#38C172"
    RED = "#E55353"
    BLUE = "#4D9DE0"
    FONT = "Segoe UI"


    def db():
        conn = sqlite3.connect(DB_NAME)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


    def update_hotel_customer_summary():
        """Rebuild the hotel-wise customer reservation summary as a text file.
        The summary contains counts only; no customer personal details are stored.
        """
        source = db()
        src = source.cursor()
        src.execute("SELECT id, hotel_name, locality FROM hotels ORDER BY hotel_name")
        hotels = src.fetchall()

        lines = [
            "HOTEL CUSTOMER RESERVATION SUMMARY",
            "=" * 70,
            "",
            f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        for hotel_id, hotel_name, locality in hotels:
            src.execute("""SELECT COUNT(DISTINCT customer_id), COUNT(*)
                           FROM reservations
                           WHERE hotel_id=? AND status='Booked'""", (hotel_id,))
            unique_customers, total_reservations = src.fetchone()
            lines.extend([
                f"Hotel Name        : {hotel_name}",
                f"Locality          : {locality}",
                f"Unique Customers  : {unique_customers or 0}",
                f"Total Reservations: {total_reservations or 0}",
                "-" * 70,
            ])

        source.close()
        with open(SUMMARY_TXT_NAME, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


    def initialize_database():
        conn = db()
        cur = conn.cursor()

        cur.execute("""CREATE TABLE IF NOT EXISTS customers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            address TEXT)""")

        # Each customer profile belongs to one login account. Existing customer rows
        # are preserved; their user_id can remain NULL until linked to an account.
        ccols = [r[1] for r in cur.execute("PRAGMA table_info(customers)").fetchall()]
        if "user_id" not in ccols:
            cur.execute("ALTER TABLE customers ADD COLUMN user_id INTEGER")

        cur.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_user_id ON customers(user_id) WHERE user_id IS NOT NULL")

        cur.execute("""CREATE TABLE IF NOT EXISTS hotels(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_name TEXT NOT NULL,
            locality TEXT NOT NULL,
            city TEXT NOT NULL,
            address TEXT,
            rating REAL DEFAULT 0,
            description TEXT,
            contact TEXT)""")

        cur.execute("""CREATE TABLE IF NOT EXISTS hotel_specs(
            hotel_id INTEGER PRIMARY KEY,
            wifi INTEGER DEFAULT 0,
            parking INTEGER DEFAULT 0,
            restaurant INTEGER DEFAULT 0,
            pool INTEGER DEFAULT 0,
            gym INTEGER DEFAULT 0,
            ac INTEGER DEFAULT 0,
            FOREIGN KEY(hotel_id) REFERENCES hotels(id) ON DELETE CASCADE)""")

        cur.execute("""CREATE TABLE IF NOT EXISTS rooms(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_id INTEGER,
            room_number TEXT NOT NULL,
            room_type TEXT NOT NULL,
            price REAL NOT NULL,
            capacity INTEGER DEFAULT 2,
            status TEXT DEFAULT 'Available',
            UNIQUE(hotel_id, room_number),
            FOREIGN KEY(hotel_id) REFERENCES hotels(id) ON DELETE CASCADE)""")

        # Upgrade the original single-hotel database without deleting existing data.
        cols = [r[1] for r in cur.execute("PRAGMA table_info(rooms)").fetchall()]
        if "hotel_id" not in cols:
            cur.execute("ALTER TABLE rooms ADD COLUMN hotel_id INTEGER")
        if "capacity" not in cols:
            cur.execute("ALTER TABLE rooms ADD COLUMN capacity INTEGER DEFAULT 2")

        cur.execute("""CREATE TABLE IF NOT EXISTS reservations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            hotel_id INTEGER,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            nights INTEGER NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Booked',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(room_id) REFERENCES rooms(id),
            FOREIGN KEY(hotel_id) REFERENCES hotels(id))""")

        rcols = [r[1] for r in cur.execute("PRAGMA table_info(reservations)").fetchall()]
        if "hotel_id" not in rcols:
            cur.execute("ALTER TABLE reservations ADD COLUMN hotel_id INTEGER")

        # Always make sure the demonstration database contains several hotels.
        # This also repairs databases created by an earlier version of the program.
        sample_hotels = [
            ("Grand Palace Hotel", "Gachibowli", "Hyderabad", "Financial District Road, Gachibowli", 4.6,
             "Premium business and leisure hotel with modern rooms and hospitality.", "+91 90000 00001", (1,1,1,1,1,1)),
            ("City Comfort Residency", "Madhapur", "Hyderabad", "Main Road, Madhapur", 4.2,
             "Comfortable rooms for business and short stays.", "+91 90000 00002", (1,1,1,0,0,1)),
            ("Royal Residency", "Banjara Hills", "Hyderabad", "Road No. 12, Banjara Hills", 4.5,
             "Elegant rooms with family-friendly facilities.", "+91 90000 00003", (1,1,1,1,1,1)),
            ("Green View Hotel", "Secunderabad", "Hyderabad", "Station Road, Secunderabad", 4.0,
             "Affordable accommodation with essential facilities.", "+91 90000 00004", (1,1,1,0,0,0)),
            ("Airport Comfort Inn", "Secunderabad", "Hyderabad", "Airport Road Extension, Secunderabad", 4.3,
             "Convenient stay with essential guest facilities and comfortable rooms.", "+91 90000 00005", (1,1,1,0,0,1)),
            ("Lake View Grand Hotel", "Gachibowli", "Hyderabad", "Nanakramguda Road, Gachibowli", 4.4,
             "Modern city hotel suited for business travellers and families.", "+91 90000 00006", (1,1,1,1,1,1)),
            ("Pearl City Inn", "Madhapur", "Hyderabad", "Kavuri Hills Road, Madhapur", 3.9,
             "Budget-friendly rooms with convenient city access.", "+91 90000 00007", (1,1,1,0,0,1)),
            ("Heritage Heights Hotel", "Banjara Hills", "Hyderabad", "Road No. 10, Banjara Hills", 4.1,
             "Comfortable central-city accommodation with dining facilities.", "+91 90000 00008", (1,1,1,0,1,1)),
            ("Metro Star Residency", "Secunderabad", "Hyderabad", "MG Road, Secunderabad", 4.0,
             "Practical hotel for business and short city stays.", "+91 90000 00009", (1,1,0,0,0,1)),
            ("City Pearl Palace", "Gachibowli", "Hyderabad", "Old Mumbai Highway, Gachibowli", 4.3,
             "Contemporary accommodation with convenient guest facilities.", "+91 90000 00010", (1,1,1,1,0,1)),
        ]

        # Do not delete existing hotels/rooms/reservations during startup.
        # Foreign-key relationships are preserved and all required sample hotels
        # are inserted below when they are missing.

        for h in sample_hotels:
            cur.execute("SELECT id FROM hotels WHERE hotel_name=? AND locality=?", (h[0], h[1]))
            existing = cur.fetchone()
            if existing:
                h_id = existing[0]
            else:
                cur.execute("""INSERT INTO hotels
                    (hotel_name, locality, city, address, rating, description, contact)
                    VALUES (?,?,?,?,?,?,?)""", h[:7])
                h_id = cur.lastrowid

            cur.execute("SELECT 1 FROM hotel_specs WHERE hotel_id=?", (h_id,))
            if not cur.fetchone():
                cur.execute("INSERT INTO hotel_specs VALUES (?,?,?,?,?,?,?)", (h_id, *h[7]))

        cur.execute("SELECT id FROM hotels ORDER BY id LIMIT 1")
        first_hotel = cur.fetchone()
        hid = first_hotel[0]

        # Assign old rooms to the first hotel.
        cur.execute("UPDATE rooms SET hotel_id=? WHERE hotel_id IS NULL", (hid,))
        cur.execute("UPDATE reservations SET hotel_id=(SELECT hotel_id FROM rooms WHERE rooms.id=reservations.room_id) WHERE hotel_id IS NULL")

        cur.execute("SELECT COUNT(*) FROM rooms")
        if cur.fetchone()[0] == 0:
            room_data = [
                (hid, "101", "Single", 1500, 1), (hid, "102", "Single", 1500, 1),
                (hid, "201", "Double", 2500, 2), (hid, "202", "Double", 2500, 2),
                (hid, "301", "Deluxe", 4000, 3), (hid, "302", "Deluxe", 4000, 3),
                (hid, "401", "Suite", 6000, 4), (hid, "402", "Suite", 6000, 4),
            ]
            cur.executemany("INSERT INTO rooms(hotel_id,room_number,room_type,price,capacity) VALUES(?,?,?,?,?)", room_data)

        # Give every hotel useful rooms. Use hotel-specific room numbers so this
        # also works with older databases where room_number was globally UNIQUE.
        for row in cur.execute("SELECT id FROM hotels ORDER BY id").fetchall():
            hotel_id = row[0]
            cur.execute("SELECT COUNT(*) FROM rooms WHERE hotel_id=?", (hotel_id,))
            if cur.fetchone()[0] == 0:
                prefix = f"H{hotel_id}-"
                rooms = [
                    (hotel_id, f"{prefix}101", "Standard", 1800, 2),
                    (hotel_id, f"{prefix}201", "Deluxe", 3000, 3),
                    (hotel_id, f"{prefix}301", "Suite", 5000, 4),
                ]
                for room in rooms:
                    # INSERT OR IGNORE protects against an old database whose
                    # room_number column is globally UNIQUE.
                    cur.execute("""INSERT OR IGNORE INTO rooms
                        (hotel_id,room_number,room_type,price,capacity)
                        VALUES(?,?,?,?,?)""", room)

        conn.commit()
        conn.close()
        update_hotel_customer_summary()


    class LoginWindow:
        def __init__(self, root):
            self.root = root
            self.root.title("Hotel Finder - User Login")
            self.root.geometry("520x680")
            self.root.configure(bg=BG)
            self.root.resizable(True, True)
            self.build_login()

        def build_login(self):
            main = tk.Frame(self.root, bg=BG)
            main.pack(fill="both", expand=True)
            tk.Label(main, text="♛", font=(FONT, 55), fg=GOLD, bg=BG).pack(pady=(35,0))
            tk.Label(main, text="HOTEL FINDER", font=(FONT, 28, "bold"), fg=GOLD_LIGHT, bg=BG).pack()
            tk.Label(main, text="MULTI-HOTEL RESERVATION SYSTEM", font=(FONT, 11, "bold"), fg=CREAM, bg=BG).pack()
            tk.Label(main, text="Login with your own account", font=(FONT, 10), fg=MUTED, bg=BG).pack(pady=(5,30))
            card = tk.Frame(main, bg=CARD, highlightbackground=GOLD, highlightthickness=1)
            card.pack(padx=50, fill="x")
            tk.Label(card, text="USER LOGIN", font=(FONT,15,"bold"), fg=CREAM, bg=CARD).pack(pady=(25,20))
            tk.Label(card, text="Username", fg=MUTED, bg=CARD).pack(anchor="w", padx=35)
            self.username = tk.Entry(card, font=(FONT,12), bg=CARD2, fg=WHITE, insertbackground=WHITE, relief="flat")
            self.username.pack(padx=35,pady=(5,15),ipady=8,fill="x")
            tk.Label(card, text="Password", fg=MUTED, bg=CARD).pack(anchor="w", padx=35)
            self.password = tk.Entry(card, show="•", font=(FONT,12), bg=CARD2, fg=WHITE, insertbackground=WHITE, relief="flat")
            self.password.pack(padx=35,pady=(5,20),ipady=8,fill="x")
            tk.Button(card, text="LOGIN", command=self.login, font=(FONT,11,"bold"), bg=GOLD, fg="#111111", activebackground=GOLD_LIGHT, relief="flat").pack(padx=35,pady=(0,10),fill="x",ipady=8)
            tk.Button(card, text="CREATE NEW ACCOUNT", command=self.register, font=(FONT,10,"bold"), bg=CARD2, fg=CREAM, activebackground=SIDEBAR, relief="flat").pack(padx=35,pady=(0,25),fill="x",ipady=7)
            tk.Label(main, text="Your username and password are stored securely in hotel.db.", font=(FONT,9), fg=MUTED, bg=BG).pack(pady=18)
            self.password.bind("<Return>", lambda e: self.login())

        def hash_password(self, password, salt=None):
            salt = salt or secrets.token_hex(16)
            hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
            return hashed, salt

        def register(self):
            username = self.username.get().strip()
            password = self.password.get()
            if len(username) < 3:
                messagebox.showwarning("Create Account", "Username must contain at least 3 characters.")
                return
            if len(password) < 4:
                messagebox.showwarning("Create Account", "Password must contain at least 4 characters.")
                return
            conn = db()
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE LOWER(username)=LOWER(?)", (username,))
            if cur.fetchone():
                conn.close()
                messagebox.showerror("Create Account", "That username already exists. Please choose another username.")
                return
            password_hash, salt = self.hash_password(password)
            cur.execute("INSERT INTO users(username,password_hash,salt) VALUES(?,?,?)", (username, password_hash, salt))
            user_id=cur.lastrowid
            conn.commit()
            conn.close()
            messagebox.showinfo("Account Created", "Account created successfully. Now complete your customer profile.")
            self.password.delete(0, tk.END)
            self.complete_profile(user_id, username)

        def login(self):
            username = self.username.get().strip()
            password = self.password.get()
            if not username or not password:
                messagebox.showwarning("Login", "Enter your username and password.")
                return
            conn = db()
            cur = conn.cursor()
            cur.execute("SELECT id, password_hash, salt FROM users WHERE LOWER(username)=LOWER(?)", (username,))
            row = cur.fetchone()
            if row:
                user_id, stored_hash, salt = row
                password_hash, _ = self.hash_password(password, salt)
                if secrets.compare_digest(password_hash, stored_hash):
                    cur.execute("SELECT id FROM customers WHERE user_id=?", (user_id,))
                    customer_row = cur.fetchone()
                    conn.close()
                    if not customer_row:
                        self.complete_profile(user_id, username)
                        return
                    self.root.destroy()
                    root = tk.Tk()
                    HotelApp(root, user_id, customer_row[0], username)
                    root.mainloop()
                    return
            conn.close()
            messagebox.showerror("Login Failed", "Invalid username or password.")

        def complete_profile(self, user_id, username):
            win = tk.Toplevel(self.root)
            win.title("Complete Your Profile")
            win.geometry("460x500")
            win.configure(bg=BG)
            win.transient(self.root)
            win.grab_set()
            tk.Label(win, text="COMPLETE YOUR PROFILE", font=(FONT,16,"bold"), fg=GOLD_LIGHT, bg=BG).pack(pady=(25,20))
            card=tk.Frame(win,bg=CARD,highlightbackground=GOLD,highlightthickness=1); card.pack(fill="both",expand=True,padx=30,pady=10)
            fields={}
            for label in ["Full Name","Phone","Email","Address"]:
                tk.Label(card,text=label,fg=MUTED,bg=CARD).pack(anchor="w",padx=25,pady=(12,4))
                e=tk.Entry(card,font=(FONT,11),bg=CARD2,fg=WHITE,insertbackground=WHITE,relief="flat")
                e.pack(fill="x",padx=25,ipady=7); fields[label]=e
            def save():
                name=fields["Full Name"].get().strip(); phone=fields["Phone"].get().strip()
                if not name or not phone:
                    messagebox.showwarning("Required","Full name and phone are required.",parent=win); return
                conn=db(); cur=conn.cursor(); cur.execute("INSERT INTO customers(user_id,name,phone,email,address) VALUES(?,?,?,?,?)",(user_id,name,phone,fields["Email"].get().strip(),fields["Address"].get().strip())); cid=cur.lastrowid; conn.commit(); conn.close(); win.destroy(); self.root.destroy(); root=tk.Tk(); HotelApp(root,user_id,cid,username); root.mainloop()
            tk.Button(card,text="SAVE PROFILE",command=save,font=(FONT,10,"bold"),bg=GOLD,fg="#111111",relief="flat",cursor="hand2").pack(fill="x",padx=25,pady=25,ipady=8)


    class HotelApp:
        def __init__(self, root, user_id, customer_id, username):
            self.root = root
            self.user_id = user_id
            self.customer_id = customer_id
            self.username = username
            self.root.title("Hotel Finder - Multi-Hotel Reservation System")
            self.root.geometry("1280x800")
            self.root.minsize(1080,700)
            self.root.configure(bg=BG)
            self.current_page = None
            self.create_style()
            self.build_interface()
            self.show_finder()

        def create_style(self):
            style = ttk.Style()
            try: style.theme_use("clam")
            except: pass
            style.configure("Treeview", background=CARD, foreground=TEXT, fieldbackground=CARD, rowheight=34, font=(FONT,10), borderwidth=0)
            style.configure("Treeview.Heading", background=SIDEBAR, foreground=GOLD_LIGHT, font=(FONT,10,"bold"), padding=8)
            style.map("Treeview", background=[("selected", "#33476A")], foreground=[("selected", WHITE)])
            style.configure("TCombobox", fieldbackground=CARD2, background=CARD2, foreground=WHITE, arrowcolor=GOLD, padding=7)

        def build_interface(self):
            header = tk.Frame(self.root,bg=BG,height=85); header.pack(side="top",fill="x")
            tk.Label(header,text="♛",font=(FONT,32),fg=GOLD,bg=BG).pack(side="left",padx=(25,8))
            tf=tk.Frame(header,bg=BG); tf.pack(side="left")
            tk.Label(tf,text="HOTEL FINDER",font=(FONT,18,"bold"),fg=GOLD_LIGHT,bg=BG).pack(anchor="w")
            tk.Label(tf,text="MULTI-HOTEL RESERVATION SYSTEM",font=(FONT,8),fg=MUTED,bg=BG).pack(anchor="w")
            tk.Label(header,text="User  •  ● Online",font=(FONT,10),fg=GREEN,bg=BG).pack(side="right",padx=30)
            body=tk.Frame(self.root,bg=BG); body.pack(fill="both",expand=True)
            self.sidebar=tk.Frame(body,bg=SIDEBAR,width=235); self.sidebar.pack(side="left",fill="y"); self.sidebar.pack_propagate(False)
            self.create_sidebar()
            self.content=tk.Frame(body,bg=BG); self.content.pack(side="left",fill="both",expand=True,padx=20,pady=15)

        def create_sidebar(self):
            tk.Label(self.sidebar,text="HOTEL SEARCH",font=(FONT,9,"bold"),fg=MUTED,bg=SIDEBAR).pack(anchor="w",padx=25,pady=(25,12))
            self.nav_button("⌂   Hotel Finder",self.show_finder)
            tk.Label(self.sidebar,text="MY BOOKING",font=(FONT,9,"bold"),fg=MUTED,bg=SIDEBAR).pack(anchor="w",padx=25,pady=(25,12))
            self.nav_button("▤   My Reservations",self.show_reservations)
            self.nav_button("✕   Cancel Reservation",self.show_cancel_reservation)
            self.nav_button("₹   My Bill / Invoice",self.show_billing)
            tk.Label(self.sidebar,text="SYSTEM",font=(FONT,9,"bold"),fg=MUTED,bg=SIDEBAR).pack(anchor="w",padx=25,pady=(25,12))
            self.nav_button("↻   Refresh",self.refresh_current)
            self.nav_button("⇥   Logout",self.logout,danger=True)
            tk.Label(self.sidebar,text="",bg=SIDEBAR).pack(expand=True)
            tk.Label(self.sidebar,text="Multi-Hotel Platform",font=(FONT,9,"bold"),fg=GOLD,bg=SIDEBAR).pack()
            tk.Label(self.sidebar,text="Locality • Choice • Booking",font=(FONT,8),fg=MUTED,bg=SIDEBAR).pack(pady=(2,20))

        def nav_button(self,text,command,danger=False):
            tk.Button(self.sidebar,text=text,command=command,anchor="w",font=(FONT,10,"bold"),fg=RED if danger else TEXT,bg=SIDEBAR,activeforeground=GOLD_LIGHT,activebackground=CARD,relief="flat",bd=0,cursor="hand2").pack(fill="x",padx=10,pady=2,ipady=9)

        def clear_content(self):
            for w in self.content.winfo_children(): w.destroy()

        def page_title(self,title,subtitle=""):
            f=tk.Frame(self.content,bg=BG); f.pack(fill="x",pady=(5,18))
            tk.Label(f,text=title,font=(FONT,23,"bold"),fg=CREAM,bg=BG).pack(anchor="w")
            if subtitle: tk.Label(f,text=subtitle,font=(FONT,10),fg=MUTED,bg=BG).pack(anchor="w",pady=(3,0))

        def card(self,parent):
            return tk.Frame(parent,bg=CARD,highlightbackground="#243552",highlightthickness=1)

        def gold_button(self,parent,text,command):
            return tk.Button(parent,text=text,command=command,font=(FONT,10,"bold"),bg=GOLD,fg="#111111",activebackground=GOLD_LIGHT,relief="flat",cursor="hand2",padx=15,pady=8)

        def dark_button(self,parent,text,command):
            return tk.Button(parent,text=text,command=command,font=(FONT,10,"bold"),bg=CARD2,fg=CREAM,activebackground="#2B3E5D",relief="flat",cursor="hand2",padx=15,pady=8)

        def show_finder(self):
            self.current_page="finder"; self.clear_content()
            self.page_title("Hotel Finder","Select a locality and specifications to find suitable hotels")
            filter_card=self.card(self.content); filter_card.pack(fill="x",pady=(0,15))
            tk.Label(filter_card,text="Locality",fg=MUTED,bg=CARD).grid(row=0,column=0,padx=12,pady=12)
            conn=db(); cur=conn.cursor(); cur.execute("SELECT DISTINCT locality FROM hotels ORDER BY locality"); localities=["All Localities"]+[r[0] for r in cur.fetchall()]
            conn.close()
            locality=ttk.Combobox(filter_card,values=localities,state="readonly",width=18); locality.set("All Localities"); locality.grid(row=0,column=1,padx=5)
            tk.Label(filter_card,text="Max Price/Night",fg=MUTED,bg=CARD).grid(row=0,column=2,padx=12)
            budget=tk.Entry(filter_card,bg=CARD2,fg=WHITE,insertbackground=WHITE,relief="flat",width=12); budget.grid(row=0,column=3,padx=5,ipady=6)
            tk.Label(filter_card,text="Required Facility",fg=MUTED,bg=CARD).grid(row=0,column=4,padx=12)
            facility=ttk.Combobox(filter_card,values=["Any","Wi-Fi","Parking","Restaurant","Pool","Gym","AC"],state="readonly",width=14); facility.set("Any"); facility.grid(row=0,column=5,padx=5)
            tk.Label(filter_card,text="Minimum Rating",fg=MUTED,bg=CARD).grid(row=0,column=6,padx=12)
            rating=ttk.Combobox(filter_card,values=["Any","3.0","3.5","4.0","4.5"],state="readonly",width=10); rating.set("Any"); rating.grid(row=0,column=7,padx=5)
            results=tk.Frame(self.content,bg=BG); results.pack(fill="both",expand=True)
            canvas=tk.Canvas(results,bg=BG,highlightthickness=0); scroll=ttk.Scrollbar(results,orient="vertical",command=canvas.yview); inner=tk.Frame(canvas,bg=BG)
            inner.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all"))); canvas.create_window((0,0),window=inner,anchor="nw"); canvas.configure(yscrollcommand=scroll.set); canvas.pack(side="left",fill="both",expand=True); scroll.pack(side="right",fill="y")

            def run_search():
                for w in inner.winfo_children(): w.destroy()
                conn=db(); cur=conn.cursor()
                sql="""SELECT h.id,h.hotel_name,h.locality,h.city,h.address,h.rating,h.description,h.contact,
                    s.wifi,s.parking,s.restaurant,s.pool,s.gym,s.ac FROM hotels h LEFT JOIN hotel_specs s ON h.id=s.hotel_id WHERE 1=1"""
                params=[]
                if locality.get() != "All Localities":
                    sql += " AND LOWER(TRIM(h.locality))=LOWER(TRIM(?))"; params.append(locality.get())
                if budget.get().strip():
                    try: max_price=float(budget.get()); sql += " AND EXISTS (SELECT 1 FROM rooms rr WHERE rr.hotel_id=h.id AND rr.price<=?)"; params.append(max_price)
                    except ValueError: messagebox.showerror("Invalid Budget","Enter a valid maximum price."); conn.close(); return
                if rating.get() != "Any": sql += " AND h.rating>=?"; params.append(float(rating.get()))
                fmap={"Wi-Fi":"wifi","Parking":"parking","Restaurant":"restaurant","Pool":"pool","Gym":"gym","AC":"ac"}
                if facility.get() in fmap: sql += f" AND s.{fmap[facility.get()]}=1"
                sql += " ORDER BY h.rating DESC,h.hotel_name"
                cur.execute(sql,params); rows=cur.fetchall(); conn.close()
                if not rows: tk.Label(inner,text="No hotels match the selected specifications.",font=(FONT,12,"bold"),fg=MUTED,bg=BG).pack(pady=50); return
                for i,row in enumerate(rows): self.hotel_result_card(inner,row,i)
            self.gold_button(filter_card,"SEARCH HOTELS",run_search).grid(row=0,column=8,padx=15)
            self.dark_button(filter_card,"RESET",lambda: self.show_finder()).grid(row=0,column=9,padx=5)
            run_search()

        def hotel_result_card(self,parent,row,index):
            hid,name,locality,city,address,rating,desc,contact,wifi,parking,restaurant,pool,gym,ac=row
            frame=self.card(parent); frame.grid(row=index,column=0,sticky="ew",padx=5,pady=8); parent.columnconfigure(0,weight=1)
            left=tk.Frame(frame,bg=CARD); left.pack(side="left",fill="both",expand=True,padx=20,pady=16)
            tk.Label(left,text=name,font=(FONT,17,"bold"),fg=GOLD_LIGHT,bg=CARD).pack(anchor="w")
            tk.Label(left,text=f"{locality}, {city}   •   ★ {rating:.1f}",font=(FONT,10,"bold"),fg=CREAM,bg=CARD).pack(anchor="w",pady=(4,2))
            tk.Label(left,text=address,font=(FONT,9),fg=MUTED,bg=CARD).pack(anchor="w")
            tk.Label(left,text=desc or "",font=(FONT,9),fg=TEXT,bg=CARD,wraplength=700,justify="left").pack(anchor="w",pady=(8,4))
            specs=[]
            for label,val in [("Wi-Fi",wifi),("Parking",parking),("Restaurant",restaurant),("Pool",pool),("Gym",gym),("AC",ac)]:
                if val: specs.append(label)
            tk.Label(left,text="Facilities: "+(", ".join(specs) if specs else "Basic"),font=(FONT,9,"bold"),fg=GREEN,bg=CARD).pack(anchor="w")
            right=tk.Frame(frame,bg=CARD); right.pack(side="right",padx=20,pady=18)
            conn=db(); cur=conn.cursor(); cur.execute("SELECT MIN(price),MAX(price) FROM rooms WHERE hotel_id=?",(hid,)); pr=cur.fetchone(); conn.close()
            if pr[0] is not None: tk.Label(right,text=f"₹{pr[0]:,.0f} - ₹{pr[1]:,.0f}",font=(FONT,15,"bold"),fg=CREAM,bg=CARD).pack(pady=(0,8))
            self.gold_button(right,"VIEW & BOOK",lambda h=hid:self.show_hotel_detail(h)).pack()

        def show_hotel_detail(self,hotel_id):
            self.current_page="hotel_detail"; self.clear_content(); conn=db(); cur=conn.cursor()
            cur.execute("""SELECT h.hotel_name,h.locality,h.city,h.address,h.rating,h.description,h.contact,
                s.wifi,s.parking,s.restaurant,s.pool,s.gym,s.ac FROM hotels h JOIN hotel_specs s ON h.id=s.hotel_id WHERE h.id=?""",(hotel_id,)); h=cur.fetchone()
            if not h: conn.close(); return
            self.page_title(h[0],f"{h[1]}, {h[2]}  •  ★ {h[4]:.1f}")
            info=self.card(self.content); info.pack(fill="x",pady=(0,15)); tk.Label(info,text=h[5] or "",font=(FONT,10),fg=TEXT,bg=CARD,wraplength=900,justify="left").pack(anchor="w",padx=20,pady=12); tk.Label(info,text=f"Address: {h[3]}    Contact: {h[6]}",fg=MUTED,bg=CARD).pack(anchor="w",padx=20,pady=(0,12))
            specs=[("Wi-Fi",h[7]),("Parking",h[8]),("Restaurant",h[9]),("Pool",h[10]),("Gym",h[11]),("AC",h[12])]
            tk.Label(info,text="Facilities: "+"  •  ".join(x for x,v in specs if v),fg=GREEN,bg=CARD,font=(FONT,10,"bold")).pack(anchor="w",padx=20,pady=(0,15))
            tk.Label(self.content,text="Available Rooms",font=(FONT,15,"bold"),fg=CREAM,bg=BG).pack(anchor="w",pady=(5,8))
            table=self.card(self.content); table.pack(fill="both",expand=True); cols=("ID","Room","Type","Capacity","Price/Night","Status")
            tree=ttk.Treeview(table,columns=cols,show="headings")
            for c in cols: tree.heading(c,text=c); tree.column(c,anchor="center",width=120)
            tree.pack(fill="both",expand=True,padx=15,pady=15)
            cur.execute("SELECT id,room_number,room_type,capacity,price,status FROM rooms WHERE hotel_id=? ORDER BY room_number",(hotel_id,));
            for r in cur.fetchall(): tree.insert("","end",values=(r[0],r[1],r[2],r[3],f"₹{r[4]:,.0f}",r[5]))
            conn.close()
            def book():
                sel=tree.selection()
                if not sel: messagebox.showwarning("Select Room","Select an available room first."); return
                vals=tree.item(sel[0])["values"]
                if vals[5] != "Available": messagebox.showwarning("Unavailable","Selected room is not available."); return
                self.show_reservations(preselected_hotel=hotel_id,preselected_room=int(vals[0]))
            self.gold_button(table,"BOOK SELECTED ROOM",book).pack(pady=(0,15))

        def show_hotels(self):
            self.current_page="hotels"; self.clear_content(); self.page_title("Hotels & Specifications","Add hotels and define the facilities shown to users")
            form=self.card(self.content); form.pack(fill="x",pady=(0,15))
            fields=[("Hotel Name",0),("Locality",1),("City",2),("Address",3),("Rating",4),("Contact",5),("Description",6)]
            ent={}
            for label,row in fields:
                tk.Label(form,text=label,fg=MUTED,bg=CARD).grid(row=row,column=0,padx=15,pady=5,sticky="w")
                e=tk.Entry(form,bg=CARD2,fg=WHITE,insertbackground=WHITE,relief="flat"); e.grid(row=row,column=1,padx=5,pady=5,ipady=5,sticky="ew"); ent[label]=e
            form.columnconfigure(1,weight=1)
            checks={}; names=["Wi-Fi","Parking","Restaurant","Pool","Gym","AC"]
            for i,n in enumerate(names):
                v=tk.IntVar(value=0); tk.Checkbutton(form,text=n,variable=v,bg=CARD,fg=TEXT,selectcolor=CARD2,activebackground=CARD,activeforeground=WHITE).grid(row=0,column=2+i%3,padx=5,pady=5); checks[n]=v
            def add():
                try:
                    name=ent["Hotel Name"].get().strip(); locality=ent["Locality"].get().strip(); city=ent["City"].get().strip(); rating=float(ent["Rating"].get() or 0)
                    if not name or not locality or not city or rating<0 or rating>5: raise ValueError
                    conn=db(); cur=conn.cursor(); cur.execute("INSERT INTO hotels(hotel_name,locality,city,address,rating,description,contact) VALUES(?,?,?,?,?,?,?)",(name,locality,city,ent["Address"].get(),rating,ent["Description"].get(),ent["Contact"].get())); hid=cur.lastrowid
                    cur.execute("INSERT INTO hotel_specs VALUES(?,?,?,?,?,?,?)",(hid,checks["Wi-Fi"].get(),checks["Parking"].get(),checks["Restaurant"].get(),checks["Pool"].get(),checks["Gym"].get(),checks["AC"].get())); conn.commit(); conn.close(); messagebox.showinfo("Success","Hotel added successfully."); self.show_hotels()
                except ValueError: messagebox.showerror("Invalid Details","Enter hotel name, locality, city and a rating from 0 to 5.")
            self.gold_button(form,"+ ADD HOTEL",add).grid(row=7,column=0,columnspan=2,pady=12)
            table=self.card(self.content); table.pack(fill="both",expand=True); cols=("ID","Hotel","Locality","City","Rating","Facilities","Contact")
            tree=ttk.Treeview(table,columns=cols,show="headings")
            for c in cols: tree.heading(c,text=c); tree.column(c,anchor="center",width=120)
            tree.pack(fill="both",expand=True,padx=15,pady=15)
            conn=db(); cur=conn.cursor(); cur.execute("""SELECT h.id,h.hotel_name,h.locality,h.city,h.rating,h.contact,s.wifi,s.parking,s.restaurant,s.pool,s.gym,s.ac FROM hotels h JOIN hotel_specs s ON h.id=s.hotel_id ORDER BY h.id""")
            for r in cur.fetchall():
                fac=", ".join(n for n,v in zip(names,r[6:]) if v); tree.insert("","end",values=(r[0],r[1],r[2],r[3],f"★ {r[4]:.1f}",fac,r[5]))
            conn.close()

        def show_customers(self):
            self.current_page="customers"; self.clear_content(); self.page_title("Guest Management","Register and manage customers")
            form=self.card(self.content); form.pack(fill="x",pady=(0,15)); entries={}
            for i,label in enumerate(["Name","Phone","Email","Address"]):
                tk.Label(form,text=label,fg=MUTED,bg=CARD).grid(row=i,column=0,padx=15,pady=7,sticky="w"); e=tk.Entry(form,bg=CARD2,fg=WHITE,insertbackground=WHITE,relief="flat"); e.grid(row=i,column=1,padx=5,pady=7,ipady=6,sticky="ew"); entries[label]=e
            form.columnconfigure(1,weight=1)
            def add():
                if not entries["Name"].get().strip() or not entries["Phone"].get().strip(): messagebox.showwarning("Required","Name and phone are required."); return
                conn=db(); conn.execute("INSERT INTO customers(name,phone,email,address) VALUES(?,?,?,?)",tuple(entries[x].get().strip() for x in ["Name","Phone","Email","Address"])); conn.commit(); conn.close(); self.show_customers()
            self.gold_button(form,"+ ADD GUEST",add).grid(row=0,column=2,rowspan=2,padx=20)
            table=self.card(self.content); table.pack(fill="both",expand=True); cols=("ID","Name","Phone","Email","Address"); tree=ttk.Treeview(table,columns=cols,show="headings")
            for c in cols: tree.heading(c,text=c); tree.column(c,width=150)
            tree.pack(fill="both",expand=True,padx=15,pady=15); conn=db(); cur=conn.cursor(); cur.execute("SELECT id,name,phone,email,address FROM customers ORDER BY id DESC")
            for r in cur.fetchall(): tree.insert("","end",values=r)
            conn.close()

        def show_rooms(self):
            self.current_page="rooms"; self.clear_content(); self.page_title("Room Management","Manage rooms belonging to each hotel")
            form=self.card(self.content); form.pack(fill="x",pady=(0,15)); conn=db(); cur=conn.cursor(); cur.execute("SELECT id,hotel_name FROM hotels ORDER BY hotel_name"); hotels=cur.fetchall(); conn.close()
            tk.Label(form,text="Hotel",fg=MUTED,bg=CARD).grid(row=0,column=0,padx=12,pady=12); hotel=ttk.Combobox(form,values=[f"{x[0]} - {x[1]}" for x in hotels],state="readonly",width=28); hotel.grid(row=0,column=1,padx=5)
            tk.Label(form,text="Room No.",fg=MUTED,bg=CARD).grid(row=0,column=2,padx=10); number=tk.Entry(form,bg=CARD2,fg=WHITE,insertbackground=WHITE,relief="flat",width=10); number.grid(row=0,column=3,padx=5,ipady=6)
            tk.Label(form,text="Type",fg=MUTED,bg=CARD).grid(row=0,column=4,padx=10); rtype=ttk.Combobox(form,values=["Single","Double","Standard","Deluxe","Suite","Family"],state="readonly",width=12); rtype.grid(row=0,column=5,padx=5)
            tk.Label(form,text="Capacity",fg=MUTED,bg=CARD).grid(row=0,column=6,padx=10); cap=tk.Entry(form,bg=CARD2,fg=WHITE,insertbackground=WHITE,relief="flat",width=7); cap.grid(row=0,column=7,padx=5,ipady=6)
            tk.Label(form,text="Price",fg=MUTED,bg=CARD).grid(row=0,column=8,padx=10); price=tk.Entry(form,bg=CARD2,fg=WHITE,insertbackground=WHITE,relief="flat",width=10); price.grid(row=0,column=9,padx=5,ipady=6)
            def add():
                try:
                    hid=int(hotel.get().split(" - ")[0]); c=int(cap.get()); p=float(price.get()); rn=number.get().strip(); rt=rtype.get()
                    if not rn or not rt or c<1 or p<=0: raise ValueError
                    conn=db(); conn.execute("INSERT INTO rooms(hotel_id,room_number,room_type,price,capacity) VALUES(?,?,?,?,?)",(hid,rn,rt,p,c)); conn.commit(); conn.close(); self.show_rooms()
                except: messagebox.showerror("Error","Enter valid room details and select a hotel.")
            self.gold_button(form,"+ ADD ROOM",add).grid(row=0,column=10,padx=15)
            table=self.card(self.content); table.pack(fill="both",expand=True); cols=("ID","Hotel","Room","Type","Capacity","Price","Status"); tree=ttk.Treeview(table,columns=cols,show="headings")
            for c in cols: tree.heading(c,text=c); tree.column(c,anchor="center",width=120)
            tree.pack(fill="both",expand=True,padx=15,pady=15); conn=db(); cur=conn.cursor(); cur.execute("SELECT r.id,h.hotel_name,r.room_number,r.room_type,r.capacity,r.price,r.status FROM rooms r JOIN hotels h ON r.hotel_id=h.id ORDER BY h.hotel_name,r.room_number")
            for r in cur.fetchall(): tree.insert("","end",values=(r[0],r[1],r[2],r[3],r[4],f"₹{r[5]:,.0f}",r[6]))
            conn.close()

        def show_reservations(self,preselected_hotel=None,preselected_room=None):
            self.current_page="reservations"; self.clear_content();
            self.page_title("My Reservations","Book a room and view only reservations belonging to your account")
            form=self.card(self.content); form.pack(fill="x",pady=(0,15)); conn=db(); cur=conn.cursor()
            cur.execute("SELECT id,hotel_name,locality FROM hotels ORDER BY hotel_name"); hotels=cur.fetchall(); conn.close()
            tk.Label(form,text="Hotel",fg=MUTED,bg=CARD).grid(row=0,column=0,padx=12,pady=10)
            hotel=ttk.Combobox(form,values=[f"{x[0]} - {x[1]} ({x[2]})" for x in hotels],state="readonly",width=32); hotel.grid(row=0,column=1,padx=5)
            tk.Label(form,text="Room",fg=MUTED,bg=CARD).grid(row=0,column=2,padx=12)
            room=ttk.Combobox(form,state="readonly",width=34); room.grid(row=0,column=3,padx=5)
            tk.Label(form,text="Check-in",fg=MUTED,bg=CARD).grid(row=1,column=0,padx=12,pady=10)
            cin=tk.Entry(form,bg=CARD2,fg=WHITE,insertbackground=WHITE,relief="flat"); cin.insert(0,datetime.now().strftime("%Y-%m-%d")); cin.grid(row=1,column=1,padx=5,ipady=6)
            tk.Label(form,text="Check-out",fg=MUTED,bg=CARD).grid(row=1,column=2,padx=12)
            cout=tk.Entry(form,bg=CARD2,fg=WHITE,insertbackground=WHITE,relief="flat"); cout.grid(row=1,column=3,padx=5,ipady=6)
            total_label=tk.Label(form,text="TOTAL: ₹0",font=(FONT,13,"bold"),fg=GOLD_LIGHT,bg=CARD); total_label.grid(row=2,column=1,columnspan=2,pady=10)
            rooms_cache=[]
            def load_rooms(event=None):
                nonlocal rooms_cache
                if not hotel.get(): return
                hid=int(hotel.get().split(" - ")[0]); conn=db(); cur=conn.cursor()
                cur.execute("SELECT id,room_number,room_type,price,capacity,status FROM rooms WHERE hotel_id=? AND status='Available' ORDER BY room_number",(hid,))
                rooms_cache=cur.fetchall(); conn.close()
                room["values"]=[f"{r[0]} - Room {r[1]} - {r[2]} - ₹{r[3]:,.0f} (up to {r[4]})" for r in rooms_cache]; room.set("")
            hotel.bind("<<ComboboxSelected>>",load_rooms)
            if preselected_hotel:
                for x in hotels:
                    if x[0]==preselected_hotel: hotel.set(f"{x[0]} - {x[1]} ({x[2]})"); break
                load_rooms()
                if preselected_room:
                    for r in rooms_cache:
                        if r[0]==preselected_room: room.set(f"{r[0]} - Room {r[1]} - {r[2]} - ₹{r[3]:,.0f} (up to {r[4]})"); break
            def calculate(show_error=True):
                try:
                    rid=int(room.get().split(" - ")[0]); selected=next(r for r in rooms_cache if r[0]==rid)
                    start=datetime.strptime(cin.get(),"%Y-%m-%d"); end=datetime.strptime(cout.get(),"%Y-%m-%d"); nights=(end-start).days
                    if nights<=0: raise ValueError("Check-out must be after check-in.")
                    total=nights*selected[3]; total_label.config(text=f"{nights} NIGHT(S)  •  TOTAL: ₹{total:,.2f}"); return nights,total,selected
                except Exception as e:
                    if show_error: messagebox.showerror("Invalid Booking",str(e))
                    return None
            def book():
                if not hotel.get() or not room.get(): messagebox.showwarning("Required","Select a hotel and available room."); return
                result=calculate()
                if not result: return
                nights,total,selected=result; hid=int(hotel.get().split(" - ")[0]); rid=selected[0]
                conn=db(); cur=conn.cursor()
                # Re-check ownership and room availability in the database before inserting.
                cur.execute("SELECT status,hotel_id FROM rooms WHERE id=?",(rid,)); room_row=cur.fetchone()
                if not room_row or room_row[0] != "Available" or room_row[1] != hid:
                    conn.close(); messagebox.showerror("Room Unavailable","That room is no longer available. Please select another room."); self.show_reservations(); return
                cur.execute("INSERT INTO reservations(customer_id,room_id,hotel_id,check_in,check_out,nights,total,status) VALUES(?,?,?,?,?,?,?, 'Booked')",(self.customer_id,rid,hid,cin.get(),cout.get(),nights,total))
                res_id=cur.lastrowid; cur.execute("UPDATE rooms SET status='Booked' WHERE id=? AND status='Available'",(rid,)); conn.commit(); conn.close()
                update_hotel_customer_summary()
                messagebox.showinfo("Reservation Confirmed",f"Booking #{res_id} created successfully.\n\nTotal: ₹{total:,.2f}"); self.show_reservations()
            self.dark_button(form,"CALCULATE",calculate).grid(row=3,column=1,pady=10); self.gold_button(form,"CONFIRM BOOKING",book).grid(row=3,column=3,pady=10)
            table=self.card(self.content); table.pack(fill="both",expand=True); cols=("ID","Hotel","Room","Check-in","Check-out","Nights","Amount","Status"); tree=ttk.Treeview(table,columns=cols,show="headings",height=9)
            for c in cols: tree.heading(c,text=c); tree.column(c,anchor="center",width=115)
            tree.pack(fill="both",expand=True,padx=15,pady=15)
            conn=db(); cur=conn.cursor()
            cur.execute("""SELECT r.id,h.hotel_name,rm.room_number,r.check_in,r.check_out,r.nights,r.total,r.status
                           FROM reservations r JOIN hotels h ON r.hotel_id=h.id JOIN customers c ON r.customer_id=c.id JOIN rooms rm ON r.room_id=rm.id
                           WHERE c.user_id=? ORDER BY r.id DESC""",(self.user_id,))
            for r in cur.fetchall(): tree.insert("","end",values=(*r[:6],f"₹{r[6]:,.2f}",r[7]))
            conn.close()
            def cancel():
                sel=tree.selection()
                if not sel: messagebox.showwarning("Select Booking","Select one of your reservations first."); return
                rid=int(tree.item(sel[0])["values"][0]); status=tree.item(sel[0])["values"][7]
                if status!="Booked": messagebox.showwarning("Already Cancelled","This reservation is already cancelled."); return
                if not messagebox.askyesno("Cancel Reservation",f"Cancel your reservation #{rid}?"): return
                conn=db(); cur=conn.cursor()
                cur.execute("""SELECT r.room_id FROM reservations r JOIN customers c ON r.customer_id=c.id
                               WHERE r.id=? AND c.user_id=? AND r.status='Booked'""",(rid,self.user_id)); x=cur.fetchone()
                if not x:
                    conn.close(); messagebox.showerror("Access Denied","This reservation does not belong to your account."); return
                cur.execute("UPDATE reservations SET status='Cancelled' WHERE id=? AND customer_id=? AND status='Booked'",(rid,self.customer_id))
                cur.execute("UPDATE rooms SET status='Available' WHERE id=?",(x[0],)); conn.commit(); conn.close(); update_hotel_customer_summary(); self.show_reservations()
            action_row=tk.Frame(table,bg=CARD); action_row.pack(fill="x",padx=15,pady=(0,15))
            self.gold_button(action_row,"CANCEL MY SELECTED BOOKING",cancel).pack(side="left")
            tk.Label(action_row,text="Select a Booked reservation above, then click Cancel.",fg=MUTED,bg=CARD,font=(FONT,9)).pack(side="left",padx=12)

        def show_cancel_reservation(self):
            """Show a dedicated page for cancelling the logged-in customer's bookings."""
            self.current_page="cancel"
            self.clear_content()
            self.page_title("Cancel Reservation", "Select one of your active bookings and cancel it")

            card=self.card(self.content)
            card.pack(fill="both", expand=True)

            info=tk.Frame(card,bg=CARD)
            info.pack(fill="x",padx=15,pady=(15,5))
            tk.Label(info,text="Your active reservations",font=(FONT,13,"bold"),fg=GOLD_LIGHT,bg=CARD).pack(anchor="w")
            tk.Label(info,text="Only reservations belonging to your account are shown.",font=(FONT,9),fg=MUTED,bg=CARD).pack(anchor="w",pady=(3,10))

            table_frame=tk.Frame(card,bg=CARD)
            table_frame.pack(fill="x",padx=15,pady=5)
            cols=("ID","Hotel","Room","Check-in","Check-out","Nights","Amount","Status")
            tree=ttk.Treeview(table_frame,columns=cols,show="headings",height=6)
            widths={"ID":70,"Hotel":180,"Room":110,"Check-in":110,"Check-out":110,"Nights":80,"Amount":110,"Status":100}
            for c in cols:
                tree.heading(c,text=c)
                tree.column(c,anchor="center",width=widths.get(c,110))
            yscroll=ttk.Scrollbar(table_frame,orient="vertical",command=tree.yview)
            tree.configure(yscrollcommand=yscroll.set)
            tree.pack(side="left",fill="both",expand=True)
            yscroll.pack(side="right",fill="y")

            conn=db(); cur=conn.cursor()
            cur.execute("""SELECT r.id,h.hotel_name,rm.room_number,r.check_in,r.check_out,r.nights,r.total,r.status
                           FROM reservations r
                           JOIN hotels h ON r.hotel_id=h.id
                           JOIN rooms rm ON r.room_id=rm.id
                           JOIN customers c ON r.customer_id=c.id
                           WHERE c.user_id=?
                           ORDER BY r.id DESC""",(self.user_id,))
            rows=cur.fetchall()
            conn.close()
            for r in rows:
                tree.insert("","end",values=(*r[:6],f"₹{r[6]:,.2f}",r[7]))

            def cancel_selected():
                selected=tree.selection()
                if not selected:
                    messagebox.showwarning("Select Booking","Please select a Booked reservation to cancel.")
                    return
                values=tree.item(selected[0],"values")
                rid=int(values[0])
                status=str(values[7])
                if status != "Booked":
                    messagebox.showwarning("Already Cancelled","This reservation is already cancelled.")
                    return
                if not messagebox.askyesno("Confirm Cancellation",f"Are you sure you want to cancel reservation #{rid}?"):
                    return

                conn=db(); cur=conn.cursor()
                # DB-level ownership check: a customer can cancel only their own booking.
                cur.execute("""SELECT r.room_id
                               FROM reservations r
                               JOIN customers c ON r.customer_id=c.id
                               WHERE r.id=? AND c.user_id=? AND r.status='Booked'""",(rid,self.user_id))
                booking=cur.fetchone()
                if not booking:
                    conn.close()
                    messagebox.showerror("Cancellation Failed","This reservation is not available for cancellation.")
                    self.show_cancel_reservation()
                    return

                cur.execute("UPDATE reservations SET status='Cancelled' WHERE id=? AND status='Booked'",(rid,))
                if cur.rowcount != 1:
                    conn.rollback()
                    conn.close()
                    messagebox.showerror("Cancellation Failed","The reservation could not be cancelled.")
                    self.show_cancel_reservation()
                    return
                cur.execute("UPDATE rooms SET status='Available' WHERE id=?",(booking[0],))
                conn.commit(); conn.close()
                update_hotel_customer_summary()
                messagebox.showinfo("Reservation Cancelled",f"Reservation #{rid} has been cancelled successfully.")
                self.show_cancel_reservation()

            action=tk.Frame(card,bg=CARD)
            action.pack(fill="x",padx=15,pady=(8,15))
            self.gold_button(action,"CANCEL SELECTED RESERVATION",cancel_selected).pack(side="left")
            self.dark_button(action,"BACK TO MY RESERVATIONS",self.show_reservations).pack(side="left",padx=10)

        def show_billing(self):
            self.current_page="billing"; self.clear_content(); self.page_title("My Bill / Invoice","Generate an invoice only for one of your reservations")
            top=self.card(self.content); top.pack(fill="x",pady=(0,15))
            tk.Label(top,text="My Reservation ID",fg=MUTED,bg=CARD).pack(side="left",padx=20)
            rid=tk.Entry(top,bg=CARD2,fg=WHITE,insertbackground=WHITE,relief="flat"); rid.pack(side="left",padx=5,pady=12,ipady=6)
            area=self.card(self.content); area.pack(fill="both",expand=True); text=tk.Text(area,bg=CARD,fg=CREAM,font=("Courier New",11),relief="flat"); text.pack(fill="both",expand=True,padx=25,pady=25); text.config(state="disabled")
            def generate():
                try: reservation_id=int(rid.get())
                except: messagebox.showerror("Error","Enter a valid reservation ID."); return
                conn=db(); cur=conn.cursor(); cur.execute("""SELECT r.id,h.hotel_name,h.locality,c.name,c.phone,c.email,rm.room_number,rm.room_type,rm.price,r.check_in,r.check_out,r.nights,r.total,r.status
                    FROM reservations r JOIN hotels h ON r.hotel_id=h.id JOIN customers c ON r.customer_id=c.id JOIN rooms rm ON r.room_id=rm.id
                    WHERE r.id=? AND c.user_id=?""",(reservation_id,self.user_id)); d=cur.fetchone(); conn.close()
                if not d: messagebox.showerror("Not Found","That reservation was not found in your account."); return
                invoice=f"""============================================================\n                    {d[1].upper()}\n              {d[2]}  •  HOTEL RESERVATION\n============================================================\n                    RESERVATION INVOICE\n\nReservation ID : #{d[0]}\nStatus         : {d[13]}\nHotel          : {d[1]}\nLocality       : {d[2]}\n\nGuest Name     : {d[3]}\nPhone          : {d[4]}\nEmail          : {d[5] or 'N/A'}\n\nRoom Number    : {d[6]}\nRoom Type      : {d[7]}\nCheck-in       : {d[9]}\nCheck-out      : {d[10]}\nNumber of Nights: {d[11]}\n\nRoom Rate      : ₹{d[8]:,.2f} / night\nTOTAL AMOUNT   : ₹{d[12]:,.2f}\n\n============================================================\n                 Thank you for your booking!\n============================================================\n"""
                text.config(state="normal"); text.delete("1.0",tk.END); text.insert("1.0",invoice); text.config(state="disabled")
            def save():
                content=text.get("1.0",tk.END).strip()
                if not content: messagebox.showwarning("No Invoice","Generate an invoice first."); return
                filename=f"invoice_{rid.get()}.txt"
                try:
                    with open(os.path.join(BASE_DIR,filename),"w",encoding="utf-8") as f: f.write(content)
                    messagebox.showinfo("Saved",f"Invoice saved as:\n{os.path.join(BASE_DIR,filename)}")
                except Exception as e: messagebox.showerror("Error",str(e))
            self.gold_button(top,"GENERATE MY INVOICE",generate).pack(side="left",padx=10); self.dark_button(top,"SAVE INVOICE",save).pack(side="left",padx=5)

        def show_dashboard(self):
            self.show_finder()

        def refresh_current(self):
            pages={"finder":self.show_finder,"reservations":self.show_reservations,"cancel":self.show_cancel_reservation,"billing":self.show_billing,"hotel_detail":self.show_finder}
            pages.get(self.current_page,self.show_finder)()

        def logout(self):
            if not messagebox.askyesno("Logout","Are you sure you want to logout?"): return
            self.root.destroy(); root=tk.Tk(); LoginWindow(root); root.mainloop()


    if __name__ == "__main__":
        initialize_database()
        root=tk.Tk()
        LoginWindow(root)
        root.mainloop()
except SystemExit:
    raise
except Exception:
    _show_startup_error(_error_traceback.format_exc())
