from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import re
from functools import wraps

app = Flask(__name__)
app.secret_key = "alif123"

DATABASE = "mahasiswa.db"

# ==================================================
# OOP
# ==================================================

class Mahasiswa:

    def __init__(self, nim, nama, prodi, ipk):
        self.__nim = nim
        self.__nama = nama
        self.__prodi = prodi
        self.__ipk = ipk

    @property
    def nim(self):
        return self.__nim

    @property
    def nama(self):
        return self.__nama

    @property
    def prodi(self):
        return self.__prodi

    @property
    def ipk(self):
        return self.__ipk

    def tampilkan(self):
        return self.nama


class MahasiswaAktif(Mahasiswa):

    def tampilkan(self):
        return f"Mahasiswa Aktif : {self.nama}"


# ==================================================
# DATABASE
# ==================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS mahasiswa(
        nim TEXT PRIMARY KEY,
        nama TEXT NOT NULL,
        prodi TEXT NOT NULL,
        ipk REAL NOT NULL
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ==================================================
# LOGIN
# ==================================================

ADMIN_USER = "admin"
ADMIN_PASS = "12345"


def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user" not in session:
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated_function


# ==================================================
# SEARCHING
# ==================================================

def linear_search(data, keyword):

    hasil = []

    for row in data:

        if keyword.lower() in row["nama"].lower():
            hasil.append(row)

    return hasil


def binary_search(data, nim):

    left = 0
    right = len(data) - 1

    while left <= right:

        mid = (left + right) // 2

        if data[mid]["nim"] == nim:
            return data[mid]

        elif data[mid]["nim"] < nim:
            left = mid + 1

        else:
            right = mid - 1

    return None


# ==================================================
# SORTING
# ==================================================

def bubble_sort(data):

    data = list(data)

    n = len(data)

    for i in range(n):

        for j in range(0, n - i - 1):

            if data[j]["nama"] > data[j + 1]["nama"]:

                data[j], data[j + 1] = \
                    data[j + 1], data[j]

    return data


def selection_sort(data):

    data = list(data)

    n = len(data)

    for i in range(n):

        min_idx = i

        for j in range(i + 1, n):

            if data[j]["ipk"] < data[min_idx]["ipk"]:

                min_idx = j

        data[i], data[min_idx] = \
            data[min_idx], data[i]

    return data


# ==================================================
# LOGIN PAGE
# ==================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USER and password == ADMIN_PASS:

            session["user"] = username

            return redirect(url_for("dashboard"))

        flash("Username atau Password salah")

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ==================================================
# DASHBOARD
# ==================================================

@app.route("/")
@login_required
def dashboard():

    conn = get_db()

    data = conn.execute(
        "SELECT * FROM mahasiswa"
    ).fetchall()

    total = len(data)

    rata_ipk = 0

    if total > 0:
        rata_ipk = round(
            sum(row["ipk"] for row in data) / total,
            2
        )

    conn.close()

    return render_template(
        "dashboard.html",
        data=data,
        total=total,
        rata_ipk=rata_ipk
    )


# ==================================================
# TAMBAH DATA
# ==================================================

@app.route("/tambah", methods=["POST"])
@login_required
def tambah():

    try:

        nim = request.form["nim"]
        nama = request.form["nama"]
        prodi = request.form["prodi"]
        ipk = float(request.form["ipk"])

        if not re.match(r"^\d{12}$", nim):
            raise ValueError(
                "NIM harus 12 digit angka"
            )

        if not re.match(
                r"^[A-Za-z ]+$",
                nama):
            raise ValueError(
                "Nama hanya boleh huruf"
            )

        if ipk < 0 or ipk > 4:
            raise ValueError(
                "IPK harus antara 0 sampai 4"
            )

        mhs = MahasiswaAktif(
            nim,
            nama,
            prodi,
            ipk
        )

        conn = get_db()

        conn.execute(
            """
            INSERT INTO mahasiswa
            VALUES (?, ?, ?, ?)
            """,
            (
                mhs.nim,
                mhs.nama,
                mhs.prodi,
                mhs.ipk
            )
        )

        conn.commit()
        conn.close()

        flash("Data berhasil ditambahkan")

    except Exception as e:

        flash(str(e))

    return redirect(url_for("dashboard"))


# ==================================================
# HAPUS
# ==================================================

@app.route("/hapus/<nim>")
@login_required
def hapus(nim):

    conn = get_db()

    conn.execute(
        "DELETE FROM mahasiswa WHERE nim=?",
        (nim,)
    )

    conn.commit()
    conn.close()

    flash("Data berhasil dihapus")

    return redirect(url_for("dashboard"))


# ==================================================
# EDIT
# ==================================================

@app.route("/edit/<nim>", methods=["POST"])
@login_required
def edit(nim):

    try:

        nama = request.form["nama"]
        prodi = request.form["prodi"]
        ipk = float(request.form["ipk"])

        conn = get_db()

        conn.execute(
            """
            UPDATE mahasiswa
            SET nama=?,
                prodi=?,
                ipk=?
            WHERE nim=?
            """,
            (
                nama,
                prodi,
                ipk,
                nim
            )
        )

        conn.commit()
        conn.close()

        flash("Data berhasil diupdate")

    except Exception as e:

        flash(str(e))

    return redirect(url_for("dashboard"))


# ==================================================
# SEARCH
# ==================================================

@app.route("/search")
@login_required
def search():

    keyword = request.args.get(
        "keyword",
        ""
    )

    conn = get_db()

    data = conn.execute(
        "SELECT * FROM mahasiswa"
    ).fetchall()

    conn.close()

    hasil = linear_search(
        data,
        keyword
    )

    return render_template(
        "dashboard.html",
        data=hasil,
        total=len(hasil),
        rata_ipk=0
    )


# ==================================================
# SORT NAMA
# ==================================================

@app.route("/sort/nama")
@login_required
def sort_nama():

    conn = get_db()

    data = conn.execute(
        "SELECT * FROM mahasiswa"
    ).fetchall()

    conn.close()

    hasil = bubble_sort(data)

    return render_template(
        "dashboard.html",
        data=hasil,
        total=len(hasil),
        rata_ipk=0
    )


# ==================================================
# SORT IPK
# ==================================================

@app.route("/sort/ipk")
@login_required
def sort_ipk():

    conn = get_db()

    data = conn.execute(
        "SELECT * FROM mahasiswa"
    ).fetchall()

    conn.close()

    hasil = selection_sort(data)

    return render_template(
        "dashboard.html",
        data=hasil,
        total=len(hasil),
        rata_ipk=0
    )


# ==================================================
# RUN
# ==================================================

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)