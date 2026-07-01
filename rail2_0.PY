import tkinter as tk
from tkinter import messagebox, ttk
import oracledb

# ============ DATABASE CONNECTION ============
def get_connection():
    oracledb.init_oracle_client(lib_dir=r"C:\instantclient-basiclite-windows.x64-23.26.2.0.0\instantclient_23_0")
    return oracledb.connect(
        user="RAIL",
        password="rail",
        dsn="localhost:1521/xe"
    )

# ============ GENERIC VIEW TABLE WINDOW (with Search/Filter) ============
def view_table(title, base_sql, columns, table_name=None):
    """
    title: window title
    base_sql: SQL to fetch all columns (no WHERE clause)
    columns: tuple of column names matching base_sql's SELECT order
    table_name: actual Oracle table name, needed to build the filtered query.
                If None, search box still works as long as base_sql has no WHERE already.
    """
    win = tk.Toplevel()
    win.title(title)
    win.geometry("950x500")
    win.configure(bg="#003366")

    tk.Label(win, text=title, font=("Arial", 14, "bold"),
             bg="#003366", fg="white").pack(pady=10)

    # ---- Search / Filter bar ----
    search_frame = tk.Frame(win, bg="#003366")
    search_frame.pack(pady=5)

    tk.Label(search_frame, text="Search in:", bg="#003366", fg="white",
              font=("Arial", 10)).grid(row=0, column=0, padx=5)

    column_var = tk.StringVar(value=columns[0])
    column_menu = ttk.Combobox(search_frame, textvariable=column_var,
                                values=columns, width=18, state="readonly")
    column_menu.grid(row=0, column=1, padx=5)

    search_entry = tk.Entry(search_frame, font=("Arial", 10), width=25)
    search_entry.grid(row=0, column=2, padx=5)

    tree = ttk.Treeview(win, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=110)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    def load_data(sql, params=None):
        # Clear existing rows
        for item in tree.get_children():
            tree.delete(item)
        try:
            conn = get_connection()
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            for row in cursor.fetchall():
                tree.insert("", "end", values=row)
            cursor.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def run_search():
        keyword = search_entry.get().strip()
        if not keyword:
            load_data(base_sql)
            return
        if not table_name:
            messagebox.showwarning("Search Unavailable",
                                    "Search is not configured for this table yet.")
            return
        col = column_var.get()
        # Wrap base_sql as a subquery so search works regardless of its SELECT list
        filtered_sql = f"SELECT * FROM ({base_sql}) WHERE UPPER({col}) LIKE UPPER(:1)"
        load_data(filtered_sql, [f"%{keyword}%"])

    def clear_search():
        search_entry.delete(0, tk.END)
        load_data(base_sql)

    tk.Button(search_frame, text="Search", font=("Arial", 10, "bold"),
              bg="#0066cc", fg="white", cursor="hand2",
              command=run_search).grid(row=0, column=3, padx=5)

    tk.Button(search_frame, text="Clear", font=("Arial", 10, "bold"),
              bg="#666666", fg="white", cursor="hand2",
              command=clear_search).grid(row=0, column=4, padx=5)

    # Press Enter in the search box to trigger search too
    search_entry.bind("<Return>", lambda event: run_search())

    # Initial load with no filter
    load_data(base_sql)

# ============ GENERIC ADD FORM WINDOW ============
def add_form(title, fields, insert_sql, value_types):
    """
    fields: list of field labels shown to user
    insert_sql: SQL with :1, :2 ... placeholders
    value_types: list of 'int' or 'str' matching fields order
    """
    win = tk.Toplevel()
    win.title(title)
    win.geometry("400x" + str(120 + len(fields) * 55))
    win.configure(bg="#003366")

    tk.Label(win, text=title, font=("Arial", 14, "bold"),
             bg="#003366", fg="white").pack(pady=10)

    entries = []
    for field in fields:
        tk.Label(win, text=field, bg="#003366", fg="white",
                  font=("Arial", 10)).pack()
        entry = tk.Entry(win, font=("Arial", 10), width=28)
        entry.pack(pady=3)
        entries.append(entry)

    def save_record():
        try:
            values = []
            for entry, vtype in zip(entries, value_types):
                val = entry.get()
                if vtype == "int":
                    val = int(val) if val else None
                values.append(val)

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(insert_sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Record added successfully!")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    tk.Button(win, text="SAVE", font=("Arial", 11, "bold"),
              bg="#0066cc", fg="white", width=15, cursor="hand2",
              command=save_record).pack(pady=15)

# ============ GENERIC EDIT / DELETE WINDOW ============
def edit_delete_form(title, table_name, pk_column, fields, select_sql, value_types):
    """
    title: window title
    table_name: actual Oracle table name
    pk_column: primary key column name (used in WHERE clause)
    fields: list of column names matching table, in order, INCLUDING pk_column first
    select_sql: SQL to fetch one row by pk, must use :1 placeholder for pk
    value_types: list of 'int' or 'str' matching fields order (including pk)
    """
    win = tk.Toplevel()
    win.title(title)
    win.geometry("420x" + str(160 + len(fields) * 55))
    win.configure(bg="#003366")

    tk.Label(win, text=title, font=("Arial", 14, "bold"),
             bg="#003366", fg="white").pack(pady=10)

    tk.Label(win, text=f"Enter {pk_column} to load record",
             bg="#003366", fg="white", font=("Arial", 10)).pack()
    pk_entry = tk.Entry(win, font=("Arial", 10), width=28)
    pk_entry.pack(pady=5)

    fields_frame = tk.Frame(win, bg="#003366")
    fields_frame.pack(pady=5)

    entries = {}
    for field in fields:
        tk.Label(fields_frame, text=field, bg="#003366", fg="white",
                  font=("Arial", 10)).pack()
        entry = tk.Entry(fields_frame, font=("Arial", 10), width=28)
        entry.pack(pady=2)
        entries[field] = entry
        if field == pk_column:
            entry.config(state="disabled")  # PK shouldn't be edited directly

    def load_record():
        try:
            pk_val = pk_entry.get()
            if not pk_val:
                messagebox.showwarning("Missing Input", f"Enter a {pk_column} first.")
                return
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(select_sql, [int(pk_val) if value_types[0] == "int" else pk_val])
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if not row:
                messagebox.showwarning("Not Found", f"No record with {pk_column} = {pk_val}")
                return

            for field, val in zip(fields, row):
                entry = entries[field]
                entry.config(state="normal")
                entry.delete(0, tk.END)
                entry.insert(0, str(val) if val is not None else "")
                if field == pk_column:
                    entry.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def update_record():
        try:
            pk_val = pk_entry.get()
            if not pk_val:
                messagebox.showwarning("Missing Input", f"Enter a {pk_column} first.")
                return

            set_clauses = []
            values = []
            for idx, field in enumerate(fields):
                if field == pk_column:
                    continue
                val = entries[field].get()
                if value_types[idx] == "int":
                    val = int(val) if val else None
                set_clauses.append(f"{field} = :{len(values)+1}")
                values.append(val)

            pk_idx = fields.index(pk_column)
            pk_value_typed = int(pk_val) if value_types[pk_idx] == "int" else pk_val
            values.append(pk_value_typed)

            sql = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {pk_column} = :{len(values)}"

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Record updated successfully!")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def delete_record():
        try:
            pk_val = pk_entry.get()
            if not pk_val:
                messagebox.showwarning("Missing Input", f"Enter a {pk_column} first.")
                return

            confirm = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete {table_name} where {pk_column} = {pk_val}?\nThis cannot be undone."
            )
            if not confirm:
                return

            pk_idx = fields.index(pk_column)
            pk_value_typed = int(pk_val) if value_types[pk_idx] == "int" else pk_val

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name} WHERE {pk_column} = :1", [pk_value_typed])
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Record deleted successfully!")
            win.destroy()
        except Exception as e:
            messagebox.showerror(
                "Database Error",
                str(e) + "\n\nTip: if this is a foreign key error, delete related child records first."
            )

    btn_frame = tk.Frame(win, bg="#003366")
    btn_frame.pack(pady=15)

    tk.Button(btn_frame, text="LOAD", font=("Arial", 10, "bold"),
              bg="#666666", fg="white", width=10, cursor="hand2",
              command=load_record).grid(row=0, column=0, padx=5)

    tk.Button(btn_frame, text="UPDATE", font=("Arial", 10, "bold"),
              bg="#0066cc", fg="white", width=10, cursor="hand2",
              command=update_record).grid(row=0, column=1, padx=5)

    tk.Button(btn_frame, text="DELETE", font=("Arial", 10, "bold"),
              bg="#cc0000", fg="white", width=10, cursor="hand2",
              command=delete_record).grid(row=0, column=2, padx=5)

# ============ USERS ============
def view_users():
    view_table("All Users",
        "SELECT USER_ID, FIRST_NAME, MIDDLE_NAME, LAST_NAME, GENDER, AGE, CITY, STATE, PIN_CODE FROM USERS",
        ("USER_ID", "FIRST_NAME", "MIDDLE_NAME", "LAST_NAME", "GENDER", "AGE", "CITY", "STATE", "PIN_CODE"),
        table_name="USERS")

def add_user():
    add_form("Add New User",
        ["USER_ID", "FIRST NAME", "MIDDLE NAME", "LAST NAME", "GENDER", "AGE", "CITY", "STATE", "PIN CODE"],
        """INSERT INTO USERS (USER_ID, FIRST_NAME, MIDDLE_NAME, LAST_NAME, GENDER, AGE, CITY, STATE, PIN_CODE)
           VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)""",
        ["int", "str", "str", "str", "str", "int", "str", "str", "str"])

def edit_delete_user():
    edit_delete_form(
        "Edit / Delete User", "USERS", "USER_ID",
        ["USER_ID", "FIRST_NAME", "MIDDLE_NAME", "LAST_NAME", "GENDER", "AGE", "CITY", "STATE", "PIN_CODE"],
        """SELECT USER_ID, FIRST_NAME, MIDDLE_NAME, LAST_NAME, GENDER, AGE, CITY, STATE, PIN_CODE
           FROM USERS WHERE USER_ID = :1""",
        ["int", "str", "str", "str", "str", "int", "str", "str", "str"])

# ============ USER MOBILE NO ============
def view_mobiles():
    view_table("User Mobile Numbers",
        "SELECT MOBILE_NO, USER_ID FROM USER_MOBILE_NO",
        ("MOBILE_NO", "USER_ID"),
        table_name="USER_MOBILE_NO")

def add_mobile():
    add_form("Add Mobile Number",
        ["MOBILE NO", "USER ID"],
        "INSERT INTO USER_MOBILE_NO (MOBILE_NO, USER_ID) VALUES (:1, :2)",
        ["str", "int"])

# ============ TRAIN ============
def view_trains():
    view_table("All Trains",
        "SELECT TRAIN_NO, TRAIN_NAME, CAPACITY, TRAIN_DESC, DESTINATION, ARRIVAL_TIME FROM TRAIN",
        ("TRAIN_NO", "TRAIN_NAME", "CAPACITY", "TRAIN_DESC", "DESTINATION", "ARRIVAL_TIME"),
        table_name="TRAIN")

def add_train():
    add_form("Add New Train",
        ["TRAIN NO", "TRAIN NAME", "CAPACITY", "DESCRIPTION", "DESTINATION", "ARRIVAL TIME"],
        """INSERT INTO TRAIN (TRAIN_NO, TRAIN_NAME, CAPACITY, TRAIN_DESC, DESTINATION, ARRIVAL_TIME)
           VALUES (:1, :2, :3, :4, :5, :6)""",
        ["int", "str", "int", "str", "str", "str"])

def edit_delete_train():
    edit_delete_form(
        "Edit / Delete Train", "TRAIN", "TRAIN_NO",
        ["TRAIN_NO", "TRAIN_NAME", "CAPACITY", "TRAIN_DESC", "DESTINATION", "ARRIVAL_TIME"],
        """SELECT TRAIN_NO, TRAIN_NAME, CAPACITY, TRAIN_DESC, DESTINATION, ARRIVAL_TIME
           FROM TRAIN WHERE TRAIN_NO = :1""",
        ["int", "str", "int", "str", "str", "str"])

# ============ STATION ============
def view_stations():
    view_table("All Stations",
        "SELECT STATION_NO, NAME, ARRIVAL_TIME, HAULT, DEPARTURE, TRAIN_NO FROM STATION",
        ("STATION_NO", "NAME", "ARRIVAL_TIME", "HAULT", "DEPARTURE", "TRAIN_NO"),
        table_name="STATION")

def add_station():
    add_form("Add New Station",
        ["STATION NO", "NAME", "ARRIVAL TIME", "HAULT", "DEPARTURE", "TRAIN NO"],
        """INSERT INTO STATION (STATION_NO, NAME, ARRIVAL_TIME, HAULT, DEPARTURE, TRAIN_NO)
           VALUES (:1, :2, :3, :4, :5, :6)""",
        ["int", "str", "str", "str", "str", "int"])

# ============ TICKET ============
def view_tickets():
    view_table("All Tickets",
        "SELECT TICKET_ID, NO_OF_PASSENGER, FIRST_NAME, TICKET_PRICE, PNR_NO, TRAIN_NO, USER_ID, STATUS FROM TICKET",
        ("TICKET_ID", "NO_OF_PASSENGER", "FIRST_NAME", "TICKET_PRICE", "PNR_NO", "TRAIN_NO", "USER_ID", "STATUS"),
        table_name="TICKET")

def add_ticket():
    win = tk.Toplevel()
    win.title("Book New Ticket")
    win.geometry("400x560")
    win.configure(bg="#003366")

    tk.Label(win, text="Book New Ticket", font=("Arial", 14, "bold"),
             bg="#003366", fg="white").pack(pady=10)

    fields = ["TICKET ID", "NO OF PASSENGER", "FIRST NAME", "TICKET PRICE",
              "PNR NO", "TRAIN NO", "USER ID"]
    entries = {}
    for field in fields:
        tk.Label(win, text=field, bg="#003366", fg="white",
                  font=("Arial", 10)).pack()
        entry = tk.Entry(win, font=("Arial", 10), width=28)
        entry.pack(pady=3)
        entries[field] = entry

    tk.Label(win, text="STATUS", bg="#003366", fg="white",
              font=("Arial", 10)).pack()
    status_var = tk.StringVar(value="CONFIRMED")
    status_menu = ttk.Combobox(win, textvariable=status_var,
                                values=["CONFIRMED", "RAC", "WAITING"], width=25)
    status_menu.pack(pady=3)

    def save_ticket():
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO TICKET (TICKET_ID, NO_OF_PASSENGER, FIRST_NAME, TICKET_PRICE,
                                     PNR_NO, TRAIN_NO, USER_ID, STATUS)
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
            """, (
                int(entries["TICKET ID"].get()),
                entries["NO OF PASSENGER"].get(),
                entries["FIRST NAME"].get(),
                entries["TICKET PRICE"].get(),
                entries["PNR NO"].get(),
                int(entries["TRAIN NO"].get()),
                int(entries["USER ID"].get()),
                status_var.get()
            ))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Ticket booked successfully!")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    tk.Button(win, text="BOOK TICKET", font=("Arial", 11, "bold"),
              bg="#0066cc", fg="white", width=15, cursor="hand2",
              command=save_ticket).pack(pady=15)

def edit_delete_ticket():
    edit_delete_form(
        "Edit / Delete Ticket", "TICKET", "TICKET_ID",
        ["TICKET_ID", "NO_OF_PASSENGER", "FIRST_NAME", "TICKET_PRICE", "PNR_NO", "TRAIN_NO", "USER_ID", "STATUS"],
        """SELECT TICKET_ID, NO_OF_PASSENGER, FIRST_NAME, TICKET_PRICE, PNR_NO, TRAIN_NO, USER_ID, STATUS
           FROM TICKET WHERE TICKET_ID = :1""",
        ["int", "str", "str", "str", "str", "int", "int", "str"])

# ============ PAYMENT ============
def view_payments():
    view_table("All Payments",
        "SELECT PAY_ID, PAY_DATE, PAY_DESC, PAID_AMT, TICKET_ID, USER_ID FROM PAYMENT",
        ("PAY_ID", "PAY_DATE", "PAY_DESC", "PAID_AMT", "TICKET_ID", "USER_ID"),
        table_name="PAYMENT")

def add_payment():
    add_form("Add New Payment",
        ["PAY ID", "PAY DATE", "PAY DESC", "PAID AMOUNT", "TICKET ID", "USER ID"],
        """INSERT INTO PAYMENT (PAY_ID, PAY_DATE, PAY_DESC, PAID_AMT, TICKET_ID, USER_ID)
           VALUES (:1, :2, :3, :4, :5, :6)""",
        ["int", "str", "str", "str", "int", "int"])

def edit_delete_payment():
    edit_delete_form(
        "Edit / Delete Payment", "PAYMENT", "PAY_ID",
        ["PAY_ID", "PAY_DATE", "PAY_DESC", "PAID_AMT", "TICKET_ID", "USER_ID"],
        """SELECT PAY_ID, PAY_DATE, PAY_DESC, PAID_AMT, TICKET_ID, USER_ID
           FROM PAYMENT WHERE PAY_ID = :1""",
        ["int", "str", "str", "str", "int", "int"])

# ============ BOOKS AND CANCEL ============
def view_books_cancel():
    view_table("Booking / Cancellation Records",
        "SELECT BOOKING_ID, USER_ID, FIRST_NAME, BOOKING_DATE, STATUS FROM BOOKS_AND_CANCEL",
        ("BOOKING_ID", "USER_ID", "FIRST_NAME", "BOOKING_DATE", "STATUS"),
        table_name="BOOKS_AND_CANCEL")

def add_books_cancel():
    win = tk.Toplevel()
    win.title("Add Booking / Cancellation")
    win.geometry("400x450")
    win.configure(bg="#003366")

    tk.Label(win, text="Add Booking / Cancellation", font=("Arial", 14, "bold"),
             bg="#003366", fg="white").pack(pady=10)

    fields = ["BOOKING ID", "USER ID", "FIRST NAME", "BOOKING DATE"]
    entries = {}
    for field in fields:
        tk.Label(win, text=field, bg="#003366", fg="white",
                  font=("Arial", 10)).pack()
        entry = tk.Entry(win, font=("Arial", 10), width=28)
        entry.pack(pady=3)
        entries[field] = entry

    tk.Label(win, text="STATUS", bg="#003366", fg="white",
              font=("Arial", 10)).pack()
    status_var = tk.StringVar(value="BOOKED")
    status_menu = ttk.Combobox(win, textvariable=status_var,
                                values=["BOOKED", "CANCELLED"], width=25)
    status_menu.pack(pady=3)

    def save_record():
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO BOOKS_AND_CANCEL (BOOKING_ID, USER_ID, FIRST_NAME, BOOKING_DATE, STATUS)
                VALUES (:1, :2, :3, :4, :5)
            """, (
                int(entries["BOOKING ID"].get()),
                int(entries["USER ID"].get()),
                entries["FIRST NAME"].get(),
                entries["BOOKING DATE"].get(),
                status_var.get()
            ))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Record added successfully!")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    tk.Button(win, text="SAVE", font=("Arial", 11, "bold"),
              bg="#0066cc", fg="white", width=15, cursor="hand2",
              command=save_record).pack(pady=15)

# ============ TRAVELS_IN ============
def view_travels_in():
    view_table("Travels In Records",
        "SELECT USER_ID, TRAIN_NO FROM TRAVELS_IN",
        ("USER_ID", "TRAIN_NO"),
        table_name="TRAVELS_IN")

def add_travels_in():
    add_form("Add Travels In Record",
        ["USER ID", "TRAIN NO"],
        "INSERT INTO TRAVELS_IN (USER_ID, TRAIN_NO) VALUES (:1, :2)",
        ["int", "int"])

# ============ REACHES ============
def view_reaches():
    view_table("Reaches Records",
        "SELECT TRAIN_NO, ARRIVAL_TIME FROM REACHES",
        ("TRAIN_NO", "ARRIVAL_TIME"),
        table_name="REACHES")

def add_reaches():
    add_form("Add Reaches Record",
        ["TRAIN NO", "ARRIVAL TIME"],
        "INSERT INTO REACHES (TRAIN_NO, ARRIVAL_TIME) VALUES (:1, :2)",
        ["int", "str"])
    add_form("Add Reaches Record",
        ["TRAIN NO", "ARRIVAL TIME"],
        "INSERT INTO REACHES (TRAIN_NO, ARRIVAL_TIME) VALUES (:1, :2)",
        ["int", "str"])

# ============ START_TABLE ============
def view_start():
    view_table("Start Records",
        "SELECT TRAIN_NO, ARRIVAL_TIME FROM START_TABLE",
        ("TRAIN_NO", "ARRIVAL_TIME"),
        table_name="START_TABLE")

def add_start():
    add_form("Add Start Record",
        ["TRAIN NO", "ARRIVAL TIME"],
        "INSERT INTO START_TABLE (TRAIN_NO, ARRIVAL_TIME) VALUES (:1, :2)",
        ["int", "str"])
    add_form("Add Start Record",
        ["TRAIN NO", "ARRIVAL TIME"],
        "INSERT INTO START_TABLE (TRAIN_NO, ARRIVAL_TIME) VALUES (:1, :2)",
        ["int", "str"])

# ============ SHOWS ============
def view_shows():
    view_table("Shows Records",
        "SELECT TICKET_ID, USER_ID FROM SHOWS",
        ("TICKET_ID", "USER_ID"),
        table_name="SHOWS")

def add_shows():
    add_form("Add Shows Record",
        ["TICKET ID", "USER ID"],
        "INSERT INTO SHOWS (TICKET_ID, USER_ID) VALUES (:1, :2)",
        ["int", "int"])

# ============ DASHBOARD ============
def open_dashboard():
    dashboard = tk.Tk()
    dashboard.title("Railway Management System")
    dashboard.geometry("950x650")
    dashboard.configure(bg="#003366")

    tk.Label(dashboard, text="Railway Management System",
             font=("Arial", 18, "bold"), bg="#003366", fg="white").pack(pady=15)

    container = tk.Frame(dashboard, bg="#003366")
    container.pack(pady=10)

    # Each row: Label, View command, Add command, Edit/Delete command (or None)
    sections = [
        ("Users",            view_users,        add_user,           edit_delete_user),
        ("Mobile Numbers",   view_mobiles,       add_mobile,         None),
        ("Trains",           view_trains,        add_train,          edit_delete_train),
        ("Stations",         view_stations,      add_station,        None),
        ("Tickets",          view_tickets,       add_ticket,         edit_delete_ticket),
        ("Payments",         view_payments,      add_payment,        edit_delete_payment),
        ("Books & Cancel",   view_books_cancel,  add_books_cancel,   None),
        ("Travels In",       view_travels_in,    add_travels_in,     None),
        ("Reaches",          view_reaches,       add_reaches,        None),
        ("Start",            view_start,         add_start,          None),
        ("Shows",            view_shows,         add_shows,          None),
    ]

    col_count = 3
    for idx, (label, view_cmd, add_cmd, edit_cmd) in enumerate(sections):
        row = idx // col_count
        col = idx % col_count

        frame = tk.Frame(container, bg="#0a4a8f", padx=10, pady=10)
        frame.grid(row=row, column=col, padx=10, pady=10)

        tk.Label(frame, text=label, font=("Arial", 12, "bold"),
                 bg="#0a4a8f", fg="white").pack(pady=(0, 8))

        tk.Button(frame, text="View " + label, font=("Arial", 10),
                  bg="#0066cc", fg="white", width=18, cursor="hand2",
                  command=view_cmd).pack(pady=3)

        tk.Button(frame, text="Add " + label, font=("Arial", 10),
                  bg="#009933", fg="white", width=18, cursor="hand2",
                  command=add_cmd).pack(pady=3)

        if edit_cmd:
            tk.Button(frame, text="Edit / Delete", font=("Arial", 10),
                      bg="#cc6600", fg="white", width=18, cursor="hand2",
                      command=edit_cmd).pack(pady=3)

    tk.Button(dashboard, text="Exit", font=("Arial", 12, "bold"),
              bg="#cc0000", fg="white", width=15, cursor="hand2",
              command=dashboard.destroy).pack(pady=20)

    dashboard.mainloop()

# ============ LOGIN ============
def login():
    if entry_user.get() == "RAIL" and entry_pass.get() == "rail123":
        login_window.destroy()
        open_dashboard()
    else:
        messagebox.showerror("Error", "Wrong Username or Password!")

login_window = tk.Tk()
login_window.title("Railway Management - Login")
login_window.geometry("400x300")
login_window.configure(bg="#003366")

tk.Label(login_window, text="Railway Management",
         font=("Arial", 16, "bold"), bg="#003366", fg="white").pack(pady=20)

tk.Label(login_window, text="Username", bg="#003366", fg="white",
          font=("Arial", 11)).pack()
entry_user = tk.Entry(login_window, font=("Arial", 11), width=25)
entry_user.pack(pady=5)

tk.Label(login_window, text="Password", bg="#003366", fg="white",
          font=("Arial", 11)).pack()
entry_pass = tk.Entry(login_window, show="*", font=("Arial", 11), width=25)
entry_pass.pack(pady=5)

tk.Button(login_window, text="LOGIN", font=("Arial", 12, "bold"),
          bg="#0066cc", fg="white", width=15, cursor="hand2",
          command=login).pack(pady=20)

login_window.mainloop()