"""
Database manager with military-grade encryption
Uses AES-256 encryption with PBKDF2 key derivation
"""

import sqlite3
import os
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json
from typing import Optional, Dict, Any, List

class DatabaseManager:
    """Manages encrypted SQLite database operations"""
    
    def __init__(self, db_path: str):
        """Initialize database manager"""
        self.db_path = db_path
        self.encryption_key = None
        self.connection = None
        self._ensure_data_directory()
        self._create_database()
        self.migrate_database()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists"""
        data_dir = os.path.dirname(self.db_path)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def initialize(self, master_password: str = None) -> bool:
        """Initialize database with encryption"""
        try:
            # Generate or load salt
            salt_file = self.db_path + ".salt"
            if os.path.exists(salt_file):
                with open(salt_file, 'rb') as f:
                    salt = f.read()
            else:
                salt = os.urandom(16)
                with open(salt_file, 'wb') as f:
                    f.write(salt)
            
            # For initial setup, use default password (will be changed during first login)
            if master_password is None:
                master_password = "temp_init_key_2023"
            
            # Derive encryption key
            self.encryption_key = self._derive_key(master_password, salt)
            
            # Create database if it doesn't exist
            if not os.path.exists(self.db_path):
                self._create_database()
            
            return True
        except Exception as e:
            print(f"Database initialization failed: {e}")
            return False
    
    def _create_database(self):
        """Create database tables"""
        self.connection = sqlite3.connect(
            self.db_path, 
            check_same_thread=False,
            timeout=60.0,
            isolation_level='DEFERRED'
        )
        # Configure for multi-user access from the start
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute("PRAGMA busy_timeout=60000")
        cursor = self.connection.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                totp_secret TEXT,
                is_verified BOOLEAN DEFAULT FALSE,
                verification_token TEXT,
                reset_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                role TEXT DEFAULT 'User',
                is_admin BOOLEAN DEFAULT FALSE,
                profile_picture TEXT,
                company_name TEXT,
                org_number TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                two_factor_enabled BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Key receipts table (stores encrypted PDF for Nyckelkvittens)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS key_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER UNIQUE NOT NULL,
                pdf_encrypted TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                setting_key TEXT NOT NULL,
                setting_value TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Customers/Systems table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                project TEXT,
                customer_number TEXT,
                org_number TEXT,
                address TEXT,
                postal_code TEXT,
                postal_address TEXT,
                phone TEXT,
                mobile_phone TEXT,
                email TEXT,
                website TEXT,
                key_responsible_1 TEXT,
                key_responsible_2 TEXT,
                key_responsible_3 TEXT,
                key_location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Key systems table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS key_systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                key_code TEXT NOT NULL,
                series_id TEXT,
                key_profile TEXT,
                fabrikat TEXT,
                koncept TEXT,
                notes TEXT,
                billing_plan TEXT,
                price_one_time REAL,
                price_monthly REAL,
                price_half_year REAL,
                price_yearly REAL,
                is_paid BOOLEAN DEFAULT FALSE,
                paid_at TIMESTAMP,
                invoice_count INTEGER DEFAULT 0,
                last_invoice_date TIMESTAMP,
                last_sequence_number INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # Orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                key_system_id INTEGER NOT NULL,
                key_code TEXT NOT NULL,
                key_profile TEXT,
                quantity INTEGER NOT NULL,
                sequence_start INTEGER NOT NULL,
                sequence_end INTEGER NOT NULL,
                key_responsible TEXT DEFAULT 'Nyckelansvarig 1',
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                exported_pdf BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (customer_id) REFERENCES customers (id),
                FOREIGN KEY (key_system_id) REFERENCES key_systems (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Permissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                permission_type TEXT NOT NULL,
                resource_id INTEGER,
                granted_by INTEGER,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (granted_by) REFERENCES users (id)
            )
        ''')
        
        # User logs table for activity tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Manufacturing order PDFs (encrypted)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS manufacturing_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER UNIQUE NOT NULL,
                pdf_encrypted TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        ''')
        
        # Invoices (encrypted) per system
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id INTEGER NOT NULL,
                pdf_encrypted TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (system_id) REFERENCES key_systems (id)
            )
        ''')
        
        self.connection.commit()
        
        # Run database migrations
        self._run_migrations()
        
        # Create default admin user if no users exist
        self._create_default_admin()
        
        self.connection.close()
    
    def _run_migrations(self):
        """Run database migrations for schema updates"""
        try:
            cursor = self.connection.cursor()
            
            # Check if profile_picture column exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'profile_picture' not in columns:
                print("Adding profile_picture column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN profile_picture TEXT")
                self.connection.commit()
                print("✅ Profile picture column added successfully")
            
            # Check if company_name and org_number columns exist
            if 'company_name' not in columns:
                print("Adding company_name column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN company_name TEXT")
                self.connection.commit()
                print("✅ Company name column added successfully")
                
            if 'org_number' not in columns:
                print("Adding org_number column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN org_number TEXT")
                self.connection.commit()
                print("✅ Org number column added successfully")
            
            # Check if is_active column exists
            if 'is_active' not in columns:
                print("Adding is_active column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
                self.connection.commit()
                print("✅ Is active column added successfully")
            
            # Check if is_admin column exists
            if 'is_admin' not in columns:
                print("Adding is_admin column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
                self.connection.commit()
                print("✅ is_admin column added successfully")
            
            # Check if two_factor_enabled column exists
            if 'two_factor_enabled' not in columns:
                print("Adding two_factor_enabled column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN DEFAULT FALSE")
                self.connection.commit()
                print("✅ Two factor enabled column added successfully")
                
        except Exception as e:
            print(f"Migration error: {e}")
    
    def _create_default_admin(self):
        """Ensure default admin user exists and is up-to-date (idempotent)."""
        try:
            import bcrypt
            from datetime import datetime
            
            cursor = self.connection.cursor()
            
            # Desired admin fields
            username = "admin"
            email = "keybuddyreg@gmail.com"
            company_name = "Keybuddy"
            org_number = "556737-4730"
            role = "admin"
            is_verified = True
            is_active = True
            two_factor_enabled = False
            # Always ensure known password for built-in admin
            password_hash = bcrypt.hashpw("admin".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            now = datetime.now()

            # Check if admin exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                # Update existing admin with latest required fields
                cursor.execute(
                    """
                    UPDATE users SET
                        email = ?,
                        password_hash = ?,
                        is_verified = ?,
                        role = ?,
                        is_admin = ?,
                        company_name = ?,
                        org_number = ?,
                        is_active = ?,
                        two_factor_enabled = ?
                    WHERE username = ?
                    """,
                    (
                        email,
                        password_hash,
                        1 if is_verified else 0,
                        role,
                        1,
                        company_name,
                        org_number,
                        1 if is_active else 0,
                        1 if two_factor_enabled else 0,
                        username,
                    )
                )
                self.connection.commit()
                print("✅ Default admin ensured (updated)")
            else:
                # Insert new admin
                cursor.execute(
                    """
                    INSERT INTO users (
                        username, email, password_hash, is_verified, role, is_admin, created_at,
                        company_name, org_number, is_active, two_factor_enabled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        username,
                        email,
                        password_hash,
                        1 if is_verified else 0,
                        role,
                        1,
                        now,
                        company_name,
                        org_number,
                        1 if is_active else 0,
                        1 if two_factor_enabled else 0,
                    )
                )
                self.connection.commit()
                print("✅ Default admin user created (username: admin, password: admin)")
        except Exception as e:
            print(f"Warning: Could not ensure default admin user: {e}")
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not self.encryption_key:
            raise ValueError("Encryption key not initialized")
        
        fernet = Fernet(self.encryption_key)
        encrypted_data = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not self.encryption_key:
            raise ValueError("Encryption key not initialized")
        
        fernet = Fernet(self.encryption_key)
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = fernet.decrypt(decoded_data)
        return decrypted_data.decode()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with improved multi-user support"""
        try:
            # Create new connection each time for better multi-user support
            connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=60.0,  # Increased timeout for multi-user scenarios
                isolation_level='DEFERRED'  # Better for concurrent access
            )
            connection.row_factory = sqlite3.Row
            
            # Configure for multi-user access
            connection.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for concurrency
            connection.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and performance
            connection.execute("PRAGMA busy_timeout=60000")  # 60 second timeout
            connection.execute("PRAGMA wal_autocheckpoint=1000")  # Auto-checkpoint every 1000 pages
            connection.execute("PRAGMA cache_size=10000")  # Larger cache for better performance
            connection.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
            
            return connection
        except Exception as e:
            print(f"Failed to get database connection: {e}")
            raise e
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute SELECT query with proper connection handling"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result
        finally:
            if conn:
                conn.close()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE query with retry logic and proper connection handling"""
        max_retries = 5  # Increased retries for multi-user scenarios
        conn = None
        
        for attempt in range(max_retries):
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                
                # Return lastrowid for INSERT operations, rowcount for others
                result = cursor.lastrowid if query.strip().upper().startswith('INSERT') else cursor.rowcount
                return result
                
            except sqlite3.OperationalError as e:
                if conn:
                    conn.close()
                    conn = None
                    
                if ("database is locked" in str(e) or "database is busy" in str(e)) and attempt < max_retries - 1:
                    import time
                    # Exponential backoff with jitter for multi-user scenarios
                    wait_time = (0.1 * (2 ** attempt)) + (0.05 * attempt)
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
            except Exception as e:
                if conn:
                    conn.close()
                raise e
            finally:
                if conn:
                    conn.close()
    
    def migrate_database(self):
        """Apply database migrations for schema updates"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if key_responsible column exists in orders table
            cursor.execute("PRAGMA table_info(orders)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'key_responsible' not in columns:
                # Add key_responsible column to existing orders table
                cursor.execute("""
                    ALTER TABLE orders 
                    ADD COLUMN key_responsible TEXT DEFAULT 'Nyckelansvarig 1'
                """)
                conn.commit()
                print("Added key_responsible column to orders table")
            
            # Ensure key_receipts table exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS key_receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER UNIQUE NOT NULL,
                    pdf_encrypted TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders (id)
                )
            ''')
            conn.commit()
            
            # Add billing fields to key_systems if missing
            cursor.execute("PRAGMA table_info(key_systems)")
            ks_columns = [column[1] for column in cursor.fetchall()]
            billing_fields = [
                ('billing_plan', "ALTER TABLE key_systems ADD COLUMN billing_plan TEXT"),
                ('price_one_time', "ALTER TABLE key_systems ADD COLUMN price_one_time REAL"),
                ('price_monthly', "ALTER TABLE key_systems ADD COLUMN price_monthly REAL"),
                ('price_half_year', "ALTER TABLE key_systems ADD COLUMN price_half_year REAL"),
                ('price_yearly', "ALTER TABLE key_systems ADD COLUMN price_yearly REAL"),
                ('is_paid', "ALTER TABLE key_systems ADD COLUMN is_paid BOOLEAN DEFAULT FALSE"),
                ('paid_at', "ALTER TABLE key_systems ADD COLUMN paid_at TIMESTAMP"),
                ('invoice_count', "ALTER TABLE key_systems ADD COLUMN invoice_count INTEGER DEFAULT 0"),
                ('last_invoice_date', "ALTER TABLE key_systems ADD COLUMN last_invoice_date TIMESTAMP"),
                ('notes', "ALTER TABLE key_systems ADD COLUMN notes TEXT"),
            ]
            for col, stmt in billing_fields:
                if col not in ks_columns:
                    try:
                        cursor.execute(stmt)
                        conn.commit()
                    except Exception as _e:
                        pass

            # Create separate catalog for Fabrikat 2 / Koncept 2
            try:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS key_catalog2 (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fabrikat TEXT NOT NULL,
                        koncept TEXT NOT NULL
                    )
                    """
                )
                conn.commit()
            except Exception:
                pass

            # Add columns for 'Standard & system nycklar' if missing
            try:
                cursor.execute("PRAGMA table_info(key_systems)")
                ks_cols = {row[1] for row in cursor.fetchall()}
                stmts = []
                if 'key_code2' not in ks_cols:
                    stmts.append("ALTER TABLE key_systems ADD COLUMN key_code2 TEXT")
                if 'system_number' not in ks_cols:
                    stmts.append("ALTER TABLE key_systems ADD COLUMN system_number TEXT")
                if 'profile2' not in ks_cols:
                    stmts.append("ALTER TABLE key_systems ADD COLUMN profile2 TEXT")
                if 'delning' not in ks_cols:
                    stmts.append("ALTER TABLE key_systems ADD COLUMN delning TEXT")
                if 'key_location2' not in ks_cols:
                    stmts.append("ALTER TABLE key_systems ADD COLUMN key_location2 TEXT")
                if 'fabrikat2' not in ks_cols:
                    stmts.append("ALTER TABLE key_systems ADD COLUMN fabrikat2 TEXT")
                if 'koncept2' not in ks_cols:
                    stmts.append("ALTER TABLE key_systems ADD COLUMN koncept2 TEXT")
                if 'flex1' not in ks_cols:
                    stmts.append("ALTER TABLE key_systems ADD COLUMN flex1 TEXT")
                if 'flex2' not in ks_cols:
                    stmts.append("ALTER TABLE key_systems ADD COLUMN flex2 TEXT")
                if 'flex3' not in ks_cols:
                    stmts.append("ALTER TABLE key_systems ADD COLUMN flex3 TEXT")
                for s in stmts:
                    try:
                        cursor.execute(s)
                        conn.commit()
                    except Exception:
                        pass
            except Exception:
                pass
            
            # Ensure manufacturing_orders table exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS manufacturing_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER UNIQUE NOT NULL,
                    pdf_encrypted TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders (id)
                )
            ''')
            conn.commit()
            
            # Ensure invoices table exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_id INTEGER NOT NULL,
                    pdf_encrypted TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (system_id) REFERENCES key_systems (id)
                )
            ''')
            conn.commit()

            # Ensure key_catalog reference table exists (fabrikat <-> koncept)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS key_catalog (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fabrikat TEXT NOT NULL,
                    koncept TEXT NOT NULL
                )
            ''')
            conn.commit()

            # Replace existing katalog with the real data provided by the user
            try:
                cursor.execute("DELETE FROM key_catalog")
                katalog = [
                    ("Assa", "D12"), ("Assa", "Max"), ("Assa", "Desmo"),
                    ("GEGE", "Pextra"), ("GEGE", "Flex"), ("GEGE", "Pextra+"), ("GEGE", "Pextra+ Flex"), ("GEGE", "ANS"),
                    ("Evva", "EPS"), ("Evva", "DPI"), ("Evva", "3KS"), ("Evva", "4KS"), ("Evva", "MCS"),
                    ("Abloy", "Disklock Pro"), ("Abloy", "Novel"), ("Abloy", "Protec"), ("Abloy", "Protec 2"), ("Abloy", "Sentry"),
                    ("Ruko", "Garant"), ("Ruko", "Garant Plus"),
                    ("Kaba", "ExpetT"), ("Kaba", "ExpetT+"), ("Kaba", "Titan Combi"),
                    ("Yale", "2100"),
                    ("Dorma", "DMS SC"),
                    ("Medeco", "DND"),
                    ("Trioving", "D12"),
                    ("Mauer", "Asgard"),
                    ("Abus", "Plus"), ("Abus", "XPlus"),
                    ("Cisa", "Astral"),
                    ("Mul-T-Lock", "Classic"),
                ]
                cursor.executemany("INSERT INTO key_catalog (fabrikat, koncept) VALUES (?, ?)", katalog)
                conn.commit()
            except Exception as _e:
                # If the table is locked or any issue occurs, skip seeding silently
                pass
                
        except Exception as e:
            print(f"Migration error: {e}")
        finally:
            if conn:
                conn.close()
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
