# 🚂 Railway Management System

A Database Management System (DBMS) project built as part of a 4th Semester 
academic curriculum. This project implements a fully functional Railway 
Management System using Oracle SQL Developer for the backend database and 
Python Tkinter for the GUI frontend.

## 📌 Features
- User registration and management
- Train and station management
- Ticket booking, cancellation, and status tracking (Confirmed / RAC / Waiting)
- Payment records management
- Search and filter across all tables
- Full CRUD — Create, Read, Update, Delete operations via GUI

## 🛠️ Tech Stack
| Layer | Technology |
|-------|-----------|
| Database | Oracle XE 11g |
| Query Language | SQL (Oracle SQL Developer) |
| Frontend | Python 3 + Tkinter |
| DB Connector | python-oracledb (Thick Mode) |

## 🗄️ Database Tables
- USERS
- USER_MOBILE_NO
- TRAIN
- STATION
- TICKET
- TICKET_STATUS
- PAYMENT
- BOOKS_AND_CANCEL
- TRAVELS_IN
- REACHES
- START_TABLE
- SHOWS

## ⚙️ Setup Instructions
1. Install Oracle XE 11g and create user `RAIL`
2. Run `railway_management.sql` in SQL Developer to create all tables
3. Install Python dependencies:
